from twisted.internet import reactor, stdio, task
from twisted.internet.endpoints import TCP4ServerEndpoint

from boom.protocol import TelnetFactory
from boom.game import (Board, Pawn, YoureDead, IllegalMove, SOFT, 
                       EMPTY, HARD)

board = Board()
board.generate(11,11)


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


factory = TelnetFactory(board)


def printBoard():
    lines = list(_printBoard())
    #print '\n'.join(lines)
    for protocol in factory.protocols:
        protocol.transport.write('\r\n'.join(lines) + '\r\n')
    

board_width = max([x[0] for x in board.fg_tiles]) + 1
board_height = max([x[1] for x in board.fg_tiles]) + 1

lc = task.LoopingCall(printBoard)
lc.start(0.2)


endpoint = TCP4ServerEndpoint(reactor, 8900)
endpoint.listen(factory)
reactor.run()


