import sys, os,  tty, termios
import copy
from threading import Event
from UCT import UCT
from math import *

	
class SimulatorDieEvent:
	stop_that=Event()
	def __init__(self):
		pass

class controler:
	def __init__(self, world):
		self.world = world

class kcontroler(controler):
	def __init__(self, world):
		controler.__init__(self, world)

	def get_next(self):
		fd = sys.stdin.fileno()
		old_settings = termios.tcgetattr(fd)
		tty.setraw(fd)
		key = sys.stdin.read(1)
		termios.tcsetattr(fd, termios.TCSANOW, old_settings)
	# in raw terminal mode CTRL+C is ASCII code 0x03
	# We exit upon CTRL+C
		if key == ' ':
			os.system("reset")
			SimulatorDieEvent.stop_that.set()
			sys.exit(0)

		if key == "z":
			return "U"
		if key == "s":
			return "D"
		if key == "q":
			return "L"
		if key == "d":
			return "R"
		if key == "a":
			return "A"
		if key == "w":
			return "W"
		if key == "e":
			return "S"

ACTIONS = ["U", "R", "L", "D"]

class explorerstate:
	def __init__(self):
		self.actionsresults = {}
		self.actionspoints = {}
		self.hope = 0
		self.maxhopeaction = "A"
		self.visited = False
		
	def explore(self, world, move, ASV):
		if world.set_movement(move):
			world_hash = world.hash()
			if world_hash not in ASV:
				self.actionsresults[move] = explorerstate()
				self.actionspoints[move] = world.get_points()
				ASV[world_hash] = self.actionsresults[move]
				return True
			else:
				self.actionsresults[move] = ASV[world_hash]
				self.actionspoints[move] = world.get_points()
		
		else:
			self.actionsresults[move] = None
			self.actionspoints[move] = None
		return False

	def __str__(self):
		print hex(id(self))
		#~ for key, value in self.actionsresults.iteritems():
			#~ print key, " : "
			#~ if value != None:
				#~ MapDrawer(value.lambda_map).draw()
		# TODO : print the map
		print "hope : ", self.hope
		print "maxkey : ", self.maxhopeaction
		print "scoring :", self.actionspoints
		print "worlds :", self.actionsresults
		print "visited :", self.visited
		return ""

class botcontroler(controler):
	
	def __init__(self, world):
		controler.__init__(self, world)
		self.explorer = UCT(world, None, 30, 200)

	def explore_step(self):
		self.explorer.run()
		return True

	def get_result(self):
		self.explorer.printResult()
		return self.explorer.GetResult()
