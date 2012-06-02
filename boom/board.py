class Board:

    def generate(self, columns, rows):
        self.tiles = []
        for c in xrange(columns):
            row = []
            for r in xrange(rows):
                if r % 2 and c % 2:
                    row.append(0)
                else:
                    row.append(1)
            self.tiles.append(row)
