package com.undertree.family;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.graphics.Color;
import android.media.AudioAttributes;
import android.media.AudioManager;
import android.media.MediaPlayer;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.OpenableColumns;
import android.util.Log;
import android.webkit.ConsoleMessage;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.SocketTimeoutException;
import java.net.URL;
import java.net.UnknownHostException;
import java.nio.charset.Charset;
import java.util.Iterator;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends Activity {
    private static final String TAG = "UnderTheTree";
    private static final int MAX_BODY = 3 * 1024 * 1024;

    private WebView web;
    private SharedPreferences prefs;
    private final Handler ui = new Handler(Looper.getMainLooper());
    private final ExecutorService pool = Executors.newFixedThreadPool(4);
    private volatile String pendingShared = null;
    private boolean pageReady = false;
    private ClipboardManager clipboard;

    // 0.7.0 music: a song the person picked is copied into this app's private storage and played here.
    private static final int REQ_SONG = 41;
    private static final long MAX_SONG_BYTES = 40L * 1024 * 1024;
    private MediaPlayer player;
    private float fadeLevel = 0.8f;
    private final Runnable songFade = new Runnable() {
        @Override
        public void run() {
            if (player == null) return;
            fadeLevel -= 0.04f;
            if (fadeLevel <= 0.02f) { finishSong(null); return; }
            try { player.setVolume(fadeLevel, fadeLevel); } catch (Exception ignored) { }
            ui.postDelayed(this, 150);
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        prefs = getSharedPreferences("utt", MODE_PRIVATE);
        clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        captureShare(getIntent());

        web = new WebView(this);
        web.setBackgroundColor(Color.parseColor("#F3F6F4"));
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setAllowFileAccess(false);          // android_asset still loads; no other file access
        s.setAllowContentAccess(false);
        s.setSupportMultipleWindows(false);
        s.setMediaPlaybackRequiresUserGesture(false);  // 0.7.0: the built-in carol plays when the app opens (the page checks silent/vibrate and the Settings switch)

        web.addJavascriptInterface(new Bridge(), "UTTNative");
        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                if (url != null && url.startsWith("file:///android_asset/")) return false;
                openUrl(url);
                return true;
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                pageReady = true;
            }
        });
        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onConsoleMessage(ConsoleMessage m) {
                Log.i(TAG, "js: " + m.message() + " (" + m.sourceId() + ":" + m.lineNumber() + ")");
                return true;
            }
        });
        setContentView(web);
        web.loadUrl("file:///android_asset/www/index.html");
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        captureShare(intent);
        if (pageReady && pendingShared != null) {
            web.evaluateJavascript("window.UTT_onShared && window.UTT_onShared()", null);
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (web != null) web.onResume();
        if (pageReady) web.evaluateJavascript("window.UTT_onResume && window.UTT_onResume()", null);
    }

    @Override
    protected void onPause() {
        finishSong(null);
        if (web != null && pageReady) web.evaluateJavascript("window.UTT_onPause && window.UTT_onPause()", null);
        if (web != null) web.onPause();
        super.onPause();
    }

    @Override
    protected void onDestroy() {
        ui.removeCallbacks(songFade);
        if (player != null) { try { player.release(); } catch (Exception ignored) { } player = null; }
        pool.shutdownNow();
        if (web != null) {
            web.removeJavascriptInterface("UTTNative");
            web.destroy();
            web = null;
        }
        super.onDestroy();
    }

    @Override
    public void onBackPressed() {
        if (!pageReady || web == null) {
            super.onBackPressed();
            return;
        }
        web.evaluateJavascript("(window.UTT_back && window.UTT_back()) ? 'yes' : 'no'", new ValueCallback<String>() {
            @Override
            public void onReceiveValue(String value) {
                if (value == null || !value.contains("yes")) MainActivity.super.onBackPressed();
            }
        });
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != REQ_SONG) return;
        if (resultCode != RESULT_OK || data == null || data.getData() == null) return;  // picker closed: nothing changes
        final Uri uri = data.getData();
        pool.execute(new Runnable() {
            @Override
            public void run() { copySong(uri); }
        });
    }

    private File songFile() { return new File(getFilesDir(), "song.audio"); }

    /** Copies the picked audio into private storage so it still plays after the picker's permission lapses. Never throws. */
    private void copySong(Uri uri) {
        String name = "your song";
        Cursor c = null;
        try {
            c = getContentResolver().query(uri, new String[]{OpenableColumns.DISPLAY_NAME, OpenableColumns.SIZE}, null, null, null);
            if (c != null && c.moveToFirst()) {
                String n = c.getString(0);
                if (n != null && n.length() > 0) name = n;
                if (!c.isNull(1) && c.getLong(1) > MAX_SONG_BYTES) { songResult(null, "That file is over 40 MB. Pick a shorter song."); return; }
            }
        } catch (Exception ignored) {
        } finally {
            if (c != null) c.close();
        }
        File tmp = new File(getFilesDir(), "song.tmp");
        InputStream in = null;
        OutputStream out = null;
        try {
            in = getContentResolver().openInputStream(uri);
            if (in == null) throw new IOException("the file could not be opened");
            out = new FileOutputStream(tmp);
            byte[] buf = new byte[65536];
            long total = 0;
            int n;
            while ((n = in.read(buf)) != -1) {
                total += n;
                if (total > MAX_SONG_BYTES) throw new IOException("That file is over 40 MB. Pick a shorter song.");
                out.write(buf, 0, n);
            }
            out.close();
            out = null;
            File dest = songFile();
            if (dest.exists() && !dest.delete()) throw new IOException("the old song could not be replaced");
            if (!tmp.renameTo(dest)) throw new IOException("the song could not be saved");
            prefs.edit().putString("utt.songName", name).commit();
            songResult(name, null);
        } catch (Exception e) {
            tmp.delete();
            songResult(null, e.getMessage() == null ? e.getClass().getSimpleName() : e.getMessage());
        } finally {
            try { if (in != null) in.close(); } catch (Exception ignored) { }
            try { if (out != null) out.close(); } catch (Exception ignored) { }
        }
    }

    private void songResult(String name, String error) {
        final JSONObject o = new JSONObject();
        try {
            if (name != null) o.put("name", name);
            if (error != null) o.put("error", error);
        } catch (Exception ignored) { }
        ui.post(new Runnable() {
            @Override
            public void run() {
                if (web != null && pageReady) web.evaluateJavascript("window.UTT_onSong && window.UTT_onSong(" + JSONObject.quote(o.toString()) + ")", null);
            }
        });
    }

    /** Main thread. Plays the picked song for up to maxMs, fading out over the last 3 seconds. */
    private void startSong(int maxMs) {
        ui.removeCallbacks(songFade);
        if (player != null) { try { player.release(); } catch (Exception ignored) { } player = null; }
        File f = songFile();
        if (!f.exists()) { finishSong("The chosen song file is missing. Choose it again in Settings."); return; }
        try {
            MediaPlayer mp = new MediaPlayer();
            mp.setAudioAttributes(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA).setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).build());
            mp.setDataSource(f.getAbsolutePath());
            mp.setOnCompletionListener(new MediaPlayer.OnCompletionListener() {
                @Override
                public void onCompletion(MediaPlayer m) { finishSong(null); }
            });
            mp.setOnErrorListener(new MediaPlayer.OnErrorListener() {
                @Override
                public boolean onError(MediaPlayer m, int what, int extra) {
                    finishSong("This phone couldn't play that file (" + what + "/" + extra + ").");
                    return true;
                }
            });
            mp.prepare();
            fadeLevel = 0.8f;
            mp.setVolume(fadeLevel, fadeLevel);
            mp.start();
            player = mp;
            int ms = Math.max(4000, Math.min(maxMs, 120000));
            ui.postDelayed(songFade, ms - 3000);
        } catch (Exception e) {
            finishSong("This phone couldn't play that file: " + e.getMessage());
        }
    }

    /** Main thread. Stops the picked song if playing and tells the page (with the error, if any). */
    private void finishSong(String error) {
        ui.removeCallbacks(songFade);
        boolean was = player != null;
        if (player != null) {
            try { player.stop(); } catch (Exception ignored) { }
            try { player.release(); } catch (Exception ignored) { }
            player = null;
        }
        if ((was || error != null) && web != null && pageReady) {
            JSONObject o = new JSONObject();
            try { if (error != null) o.put("error", error); } catch (Exception ignored) { }
            web.evaluateJavascript("window.UTT_onMusicEnd && window.UTT_onMusicEnd(" + JSONObject.quote(o.toString()) + ")", null);
        }
    }

    private void captureShare(Intent i) {
        if (i == null || !Intent.ACTION_SEND.equals(i.getAction())) return;
        String text = i.getStringExtra(Intent.EXTRA_TEXT);
        if (text == null) return;
        String subject = i.getStringExtra(Intent.EXTRA_SUBJECT);
        pendingShared = (subject != null && !text.contains(subject)) ? subject + "\n" + text : text;
    }

    private void openUrl(String url) {
        if (url == null) return;
        String lower = url.toLowerCase();
        if (!lower.startsWith("https://") && !lower.startsWith("http://")) return;
        try {
            startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
        } catch (ActivityNotFoundException e) {
            Toast.makeText(this, "No app on this phone can open that link.", Toast.LENGTH_LONG).show();
        }
    }

    private void deliver(final String id, final String json) {
        ui.post(new Runnable() {
            @Override
            public void run() {
                if (web == null) return;
                String js = "window.UTT_onNative(" + JSONObject.quote(id) + "," + JSONObject.quote(json) + ")";
                js = js.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029");
                web.evaluateJavascript(js, null);
            }
        });
    }

    /** One HTTP call. Follows up to 6 redirects by hand so https->https hops across hosts work. Never throws. */
    private String doRequest(String method, String urlStr, String headersJson, String body) {
        JSONObject out = new JSONObject();
        HttpURLConnection conn = null;
        try {
            JSONObject headers = (headersJson == null || headersJson.length() == 0) ? new JSONObject() : new JSONObject(headersJson);
            String current = urlStr;
            String m = method == null ? "GET" : method.toUpperCase();
            String sendBody = body;
            for (int hop = 0; hop < 7; hop++) {
                URL u = new URL(current);
                String proto = u.getProtocol();
                if (!"https".equals(proto) && !"http".equals(proto)) {
                    out.put("error", "Only web links (https://) can be read.");
                    return out.toString();
                }
                conn = (HttpURLConnection) u.openConnection();
                conn.setInstanceFollowRedirects(false);
                conn.setConnectTimeout(15000);
                conn.setReadTimeout(20000);
                conn.setUseCaches(false);
                conn.setRequestMethod(m);
                Iterator<String> keys = headers.keys();
                while (keys.hasNext()) {
                    String k = keys.next();
                    conn.setRequestProperty(k, headers.getString(k));
                }
                if (sendBody != null && sendBody.length() > 0 && !"GET".equals(m)) {
                    byte[] bytes = sendBody.getBytes("UTF-8");
                    conn.setDoOutput(true);
                    conn.setFixedLengthStreamingMode(bytes.length);
                    OutputStream os = conn.getOutputStream();
                    os.write(bytes);
                    os.close();
                }
                int code = conn.getResponseCode();
                if (code >= 300 && code < 400 && code != 304) {
                    String loc = conn.getHeaderField("Location");
                    if (loc != null && hop < 6) {
                        current = new URL(u, loc).toString();
                        if (code == 303 || ((code == 301 || code == 302) && "POST".equals(m))) {
                            m = "GET";
                            sendBody = null;
                        }
                        conn.disconnect();
                        conn = null;
                        continue;
                    }
                    if (loc != null) {
                        out.put("error", "The link redirected too many times.");
                        return out.toString();
                    }
                }
                InputStream is = code >= 400 ? conn.getErrorStream() : conn.getInputStream();
                String text = is == null ? "" : readLimited(is, charsetOf(conn.getContentType()));
                out.put("status", code);
                out.put("body", text);
                out.put("finalUrl", current);
                return out.toString();
            }
            out.put("error", "The link redirected too many times.");
        } catch (Exception e) {
            try { out.put("error", describe(e, urlStr)); } catch (Exception ignored) { }
            Log.w(TAG, "request failed: " + e);
        } finally {
            if (conn != null) conn.disconnect();
        }
        return out.toString();
    }

    private static String describe(Exception e, String url) {
        String msg = String.valueOf(e.getMessage());
        if (e instanceof UnknownHostException) return "No connection, or the web address doesn't exist.";
        if (e instanceof SocketTimeoutException) return "The site took too long to answer.";
        if (e instanceof javax.net.ssl.SSLException) return "A secure connection to the site couldn't be made.";
        if (msg.contains("Cleartext") || msg.contains("CLEARTEXT")) return "Android blocks plain http:// links. Use the https:// version.";
        if (e instanceof IOException) return "Network problem: " + msg;
        return "Unexpected problem (" + e.getClass().getSimpleName() + "): " + msg;
    }

    private static Charset charsetOf(String contentType) {
        if (contentType != null) {
            for (String part : contentType.split(";")) {
                String p = part.trim();
                if (p.toLowerCase().startsWith("charset=")) {
                    String name = p.substring(8).replace("\"", "").trim();
                    try {
                        if (Charset.isSupported(name)) return Charset.forName(name);
                    } catch (Exception ignored) { }
                }
            }
        }
        return Charset.forName("UTF-8");
    }

    private static String readLimited(InputStream is, Charset cs) throws IOException {
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        byte[] buf = new byte[16384];
        int n;
        try {
            while ((n = is.read(buf)) != -1) {
                int room = MAX_BODY - bos.size();
                if (room <= 0) break;
                bos.write(buf, 0, Math.min(n, room));
            }
        } finally {
            is.close();
        }
        return new String(bos.toByteArray(), cs);
    }

    /** Everything the page may call. Runs on WebView's bridge thread. */
    public class Bridge {
        @JavascriptInterface
        public String getItem(String key) { return prefs.getString(key, null); }

        @JavascriptInterface
        public boolean setItem(String key, String value) { return prefs.edit().putString(key, value).commit(); }

        @JavascriptInterface
        public boolean removeItem(String key) { return prefs.edit().remove(key).commit(); }

        @JavascriptInterface
        public String consumeSharedText() {
            String t = pendingShared;
            pendingShared = null;
            return t == null ? "" : t;
        }

        @JavascriptInterface
        public void request(final String id, final String method, final String url, final String headersJson, final String body) {
            pool.execute(new Runnable() {
                @Override
                public void run() { deliver(id, doRequest(method, url, headersJson, body)); }
            });
        }

        @JavascriptInterface
        public void openExternal(final String url) {
            ui.post(new Runnable() {
                @Override
                public void run() { openUrl(url); }
            });
        }

        @JavascriptInterface
        public void shareText(final String text) {
            ui.post(new Runnable() {
                @Override
                public void run() {
                    Intent send = new Intent(Intent.ACTION_SEND);
                    send.setType("text/plain");
                    send.putExtra(Intent.EXTRA_TEXT, text);
                    try {
                        startActivity(Intent.createChooser(send, "Send invite"));
                    } catch (ActivityNotFoundException e) {
                        Toast.makeText(MainActivity.this, "No app on this phone can share text.", Toast.LENGTH_LONG).show();
                    }
                }
            });
        }

        @JavascriptInterface
        public boolean copyText(String text) {
            try {
                ClipboardManager cm = clipboard;
                if (cm == null) return false;
                cm.setPrimaryClip(ClipData.newPlainText("Under the Tree invite", text));
                return true;
            } catch (Exception e) {
                return false;
            }
        }

        @JavascriptInterface
        public String appVersion() { return "0.10.1"; }

        /** True when the phone is on silent or vibrate: the page then plays no music. */
        @JavascriptInterface
        public boolean ringerQuiet() {
            AudioManager am = (AudioManager) getSystemService(Context.AUDIO_SERVICE);
            return am != null && am.getRingerMode() != AudioManager.RINGER_MODE_NORMAL;
        }

        @JavascriptInterface
        public String songName() { return songFile().exists() ? prefs.getString("utt.songName", "your song") : ""; }

        @JavascriptInterface
        public void pickSong() {
            ui.post(new Runnable() {
                @Override
                public void run() {
                    Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                    i.addCategory(Intent.CATEGORY_OPENABLE);
                    i.setType("audio/*");
                    try {
                        startActivityForResult(i, REQ_SONG);
                    } catch (ActivityNotFoundException e) {
                        songResult(null, "This phone has no file picker for music.");
                    }
                }
            });
        }

        @JavascriptInterface
        public boolean clearSong() {
            ui.post(new Runnable() {
                @Override
                public void run() { finishSong(null); }
            });
            File f = songFile();
            boolean ok = !f.exists() || f.delete();
            prefs.edit().remove("utt.songName").commit();
            return ok;
        }

        @JavascriptInterface
        public boolean playSong(final int maxMs) {
            if (!songFile().exists()) return false;
            ui.post(new Runnable() {
                @Override
                public void run() { startSong(maxMs); }
            });
            return true;
        }

        @JavascriptInterface
        public void stopSong() {
            ui.post(new Runnable() {
                @Override
                public void run() { finishSong(null); }
            });
        }
    }
}
