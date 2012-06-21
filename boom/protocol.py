from twisted.internet.protocol import Protocol, Factory
import string


from boom.game import Pawn, YoureDead, IllegalMove


class SimpleProtocol(Protocol):

    num = 0

    move_mapping = {
        'w': 'u',
        'a': 'l',
        'd': 'r',
        's': 'd',
    }

    def connectionMade(self):
        self.factory.protocols.append(self)
        name = string.uppercase[self.num % len(string.uppercase)]
        SimpleProtocol.num += 1
        self.pawn = Pawn(name)
        self.factory.board.insertPawn((0,0), self.pawn)


    def connectionLost(self, reason):
        self.factory.protocols.remove(self)
        self.factory.board.pawns.remove(self.pawn)


    def dataReceived(self, data):
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



class SimpleFactory(Factory):
    """
    A factory for making L{SimpleProtocol}s
    
    @ivar board: the game board on which I'll be playing
    @ivar protocols: A list of L{SimpleProtocol} instances currently
        in use.
    """
    
    protocol = SimpleProtocol
    
    
    def __init__(self, board):
        self.board = board
        self.protocols = []
