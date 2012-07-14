#!/usr/bin/env python
# -*- indent-tabs-mode: t -*-


import sys, os, signal, time
from threading import Thread
from threading import Event
from displayer import MapDrawer
from mapupdater import world
from controler import controler, kcontroler, botcontroler, SimulatorDieEvent

if len(sys.argv) == 3:
	debug = True
else:
	debug = False

def reset_tty_and_exit():
	#termios.tcsetattr(fd, termios.TCSANOW, old_settings)
	SimulatorDieEvent.stop_that.set()
	os.system("reset")
	time.sleep(1)
	sys.exit(0)
	

		
limiter_thread=None

def handler(signum, frame):
	print 'Signal ', signum, 'catched'
	if signum == signal.SIGINT:
		print 'SIGINT, we exit !'
		cont.set_movement("A")
		reset_tty_and_exit()
	if signum == signal.SIGTERM:
		print 'SIGTERM, we exit as well, did we miss SIGINT ??'
		cont.set_movement("A")
		reset_tty_and_exit()
		
signal.signal(signal.SIGINT, handler)
signal.signal(signal.SIGTERM, handler)

#time.clock() returns cpu time for the whole process (under linux/unix)
#wait on locks or IO are not included
def limiter_simulator():
	while not SimulatorDieEvent.stop_that.wait(1) :
		#print >> sys.stderr,"time clock"+str(time.clock())
		if time.clock() > 160:
			print >> sys.stderr, "Sending SIGTERM"
			handler(signal.SIGTERM,None)
			print "Simulator died"
			return
		if time.clock()>150: #will return true if flag is set
			print >> sys.stderr,  "Sending SIGINT"
			handler(signal.SIGINT,None)
			print "Simulator died"
			return
	return


if debug:
	limiter_thread=Thread(None,limiter_simulator,"Resources limiter").start()






lambda_map = [[]]

if len(sys.argv) != 1 and len(sys.argv) != 3:
	print "usage: ", sys.argv[0], " debug <map_file_map>"
	print "       or ",sys.argv[0]," < <map_file_map>"
	exit(1)




if debug :
	f = open(sys.argv[2])
else:
	f = sys.stdin
	
with f as m:
	water_value=0
	flooding_value=0
	waterproof_value=10
	for line in m:
		if "Waterproof" in line:
			words=line.split(" ")
			waterproof_value=int(words[1])
			continue
		elif "Water" in line:
			words=line.split(" ")
			water_value=int(words[1])
			continue
		elif "Flooding" in line:
			words=line.split(" ")
			flooding_value=int(words[1])
			continue
		if line.strip() == "":
			continue
		for c in line:
			if c == '\n':
				lambda_map.insert(0,[])
				continue
			lambda_map[0].append(c)



lambda_map.pop(0)
#padding with ' '
maxcol = max([len(lambda_map[i]) for i,v in enumerate(lambda_map)])
for i, val in enumerate(lambda_map):
	if len(lambda_map[i]) != maxcol:
		val.extend([' ' for padder in range(maxcol - len(val)+1)])
	

displayer=MapDrawer(lambda_map)
#Now lambda_map is "reindexed"
lambda_map=displayer.getmap()



waterstuff=(water_value,flooding_value,waterproof_value)
world = world(lambda_map, waterstuff)
control = kcontroler(lambda_map)

if debug :
	os.system("clear")
	displayer.draw()
	world.print_status()
#~ control = botcontroler(world)

# We set terminal in raw mode to catch single key events
# This allows stdin.read() to be unbuffered
# which means read(1) will return, even without any \n


if debug:
	score = 0
	while 1:
		world.set_movement(control.get_next())
		score += world.get_points()
		os.system("clear")
		displayer.draw()
		world.print_status()
		if world.killed:
			print "lost"
			reset_tty_and_exit()
		elif world.won:
			print score
			reset_tty_and_exit()