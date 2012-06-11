from twisted.internet import reactor, stdio, task
from twisted.internet.protocol import Protocol

from boom.game import (Board, Pawn, YoureDead, IllegalMove, SOFT, 
                       EMPTY, HARD)

board = Board()
board.generate(11,11)

pawn = Pawn('Me')
pawn.bombs = 3
pawn.flame_size = 2
board.insertPawn((0,0), pawn)


class PlayerProtocol(Protocol):


    def __init__(self, pawn):
        self.pawn = pawn

    def dataReceived(self, data):
        for c in data:
            if c in ['w','a','s','d']:
                direction = {
                    'w':'u',
                    'a':'l',
                    's':'d',
                    'd':'r',
                }[c]
                try:
                    self.pawn.move(direction)
                except YoureDead:
                    print "You're dead"
                except IllegalMove:
                    pass
            elif c == 'e':
                try:
                    self.pawn.dropBomb()
                except YoureDead:
                    print "You're dead"
        printBoard()



def _printBoard():
    yield '+' + '-'*board_width + '+'
    for y in xrange(board_height):
        row = '|'
        for x in xrange(board_width):
            coord = (x,y)
            pawns = [x for x in board.pawns if x.loc == coord]
            if pawns:
                p = pawns[0]
                if p.alive:
                    row += p.name[0].upper()
                else:
                    row += p.name[0].lower()
                continue
            if coord in board.bombs:
                row += 'O'
                continue
            if coord in board.fires:
                row += 'x'
                continue
            tile = board.fg_tiles[coord]
            row += {
                EMPTY: ' ',
                SOFT: ':',
                HARD: '#',
            }[tile]
        row += '|'
        yield row
    yield '+' + '-'*board_width + '+'


def printBoard():
    print '\n'.join(_printBoard())

board_width = max([x[0] for x in board.fg_tiles]) + 1
board_height = max([x[1] for x in board.fg_tiles]) + 1

lc = task.LoopingCall(printBoard)
lc.start(0.1)



stdio.StandardIO(PlayerProtocol(pawn))
reactor.run()

