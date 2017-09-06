# This is a very simple implementation of the UCT Monte Carlo Tree Search algorithm in Python 2.7.
# The function UCT(rootstate, itermax, verbose = False) is towards the bottom of the code.
# It aims to have the clearest and simplest possible code, and for the sake of clarity, the code
# is orders of magnitude less efficient than it could be made, particularly by using a 
# state.GetRandomMove() or state.DoRandomRollout() function.
# 
# Example GameState classes for Nim, OXO and Othello are included to give some idea of how you
# can write your own GameState use UCT in your 2-player game. Change the game to be played in 
# the UCTPlayGame() function at the bottom of the code.
# 
# Written by Peter Cowling, Ed Powley, Daniel Whitehouse (University of York, UK) September 2012.
# 
# Licence is granted to freely use and distribute for any sensible/legal purpose so long as this comment
# remains in any distributed code.
# 
# For more information about Monte Carlo Tree Search check out our web site at www.mcts.ai
import signal
from math import *
import time
import random
import os
import numpy as np
import sys

def printErr(str):
    sys.stderr.write(str + "\n")

class Node:
    """ A node in the game tree. Note wins is always from the viewpoint of playerJustMoved.
        Crashes if state not specified.
    """
    maxScoreInGame = 0
    minScoreInGame = 0
    def __init__(self, move = None, parent = None, state = None):
        self.move = move # the move that got us to this node - "None" for the root node
        self.parentNode = parent # "None" for the root node
        self.childNodes = np.array([])
        self.wins = 0
        self.visits = 0
        self.untriedMoves = state.GetMoves() # future child nodes
        self.state = state
        self.maxScore = None

    def UCTSelectChild(self, explore = 1):
        """ Use the UCB1 formula to select a child node. Often a constant UCTK is applied so we have
            lambda c: c.wins/c.visits + UCTK * sqrt(2*log(self.visits)/c.visits to vary the amount of
            exploration versus exploitation.
        """
        s = sorted(self.childNodes, key=lambda c: c.maxScore + explore * sqrt(2*log(self.visits) / c.visits))[-1]
        #s = sorted(self.childNodes, key=lambda c: c.wins / c.visits)[-1]
        return s
    
    def AddChild(self, m, s):
        """ Remove m from untriedMoves and add a new child node for this move.
            Return the added child node
        """
        n = Node(move = m, parent = self, state = s)
        self.untriedMoves.remove(m)
        self.childNodes = np.append(self.childNodes, n)
        return n
    
    def Update(self, result):
        """ Update this node - one additional visit and result additional wins. result must be from the viewpoint of playerJustmoved.
        """
        self.visits += 1
        if Node.maxScoreInGame < result:
            Node.maxScoreInGame = result
        if Node.minScoreInGame > result:
            Node.minScoreInGame = result
        #normalize scores
        result = (result - Node.minScoreInGame) / (Node.maxScoreInGame - Node.minScoreInGame)

        if not self.maxScore or self.maxScore < result:
            self.maxScore = result
        self.wins += result

    def __repr__(self):
        return "[M:" + str(self.move) + " W/V:" + str(self.wins) + "/" + str(self.visits) + " U:" + str(self.untriedMoves) + "]"

    def TreeToString(self, indent):
        s = self.IndentString(indent) + str(self)
        for c in self.childNodes:
             s += c.TreeToString(indent+1)
        return s

    def IndentString(self,indent):
        s = "\n"
        for i in range (1,indent+1):
            s += "| "
        return s

    def ChildrenToString(self):
        s = ""
        for c in self.childNodes:
             s += str(c) + "\n"
        return s

class UCTModelBase:
    def __init__(self):
        pass

    def Clone(self):
        return UCTModelBase()

    def DoMove(self, move):
        #executes the move
        pass

    def GetResult(self):
        #returns the score of the state
        return 0

    def GetMoves(self):
        #return the list of available moves
        return []

    def GetRandomMove(self):
        #return a randomMove
        pass

    def isTerminal(self):
        #return True if state if a win or a loss
        return False

    def won(self):
        #return True if state is a win
        return False

