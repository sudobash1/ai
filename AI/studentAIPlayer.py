
import random
import math

from Player import *
from Constants import *
from Construction import CONSTR_STATS
from Ant import UNIT_STATS
from Move import Move
from GameState import *
from Ant import *
from AIPlayerUtils import *


# Preference for which ant to attack first if there is a choice
ATTACK_PREFERENCE = [QUEEN, SOLDIER, R_SOLDIER, DRONE, WORKER]

#Grading weight for different factors
ANTSCOREWEIGHT = lambda x: 20 * math.atan(x/35. * math.pi)
FOODSCOREWEIGHT = lambda x: (x/2.-1.)**3+1.
CARRYINGWEIGHT = lambda x: x
HILLPROTECTIONWEIGHT = lambda x: x
WORKERLOCATIONPENALTY = lambda x: -x #Distance from goal is bad
SOLDIERLOCATIONSCORE = lambda x: 40 * x

#Grading weight for ant types count
#Queen, worker, drone, soldier, ranged soldier
antTypeGradingWeight = [
    lambda x: 0, #QUEEN
    lambda x: 20 * math.log(2) if x > 2 else 20 * math.log(x+.000001), #WORKER
    lambda x: 10 if x else 0, #DRONE
    lambda x: 11 * math.log(x+1), #SOLDIER
    lambda x: 3 * math.log(x+1), #RANGE SOLDIER
    ]

