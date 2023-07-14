def tree_to_list(tree, ls):
    """recursively append all elements in a tree into a list"""
    ls.append(tree)
    for child in tree.children:
        tree_to_list(child, ls)
    return ls