from Board import *

def main():
    while True:
        try:
            playerFen = input("Would you like to play with a custom FEN. If so put it here, or press enter for a default board: ")
            if playerFen:
                b = Board(playerFen)
            else:
                b = Board()
            break
        except:
            print("Invalid FEN")
    
    playingAgainst = ["f","r","c"].index(input("Would you like to play against a computer (c), random opponent (r) or against a friend (f)?: ").lower())
    if playingAgainst: # Not playing versus friend
        if playingAgainst == 2:
            mirror = input("Would you like the computer to take the same time as you per move (m), or a set time (s)?: ") == "m"
        playerColourChoice = input("Would you like to play as white (w), black (b), or a random colour (r)?: ").lower()
        playerColour = playerColourChoice if playerColourChoice in ["w","b"] else random.choice(["w","b"])
        playerWhite = playerColour == "w"
    else:
        # Stops the computer playing
        playerTurn = True
    
    print("Moves can either be inputted as the start position, then it tells you the legal end positions and then you put the end position, or you type them both next to each other (eg. \"e2e4\")")
    # Main loop
    while True:
        if len(b.CalculateAllLegalMoves()) == 0:
            b.DisplayBoard()
            if b.KingInCheck(Piece.white):
                print("Black won!")
            elif b.KingInCheck(Piece.black):
                print("White won!")
            else:
                print("It's a draw")
            print("Moves played:")
            for index in range(len(b.moveList)//2):
                print(f"{index}. {b.moveList[index*2]} {b.moveList[index*2+1]}")
            if len(b.moveList) % 2 == 1:
                print(f"{len(b.moveList)//2+1}. {b.moveList[-1]}")
            break
        
        if not playingAgainst: # If playing against friend
            boardDisplaySide = b.whiteToMove
        else:
            playerTurn = playerWhite and b.whiteToMove or not playerWhite and not b.whiteToMove
            boardDisplaySide = playerWhite
        
        if playerTurn:
            b.DisplayBoard(boardDisplaySide)
            moves = b.CalculateAllLegalMoves()
            turnStartTime = time.time()
            while True:
                try:
                    start = input("\nEnter start or move: ")
                    
                    if start == "undo":
                        b.UnmakeMove()
                        if playingAgainst:
                            b.UnmakeMove()
                            
                    elif len(start) == 2:
                        legalEnds = []
                        for move in moves:
                            if move.startSquare == BoardRepresentation.NameToSquare(start):
                                legalEnds.append(BoardRepresentation.SquareToName(move.endSquare))
                        if len(legalEnds) == 0:
                            print("No legal moves from that square")
                            continue
                        else:
                            print(f"You can move to: {', '.join(legalEnds)}")
                            move = b.FindMove(start + input("Enter end: "))
                            b.MakeMove(move)
                        
                    elif len(start) == 4:
                        b.MakeMove(b.FindMove(start))
                    
                    else:
                        print("Invalid move")
                        continue
                    
                    playerMoveTime = time.time() - turnStartTime
                    break
                
                except:
                    print("Invalid move")
                    continue
        
        elif playingAgainst == 1:
            move = random.choice(b.CalculateAllLegalMoves())
            b.MakeMove(move)
        elif playingAgainst == 2:
            if mirror:
                b.MakeMove(b.CalculateBestMove(playerMoveTime))
            else:
                b.MakeMove(b.CalculateBestMove(5))

import time
def FindTime(func, tests, *args, **kwargs):
    total = 0
    for _ in range(tests):
        startTime = time.time()
        func(*args, **kwargs)
        total += time.time() - startTime
    return total

def test(fen=None, max=5):
    if fen:
        b=Board(fen)
    else:
        b = Board()
    b.DisplayBoard()
    for num in range(1,max+1):
        timeBefore = time.time()
        result = b.Perft(num)
        totalTime = time.time() - timeBefore
        if num == 1:
            print(f"{num}\t{result}\t{totalTime}")
        else:
            print(f"{num}\t{result[1]}\t{totalTime}")

def RunTests(file):
    tests = open(file, "r").read().split("\n")
    for index, test in enumerate(tests):
        parts = test.split(",")
        b = Board(parts[2])
        timeBefore = time.time()
        found = b.Perft(int(parts[0]))[1]
        passed = found == int(parts[1])
        print(f"""Test {index+1} of {len(tests)}\tPassed: {passed}
              \tFound: {found}
              \tExpected: {parts[1]}
              \tTime taken: {time.time()-timeBefore}
              \tDepth: {parts[0]}
              \tPosition: {parts[2]}
              """)

if __name__ == "__main__":
    main()
