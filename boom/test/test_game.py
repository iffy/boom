from twisted.trial.unittest import TestCase

from boom.game import Bomb

class BombTest(TestCase):

    timeout = 2

    def test_init(self):
        bomb = Bomb(3, 4)
        self.assertEqual(bomb.fuse, 3)
        self.assertEqual(bomb.size, 4)

    def test_ignite(self):
        bomb = Bomb(1, 4)
        d = bomb.ignite()
        def check(result):
            self.assertEqual(result, bomb)
        return d.addCallback(check)
