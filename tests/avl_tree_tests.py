from sverchok.utils.testing import SverchokTestCase
from sverchok.utils.avl_tree import AVLTree, Node


class AVLTreeTest(SverchokTestCase):
    def setUp(self):
        self.custom_tree = self.get_custom_tree()
        self.empty_tree = AVLTree()
        self.only_root_tree = AVLTree([10])
        self.huge_tree = self.get_huge_random_tree()

    def test_avl_tree_search(self):
        with self.subTest(tree="custom tree"):
            self.assertEqual(self.custom_tree.find(6).key, 6)
        with self.subTest(tree="empty tree"):
            self.assertIsNone(self.empty_tree.find(6))
        with self.subTest(tree="only root tree (10)"):
            self.assertIsNone(self.empty_tree.find(6))
        with self.subTest(tree="huge tree"):
            self.assertIsNone(self.huge_tree.find(500))
            self.assertIsNone(self.huge_tree.find(1000))
            self.assertIsNone(self.huge_tree.find(100))
            self.assertEqual(self.huge_tree.find(533).key, 533)
            self.assertEqual(self.huge_tree.find(367).key, 367)

    def test_avl_tree_find_nearest_left(self):
        values = [6, 5.5, 12, 500]
        expect_custom_tree = [6, 5, 10, 15]
        expect_only_root_tree = [None, None, 10, 10]
        expect_huge_tree = [1, 1, 1, 483]
        for val, ex, ro, hu in zip(values, expect_custom_tree, expect_only_root_tree, expect_huge_tree):
            with self.subTest(tree="custom tree", value=val, expected=ex):
                node = self.custom_tree.find_nearest_left(val)
                self.assertEqual(node.key, ex)
            with self.subTest(tree="empty tree", value=val):
                self.assertIsNone(self.empty_tree.find_nearest_left(val))
            for tree, expect in zip([self.only_root_tree, self.huge_tree], [ro, hu]):
                with self.subTest(tree="root tree or huge tree", value=val, expected=expect):
                    res = tree.find_nearest_left(val)
                    if isinstance(res, Node):
                        self.assertEqual(res.key, expect)
                    else:
                        self.assertIsNone(res)

    @staticmethod
    def get_custom_tree():
        """
             10
            /  \
           5    15
            \
            9
           /
          6
        """
        tree = AVLTree([10])
        root = tree.rootNode
        n5 = Node(5)
        n5.parent = root
        root.leftChild = n5
        n15 = Node(15)
        n15.parent = root
        root.rightChild = n15
        n9 = Node(9)
        n9.parent = n5
        n5.rightChild = n9
        n6 = Node(6)
        n6.parent = n9
        n9.leftChild = n6
        return tree

    @staticmethod
    def get_huge_random_tree():
        values = [1, 14, 27, 31, 45, 55, 77, 103, 141, 175, 230, 231, 239, 251, 267, 298, 306, 310, 311, 316,
                  356, 367, 451, 457, 482, 483, 518, 533, 553, 615, 634, 674, 688, 708, 711, 728, 737, 771, 789,
                  798, 820, 833, 862, 864, 919, 928, 985, 994, 997, 999]
        return AVLTree(values)

    @staticmethod
    def get_custom2_tree():
        """
        ****************************************55(3)*******************************************
        **************************16(2)**********************86(2)******************************
        ****************7(1)************53(1)***********75(1)***********94(1)*******************
        ********2(0)*****13(0)****26(0)****54(0)****73(0)****78(0)****93(0)****96(0)************
        """
        val = [2, 7, 13, 16, 26, 53, 54, 55, 73, 75, 78, 86, 93, 94, 96]
        return AVLTree(val)
