from typing import Callable, Optional, List
from gi.repository import Gtk, GObject, Adw


@Gtk.Template(resource_path='/org/gabmus/gfeeds/ui/scrolled_dialog.ui')
class ScrolledDialog(Adw.Window):
    __gtype_name__ = 'ScrolledDialog'
    __gsignals__ = {
        'response': (
            GObject.SignalFlags.RUN_LAST,
            None,
            (Gtk.ResponseType,)
        )
    }
    title_label: Gtk.Label = Gtk.Template.Child()
    message_label: Gtk.Label = Gtk.Template.Child()

    def __init__(
            self, transient_for: Gtk.Window, title: Optional[str] = None,
            message: Optional[str] = None
    ):
        super().__init__(
            modal=True, transient_for=transient_for
        )
        for txt, label in (
                (title, self.title_label), (message, self.message_label)
        ):
            if txt is not None:
                label.set_text(txt)

    @Gtk.Template.Callback()
    def on_yes_clicked(self, _):
        self.emit('response', Gtk.ResponseType.YES)

    @Gtk.Template.Callback()
    def on_no_clicked(self, _):
        self.emit('response', Gtk.ResponseType.NO)


class ScrolledDialogResponse:
    def __init__(
            self, name: str, label: str,
            callback: Optional[Callable] = None,
            appearance: Optional[Adw.ResponseAppearance] = None,
    ):
        self.name = name
        self.label = label
        self.callback = callback
        self.appearance = appearance


class ScrolledDialogV2(Adw.MessageDialog):
    def __init__(
            self, parent: Gtk.Window, title: str, body: str,
            responses: List[ScrolledDialogResponse]
    ):
        self.__parent = parent
        self.__title = title
        self.__body = body
        self.__responses = responses

        super().__init__(
            transient_for=self.__parent,
            heading=self.__title,
            extra_child=Gtk.ScrolledWindow(
                css_classes=['card'],
                hscrollbar_policy=Gtk.PolicyType.NEVER,
                width_request=270,
                height_request=270,
                margin_start=12,
                margin_end=12,
                child=Gtk.Label(
                    wrap=True,
                    xalign=0.0,
                    margin_top=12,
                    margin_bottom=12,
                    margin_start=12,
                    margin_end=12,
                    label=self.__body
                )
            )
        )

        for r in self.__responses:
            self.add_response(r.name, r.label)
            if r.appearance is not None:
                self.set_response_appearance(r.name, r.appearance)

        self.connect('response', self.on_response)

    def on_response(self, _, res: str):
        self.close()
        for r in self.__responses:
            if r.name == res:
                if r.callback is not None:
                    r.callback()
                return
