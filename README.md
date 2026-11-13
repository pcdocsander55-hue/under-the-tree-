# Under the Tree

Under the Tree is a free Christmas wish-list app I originally put together for my own family.

I wanted something simple: everybody can keep a wish list, people can claim gifts so we do not buy the same thing twice, and we can suggest gift ideas for someone without that person seeing them.

It turned into a much better app than I expected, so I decided to share it. If another family finds it useful, that is really the whole point.

## How it was built

One thing I want to be upfront about: **Under the Tree is an AI-assisted app.**

I came up with what I wanted the app to do, tested it, made the decisions, and kept pushing it in the direction I wanted. AI assistants did a lot of the coding and helped me work through problems along the way.

I think that is worth saying because it is a big part of how this app came together. This project would not exist in its current form without AI-assisted development, and I am not interested in pretending otherwise.

## What it does

- Create and share Christmas wish lists with your family.
- Add **Gift Ideas** for someone without spoiling the surprise for them.
- Reserve a gift so other family members know somebody is taking care of it.
- Mark gifts as bought while keeping that information hidden from the person receiving them.
- Use 48-hour holds so something is not tied up forever if somebody changes their mind.
- Add children or other family members whose lists are managed by someone else.
- Let a managed family member claim their own profile later without creating a duplicate.
- Use it on Android or in a web browser.

## Try it

### Android

Download the latest APK from the GitHub Releases page:

**[Download Under the Tree for Android](https://github.com/pcdocsander55-hue/under-the-tree-/releases/latest)**

If you already have Under the Tree installed, install the new APK over the existing copy instead of uninstalling it first.

### Web, iPhone and iPad

You can use the web version here:

**[under-the-tree-1ee02.web.app](https://under-the-tree-1ee02.web.app)**

On an iPhone or iPad, open it in Safari and use **Add to Home Screen** if you want it to work more like a regular app.

## A few things I cared about when building it

I did not want this turning into another app full of ads and tracking.

There are **no ads, no behavioral tracking, and no selling your data**. The app stores the information it needs to make the family lists, gift ideas, reservations, and other features work.

I also wanted the surprise part of Christmas to actually stay a surprise. Gift Ideas for you are hidden from you, even though the rest of the family can see and work with them.

## Support Under the Tree

Under the Tree is free and I intend to keep it that way. If your family finds it useful and you would like to help with hosting and future development, donations are appreciated but never required.

**[Buy me a coffee](https://www.buymeacoffee.com/Sander55)**

## Source code

The source is here because I wanted the app to stay available and give other people the chance to improve it.

The main pieces are:

- `shared/index.html` — the shared app itself
- `web/` — the web/PWA version
- `android/` — the Android wrapper
- `build-android.sh` — Android build script
- `baseline/` — baseline files and Firestore rules
- `tests/` — automated tests
- `tools/` — project utilities

If you fork the project for your own use, set up your own Firebase project rather than using the live Under the Tree backend.

## Bugs, ideas and improvements

If you find something that does not work, open an Issue.

If you have an idea that would make the app better, I am open to that too. This started as a family project, and I would like to keep making it useful without turning it into something complicated just for the sake of adding features.

Pull requests are welcome.

## License

Under the Tree is licensed under the **GNU General Public License v3.0 (GPL-3.0-only)**.

You are welcome to use, modify, and share the code under the terms of the GPL. If you distribute a modified version, the GPL requires the corresponding source code to remain available under the same license.

See [LICENSE](LICENSE) for the full license text.
