from typing import Callable, List
from gi.repository import Gtk


class Accelerator:
    def __init__(self, combo: str, cb: Callable):
        self.combo = combo
        self.cb = cb


def add_accelerators(
    window: Gtk.Window, shortcuts_l: List[Accelerator]
) -> Gtk.ShortcutController:
    shortcut_controller = Gtk.ShortcutController()
    shortcut_controller.set_scope(Gtk.ShortcutScope.GLOBAL)
    for s in shortcuts_l:
        __add_accelerator(shortcut_controller, s.combo, s.cb)
    window.add_controller(shortcut_controller)
    return shortcut_controller


def __add_accelerator(
    controller: Gtk.ShortcutController, shortcut: str, callback: Callable
):
    if shortcut:
        # res is bool, don't know what it is
        _, key, mod = Gtk.accelerator_parse(shortcut)
        gshcut = Gtk.Shortcut(
            trigger=Gtk.KeyvalTrigger(keyval=key, modifiers=mod),
            action=Gtk.CallbackAction.new(callback),
        )
        controller.add_shortcut(gshcut)


def add_mouse_button_accel(
    widget: Gtk.Widget,
    function: Callable,
    propagation: Gtk.PropagationPhase = Gtk.PropagationPhase.BUBBLE,
) -> Gtk.GestureClick:
    """Adds an accelerator for mouse btn press for widget to function.
    NOTE: this returns the Gtk.Gesture, you need to keep this around or it
    won't work. Assign it to some random variable and don't let it go out of
    scope"""

    gesture = Gtk.GestureClick.new()
    gesture.set_button(0)
    gesture.set_propagation_phase(propagation)
    gesture.connect("pressed", function)
    widget.add_controller(gesture)
    return gesture


def add_longpress_accel(
    widget: Gtk.Widget,
    function: Callable,
    propagation: Gtk.PropagationPhase = Gtk.PropagationPhase.BUBBLE,
) -> Gtk.GestureLongPress:
    """Adds an accelerator for mouse btn press for widget to function.
    NOTE: this returns the Gtk.Gesture, you need to keep this around or it
    won't work. Assign it to some random variable and don't let it go out of
    scope"""

    gesture = Gtk.GestureLongPress.new()
    gesture.set_propagation_phase(propagation)
    gesture.set_touch_only(False)
    gesture.connect("pressed", function)
    widget.add_controller(gesture)
    return gesture
