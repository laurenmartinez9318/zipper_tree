# zipper_tree

An immutable zipper for node-based trees: O(1) movement to parent, left child, and right child, with O(depth) rebuilding of a modified subtree back into the root without mutating the original.

## Usage

```python
from zipper_tree import Zipper, tree

# Build a tree:
#     a
#    / \
#   b   c
t = tree("a", tree("b"), tree("c"))

z = Zipper.from_tree(t)
z = z.down()          # focus on "b"
z = z.set_value("B")  # immutable update
new_root = z.root()   # rebuilds the tree with "B"

assert new_root.children[0].value == "B"
assert t.children[0].value == "b"  # original unchanged
```

## Why this exists

Tree editing often requires walking from the root to a node and then rebuilding the path back up.  A zipper makes the walk cheap: the focus and the path to the root are kept together, so moving to a sibling or parent is O(1) and rebuilding after an edit is O(depth).  The trade-off is that the tree is treated as immutable; every edit produces a new root, which is safe but means you cannot mutate a node in place.  This library chooses that trade-off deliberately: it keeps the original tree intact and makes the update path explicit.

## The awkward edge

The zipper can only move to a left or right sibling if the focus has a parent.  At the root, `left()` and `right()` return `None`, and `up()` also returns `None`.  If you need to find a sibling from the root, you must first descend into a child.  Also, `next()` and `prev()` are provided for traversal but are not O(1); they are included because they make iterating a zipper natural.

## API

- `Node(value, children=())` — a tree node with a value and a tuple of children.
- `node(value, *children)` — convenience constructor.
- `tree(value, *children)` — alias for `node`.
- `Zipper.from_tree(root)` — create a zipper focused on the root.
- `Zipper.focus` — the currently focused `Node`.
- `Zipper.value` — the value of the focused node.
- `Zipper.is_root()` — true if the focus is the root.
- `Zipper.up()`, `Zipper.left()`, `Zipper.right()`, `Zipper.down()` — movement; return `None` when the move is not possible.
- `Zipper.next()`, `Zipper.prev()` — depth-first pre-order traversal.
- `Zipper.set_value(value)`, `Zipper.set_children(children)` — immutable updates.
- `Zipper.root()` — rebuild and return the root.

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.

