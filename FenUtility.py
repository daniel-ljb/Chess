from Piece import *
from BoardRepresentation import *

class FenUtility():
    __startingFen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    
    @staticmethod
    def LoadFromFen(fenToLoad = None):
        if not fenToLoad: fenToLoad = FenUtility.__startingFen
        
        loadPositionInfo = FenUtility.__LoadPositionInfo()
        sections = fenToLoad.split()
        
        # Squares
        rank = 7
        file = 0
        for char in sections[0]:
            if char == "/":
                rank -= 1
                file = 0
            elif char.isdigit():
                file += int(char)
            else:
                loadPositionInfo.squares[rank*8 + file] = Piece.LetterToPiece(char)
                file += 1
        
        # Turn
        loadPositionInfo.whiteToMove = sections[1] == "w"
        
        # Castling
        loadPositionInfo.whiteCastleKingside = "K" in sections[2]
        loadPositionInfo.whiteCastleQueenside = "Q" in sections[2]
        loadPositionInfo.blackCastleKingside = "k" in sections[2]
        loadPositionInfo.blackCastleQueenside = "q" in sections[2]
        
        # En Passant
        loadPositionInfo.epFile = 8 if sections[3] == "-" \
                                    else BoardRepresentation.FileIndex(BoardRepresentation.NameToSquare(sections[3]))

        # HalfMove Clock
        loadPositionInfo.halfMove = int(sections[4])
        
        # PlyCount (Total Half Moves)
        if len(sections) == 6:
            loadPositionInfo.plyCount = (int(sections[5])-1)*2 + (not loadPositionInfo.whiteToMove)
        else:
            loadPositionInfo.plyCount = 0
        
        return loadPositionInfo
                
    class __LoadPositionInfo():
        def __init__(self):
            self.squares = [Piece.none for _ in range(64)]