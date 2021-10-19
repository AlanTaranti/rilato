from gi.repository import Gtk


def get_children(container):
    is_valid = lambda _: True
    first_child = container.get_first_child()
    if first_child is None:
        return []
    if isinstance(container, Gtk.ListBox):
        is_valid = lambda c: isinstance(c, Gtk.ListBoxRow)
    res = []
    if is_valid(first_child):
        res.append(first_child)
    child = first_child.get_next_sibling()
    while child is not None:
        if is_valid(child):
            res.append(child)
        child = child.get_next_sibling()
    return res
