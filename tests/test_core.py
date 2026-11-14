import unittest

from zipper_tree import Zipper, Node, node, tree


class TestZipper(unittest.TestCase):
    def setUp(self):
        # A small tree:
        #        a
        #       / \
        #      b   c
        #     / \   \
        #    d   e   f
        self.t = tree(
            "a",
            tree("b", tree("d"), tree("e")),
            tree("c", tree("f")),
        )

    def test_root_focus(self):
        z = Zipper.from_tree(self.t)
        self.assertEqual(z.focus, self.t)
        self.assertTrue(z.is_root())
        self.assertIsNone(z.up())
        self.assertIsNone(z.left())
        self.assertIsNone(z.right())

    def test_down_and_up(self):
        z = Zipper.from_tree(self.t)
        b = z.down()
        self.assertIsNotNone(b)
        self.assertEqual(b.value, "b")
        self.assertFalse(b.is_root())
        back = b.up()
        self.assertEqual(back.focus, self.t)

    def test_left_right_siblings(self):
        z = Zipper.from_tree(self.t)
        b = z.down()
        c = b.right()
        self.assertEqual(c.value, "c")
        b2 = c.left()
        self.assertEqual(b2.value, "b")
        self.assertIsNone(b.left())
        self.assertIsNone(c.right())

    def test_down_none_on_leaf(self):
        z = Zipper.from_tree(self.t)
        d = z.down().down()
        self.assertEqual(d.value, "d")
        self.assertIsNone(d.down())

    def test_immutable_set_value(self):
        z = Zipper.from_tree(self.t)
        b = z.down()
        b2 = b.set_value("B")
        self.assertEqual(b.value, "b")
        self.assertEqual(b2.value, "B")
        new_root = b2.root()
        self.assertEqual(new_root.value, "a")
        self.assertEqual(new_root.children[0].value, "B")
        self.assertEqual(new_root.children[1].value, "c")
        # original unchanged
        self.assertEqual(self.t.children[0].value, "b")

    def test_immutable_set_children(self):
        z = Zipper.from_tree(self.t)
        c = z.down().right()
        self.assertEqual(c.value, "c")
        new_c = c.set_children((node("g"),))
        new_root = new_c.root()
        self.assertEqual(new_root.children[1].children[0].value, "g")
        self.assertEqual(self.t.children[1].children[0].value, "f")

    def test_root_after_no_change(self):
        z = Zipper.from_tree(self.t)
        self.assertEqual(z.root(), self.t)

    def test_deep_modification(self):
        z = Zipper.from_tree(self.t)
        e = z.down().down().right()
        self.assertEqual(e.value, "e")
        e2 = e.set_value("E")
        new_root = e2.root()
        self.assertEqual(new_root.children[0].children[1].value, "E")
        self.assertEqual(self.t.children[0].children[1].value, "e")

    def test_next_traversal(self):
        z = Zipper.from_tree(self.t)
        values = [z.value]
        while True:
            z = z.next()
            if z is None:
                break
            values.append(z.value)
        self.assertEqual(values, ["a", "b", "d", "e", "c", "f"])

    def test_prev_traversal(self):
        z = Zipper.from_tree(self.t)
        # move to the last node in pre-order
        while z.next() is not None:
            z = z.next()
        self.assertEqual(z.value, "f")
        values = [z.value]
        while True:
            z = z.prev()
            if z is None:
                break
            values.append(z.value)
        self.assertEqual(values, ["f", "c", "e", "d", "b", "a"])

    def test_equality_and_repr(self):
        z1 = Zipper.from_tree(self.t)
        z2 = Zipper.from_tree(self.t)
        self.assertEqual(z1, z2)
        self.assertIn("Zipper", repr(z1))

    def test_set_value_returns_new_zipper(self):
        z = Zipper.from_tree(self.t)
        z2 = z.set_value("x")
        self.assertIsNot(z, z2)
        self.assertEqual(z.value, "a")
        self.assertEqual(z2.value, "x")


if __name__ == "__main__":
    unittest.main()
