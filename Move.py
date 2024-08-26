from BoardRepresentation import *
from Piece import *

class Move():
    class Flag():
        none = 0
        enPassantCapture = 1
        castling = 2
        pawnTwoForward = 3
        promoteToQueen = 4
        promoteToKnight = 5
        promoteToRook = 6
        promoteToBishop = 7
        
    __startSquareMask = 0b000000000111111
    __endSquareMask = 0b000111111000000
    __flagMask = 0b111000000000000
    
    def __init__(self, *args):
        if len(args) == 1: # Parameter is moveValue
            self.moveValue = args[0]
        elif len(args) == 2: # Parameter is startSquare and endSquare
            self.moveValue = args[0] | args[1] << 6
        else: # Parameter is startSquare, endSquare and moveFlag
            self.moveValue = args[0] | args[1] << 6 | args[2] << 12
    
    @property
    def startSquare(self) -> int:
        return self.moveValue & self.__startSquareMask
    
    @property
    def endSquare(self) -> int:
        return (self.moveValue & self.__endSquareMask) >> 6
    
    @property
    def moveFlag(self) -> int:
        return self.moveValue >> 12
    
    def __eq__(self, other):
        return self.moveValue == other.moveValue
    
    @property
    def isPromotion(self) -> bool:
        # not not faster than bool()
        return not not self.moveFlag >> 2
    
    @property
    def promotionPieceType(self) -> int:
        flag = self.moveFlag
        if flag == self.Flag.promoteToQueen:
            return Piece.queen
        elif flag == self.Flag.promoteToKnight:
            return Piece.knight
        elif flag == self.Flag.promoteToRook:
            return Piece.rook
        elif flag == self.Flag.promoteToBishop:
            return Piece.bishop        
    
    def __repr__(self):
        return BoardRepresentation.SquareToName(self.startSquare) + "-" + BoardRepresentation.SquareToName(self.endSquare)