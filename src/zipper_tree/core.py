"""Immutable zipper over node-based trees.

This module provides a `Zipper` that wraps any tree of `Node` objects and allows
O(1) movement to the parent, left child, or right child.  Modified subtrees can be
rebuilt back into the root in O(depth) time without mutating the original tree.

The design decision is to treat the tree as a persistent immutable structure:
updates produce a new root, leaving the original untouched.  The zipper keeps a
path from the current focus up to the root, so rebuilding the root after a change
is simply a matter of walking the path and replacing the focused subtree.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Optional, Tuple


@dataclass(frozen=True)
class Node:
    """A node in a tree.

    The tree is represented as a node with a value and a tuple of children.
    Children are ordered left-to-right.  A leaf has an empty children tuple.
    """

    value: Any
    children: Tuple["Node", ...] = ()

    def __post_init__(self) -> None:
        # Ensure children is always a tuple for immutability and hashability.
        if not isinstance(self.children, tuple):
            object.__setattr__(self, "children", tuple(self.children))


def node(value: Any, *children: Node) -> Node:
    """Convenience constructor for a Node with children."""
    return Node(value, children)


def tree(value: Any, *children: Node) -> Node:
    """Alias for `node`; reads better when building a whole tree."""
    return Node(value, children)


@dataclass(frozen=True)
class _Crumb:
    """A single step in the path from the focus back to the root.

    `left` and `right` are the siblings of the child we descended into,
    preserved so that rebuilding can reassemble the correct child order.
    """

    parent_value: Any
    left: Tuple[Node, ...]
    right: Tuple[Node, ...]


class Zipper:
    """An immutable zipper over a tree of `Node` objects.

    The zipper focuses on a single node.  Movement to the parent, left child,
    or right child is O(1).  Rebuilding the root after modifying the focus is
    O(depth) because it replays the saved path.

    The original tree is never mutated; `root()` returns a new tree if the focus
    has been changed, or the original tree if nothing changed.
    """

    __slots__ = ("_focus", "_path")

    def __init__(self, focus: Node, path: Tuple[_Crumb, ...] = ()) -> None:
        self._focus = focus
        self._path = path

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_tree(cls, root: Node) -> "Zipper":
        """Create a zipper focused on the root of `root`."""
        return cls(root, ())

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @property
    def focus(self) -> Node:
        """Return the currently focused node."""
        return self._focus

    @property
    def value(self) -> Any:
        """Return the value of the focused node."""
        return self._focus.value

    def is_root(self) -> bool:
        """True if the focus is the root of the tree."""
        return not self._path

    def up(self) -> Optional["Zipper"]:
        """Move to the parent, or return None if already at the root."""
        if not self._path:
            return None
        crumb = self._path[-1]
        parent_children = crumb.left + (self._focus,) + crumb.right
        parent = Node(crumb.parent_value, parent_children)
        return Zipper(parent, self._path[:-1])

    def left(self) -> Optional["Zipper"]:
        """Move to the left sibling, or return None if there is none."""
        if not self._path:
            return None
        crumb = self._path[-1]
        if not crumb.left:
            return None
        new_focus = crumb.left[-1]
        new_left = crumb.left[:-1]
        new_right = (self._focus,) + crumb.right
        new_crumb = _Crumb(crumb.parent_value, new_left, new_right)
        return Zipper(new_focus, self._path[:-1] + (new_crumb,))

    def right(self) -> Optional["Zipper"]:
        """Move to the right sibling, or return None if there is none."""
        if not self._path:
            return None
        crumb = self._path[-1]
        if not crumb.right:
            return None
        new_focus = crumb.right[0]
        new_left = crumb.left + (self._focus,)
        new_right = crumb.right[1:]
        new_crumb = _Crumb(crumb.parent_value, new_left, new_right)
        return Zipper(new_focus, self._path[:-1] + (new_crumb,))

    def down(self) -> Optional["Zipper"]:
        """Move to the first child, or return None if there are no children."""
        if not self._focus.children:
            return None
        first, *rest = self._focus.children
        crumb = _Crumb(self._focus.value, (), tuple(rest))
        return Zipper(first, self._path + (crumb,))

    def next(self) -> Optional["Zipper"]:
        """Move to the next node in depth-first pre-order, or None if done.

        This is a convenience for traversal; it is not O(1) in the worst case
        but is included because it is the natural way to iterate a zipper.
        """
        if self._focus.children:
            return self.down()
        current: Optional[Zipper] = self
        while current is not None:
            sibling = current.right()
            if sibling is not None:
                return sibling
            current = current.up()
        return None

    def prev(self) -> Optional["Zipper"]:
        """Move to the previous node in depth-first pre-order, or None.

        This is the inverse of `next` where it exists.
        """
        left = self.left()
        if left is None:
            return self.up()
        # Descend to the rightmost leaf of the left sibling.
        current = left
        while current.focus.children:
            current = current.down()  # type: ignore[assignment]
            while current.right() is not None:
                current = current.right()  # type: ignore[assignment]
        return current

    # ------------------------------------------------------------------
    # Modification
    # ------------------------------------------------------------------

    def set_value(self, value: Any) -> "Zipper":
        """Return a new zipper with the focused node's value replaced."""
        return Zipper(replace(self._focus, value=value), self._path)

    def set_children(self, children: Tuple[Node, ...]) -> "Zipper":
        """Return a new zipper with the focused node's children replaced."""
        return Zipper(replace(self._focus, children=children), self._path)

    # ------------------------------------------------------------------
    # Rebuilding
    # ------------------------------------------------------------------

    def root(self) -> Node:
        """Rebuild and return the root of the tree from the current focus.

        If the focus has not been modified, this returns the original root
        (structurally equal, and the same object where possible).  The original
        tree passed to `from_tree` is never mutated.
        """
        focus = self._focus
        for crumb in reversed(self._path):
            children = crumb.left + (focus,) + crumb.right
            focus = Node(crumb.parent_value, children)
        return focus

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Zipper):
            return NotImplemented
        return self._focus == other._focus and self._path == other._path

    def __repr__(self) -> str:
        return f"Zipper(focus={self._focus!r}, depth={len(self._path)})"
