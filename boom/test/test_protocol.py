from twisted.trial.unittest import TestCase
from twisted.test.proto_helpers import StringTransport


from boom.game import Board, Pawn
from boom.protocol import TelnetProtocol, TelnetFactory



class TelnetFactoryTest(TestCase):


    def test_init(self):
        """
        You initialize the factory with a Board
        """
        board = object()
        f = TelnetFactory(board)
        self.assertEqual(f.board, board)
        self.assertEqual(f.protocols, [])



class TelnetProtocolTest(TestCase):


    def test_connect_disconnect(self):
        """
        After making a connection, the factory should know about it.
        And when the protocol disconnects, the factory should know
        that too.
        """
        board = Board()
        factory = TelnetFactory(board)
        proto = TelnetProtocol()
        proto.factory = factory
        transport = StringTransport()
        proto.makeConnection(transport)
        self.assertTrue(isinstance(proto.pawn, Pawn))
        self.assertTrue(proto.pawn in board.pawns, "Should "
                        "add a pawn to the board")
        self.assertTrue(proto in factory.protocols, "When a "
                        "protocol connects, it should be "
                        "added to the Factory's pool of "
                        "protocols")
        proto.connectionLost(None)
        self.assertTrue(proto not in factory.protocols, "When "
                        "a protocol disconnects, it should be "
                        "removed from the Factory's pool of "
                        "protocols")
        self.assertTrue(proto.pawn not in board.pawns, "Should "
                        "remove pawn from the board")


    def test_controls(self):
        """
        You can control the pawn with the protocol
        """
        board = Board()
        factory = TelnetFactory(board)
        protocol = factory.buildProtocol(None)
        transport = StringTransport()
        protocol.makeConnection(transport)
        
        # fake out pawn.move and pawn.dropBpmb
        called = []
        pawn = protocol.pawn
        pawn.move = called.append
        pawn.dropBomb = lambda: called.append('drop')
        
        protocol.dataReceived('w')
        self.assertEqual(called, ['u'])
        called.pop()
        
        protocol.dataReceived('d')
        self.assertEqual(called, ['r'])
        called.pop()
        
        protocol.dataReceived('a')
        self.assertEqual(called, ['l'])
        called.pop()
        
        protocol.dataReceived('s')
        self.assertEqual(called, ['d'])
        called.pop()

        protocol.dataReceived('e')
        self.assertEqual(called, ['drop'])
        called.pop()
        
        protocol.dataReceived('w\r\ndo\rq\nae')
        self.assertEqual(called, ['u','r','l','drop'])



