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
    def __init__(self, move = None, parent = None, state = None):
        self.move = move # the move that got us to this node - "None" for the root node
        self.parentNode = parent # "None" for the root node
        self.childNodes = np.array([])
        self.wins = 0
        self.visits = 0
        self.untriedMoves = state.GetMoves() # future child nodes
        self.state = state
        self.maxScore = None

    def UCTSelectChild(self):
        """ Use the UCB1 formula to select a child node. Often a constant UCTK is applied so we have
            lambda c: c.wins/c.visits + UCTK * sqrt(2*log(self.visits)/c.visits to vary the amount of
            exploration versus exploitation.
        """
        s = sorted(self.childNodes, key=lambda c: c.maxScore
                    + (self.state.lambda_map[self.state.portal[0]][self.state.portal[1]] == "O") /
                      ((abs(self.state.robotpos[0] - self.state.portal[0]) + abs(self.state.robotpos[1] - self.state.portal[1])) * self.visits))[-1]

        #s = sorted(self.childNodes, key=lambda c: c.wins / c.visits + sqrt(log(self.visits) / c.visits)
        #            + (self.state.lambda_map[self.state.portal[0]][self.state.portal[1]] == "O") /
        #              ((abs(self.state.robotpos[0] - self.state.portal[0]) + abs(self.state.robotpos[1] - self.state.portal[1])) * self.visits))[-1]
        #s = sorted(self.childNodes, key=lambda c: c.wins / c.visits + sqrt(log(self.visits) / c.visits) + sqrt(100/c.visits))[-1]
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
        self.wins += result
        if not self.maxScore or self.maxScore < result:
            self.maxScore = result

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


class UCT:

    stabilityRef = 100
    def __init__(self, rootstate, timeout, depthMax, k):
        self.timeout = timeout
        self.depthMax = depthMax
        self.rootNode = Node(state = rootstate)
        self.rootState = rootstate
        self.multipleRollout = k
        self.stop = False
        self.number_of_evolutions = 0
    def playMove(self, move):
        for child in self.rootNode.childNodes:
            if child.move == move:
                self.rootNode = child
                break
        self.rootState.DoMove(move)
        self.resultStability = self.stabilityRef

    def stop_loop(self):
        self.stop = True

    def run(self):
        """ Conduct a UCT search for itermax iterations starting from rootstate.
            Return the best move from the rootstate.
            Assumes 2 alternating players (player 1 starts), with game results in the range [0.0, 1.0]."""
        startTime = time.time()
        number_of_addchild = 0
        self.startTime = time.time()

        signal.signal(signal.SIGINT, lambda signum, frame:self.stop_loop())

        while not self.stop:
            explored = 0
            node = self.rootNode

            # Select
            while node.untriedMoves == [] and node.childNodes.size != 0:  # node is fully expanded and non-terminal
                node = node.UCTSelectChild()
                explored += 1

            if explored > 0:
                state = node.state.Clone()
                print state
                if state.isTerminal(node.move):
                    if node.state.won:
                        break
                    while node != None:  # backpropagate from the expanded node and work back to the root node
                        node.Update(state.GetResult())  # state is terminal. Update node with result from POV of node.playerJustMoved
                        node = node.parentNode
                    printErr("explored : " + str(number_of_addchild) + " evolved : " + str(
                        self.number_of_evolutions) + " length : " + str(explored) + " multiple factor : " + str(
                        self.multipleRollout))

                    continue
            else:
                state = self.rootState.Clone()

            if node.untriedMoves != []: # if we can expand (i.e. state/node is non-terminal)
                m = random.choice(node.untriedMoves)
                state.DoMove(m)
                node = node.AddChild(m,state) # add child and descend tree
                number_of_addchild += 1
                self.number_of_evolutions += 1


            # Rollout - this can often be made orders of magnitude quicker using a state.GetRandomMove() function
            bestscore = None
            for i in range(0, self.multipleRollout):
                stateRollout = state.Clone()
                rolloutNode = node
                terminal = False
                iteration = 0
                m=None
                while (not stateRollout.isTerminal(m) and not terminal): # while state is non-terminal
                    m = stateRollout.GetRandomMove()
                    if m:
                        stateRollout.DoMove(m)
                        self.number_of_evolutions += 1
                    iteration += 1
                    score = stateRollout.GetResult()
                    if not bestscore or bestscore < score:
                        bestscore = score
                    if iteration > self.depthMax:
                        terminal = True
            if not bestscore:
                bestscore = state.GetResult()
            while rolloutNode != None: # backpropagate from the expanded node and work back to the root node
                rolloutNode.Update(bestscore) # state is terminal. Update node with result from POV of node.playerJustMoved
                rolloutNode = rolloutNode.parentNode

            printErr("explored : " + str(number_of_addchild) + " evolved : " + str(self.number_of_evolutions) + " length : " + str(explored) + " multiple factor : " + str(self.multipleRollout))

        self.stopTime = time.time()
        return self.GetResult()

    def GetResult(self):
        result = []
        node = self.rootNode
        state = self.rootState
        while node.untriedMoves == [] and node.childNodes.size != 0:  # node is fully expanded and non-terminal
            node = node.UCTSelectChild()
            result.append(node.move)
        return result # return the move that was most visited


    def printResult(self):
        node = self.rootNode
        print "printing result"
        while node.untriedMoves == [] and node.childNodes.size != 0:  # node is fully expanded and non-terminal
            node = node.UCTSelectChild()
            os.system("clear")
            print node.state
            time.sleep(0.25)
        print str(int(self.number_of_evolutions / (self.stopTime - self.startTime)))
        print node.state.GetResult()
