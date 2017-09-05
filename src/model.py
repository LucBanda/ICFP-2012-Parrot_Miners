import copy
import sys
import random

class LambdaMapState:
    """ A state of the game, i.e. the game board. These are the only functions which are
        absolutely necessary to implement UCT in any 2-player complete information deterministic
        zero-sum game, although they can be enhanced and made quicker, for example by using a
        GetRandomMove() function to generate a random move during rollout.
        By convention the players are numbered 1 and 2.
    """
    def __init__(self, lambda_map, robotpos=None):
        self.lambda_map = lambda_map
        self.killed = False
        self.score = 0
        self.won = False
        if robotpos:
            self.robotpos = robotpos
        else:
            self.lambdas = 0
            for x in range(len(self.lambda_map)):
                for y in range(len(self.lambda_map[0])):
                    if self.lambda_map[x][y] == "R":
                        self.robotpos = (x,y)
                    if self.lambda_map[x][y] == "\\":
                        self.lambdas += 1
            self.lambdamax = self.lambdas

    def Clone(self):
        clone = LambdaMapState(copy.deepcopy(self.lambda_map))
        clone.score = self.score
        clone.lambdas = self.lambdas
        clone.lambdamax = self.lambdamax
        clone.won = self.won
        clone.killed = self.killed
        return clone

    def DoMove(self, move):
        if move == "U":
            self.move(self.robotpos[0], self.robotpos[1], self.robotpos[0], self.robotpos[1] + 1)
        if move == "D":
            self.move(self.robotpos[0], self.robotpos[1], self.robotpos[0], self.robotpos[1] - 1)
        if move == "L":
            self.move(self.robotpos[0], self.robotpos[1], self.robotpos[0] - 1, self.robotpos[1])
        if move == "R":
            self.move(self.robotpos[0], self.robotpos[1], self.robotpos[0] + 1, self.robotpos[1])
        if move == "A":
            self.score += 25 * (self.lambdamax - self.lambdas)

        self.UpdateMap()

    def CheckValid(self, move):
        if move == 'A':
            return True
        if move == 'R':
            targetX = self.robotpos[0] + 1
            targetY = self.robotpos[1]
        elif move == 'L':
            targetX = self.robotpos[0] - 1
            targetY = self.robotpos[1]
        elif move == 'D':
            targetX = self.robotpos[0]
            targetY = self.robotpos[1] - 1
        elif move == 'U':
            targetX = self.robotpos[0]
            targetY = self.robotpos[1] + 1
        if (self.lambda_map[targetX][targetY] in [' ', '.', '\\', 'O']):
            return True
        if self.is_rock(self.lambda_map[targetX][targetY]):
            if (move == 'R') and self.lambda_map[targetX+1][targetY] == ' ':
                return True
            if (move == 'L') and self.lambda_map[targetX-1][targetY] == ' ':
                return True

        return False

    def GetMoves(self):
        if self.killed or self.won:
            return []
        moves = [move for move in ['R','L','U','D'] if self.CheckValid(move)]
        return moves

    def GetRandomMove(self):
        if not self.killed and not self.won:
            moves = self.GetMoves()
            if moves != []:
                return random.choice(moves)
        return None

    def GetResult(self):
        if self.killed:
            return self.score
        if self.won:
            return self.score
        return self.score

    def isTerminal(self, move):
        if self.killed or self.won:
            return True
        else:
            return False

    def __str__(self):
        map_str = ""
        height = len(self.lambda_map[0])
        width = len(self.lambda_map)
        for y in range(height):
            for x in range(width):
                map_str += (self.lambda_map[x][height - y - 1])
            map_str += "\n"
        if self.killed:
            print >> sys.stderr, 'Dead robot is dead :('
            # ~ print self.waterworld
            # ~ print self.wadlersbeard
        return map_str

    def is_rock(self, char):
        return (char == '*') or (char == '@')

    def UpdateMap(self):
        for x in range(len(self.lambda_map)):
            for y in range(len(self.lambda_map[x])):
                if self.is_rock(self.lambda_map[x][y]):
                    # Rock falling straigth
                    if self.lambda_map[x][y - 1] == ' ':
                        self.lambda_map[x][y - 1] = '*'
                        self.lambda_map[x][y] = ' '
                        # Rock rolling over rock to the right
                        self.am_i_dead((x, y - 1))
                    elif self.is_rock(self.lambda_map[x][y - 1]) and self.lambda_map[x + 1][y] == ' ' and \
                                    self.lambda_map[x + 1][y - 1] == ' ':
                        self.lambda_map[x + 1][y - 1] = self.lambda_map[x][y]
                        self.lambda_map[x][y] = ' '
                        # Rock rolling over rock to the left
                        self.am_i_dead((x + 1, y - 1))
                    elif self.is_rock(self.lambda_map[x][y - 1]) and (
                            self.lambda_map[x + 1][y] != ' ' or self.lambda_map[x + 1][y - 1] != ' ') and \
                                    self.lambda_map[x - 1][y] == ' ' and self.lambda_map[x - 1][y - 1] == ' ':
                        self.lambda_map[x - 1][y - 1] = self.lambda_map[x][y]
                        self.lambda_map[x][y] = ' '
                        # Rock rolling over lambda to the right
                        self.am_i_dead((x - 1, y - 1))
                    elif self.lambda_map[x][y - 1] == '\\' and self.lambda_map[x + 1][y] == ' ' and \
                                    self.lambda_map[x + 1][y - 1] == ' ':
                        self.lambda_map[x + 1][y - 1] = self.lambda_map[x][y]
                        self.lambda_map[x][y] = ' '
                        self.am_i_dead((x + 1, y - 1))
                # No lambdas left, opening lift
                if self.lambda_map[x][y] == 'L' and self.lambdas == 0:
                    self.lambda_map[x][y] = 'O'

    # If i have a rock over my head that's just been moved there, i'm dead :<
    # This must be called each time a rock moves
    def am_i_dead(self, rockpos):
        if self.robotpos[0] == rockpos[0] and self.robotpos[1] == rockpos[1] - 1:
            self.kill()

    def kill(self):
        self.killed = True

    def move(self, x, y, xp, yp):
        self.score -= 1
        if self.lambda_map[xp][yp] == ' ' \
                or self.lambda_map[xp][yp] == '.' \
                or self.lambda_map[xp][yp] == '\\' \
                or self.lambda_map[xp][yp] == '!':
            if self.lambda_map[xp][yp] == '\\':  # Pick up lambda
                self.lambda_pickedup = True
                self.lambdas -= 1
                self.score += 25
                # ~ if self.lambda_map[xp][yp] == '!': # Pick up razor
                # ~ self.wadlersbeard.pickupRazor()
            self.lambda_map[xp][yp] = 'R'
            self.lambda_map[x][y] = ' '
            self.robotpos = (xp, yp)
            return True
        # Pushing rock to the right
        elif xp == x + 1 and self.is_rock(self.lambda_map[xp][yp]) and self.lambda_map[x + 2][y] == ' ':
            self.lambda_map[xp + 1][yp] = self.lambda_map[xp][yp]
            self.lambda_map[xp][yp] = 'R'
            self.lambda_map[x][y] = ' '
            self.robotpos = (xp, yp)
            return True
        # Pushing rock to the left
        elif xp == x - 1 and self.is_rock(self.lambda_map[xp][yp]) and self.lambda_map[x - 2][y] == ' ':
            self.lambda_map[xp - 1][yp] = self.lambda_map[xp][yp]
            self.lambda_map[xp][yp] = 'R'
            self.lambda_map[x][y] = ' '
            self.robotpos = (xp, yp)
            return True
        # Going into open lift
        elif self.lambda_map[xp][yp] == 'O':
            self.score += 50 * self.lambdamax
            self.won = True
            self.lambda_map[xp][yp] = 'R'
            self.robotpos = (xp, yp)
            self.lambda_map[x][y] = ' '
            return True
        else:
            return False

