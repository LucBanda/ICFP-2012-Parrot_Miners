import networkx as nx

class Node:
    idMax = 0
    def __init__(self, move, state, parent):
        self.id = self.idMax
        self.idMax += 1
        self.state = state
        self.move = move
        self.untriedMoves = state.GetMoves()  # future child nodes

class PathExplorer(nx.Graph):
    def __init__(self, rootstate):
        self.rootState = rootstate

    def ConstructGraph(self):
        state = self.rootState
        idx = 0
        while 1:
            node = self.add_node(Node(None, state, None))
            for move in node.untriedMoves:



    def playMove(self, move):
        for child in self.rootNode.childNodes:
            if child.move == move:
                self.rootNode = child
                break
        self.rootState.DoMove(move)

    def run(self):
        """ Conduct a UCT search for itermax iterations starting from rootstate.
            Return the best move from the rootstate.
            Assumes 2 alternating players (player 1 starts), with game results in the range [0.0, 1.0]."""
        startTime = time.time()
        number_of_addchild = 0
        number_of_evolution = 0
        while not self.timeout or (time.time() - startTime < self.timeout - 0.20):
            # iterMax = 20000
            # while iterMax:
            #    iterMax -= 1
            explored = 0
            node = self.rootNode

            # Select
            while node.untriedMoves == [] and node.childNodes != []:  # node is fully expanded and non-terminal
                node = node.UCTSelectChild()
                explored += 1

            if explored:
                state = node.state.Clone()
            else:
                state = self.rootState.Clone()

            # Expand
            if node.untriedMoves != []:  # if we can expand (i.e. state/node is non-terminal)
                m = random.choice(node.untriedMoves)
                state.DoMove(m)
                node = node.AddChild(m, state)  # add child and descend tree
                number_of_addchild += 1
                number_of_evolution += 1
                if self.displayDebug:
                    state.displayMove(m, 'g-')
            else:
                break
            # Rollout - this can often be made orders of magnitude quicker using a state.GetRandomMove() function
            bestResult = 0
            for i in range(0, self.multipleRollout):
                # if True:
                stateRollout = state.Clone()
                depthAllowed = self.depthMax
                rolloutNode = node
                while depthAllowed > 0:  # while state is non-terminal
                    m = stateRollout.GetRandomMove()
                    if m:
                        stateRollout.DoMove(m)
                        number_of_evolution += 1
                        if self.displayDebug:
                            stateRollout.displayMove(m, 'y-')
                    depthAllowed -= 1
                # Backpropagate
                # Backpropagate
                while rolloutNode != None:  # backpropagate from the expanded node and work back to the root node
                    rolloutNode.Update(
                        stateRollout.GetResult())  # state is terminal. Update node with result from POV of node.playerJustMoved
                    rolloutNode = rolloutNode.parentNode

        if self.charged and explored < 5:
            self.multipleRollout = max(self.multipleRollout - 1, 1)
        elif not self.charged and explored > 1:
            self.charged = True
        elif explored > 10:
            self.multipleRollout += 1

        printErr("explored : " + str(number_of_addchild) + " evolved : " + str(
            number_of_evolution) + " explored : " + str(explored) + " multiple factor : " + str(
            self.multipleRollout), file=sys.stderr)
        bestMoves = sorted(self.rootNode.childNodes, key=lambda c: c.visits)
        if bestMoves:
            return bestMoves[-1].move  # return the move that was most visited
        else:
            return None
