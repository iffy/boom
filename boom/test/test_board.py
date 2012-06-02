from unittest import TestCase
from boom.board import Board

class BoardTest(TestCase):

    def test_generate(self):
        board = Board()
        board.generate(5, 5)
        self.assertEqual(board.tiles, [
            [1, 1, 1, 1, 1],
            [1, 0, 1, 0, 1],
            [1, 1, 1, 1, 1],
            [1, 0, 1, 0, 1],
            [1, 1, 1, 1, 1],
        ])