class UCT:

    def __init__(self, rootstate, timeout, depthMax=50, mcDispersion = 50, printf_debug=True):
        self.printf_debug = printf_debug
        self.timeout = timeout
        self.depthMax = depthMax
        self.rootNode = Node(state = rootstate)
        self.rootState = rootstate
        self.stop = False
        self.number_of_evolutions = 0
        self.mcDispersion = mcDispersion

    def playMove(self, move):
        for child in self.rootNode.childNodes:
            if child.move == move:
                self.rootNode = child
                break
        self.rootState.DoMove(move)

    def stop_loop(self):
        self.stop = True

    def set_infinite_sigint_loot(self):
        signal.signal(signal.SIGINT, lambda signum, frame: self.stop_loop())

    def run(self, timeout=None):
        """ Conduct a UCT search for itermax iterations starting from rootstate.
            Return the best move from the rootstate.
            Assumes 2 alternating players (player 1 starts), with game results in the range [0.0, 1.0]."""
        number_of_addchild = 0
        self.startTime = time.time()

        self.won = 0
        self.lose = 0
        if not timeout:
            self.set_infinite_sigint_loot()
        while not self.stop:
            explored = 0
            node = self.rootNode
            state = self.rootState.Clone()

            # Select
            while node.untriedMoves == [] and not state.isTerminal():  # node is fully expanded and non-terminal
                if node.childNodes.size == 0:
                    pass
                node = node.UCTSelectChild()
                state.DoMove(node.move)
                explored += 1

            if explored > 0:
                if state.isTerminal():
                    if state.won():
                        self.won += 1
                        if self.won > 100:
                            break
                    else:
                        self.lose += 1
                        if self.lose > 100:
                            #reset
                            self.rootNode = Node(state = self.rootState)
                            self.won = 0
                            self.lose = 0
                            continue
                    while node != None:  # backpropagate from the expanded node and work back to the root node
                        node.Update(state.GetResult())  # state is terminal. Update node with result from POV of node.playerJustMoved
                        node = node.parentNode
                    #printErr("explored : " + str(number_of_addchild) + " evolved : " + str(
                    #    self.number_of_evolutions) + " length : " + str(explored))
                    continue
                else:
                    self.lose = 0

            if node.untriedMoves != []: # if we can expand (i.e. state/node is non-terminal)
                m = random.choice(node.untriedMoves)
                state.DoMove(m)
                node = node.AddChild(m,state) # add child and descend tree
                number_of_addchild += 1
                self.number_of_evolutions += 1

            # Rollout - this can often be made orders of magnitude quicker using a state.GetRandomMove() function
            bestScore = None
            for i in range(0, self.mcDispersion):
                iteration = 0
                rolloutState = state.Clone()
                rolloutNode = node
                while (not rolloutState.isTerminal() and iteration < self.depthMax): # while state is non-terminal
                    m = rolloutState.GetRandomMove()
                    if m:
                        rolloutState.DoMove(m)
                        self.number_of_evolutions += 1
                    iteration += 1
                score = rolloutState.GetResult()
                if not bestScore or bestScore < score:
                    bestScore = score
            if not bestScore:
                bestScore = state.GetResult()
            while rolloutNode != None: # backpropagate from the expanded node and work back to the root node
                rolloutNode.Update(bestScore) # state is terminal. Update node with result from POV of node.playerJustMoved
                rolloutNode = rolloutNode.parentNode

            if timeout > time.time() - self.startTime:
                self.stop_loop()

            if self.printf_debug:
                os.system("clear")
                print state
                printErr("explored : " + str(number_of_addchild)
                         + " evolved : " + str(self.number_of_evolutions)
                         + " length : " + str(explored)
                         + " won : " + str(self.won)
                         + " lost :" + str(self.lose))

        print ("Solution Found")
        self.stopTime = time.time()
        return self.GetResult()

    def GetResult(self):
        result = []
        node = self.rootNode
        state = self.rootState
        while node.untriedMoves == [] and node.childNodes.size != 0:  # node is fully expanded and non-terminal
            node = sorted(node.childNodes, key = lambda c: c.visits)[-1]
            result.append(node.move)
        return result # return the move that was most visited


    def printResult(self):
        node = self.rootNode
        state = self.rootState
        print "printing result"
        while node.untriedMoves == [] and node.childNodes.size != 0:  # node is fully expanded and non-terminal
            node = sorted(node.childNodes, key = lambda c: c.visits)[-1]
            state.DoMove(node.move)
            os.system("clear")
            print state
            time.sleep(0.15)
        print str(int(self.number_of_evolutions / (self.stopTime - self.startTime)))
        print node.state.GetResult()
