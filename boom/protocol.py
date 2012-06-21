from twisted.internet.protocol import Protocol, Factory


from boom.game import Pawn


class SimpleProtocol(Protocol):


    move_mapping = {
        'w': 'u',
        'a': 'l',
        'd': 'r',
        's': 'd',
    }

    def connectionMade(self):
        self.factory.protocols.append(self)
        self.pawn = Pawn()
        self.factory.board.insertPawn((0,0), self.pawn)


    def connectionLost(self, reason):
        self.factory.protocols.remove(self)
        self.factory.board.pawns.remove(self.pawn)


    def dataReceived(self, data):
        for k in data:
            if k in self.move_mapping:
                self.pawn.move(self.move_mapping[k])
            elif k == 'e':
                self.pawn.dropBomb()


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
