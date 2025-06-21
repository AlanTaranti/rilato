from typing import Callable, Optional, List
from gi.repository import Gtk, Adw


class ScrolledDialogResponse:
    def __init__(
        self,
        name: str,
        label: str,
        callback: Optional[Callable] = None,
        appearance: Optional[Adw.ResponseAppearance] = None,
    ):
        self.name = name
        self.label = label
        self.callback = callback
        self.appearance = appearance


class ScrolledDialog(Adw.MessageDialog):
    def __init__(
        self,
        parent: Gtk.Window,
        title: str,
        body: str,
        responses: List[ScrolledDialogResponse],
    ):
        self.__parent = parent
        self.__title = title
        self.__body = body
        self.__responses = responses

        super().__init__(
            transient_for=self.__parent,
            heading=self.__title,
            extra_child=Gtk.ScrolledWindow(
                css_classes=["card"],
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
                    label=self.__body,
                ),
            ),
        )

        for r in self.__responses:
            self.add_response(r.name, r.label)
            if r.appearance is not None:
                self.set_response_appearance(r.name, r.appearance)

        self.connect("response", self.on_response)

    def on_response(self, dialog: "ScrolledDialog", res: str):
        for r in self.__responses:
            if r.name == res:
                if r.callback is not None:
                    r.callback(dialog, res)
                return
