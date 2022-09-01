from gettext import gettext as _
from os import remove, listdir
from os.path import isfile, abspath, join
from gi.repository import Gtk, Adw
from gfeeds.confManager import ConfManager
from gfeeds.base_preferences import (
    MPreferencesPage, MPreferencesGroup, PreferencesButtonRow,
    PreferencesComboRow, PreferencesSpinButtonRow, PreferencesToggleRow,
    PreferencesEntryRow, PreferencesFontChooserRow
)
from typing import Optional


def show_preferences_window(parent_win, *args):
    settings_win = PreferencesWindow(parent_win)
    settings_win.present()


class GeneralPreferencesPage(MPreferencesPage):
    def __init__(self):
        super().__init__(
            title=_('General'), icon_name='preferences-other-symbolic',
            pref_groups=[
                MPreferencesGroup(
                    title=_('General preferences'), rows=[
                        PreferencesToggleRow(
                            title=_('Show newer articles first'),
                            conf_key='new_first',
                            signal='gfeeds_new_first_changed'
                        ),
                        PreferencesToggleRow(
                            title=_('Open links in your browser'),
                            conf_key='open_links_externally'
                        ),
                        PreferencesToggleRow(
                            title=_('Use external video player for YouTube'),
                            subtitle=_(
                                'Requires youtube-dl and a compatible '
                                'video player'
                            ),
                            conf_key='open_youtube_externally'
                        ),
                        PreferencesEntryRow(
                            title=_('Preferred video player'),
                            conf_key='media_player'
                        ),
                        PreferencesSpinButtonRow(
                            title=_('Maximum article age'),
                            subtitle=_('In days'),
                            min_v=1, max_v=9999,
                            conf_key='max_article_age_days'
                        )
                    ]
                ),
                MPreferencesGroup(
                    title=_('Refresh preferences'), rows=[
                        PreferencesToggleRow(
                            title=_('Refresh articles on startup'),
                            conf_key='refresh_on_startup'
                        ),
                        PreferencesToggleRow(
                            title=_('New articles notification'),
                            conf_key='notify_new_articles'
                        ),
                        PreferencesToggleRow(
                            title=_('Enable auto-refresh'),
                            conf_key='auto_refresh_enabled'
                        ),
                        PreferencesSpinButtonRow(
                            title=_('Auto-refresh interval'),
                            subtitle=_('In seconds'),
                            min_v=60, max_v=86400,  # 1 min to 24 hours
                            conf_key='auto_refresh_time_seconds'
                        )
                    ]
                ),
                MPreferencesGroup(
                    title=_('Cache'), rows=[
                        PreferencesButtonRow(
                            title=_('Clear caches'),
                            button_label=_('Clear'),
                            onclick=self.clear_caches,
                            button_style_class='destructive-action',
                            signal='gfeeds_repopulation_required'
                        )
                    ]
                )
            ]
        )

    def clear_caches(self, confman, *args):
        for p in [
                confman.cache_path,
                confman.thumbs_cache_path,
        ]:
            files = [
                abspath(join(p, f)) for f in listdir(p)
            ]
            for f in files:
                if isfile(f):
                    remove(f)
        confman.conf['saved_items'] = {}
        confman.save_conf()


class AppearancePreferencesPage(MPreferencesPage):
    def __init__(self):
        super().__init__(
            title=_('Appearance'), icon_name='applications-graphics-symbolic',
            pref_groups=[
                MPreferencesGroup(
                    title=_('Appearance preferences'), rows=[
                        PreferencesToggleRow(
                            title=_('Dark mode'), conf_key='dark_mode',
                            signal='dark_mode_changed'
                        ),
                        PreferencesComboRow(
                            title=_('Reader mode theme'),
                            conf_key='reader_theme',
                            values=['auto', 'light', 'dark'],
                            value_names=[
                                _('Automatic'), _('Light'), _('Dark')
                            ]
                        ),
                        PreferencesToggleRow(
                            title=_('Show article thumbnails'),
                            conf_key='show_thumbnails',
                            signal='show_thumbnails_changed'
                        ),
                        PreferencesToggleRow(
                            title=_('Show full articles titles'),
                            conf_key='full_article_title',
                            signal='gfeeds_full_article_title_changed'
                        ),
                        PreferencesToggleRow(
                            title=_('Show full feeds names'),
                            conf_key='full_feed_name',
                            signal='gfeeds_full_feed_name_changed'
                        )
                    ]
                ),
                MPreferencesGroup(
                    title=_('Font preferences'), rows=[
                        PreferencesToggleRow(
                            title=_('Use system font for titles'),
                            conf_key='font_use_system_for_titles'
                        ),
                        PreferencesToggleRow(
                            title=_('Use system font for paragraphs'),
                            conf_key='font_use_system_for_paragraphs'
                        ),
                        PreferencesFontChooserRow(
                            title=_('Custom title font'),
                            conf_key='font_titles_custom'
                        ),
                        PreferencesFontChooserRow(
                            title=_('Custom paragraph font'),
                            conf_key='font_paragraphs_custom'
                        ),
                        PreferencesFontChooserRow(
                            title=_('Custom monospace font'),
                            conf_key='font_monospace_custom'
                        ),
                    ]
                )
            ]
        )


class PrivacyPreferencesPage(MPreferencesPage):
    def __init__(self):
        super().__init__(
            title=_('Privacy'), icon_name='eye-not-looking-symbolic',
            pref_groups=[
                MPreferencesGroup(
                    title=_('Privacy preferences'), rows=[
                        PreferencesToggleRow(
                            title=_('Enable JavaScript'),
                            conf_key='enable_js',
                            signal='gfeeds_webview_settings_changed'
                        ),
                        PreferencesToggleRow(
                            title=_('Try to block advertisements'),
                            conf_key='enable_adblock',
                            subtitle=_('Requires app restart'),
                            signal='on_apply_adblock_changed'
                        ),
                        PreferencesButtonRow(
                            title=_('Update advertisement blocking list'),
                            subtitle=_('Updates automatically every 10 days'),
                            button_label=_('Update'),
                            onclick=lambda *args: None,
                            signal='on_refresh_blocklist'
                        )
                    ]
                )
            ]
        )


class AdvancedPreferencesPage(MPreferencesPage):
    def __init__(self):
        super().__init__(
            title=_('Advanced'), icon_name='system-run-symbolic',
            pref_groups=[
                MPreferencesGroup(
                    title=_('Advanced preferences'), rows=[
                        PreferencesSpinButtonRow(
                            title=_('Maximum refresh threads'),
                            subtitle=_(
                                'How many threads to use for feeds refresh'
                            ),
                            min_v=1, max_v=32,
                            conf_key='max_refresh_threads',
                        ),
                        PreferencesToggleRow(
                            title=_(
                                'Experimental GtkListView for articles list'
                            ),
                            subtitle=_('Requires app restart'),
                            conf_key='use_experimental_listview'
                        )
                    ]
                )
            ]
        )


class PreferencesWindow(Adw.PreferencesWindow):
    def __init__(self, parent_win: Optional[Gtk.Window]):
        super().__init__(default_width=360, default_height=600)
        if parent_win:
            self.set_transient_for(parent_win)
            self.set_modal(True)
        self.confman = ConfManager()

        self.pages = [
            GeneralPreferencesPage(),
            PrivacyPreferencesPage(),
            AppearancePreferencesPage(),
            AdvancedPreferencesPage()
        ]
        for p in self.pages:
            self.add(p)