##
#AIPlayer
#Description: The responsbility of this class is to interact with the game by
#deciding a valid move based on a given game state. This class has methods that
#will be implemented by students in Dr. Nuxoll's AI course.
#
#Variables:
#   playerId - The id of the player.
##
class AIPlayer(Player):

    #__init__
    #Description: Creates a new Player
    #
    #Parameters:
    #   inputPlayerId - The id to give the new player (int)
    ##
    def __init__(self, inputPlayerId):
        super(AIPlayer,self).__init__(inputPlayerId, "INSERT COOL NAME HERE AI")

    ##
    #getPlacement
    #
    #Description: called during setup phase for each Construction that
    #   must be placed by the player.  These items are: 1 Anthill on
    #   the player's side; 1 tunnel on player's side; 9 grass on the
    #   player's side; and 2 food on the enemy's side.
    #
    #Parameters:
    #   construction - the Construction to be placed.
    #   currentState - the state of the game at this point in time.
    #
    #Return: The coordinates of where the construction is to be placed
    ##
    def getPlacement(self, currentState):
        numToPlace = 0
        #implemented by students to return their next move
        if currentState.phase == SETUP_PHASE_1:    #stuff on my side
            numToPlace = 11
            moves = []
            for i in range(0, numToPlace):
                move = None
                while move == None:
                    #Choose any x location
                    x = random.randint(0, 9)
                    #Choose any y location on your side of the board
                    y = random.randint(0, 3)
                    #Set the move if this space is empty
                    if currentState.board[x][y].constr == None and (x, y) not in moves:
                        move = (x, y)
                        #Just need to make the space non-empty. So I threw whatever I felt like in there.
                        currentState.board[x][y].constr == True
                moves.append(move)
            return moves
        elif currentState.phase == SETUP_PHASE_2:   #stuff on foe's side
            numToPlace = 2
            moves = []
            for i in range(0, numToPlace):
                move = None
                while move == None:
                    #Choose any x location
                    x = random.randint(0, 9)
                    #Choose any y location on enemy side of the board
                    y = random.randint(6, 9)
                    #Set the move if this space is empty
                    if currentState.board[x][y].constr == None and (x, y) not in moves:
                        move = (x, y)
                        #Just need to make the space non-empty. So I threw whatever I felt like in there.
                        currentState.board[x][y].constr == True
                moves.append(move)
            return moves
        else:
            return [(0, 0)]

    ##
    #getMove
    #Description: Gets the next move from the Player.
    #
    #Parameters:
    #   currentState - The state of the current game waiting for the player's move (GameState)
    #
    #Return: The Move to be made
    ##
    def getMove(self, currentState):

        moves = {}

        for move in listAllLegalMoves(currentState):
            hypotheticalState = self.hypotheticalMove(currentState, move)
            rating = self.evaluateMove(hypotheticalState)

            if not rating in moves:
                moves[rating] = [move]
            else:
                moves[rating].append(move)

        # randomly select from the best moves
        bestMoves = moves[max(moves.keys())]
        return bestMoves[random.randint(0, len(bestMoves) - 1)]

    ##
    #getAttack
    #Description: Gets the attack to be made from the Player
    #
    #Parameters:
    #   currentState - A clone of the current state (GameState)
    #   attackingAnt - The ant currently making the attack (Ant)
    #   enemyLocation - The Locations of the Enemies that can be attacked (Location[])
    ##
    def getAttack(self, currentState, attackingAnt, enemyLocations):
        target = None
        for coords in enemyLocations:
            ant = getAntAt(currentState, coords)
            if (not target or
                ATTACK_PREFERENCE.index(ant.type) < ATTACK_PREFERENCE.index(target.type)
                ):
                target = ant

        return target.coords


    ##
    #hypotheticalMove
    #
    #Description: Determine what the agent's state would look like after a given move.
    #             We Will assume that all Move objects passed are valid.
    #
    #Parameters:
    #   state - A clone of the theoretical state given (GameState)
    #   move - a list of all move objects passed (Move)
    #
    #Returns:
    #   What the agent's state would be like after a given move.
    ##
    def hypotheticalMove(self, state, move):
        newState = state.clone()
        if move.moveType == END:
            return newState
        elif move.moveType == MOVE_ANT:
            ant = getAntAt(newState, move.coordList[0])
            ant.coords = move.coordList[-1]

            #check if ant can attack
            targets = [] #coordinates of attackable ants
            range = UNIT_STATS[ant.type][RANGE]

            for ant in newState.inventories[1 - self.playerId].ants:
                dist = math.sqrt((ant.coords[0] - ant.coords[0]) ** 2 +
                                 (ant.coords[1] - ant.coords[1]) ** 2)
                if dist <= range:
                    #target is in range and may be attacked
                    targets.append(ant.coords)

            if targets:
                #Attack the ant chosen by the AI
                target = self.getAttack(newState, ant, targets)
                targetAnt = getAntAt(newState, target)
                targetAnt.health -= UNIT_STATS[ant.type][ATTACK]

                if targetAnt.health <= 0:
                    #Remove the dead ant
                    newState.board[target[0]][target[1]].ant = None
                    newState.inventories[1 - self.playerId].ants.remove(targetAnt)

        else: #Move type BUILD
            if move.buildType in (WORKER, DRONE, SOLDIER, R_SOLDIER):
                #Build ant on hill
                ant = Ant(move.coordList[0], move.buildType, self.playerId)
                newState.board[move.coordList[0][0]][move.coordList[0][1]].ant = ant
                newState.inventories[self.playerId].ants.append(ant)

                newState.inventories[self.playerId].foodCount -= UNIT_STATS[move.buildType][COST]
            else:
                #build new building
                building = Building(move.coordList[0], move.buildType, self.playerId)
                newState.board[move.coordList[0][0]][move.coordList[0][1]].constr = building
                newState.inventories[self.playerId].constrs.append(building)

                newState.inventories[self.playerId].foodCount -= CONSTR_STATS[move.buildType][BUILD_COST]

        return newState


    def scoreAnts(self, ants, type):
        count = 0.

        for ant in ants:
            if ant.type == type:
                count += float(ant.health) / float(UNIT_STATS[ant.type][HEALTH])

        return antTypeGradingWeight[type](count)


    def getPlayerScore(self, hypotheticalState, playerNo):

        #get the number of ants on the board, and for certain types of ants
        antScore = 0
        for type in (WORKER, DRONE, SOLDIER, R_SOLDIER):
            antScore += self.scoreAnts(hypotheticalState.inventories[playerNo].ants, type)

            if playerNo == self.playerId and type == WORKER:
                print antScore

        #get the food count from the move
        foodScore = hypotheticalState.inventories[playerNo].foodCount

        #get the total food which will be being carried at the end of this turn
        carrying = 0
        for worker in getAntList(hypotheticalState, playerNo, (WORKER,)):
            if not worker.carrying:
                # Check if the worker is standing on a food source
                if getConstrAt(hypotheticalState, worker.coords) == FOOD:
                    carrying += 1


        #workers get bonus points for being closer to a goal
        workerLocationPenalty = 0
        for worker in getAntList(hypotheticalState, playerNo, (WORKER,)):
            if worker.carrying:
                goals = [b.coords for b in getConstrList(hypotheticalState, self.playerId, (ANTHILL, TUNNEL))]
            else:
                goals = [f.coords for f in getConstrList(hypotheticalState, None, (FOOD,))]

            wc = worker.coords
            dist = min(abs(wc[0]-gc[0]) + abs(wc[1]-gc[1]) for gc in goals)

            workerLocationPenalty += dist

        if workerLocationPenalty:
            workerLocationPenalty /= len(getAntList(hypotheticalState, playerNo, (WORKER,)))

        #war ants get bonus points for being on the other side of the field
        soldierLocationScore = 0
        for soldier in getAntList(hypotheticalState, playerNo, (SOLDIER, R_SOLDIER, DRONE)):
            if soldier.coords[1] > 3:
                soldierLocationScore += 1

        if soldierLocationScore:
            soldierLocationScore /= len(getAntList(hypotheticalState, playerNo, (SOLDIER, R_SOLDIER, DRONE)))

        #get anthill protection
        #how do you grade this?
        hillProtectionScore = 0

        if self.playerId == playerNo:
            asciiPrintState(hypotheticalState)
            print ANTSCOREWEIGHT(antScore)

        return (ANTSCOREWEIGHT(antScore) +
                FOODSCOREWEIGHT(foodScore) +
                CARRYINGWEIGHT(carrying) +
                WORKERLOCATIONPENALTY(workerLocationPenalty) +
                SOLDIERLOCATIONSCORE(soldierLocationScore) +
                HILLPROTECTIONWEIGHT(hillProtectionScore))


    def hasWon(self, hypotheticalState, playerNo):

        #Check if enemy anthill has been captured
        for constr in hypotheticalState.inventories[1 - playerNo].constrs:
            if constr.type == ANTHILL and constr.captureHealth == 1:
                #This anthill will be destroyed if there is an opposing ant sitting on it
                for ant in hypotheticalState.inventories[playerNo].ants:
                    if tuple(ant.coords) == tuple(constr.coords):
                        return True
                break

        #Check if enemy queen is dead
        for ant in hypotheticalState.inventories[1 - playerNo].ants:
            if ant.type == QUEEN and ant.health == 0:
                return True

        #Check if we have 11 food
        if hypotheticalState.inventories[playerNo].foodCount >= 11:
            return True

        return False


    ##
    #evaluateMove
    #
    #Description: Examines a GameState and ranks how "good" that state is for the agent whose turn it is.
    #              A rating is given on the players state. 1.0 is if the agent has won, 0.0 if the enemy has won,
    #              any value > 0.5 means the agent is winning.
    #
    #Parameters:
    #   hypotheticalState - The state being considered by the AI for ranking.
    #
    #Return:
    #   The move rated as the "best"
    ##
    def evaluateMove(self, hypotheticalState):

        #Check if the game is over
        if self.hasWon(hypotheticalState, self.playerId):
            return 1.0
        elif self.hasWon(hypotheticalState, 1 - self.playerId):
            return 0.0

        playerScore = self.getPlayerScore(hypotheticalState, self.playerId)
        enemyScore = self.getPlayerScore(hypotheticalState, 1 - self.playerId)

        #Normalize the score to be between 0.0 and 1.0
        return (math.atan(playerScore - enemyScore) + math.pi/2) / math.pi


"""
        AITurn = hypotheticalState.whoseTurn #reference value for this AI agent

        #store the enemy score (for reference to see if this agent is winning)
        enemyScore = 0
        enemyTurn = None
        if AITurn == 0:
            enemyTurn = 1
        else:
            enemyTurn = 0
        eNumberAnts = len(getAntList(hypotheticalState, enemyTurn,(QUEEN, WORKER, DRONE, SOLDIER, R_SOLDIER)))
        eNumWorkers = len(getAntList(hypotheticalState, enemyTurn,(None, WORKER, None, None, None)))
        eNumDrones = len(getAntList(hypotheticalState, enemyTurn,(None, None, DRONE, None, None)))
        eNumSoldiers = len(getAntList(hypotheticalState, enemyTurn,(None, None, None, SOLDIER, R_SOLDIER)))
        efoodScore = hypotheticalState.inventories[enemyTurn].foodCount
        #store the enemy score
        enemyScore = .2*(eNumberAnts) + .1*(eNumWorkers) + .05*(eNumDrones) + .1*(eNumSoldiers) + .3*(eFoodScore)
        """
