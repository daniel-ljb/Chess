class BoardRepresentation():
    @staticmethod
    def SquareToName(square : int) -> str:
        column = chr(square%8+97)
        row = str(square//8+1)
        return column + row
    
    @staticmethod
    def NameToSquare(name : str) -> int:
        column = ord(name[0]) - 97
        row = int(name[1]) - 1
        return column + row*8
    
    @staticmethod
    def FileIndex(square : int) -> int:
        return square % 8
    
    @staticmethod
    def RankIndex(square: int) -> int:
        return square // 8
    
    @staticmethod
    def RankFileToSquare(rank : int, file : int) -> int:
        return rank*8 + file