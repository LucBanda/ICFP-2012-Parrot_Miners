import copy
import sys
import random
from UCT import UCTModelBase

class LambdaMapState(UCTModelBase):
    """ A state of the game, i.e. the game board. These are the only functions which are
        absolutely necessary to implement UCT in any 2-player complete information deterministic
        zero-sum game, although they can be enhanced and made quicker, for example by using a
        GetRandomMove() function to generate a random move during rollout.
        By convention the players are numbered 1 and 2.
    """
    def __init__(self, lambda_map, robotpos=None):
        self.lambda_map = lambda_map
        self.killed = False
        self.score = 0.
        self.realScore = 0.
        self.win = False
        self.rocks=[]
        self.lambdaPos=[]
        if robotpos:
            self.robotpos = robotpos

        self.lambdas = 0
        self.robotpos = None
        for x in range(len(self.lambda_map)):
            for y in range(len(self.lambda_map[x])):
                if self.lambda_map[x][y] == "R":
                    self.robotpos = (x,y)
                if self.lambda_map[x][y] == "\\":
                    self.lambdas += 1
                    self.lambdaPos.append((x,y))
                if self.lambda_map[x][y] == "O" or self.lambda_map[x][y] == "L":
                    self.portal = (x,y)
                if self.lambda_map[x][y] == "*":
                    self.rocks.append((x,y))
        self.lambdamax = self.lambdas
        if not self.robotpos:
            pass

    def Clone(self):
        clone = LambdaMapState(copy.deepcopy(self.lambda_map))
        clone.score = self.score
        clone.realScore = self.realScore
        clone.lambdas = self.lambdas
        clone.lambdamax = self.lambdamax
        clone.win = self.win
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

        self.UpdateMap()

    def won(self):
        return self.win

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
        if self.killed or self.win or self.portal_is_blocked():
            return []
        moves = [move for move in ['R','L','U','D'] if self.CheckValid(move)]
        return moves

    def GetRandomMove(self):
        if not self.killed and not self.win:
            moves = self.GetMoves()
            if moves != []:
                return random.choice(moves)
        return None

    def GetResult(self):
        modified_score = self.score
        if self.win:
            return self.score

        if self.isTerminal():
            modified_score -= 25. * self.lambdamax
        elif self.lambda_map[self.portal[0]][self.portal[1]] == 'O':
            modified_score += 25. * self.lambdamax

        return modified_score

    def getAtoms(self):
        state = [('*',(x,y)) for (x,y) in self.rocks] \
        + [('\\',(x,y)) for (x,y) in self.lambdaPos] \
        + [(self.lambda_map[self.portal[0]][self.portal[1]], (self.portal[0],self.portal[1]))] \
        + [('R', (self.robotpos[0], self.robotpos[1]))] \
        + [("score", self.lambdas)]
        return [tuple(state)]

    def isTerminal(self):
        if self.killed or self.win or self.portal_is_blocked() or len(self.GetMoves()) == 0:
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
        return map_str

    def is_rock(self, char):
        return (char == '*') or (char == '@')

    def UpdateMap(self):
        self.newrocks = []
        for x, y in self.rocks:
            # Rock falling straigth
            if self.lambda_map[x][y - 1] == ' ':
                self.lambda_map[x][y - 1] = '*'
                self.lambda_map[x][y] = ' '
                self.newrocks.append((x,y-1))
                # Rock rolling over rock to the right
                self.am_i_dead((x, y - 1))
            elif self.is_rock(self.lambda_map[x][y - 1]) and self.lambda_map[x + 1][y] == ' ' and \
                            self.lambda_map[x + 1][y - 1] == ' ':
                self.lambda_map[x + 1][y - 1] = '*'
                self.lambda_map[x][y] = ' '
                self.newrocks.append((x+1, y - 1))
                # Rock rolling over rock to the left
                self.am_i_dead((x + 1, y - 1))
            elif self.is_rock(self.lambda_map[x][y - 1]) and (
                    self.lambda_map[x + 1][y] != ' ' or self.lambda_map[x + 1][y - 1] != ' ') and \
                            self.lambda_map[x - 1][y] == ' ' and self.lambda_map[x - 1][y - 1] == ' ':
                self.lambda_map[x - 1][y - 1] = '*'
                self.lambda_map[x][y] = ' '
                self.newrocks.append((x - 1, y - 1))
                # Rock rolling over lambda to the right
                self.am_i_dead((x - 1, y - 1))
            elif self.lambda_map[x][y - 1] == '\\' and self.lambda_map[x + 1][y] == ' ' and \
                            self.lambda_map[x + 1][y - 1] == ' ':
                self.lambda_map[x + 1][y - 1] = self.lambda_map[x][y]
                self.lambda_map[x][y] = ' '
                self.newrocks.append((x+1, y-1))
                self.am_i_dead((x + 1, y - 1))
            else:
                self.newrocks.append((x,y))

        self.rocks = self.newrocks
        self.rocks.sort(key = lambda x:x[1])
        self.rocks.sort(key = lambda x:x[0])

        # No lambdas left, opening lift
        if self.lambdas == 0 and self.lambda_map[self.portal[0]][self.portal[1]]:
            self.lambda_map[self.portal[0]][self.portal[1]] = 'O'

    # If i have a rock over my head that's just been moved there, i'm dead :<
    # This must be called each time a rock moves
    def am_i_dead(self, rockpos):
        if self.robotpos[0] == rockpos[0] and self.robotpos[1] == rockpos[1] - 1:
            self.kill()

    def kill(self):
        self.killed = True

    def portal_is_blocked(self):
        for (x,y) in [(self.portal[0] + 1, self.portal[1]),
                      (self.portal[0] - 1, self.portal[1]),
                      (self.portal[0], self.portal[1] + 1),
                      (self.portal[0], self.portal[1] - 1)]:
            if (x < 0) or (y < 0) or (x >= len(self.lambda_map)) or y >= (len(self.lambda_map[x])):
                continue
            if self.lambda_map[x][y] == '#' or self.lambda_map[x][y] == '*':
                continue
            if self.lambda_map[x][y] == '\\' or self.lambda_map == '.':
                for (x2, y2) in [(x + 1, y),
                               (x - 1, y),
                               (x, y + 1),
                               (x, y - 1)]:
                    if (x2 < 0) or (y2 < 0) or (x2 >= len(self.lambda_map)) or y2 >= (len(self.lambda_map[x])):
                        continue
                    if self.lambda_map[x2][y2] == '#' or self.lambda_map[x2][y2] == '*' or self.lambda_map[x2][y2] == 'L':
                        continue
                    return False
                continue
            return False # it should be either . \ ' ' R
        return True


    def move(self, x, y, xp, yp):
        self.score -= 2.
        self.realScore -= 1.
        if self.lambda_map[xp][yp] == ' ' \
                or self.lambda_map[xp][yp] == '.' \
                or self.lambda_map[xp][yp] == '\\' \
                or self.lambda_map[xp][yp] == '!':
            if self.lambda_map[xp][yp] == '\\':  # Pick up lambda
                self.lambda_pickedup = True
                self.lambdas -= 1
                self.score += 25.
                self.realScore += 25.
                self.lambdaPos.remove((xp,yp))
                # ~ if self.lambda_map[xp][yp] == '!': # Pick up razor
                # ~ self.wadlersbeard.pickupRazor()
            self.lambda_map[xp][yp] = 'R'
            self.lambda_map[x][y] = ' '
            self.robotpos = (xp, yp)
            return True
        # Pushing rock to the right
        elif xp == x + 1 and self.lambda_map[xp][yp] == '*' and self.lambda_map[x + 2][y] == ' ':
            self.lambda_map[xp + 1][yp] = '*'
            self.lambda_map[xp][yp] = 'R'
            self.lambda_map[x][y] = ' '
            self.rocks.append((xp + 1,yp))
            self.rocks.remove((xp, yp))
            self.robotpos = (xp, yp)
            return True
        # Pushing rock to the left
        elif xp == x - 1 and self.lambda_map[xp][yp] == '*' and self.lambda_map[x - 2][y] == ' ':
            self.lambda_map[xp - 1][yp] = '*'
            self.lambda_map[xp][yp] = 'R'
            self.lambda_map[x][y] = ' '
            self.robotpos = (xp, yp)
            self.rocks.append((xp - 1,yp))
            self.rocks.remove((xp, yp))
            return True
        # Going into open lift
        elif self.lambda_map[xp][yp] == 'O':
            self.score += 50. * self.lambdamax
            self.realScore += 50. * self.lambdamax
            self.win = True
            self.lambda_map[xp][yp] = 'R'
            self.robotpos = (xp, yp)
            self.lambda_map[x][y] = ' '
            return True
        else:
            return False

