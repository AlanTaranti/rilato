from gi.repository import Gtk


def add_accelerators(window, shortcuts_l: list):
    window._auto_shortcut_controller = Gtk.ShortcutController()
    window._auto_shortcut_controller.set_scope(Gtk.ShortcutScope.GLOBAL)
    for s in shortcuts_l:
        __add_accelerator(
            window._auto_shortcut_controller, s['combo'], s['cb']
        )
    window.add_controller(window._auto_shortcut_controller)


def __add_accelerator(controller, shortcut, callback):
    if shortcut:
        # res is bool, don't know what it is
        res, key, mod = Gtk.accelerator_parse(shortcut)
        trigger = Gtk.KeyvalTrigger.new(key, mod)
        cb = Gtk.CallbackAction.new(callback)
        gshcut = Gtk.Shortcut.new(trigger, cb)
        controller.add_shortcut(gshcut)


def add_mouse_button_accel(widget, function,
                           propagation=Gtk.PropagationPhase.BUBBLE):
    '''Adds an accelerator for mouse btn press for widget to function.
    NOTE: this returns the Gtk.Gesture, you need to keep this around or it
    won't work. Assign it to some random variable and don't let it go out of
    scope'''

    gesture = Gtk.GestureClick.new()
    gesture.set_button(0)
    gesture.set_propagation_phase(propagation)
    gesture.connect('pressed', function)
    widget.add_controller(gesture)
    widget._auto_gesture_click = gesture
    return gesture


def add_longpress_accel(widget, function,
                        propagation=Gtk.PropagationPhase.BUBBLE):
    '''Adds an accelerator for mouse btn press for widget to function.
    NOTE: this returns the Gtk.Gesture, you need to keep this around or it
    won't work. Assign it to some random variable and don't let it go out of
    scope'''

    gesture = Gtk.GestureLongPress.new()
    gesture.set_propagation_phase(propagation)
    gesture.set_touch_only(False)
    gesture.connect('pressed', function)
    widget.add_controller(gesture)
    widget._auto_gesture_longpress = gesture
    return gesture
