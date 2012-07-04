from twisted.internet.protocol import Factory
from twisted.conch.telnet import Telnet, ECHO, SGA, LINEMODE
import string

from twisted.python import log


from boom.game import Pawn, YoureDead, IllegalMove


class TelnetProtocol(Telnet):

    num = 0

    move_mapping = {
        'w': 'u',
        'a': 'l',
        'd': 'r',
        's': 'd',
    }

    def connectionMade(self):
        self.factory.protocols.append(self)
        self.will(ECHO).addErrback(log.msg)
        self.will(SGA).addErrback(log.msg)
        self.wont(LINEMODE).addErrback(log.msg)

        name = string.uppercase[self.num % len(string.uppercase)]
        TelnetProtocol.num += 1
        self.pawn = Pawn(name)
        self.factory.board.insertPawn((0,0), self.pawn)


    def enableLocal(self, option):
        return option in (ECHO, SGA)


    def connectionLost(self, reason):
        self.factory.protocols.remove(self)
        self.factory.board.pawns.remove(self.pawn)


    def applicationDataReceived(self, data):
        for k in data:
            if k in self.move_mapping:
                try:
                    self.pawn.move(self.move_mapping[k])
                except YoureDead, e:
                    pass
                except IllegalMove, e:
                    pass
            elif k == 'e':
                try:
                    self.pawn.dropBomb()
                except YoureDead, e:
                    pass
                except IllegalMove, e:
                    pass



class TelnetFactory(Factory):
    """
    A factory for making L{TelnetProtocol}s
    
    @ivar board: the game board on which I'll be playing
    @ivar protocols: A list of L{TelnetProtocol} instances currently
        in use.
    """
    
    protocol = TelnetProtocol
    
    
    def __init__(self, board):
        self.board = board
        self.protocols = []
