from unittest import TestCase

from boom.game import Bomb

class BombTest(TestCase):

    def test_init(self):
        bomb = Bomb(3, 4)
        self.assertEqual(bomb.fuse, 3)
        self.assertEqual(bomb.size, 4)
