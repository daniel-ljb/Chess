import time
from Piece import *
from FenUtility import *
from Move import *

class Board():
    whiteIndex = 0
    blackIndex = 1
    @property
    def colourToMove(self): return Piece.white if self.whiteToMove else Piece.black
    @property
    def colourNotToMove(self): return Piece.black if self.whiteToMove else Piece.white
    
    __cardinalDirections = ((1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (-1, 1), (-1, -1), (1, -1)) # N E S W NE SE SW NW
    __knightDirections = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)) # SSW SSE WSW ESE WNW ENE NNW NNE
    
    # ss = starting square
    __ssWhiteKing = 4
    __ssBlackKing = 60
    __ssQRook = 0
    __ssKRook = 7
    __ssqRook = 56
    __sskRook = 63
    
    def __init__(self, passedFen = None):
        loadPositionInfo = FenUtility.LoadFromFen(passedFen)
        
        self.squares = loadPositionInfo.squares
        self.whiteToMove = loadPositionInfo.whiteToMove
        
        # Gamestate
        # 0-3 = Castling (0 = K, 3 = q)
        # 4-7 = file of ep square (8 = none)
        # 8-12 = captured piece
        # 13-... = fiftymove
        whiteCastle = loadPositionInfo.whiteCastleKingside      | loadPositionInfo.whiteCastleQueenside << 1
        blackCastle = loadPositionInfo.blackCastleKingside << 2 | loadPositionInfo.blackCastleQueenside << 3
        self.__gameState = whiteCastle | blackCastle | loadPositionInfo.epFile << 4 | loadPositionInfo.halfMove << 13
        self.__gameStateHistory = [self.__gameState]
        
        self.__plyCount = loadPositionInfo.plyCount
        self.__moveList = []
        
        self.squares = loadPositionInfo.squares
        
        # King list
        self.kingSquares = [-1 for _ in range(2)]
        for index, square in enumerate(self.squares):
            #If King
            if Piece.Type(square) == Piece.king:
                # If Black
                if Piece.IsColour(square, Piece.black):
                    self.kingSquares[self.blackIndex] = index
                # If White
                else:
                    self.kingSquares[self.whiteIndex] = index
        
        self.__endGameMove = 100000
   
    def DisplayBoard(self, fromWhiteSide=True):
        toPrint = "\n\n\t" + "  " + "+---" * 8 + "+"
        if fromWhiteSide:
            for rank in range(8, 0, -1):
                toPrint += "\n\t" + str(rank) + " | "
                toPrint += " | ".join([Piece.PieceToLetter(piece) for piece in self.squares[rank*8-8:rank*8]])
                toPrint += " |\n\t  " + "+---" * 8 + "+"
            toPrint += "\n\t    " + "   ".join([chr(num) for num in range(65, 73)])
        else:
            for rank in range(1, 9):
                toPrint += "\n\t" + str(rank) + " | "
                # using [rank*8-8:rank*8][::-1] instead of [rank*8-1:rank*8-9:-1] because [7:-1,-1] returns []
                toPrint += " | ".join([Piece.PieceToLetter(piece) for piece in self.squares[rank*8-8:rank*8][::-1]])
                toPrint += " |\n\t  " + "+---" * 8 + "+"
            toPrint += "\n\t    " + "   ".join([chr(num) for num in range(72, 64, -1)])
        print(toPrint)
    
    # Board State Parts
    @property
    def __whiteCastling(self) -> int: # QK
        return self.__gameState & 0b11
    
    @property
    def __blackCastling(self) -> int: # qk
        return self.__gameState >> 2 & 0b11
    
    @property
    def __epFile(self) -> int: # 0-7 or 8 = none
        return self.__gameState >> 4 & 0b1111
    
    @property
    def __capturedPiece(self) -> int:
        return self.__gameState >> 8 & 0b11111
    
    @property
    def __halfMove(self) -> int:
        return self.__gameState >> 13
    
    def MakeMoveNumber(self, number):
        self.MakeMove(self.__allLegalMoves[number])
    
    def MakeMove(self, move):
        if not isinstance(move, Move):
            raise TypeError("move must be of type Move")
        
        self.__moveList.append(move)
        # Update information
        self.whiteToMove = not self.whiteToMove
        self.__plyCount += 1
        
        # Gamestate
        epFile = 8 if move.moveFlag != Move.Flag.pawnTwoForward else BoardRepresentation.FileIndex(move.startSquare)
        castling = self.__gameState & 0b1111
        startEndSquares = [move.startSquare, move.endSquare]
        # Moving white king (or moving piece from that square afterwards means it's already moved so it's fine to remove castling rights again)
        if   self.__ssWhiteKing in startEndSquares:    castling &= 0b1100
        elif self.__ssBlackKing in startEndSquares:    castling &= 0b0011 # Black King
        elif self.__ssKRook in startEndSquares:        castling &= 0b1110 # White Kingside Rook
        elif self.__ssQRook in startEndSquares:        castling &= 0b1101 # White Queenside Rook
        elif self.__sskRook in startEndSquares:        castling &= 0b1011 # Black Kingside Rook
        elif self.__ssqRook in startEndSquares:        castling &= 0b0111 # Black Queenside Rook
        
        capturedPiece = self.squares[move.endSquare]
        halfMove = self.__gameState >> 13
        if ( capturedPiece != Piece.none # If capturing
             or Piece.Type(self.squares[move.startSquare]) == Piece.pawn ): # or advancing a pawn
            halfMove = 0 # reset half-move clock
        else:
            halfMove += 1 # otherwise increment
        
        self.__gameState = castling | epFile << 4 | capturedPiece << 8 | halfMove << 13
        self.__gameStateHistory.append(self.__gameState)
        
        # Move Piece
        # En Passant
        if move.moveFlag == Move.Flag.enPassantCapture:
            self.squares[ move.endSquare + (8 if Piece.IsColour(self.squares[move.startSquare], Piece.black) else -8) ] \
                          = Piece.none
        elif move.moveFlag == Move.Flag.castling:
            rookStartSquare = ( move.endSquare + 1 if move.endSquare > move.startSquare # Kingside
                                else move.endSquare - 2 ) # Queenside
            rookEndSquare = (move.startSquare + move.endSquare) // 2
            
            # Move rook
            self.squares[rookEndSquare] = self.squares[rookStartSquare]
            self.squares[rookStartSquare] = Piece.none
        
        # Promotion
        if not move.isPromotion:
            endPiece = self.squares[move.startSquare]
        else:
            pieceColour = Piece.Colour(self.squares[move.startSquare])
            
            if move.moveFlag == Move.Flag.promoteToQueen:
                endPieceType = Piece.queen
            elif move.moveFlag == Move.Flag.promoteToKnight:
                endPieceType = Piece.knight
            elif move.moveFlag == Move.Flag.promoteToRook:
                endPieceType = Piece.rook
            elif move.moveFlag == Move.Flag.promoteToBishop:
                endPieceType = Piece.bishop
            
            endPiece = pieceColour + endPieceType
            
        # Move piece
        self.squares[move.endSquare] = endPiece
        self.squares[move.startSquare] = Piece.none
        # Moving king
        if Piece.Type(endPiece) == Piece.king:
            colourIndex = self.whiteIndex if Piece.IsColour(endPiece, Piece.white) else self.blackIndex
            self.kingSquares[colourIndex] = move.endSquare
        
        # Calculate if EndGame
        if ( self.__endGameMove == 100000 and
             (Piece.white + Piece.queen) not in self.squares and
             (Piece.black + Piece.queen) not in self.squares ):
            self.__endGameMove = self.__plyCount
        
    def UnmakeMove(self):
        moveToUndo = self.__moveList.pop()
        
        if moveToUndo.isPromotion:
            movingPiece = ( Piece.Colour(self.squares[moveToUndo.endSquare]) # Colour of piece
                            + Piece.pawn ) # Resets to pawn
        else:
            movingPiece = self.squares[moveToUndo.endSquare] # Otherwise just the end square value
            
        self.squares[moveToUndo.startSquare] = movingPiece        
        self.squares[moveToUndo.endSquare] = self.__capturedPiece # Remove piece from end square
        
        # Castling
        if moveToUndo.moveFlag == Move.Flag.castling:
            if moveToUndo.startSquare > moveToUndo.endSquare: # Queenside
                self.squares[moveToUndo.endSquare -2] = self.squares[moveToUndo.endSquare +1]
                self.squares[moveToUndo.endSquare +1] = Piece.none
            else: # Kingside
                self.squares[moveToUndo.endSquare +1] = self.squares[moveToUndo.endSquare -1]
                self.squares[moveToUndo.endSquare -1] = Piece.none
        
        # En Passant
        elif moveToUndo.moveFlag == Move.Flag.enPassantCapture:
            enemyPawn = Piece.pawn + Piece.GetEnemyColour(self.squares[moveToUndo.startSquare])
            enemyPawnSquare = BoardRepresentation.RankFileToSquare(
                BoardRepresentation.RankIndex(moveToUndo.startSquare),
                BoardRepresentation.FileIndex(moveToUndo.endSquare) )
            self.squares[enemyPawnSquare] = enemyPawn
            
        # Update Information
        self.__gameStateHistory.pop()
        self.__gameState = self.__gameStateHistory[-1]
        self.whiteToMove = not self.whiteToMove
        self.__plyCount -= 1
        
        # King squares
        if Piece.Type(movingPiece) == Piece.king:
            colourIndex = self.whiteIndex if Piece.IsColour(movingPiece, Piece.white) else self.blackIndex
            self.kingSquares[colourIndex] = moveToUndo.startSquare
        
        if self.__endGameMove > self.__plyCount:
            self.__endGameMove = 100000
    
    @property
    def moveList(self):
        return self.__moveList
    
    @property
    def gameState(self):
        return self.__gameState
    
    def PrintAllLegalMoves(self):
        print("\nMoves:")
        for index, move in enumerate(self.__allLegalMoves):
            print(str(index) + ".",
                  BoardRepresentation.SquareToName(move.startSquare),
                  BoardRepresentation.SquareToName(move.endSquare),
                  move.moveFlag if move.moveFlag != move.Flag.none else "")
    
    def CalculateAllLegalMoves(self, checkOpponentsMovesInstead = False, inSearch = False):
        # If inSearch, Pawns check empty squares diagonally and it's not checked if the move results in being in check, meaning it checks if the previous player is in check.
        legalMoves = []
        for pieceSquare, piece in enumerate(self.squares):
            if (piece == Piece.none # Empty square
                or ( not checkOpponentsMovesInstead and not Piece.IsColour(piece, self.colourToMove) )
                # Checking currents players moves and it's not that player's piece
                or ( checkOpponentsMovesInstead and Piece.IsColour(piece, self.colourToMove) )
                # Checking opponents moves to see if in check and it's not that player's piece
                ):
                continue
            
            elif Piece.Type(piece) == Piece.king:
                # King
                if not inSearch: # King cannot deliver check so no point. Also creates recursion through checking castling
                    legalMoves += self.__CalculateMoves(pieceSquare, isKing = True)
                    # inSearch only matters for checking that castling doesn't move through check because we remove all moves in check after find all.
            
            elif Piece.Type(piece) == Piece.queen:
                # Queen
                legalMoves += self.__CalculateMoves(pieceSquare)
                
            elif Piece.Type(piece) == Piece.rook:
                # Rook
                legalMoves += self.__CalculateMoves(pieceSquare, end = 3)
                
            elif Piece.Type(piece) == Piece.bishop:
                # Bishop
                legalMoves += self.__CalculateMoves(pieceSquare, start = 4)  
            
            elif Piece.Type(piece) == Piece.knight:
                # Knight
                legalMoves += self.__CalculateMoves(pieceSquare, isKnight = True)
            
            elif Piece.Type(piece) == Piece.pawn:
                # Pawn
                legalMoves += self.__CalculatePawnMoves(pieceSquare, inSearch=inSearch)
                
                
        # Remove moves resulting in check only if not inSearch
        if not inSearch:
            colourMoving = self.colourToMove
            i = 0
            while i < len(legalMoves):
                self.MakeMove(legalMoves[i])
                if self.KingInCheck(colourMoving):
                    legalMoves.pop(i)
                else:
                    i += 1
                self.UnmakeMove()
        
        if checkOpponentsMovesInstead:
            self.__allOpponentsMoves = legalMoves
        else:
            self.__allLegalMoves = legalMoves
        
        return legalMoves
    
    def __CalculatePawnMoves(self, pieceSquare, inSearch = False) -> list:
        legalMoves = []
        pieceColour = Piece.Colour(self.squares[pieceSquare])
        if pieceColour == Piece.white:
            direction = 1
            startingRank = 1
        else:
            direction = -1
            startingRank = 6
        pawnRank = BoardRepresentation.RankIndex(pieceSquare)
        aboutToPromote = pawnRank == startingRank + direction*5
        onEpRank = pawnRank == startingRank + direction*3
        
        # 1 Forwards
        targetSquare = pieceSquare + 8*direction
        if ( self.squares[targetSquare] == Piece.none
             and not inSearch ): # Pawns can't check empty squares in front of them for ensuring king doesn't castle through check.
            if aboutToPromote:
                legalMoves += [
                    Move(pieceSquare, targetSquare, Move.Flag.promoteToQueen),
                    Move(pieceSquare, targetSquare, Move.Flag.promoteToKnight),
                    Move(pieceSquare, targetSquare, Move.Flag.promoteToRook),
                    Move(pieceSquare, targetSquare, Move.Flag.promoteToBishop),
                    ]
            else:
                legalMoves.append( Move(pieceSquare, targetSquare) )
            
                # 2 Forwards (only works if next line is empty and not on penultimate rank which is previously checked)
                if BoardRepresentation.RankIndex(pieceSquare) == startingRank:
                    targetSquare = pieceSquare + 16*direction
                    if self.squares[targetSquare] == Piece.none:
                        legalMoves.append( Move(pieceSquare, targetSquare, Move.Flag.pawnTwoForward) )
        
        # Normal Captures
        targetSquares = []
        pawnFile = BoardRepresentation.FileIndex(pieceSquare)
        if pawnFile != 0:    targetSquares.append(pieceSquare + 8*direction - 1)
        if pawnFile != 7:    targetSquares.append(pieceSquare + 8*direction + 1)
        
        for targetSquare in targetSquares:
            if ( Piece.IsEnemyPiece(self.squares[pieceSquare], self.squares[targetSquare])
                 or inSearch): # Can check empty squares diagonally for checking king doesn't move through check when castling
                if aboutToPromote:
                    legalMoves += [
                        Move(pieceSquare, targetSquare, Move.Flag.promoteToQueen),
                        Move(pieceSquare, targetSquare, Move.Flag.promoteToKnight),
                        Move(pieceSquare, targetSquare, Move.Flag.promoteToRook),
                        Move(pieceSquare, targetSquare, Move.Flag.promoteToBishop),
                        ]
                else:
                    legalMoves.append( Move(pieceSquare, targetSquare) )
            
            # En Passant
            if ( onEpRank # If on the correct rank
                and BoardRepresentation.FileIndex(targetSquare) == self.__epFile # and the correct file to en passant
                 # Assuming target square is empty and square next to pawn is an enemy pawn because otherwise the ep state would not be this file                 
                 ):
                legalMoves.append( Move(pieceSquare, targetSquare, Move.Flag.enPassantCapture) )
        
        return legalMoves
    
    def __CalculateMoves(self, pieceSquare:int, start:int=0, end:int=7, isKing:bool=False, isKnight:bool=False, inSearch:bool=False) -> list:
        legalMoves = []
        directions = self.__cardinalDirections[start:end+1] if not isKnight else self.__knightDirections
        pieceColour = Piece.Colour(self.squares[pieceSquare])
        
        for direction in directions:
            rank = BoardRepresentation.RankIndex(pieceSquare)
            file = BoardRepresentation.FileIndex(pieceSquare)
            
            while True:
                # Update the current square being checked
                rank += direction[0]
                file += direction[1]
                
                if not (0 <= rank <= 7 and 0 <= file <= 7):
                    # If off board
                    break
                
                endSquarePiece = self.GetBoardValue(rank, file)
                if Piece.IsColour(endSquarePiece, pieceColour): 
                    # Or own piece
                    break
            
                landingOnEnemyPiece = Piece.IsEnemyPiece(pieceColour, endSquarePiece)
                if ( endSquarePiece == Piece.none # If empty square
                   or landingOnEnemyPiece ): # Or enemy piece
                    legalMoves.append(Move(pieceSquare, rank*8+file))
                    
                    if landingOnEnemyPiece:
                        # Don't search beyond enemy piece
                        break
                
                # Limits king and knight moves to 1 jump
                if isKnight or isKing:
                    break
        
        if isKing:
            # Castling
            castlingRights = self.__whiteCastling if pieceColour == Piece.white else self.__blackCastling
            
            # Queenside
            if castlingRights & 0b10 == 0b10:
                # Check squares between are empty
                if sum(self.squares[pieceSquare-3:pieceSquare]) == Piece.none:
                    # Check not moving through check
                    if not True in [self.SquareInCheck(s, pieceColour) for s in range(pieceSquare-2, pieceSquare+1)]:
                        legalMoves.append( Move(pieceSquare, pieceSquare-2, Move.Flag.castling) )
            
            # Kingside
            if castlingRights & 0b01 == 0b01:
                # Check squares between are empty
                if sum(self.squares[pieceSquare+1:pieceSquare+3]) == Piece.none:
                    # Check not moving through check
                    if not True in [self.SquareInCheck(s, pieceColour) for s in range(pieceSquare, pieceSquare+3)]:
                        legalMoves.append( Move(pieceSquare, pieceSquare+2, Move.Flag.castling) )
        
        return legalMoves
    
    def GetBoardValue(self, *args):
        return self.squares[BoardRepresentation.RankFileToSquare(*args)] if len(args) == 2 else self.squares[args[0]]
    
    def SquareInCheck(self, square, friendlyColour=None):
        
        if not friendlyColour:
            if self.squares[square] != Piece.none:
                friendlyColour = Piece.Colour(self.squares[square])
                enemyColour = Piece.GetEnemyColour(friendlyColour)
            else:
                enemyColour = self.colourNotToMove # Default to checking if current player is in check
                friendlyColour = self.colourToMove
        else:
            enemyColour = Piece.GetEnemyColour(friendlyColour)
        
        enemyKing   = enemyColour + Piece.king
        enemyPawn   = enemyColour + Piece.pawn
        enemyKnight = enemyColour + Piece.knight
        enemyBishop = enemyColour + Piece.bishop
        enemyRook   = enemyColour + Piece.rook
        enemyQueen  = enemyColour + Piece.queen
        
        rank = BoardRepresentation.RankIndex(square)
        file = BoardRepresentation.FileIndex(square)
        
        # Pawns
        enemyPawnSquares = ((1,1),(1,-1)) if Piece.IsColour(friendlyColour, Piece.white) else ((-1,1),(-1,-1))
        for enemyPawnSquare in enemyPawnSquares:
            tempRank = rank + enemyPawnSquare[0]
            tempFile = file + enemyPawnSquare[1]
            if 0 <= tempRank <= 7 and 0 <= tempFile <= 7:
                if self.squares[BoardRepresentation.RankFileToSquare(tempRank, tempFile)] == enemyPawn:
                    return True
        
        # Straights, Diagonals, Knight Moves
        directionTypes = (self.__cardinalDirections[:4], self.__cardinalDirections[4:], self.__knightDirections)
        piecesThatCouldCheckForDifferentDirections = ((enemyQueen, enemyRook), (enemyQueen, enemyBishop), (enemyKnight,))
        
        for directions, piecesThatCouldCheck, knightMoves in zip(directionTypes, piecesThatCouldCheckForDifferentDirections, [False, False, True]):
            for direction in directions:
                tempRank = rank
                tempFile = file
                
                one = True
                while True:
                    # Update the current square being checked
                    tempRank += direction[0]
                    tempFile += direction[1]
                    
                    if not (0 <= tempRank <= 7 and 0 <= tempFile <= 7):
                        # If off board
                        break
                    
                    endSquarePiece = self.GetBoardValue(tempRank, tempFile)
                    if endSquarePiece == Piece.none:
                        if knightMoves:
                            break
                        one = False
                        continue
                    elif endSquarePiece in piecesThatCouldCheck or (endSquarePiece == enemyKing and not knightMoves and one):
                        return True
                    else:
                        one = False
                        break
        return False

    def KingInCheck(self, colour):
        kingPos = self.kingSquares[self.whiteIndex] if colour == Piece.white else self.kingSquares[self.blackIndex]
        return self.SquareInCheck(kingPos, colour)

    def FindMove(self, moveToFind):
        startSquare = BoardRepresentation.NameToSquare(moveToFind[:2])
        endSquare = BoardRepresentation.NameToSquare(moveToFind[2:4])
        
        toPromoteTo = 0
        for move in self.__allLegalMoves:
            if move.startSquare == startSquare and move.endSquare == endSquare:
                # If promotion
                if move.isPromotion:
                    # If player hasn't chosen
                    if not toPromoteTo:
                        promotionChoice = input("Would you like to promote to a queen (q), knight (n) rook (r), bishop (b)?: ").lower()
                        toPromoteTo = ( Move.Flag.promoteToKnight if promotionChoice == "n"
                                         else Move.Flag.promoteToRook if promotionChoice == "r"
                                         else Move.Flag.promoteToBishop if promotionChoice == "b"
                                         else Move.Flag.promoteToQueen # Default queen
                                         )
                    
                    if move.moveFlag == toPromoteTo:
                        return move
                    
                # If not promotion
                else:
                    return move
        
        return False

    def Perft(self, depth, top=True):
        moves = self.CalculateAllLegalMoves()
        if depth == 1:
            return len(moves)
        else:
            if top:
                keys = []
                totals = []
                for move in moves:
                    self.MakeMove(move)
                    totals.append(self.Perft(depth-1, False))
                    keys.append(move)
                    self.UnmakeMove()
                i = 0
                l = len(keys)
                while i < l:
                    if keys[i].moveFlag == Move.Flag.pawnTwoForward:
                        keys.append(keys.pop(i))
                        totals.append(totals.pop(i))
                        l-=1
                    else:
                        i+=1
                return ("\n".join([f"{key}: {total}" for key, total in zip(keys, totals)]), sum(totals))
            else:   
                total = 0
                for move in moves:
                    self.MakeMove(move)
                    total += self.Perft(depth-1, False)
                    self.UnmakeMove()
                return total
    
    def Evaluate(self) -> int:
        evaluation = sum([Piece.PieceScore(piece, square, self.isEndGame) for square, piece in enumerate(self.squares)])
        
        return evaluation if self.whiteToMove else evaluation * -1
    
    def Search(self, depth, alpha=-1000000000, beta=1000000000, returnMove = True, endTime = False):
        if endTime and endTime < time.time():
            return False
        if depth == 0:
            return self.Evaluate()
        
        moves = self.CalculateAllLegalMoves()
        moves = self.OrderMoves(moves)
        if not moves:
            if self.KingInCheck(self.colourToMove):
                return -100000000
            return 0
        
        bestValue = -1000000000
        bestValueMove = None
        for move in moves:
            self.MakeMove(move)
            value = -self.Search(depth-1, -beta, -alpha, False)
            self.UnmakeMove()
            
            if endTime and endTime < time.time():
                return False
            
            if value > bestValue:
                bestValue = value
                bestValueMove = move
            
            if bestValue > alpha:
                alpha = bestValue
            
            if alpha >= beta:
                break
        
        return bestValueMove if returnMove else bestValue
    
    def CalculateBestMove(self, timeAllowed):
        endTime = time.time() + timeAllowed
        previousMove = None
        depth = 1
        while time.time() < endTime:
            move = self.Search(depth, endTime = endTime)
            if not move:
                return previousMove
            else:
                previousMove = move
                depth += 1
        return move    
    
    def OrderMoves(self, moves):
        return sorted(moves, key = self.__EvaluateMove)[::-1]
    
    def __EvaluateMove(self, move):
        moveScoreGuess = 0
        movePieceType = self.squares[move.startSquare]
        capturePieceType = self.squares[move.endSquare]
        
        # Prioritise capturing opponents most valuable pieces with our least valuable pieces
        if capturePieceType != Piece.none:
            moveSquareGuess = 10 * Piece.PieceScore(capturePieceType, move.endSquare, self.isEndGame) - Piece.PieceScore(movePieceType, move.startSquare, self.isEndGame)
            
        if move.isPromotion:
            moveScoreGuess += Piece.PieceScore(move.promotionPieceType, move.endSquare, self.isEndGame)
        
        return moveScoreGuess
    
    @property
    def isEndGame(self):
        return self.__plyCount >= self.__endGameMove