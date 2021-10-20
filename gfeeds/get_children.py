from gi.repository import Gtk


def __is_valid_true(c: Gtk.Widget):
    return True


def __is_valid_listbox(c: Gtk.Widget):
    return isinstance(c, Gtk.ListBoxRow)


def get_children(container):
    is_valid = __is_valid_true
    first_child = container.get_first_child()
    if first_child is None:
        return []
    if isinstance(container, Gtk.ListBox):
        is_valid = __is_valid_listbox
    res = []
    if is_valid(first_child):
        res.append(first_child)
    child = first_child.get_next_sibling()
    while child is not None:
        if is_valid(child):
            res.append(child)
        child = child.get_next_sibling()
    return res
