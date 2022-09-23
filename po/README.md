# Contribute translations using Damned Lies

This app can be translated using GNOME's Damned Lies website.

- Visit [the Damned Lies website](https://l10n.gnome.org/) and create an account.
- Visit [the Damned Lies page for this project](https://l10n.gnome.org/module/gfeeds/) and choose the language you want to translate to.
  - If your language is not listed, open an issue on the project's [issue tracker](https://gitlab.gnome.org/World/gfeeds/-/issues) asking to add it.
- On the page, submit a _Reserve for translation_ action, so that others will not work on a new translation when you're already working on one.
- Download the latest PO file from the language page using the download button (not the POT file).
- Edit your translation by opening the PO file with a translation editor like [Lokalize](https://apps.kde.org/lokalize/) or [Gtranslator](https://flathub.org/apps/details/org.gnome.Gtranslator).
- Save your edited PO file, then go back to the language page.
- Submit an _Upload new translation_ action, attaching your edited PO file.
- Interact with the language theme, reading their comments and making changes until your translation gets approved and merged into the repository.

## Manually adding translation

**NOTE: this method is considered legacy, always prefer using Damned Lies istead**

First, run the script `update_potfiles.sh` like this, where `LANGUAGE` is the language code that you want to add or update (`it`: italian, `fr`: french, `es`: spanish...):

```bash
cd po
./update_potfiles.sh LANGUAGE
```

It will ask for an email, provide yours if you want and it will be used to credit you. It's historically been used to report issues in the translation for a specific language, but nowadays with issue systems and easier bug reporting than ever it's not really necessary.

Finally edit the `.po` file that was just created with the language code you used. You can use a normal text editor or a simpler tool like **lokalize** or **poedit** (you can probably find both in your distribution's repositories).

If you need any help, feel free to open an issue.
