def get_children(container):
    first_child = container.get_first_child()
    if first_child is None:
        return []
    res = []
    res.append(first_child)
    child = first_child.get_next_sibling()
    while child is not None:
        res.append(child)
        child = child.get_next_sibling()
    return res
