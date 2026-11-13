# Real iPhone acceptance test — Under the Tree 0.10.1 Web / PWA

**Devices:** one Android phone with the 0.10.1 APK ("Android Dad") and one iPhone ("iPhone"). A second iPhone or an iPad helps for step 16–17.
**Before you start:** the Hosting site is deployed (WEB_DEPLOYMENT.md) and you have the URL. Write PASS / FAIL and a note beside every step. Any FAIL: stop and screenshot.

| # | Step | Expected |
|---|------|----------|
| 1 | On the iPhone, open the URL in **Safari**. | App loads. If music is on: "Enter Under the Tree" screen. A small "Install Under the Tree" button is at the bottom left. |
| 2 | Tap **Install Under the Tree** → read the steps → **Got it**. Then Share → **Add to Home Screen** → **Add**. | Icon appears on the Home Screen (pine green, gift tag with tree). Label may be cut short ("Under the T…") — expected. |
| 3 | Close Safari. Launch from the **Home Screen icon**. | Opens full screen, no Safari address bar. Green header clears the Dynamic Island/notch; bottom tabs clear the home indicator. No install button shown. |
| 4 | Tap **Enter** (if shown). Join my family → paste the UTT2 code from Android Dad → continue. | Joins "Family Christmas List" (your family name). Do **not** join in Safari first — the installed app keeps its own sign-in. |
| 5 | Pick your existing profile (or "I'm new" only if you are not on the list). | Header shows "This phone: <your name>". No second copy of you appears in Family. |
| 6 | Swipe the app away completely (app switcher). | — |
| 7 | Reopen from the Home Screen. | Same name in the header, straight into the family. No join screen. |
| 8 | My List → add a wish "iPhone test wish". | Saves, appears on My List. |
| 9 | Android Dad: Refresh → Family → your name. | "iPhone test wish" is there. |
| 10 | Android Dad reserves it, then marks it **Bought**. | Moves to Dad's Shopping. |
| 11 | iPhone: Refresh, look at My List and every tab. | Wish looks exactly as before. No "reserved", "bought", badge, count, or change of any kind. |
| 12 | iPhone: Family → Dad → **Gift Ideas** → add "iPhone secret idea". | Saves under Ideas for Dad. |
| 13 | Android Dad: Refresh, check every tab and his own list. | Nothing about the idea anywhere — no item, no count, no "ideas" tab for himself. |
| 14 | iPhone: reserve the idea, then mark it Bought. Android Dad refreshes again. | iPhone Shopping shows it. Dad still sees nothing. |
| 15 | Android Dad reserves one of *another* person's wishes. iPhone: Refresh → try to reserve the same wish. | iPhone shows it as taken / not available; the iPhone cannot take it. Undo Bought on the idea from step 14 puts it back to reserved on the iPhone only. |
| 16 | Android Dad: Settings → Add Child "Emma", add yourself (iPhone person) as a second manager. Create Emma's setup code. | Emma appears with both managers. Dad sees a 20-character code (5 groups of 4). |
| 17 | Second iPhone/iPad (installed as in 1–3): Join with UTT2 → **Claim my existing profile** → Emma → enter the setup code. Also try a wrong code first. | Wrong code refused, nothing changes. Right code: header says Emma. Family shows **one** Emma. Emma's existing wishes still there. Ideas for Emma: not visible on Emma's device. Dad and you can still edit Emma's Wish List. |
| 18 | If the iPhone person is an organizer: Settings → Manage family → try promote/demote, Disconnect, Remove, Restore on a test member. | Allowed actions work; protected ones (e.g. removing the last organizer) are refused with a clear message. Ideas for yourself stay invisible even as organizer. |
| 19 | Settings → Theme → switch to **Santa Chases Rudolph**, then back to **Classic Christmas**. Also turn on iOS Reduce Motion and relaunch. | Both themes work; snow runs smoothly. With Reduce Motion: no opening scene, app still usable. |
| 20 | Music on: relaunch, tap **Enter**. Then Settings → music off, relaunch. | With the ringer on: carol plays after Enter. Silent switch on: no sound, no error. Music off: no Enter screen at all. |
| 21 | Ask whoever deploys to deploy a new build. Reopen the installed app (bring it to the front after >30 min, or relaunch). | "An Under the Tree update is ready." → **Update** reloads into the new build (Settings → About shows the new build number). With a wish form open, Update refuses until you Cancel. You stay signed in. |

**Also check:** Settings → About reads "Under the Tree 0.10.1 / Web / PWA (installed)". Typing in any field does not zoom the page. Long product titles wrap. Cancel is visible on every sheet with the keyboard open.
