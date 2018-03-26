import os
from socket import *
from json import loads, dumps
from threading import Thread
from time import time, sleep

def genUID():
	return hash(bytes(str(time()), 'UTF-8')+os.urandom(4))

class reciever(Thread):
	def __init__(self, core):
		Thread.__init__(self)
		self.core = core
		self.s = socket()
		self.s.connect(('127.0.0.1', 4433))
		self.start()

	def send(self, d):
		data = dumps(d)
		self.s.send(bytes(data,'UTF-8'))

	def close(self):
		self.s.close()

	def run(self):
		while 1:
			data = self.s.recv(8192)
			jdata = loads(data.decode('UTF-8'))
			print('[Recieved] {}'.format(jdata))
			self.core['data'].append(jdata)

			if 'result' in jdata:
				if 'asset' in jdata:
					if jdata['asset'] == 'lobbys':
						if 'action' in jdata and jdata['action'] == 'list':
							print('[Lobby] Setting lobby to {}'.format(jdata['result'][0]))
							self.core['lobby'] = jdata['result'][0] # Show only one lobby'
							continue
						elif 'action' in jdata and jdata['action'] == 'create':
							self.core['lobby'] = jdata['result']['lobby_uid']
							continue

def convert(key, val, mute=True):
	global core
	if type(val) == str and '%' in val:
		if not mute:
			print('Inline modifying {} ({} in core: {})'.format(val, val[1:-1], val[1:-1] in core))
		if val[1:-1] in core:
			val = core[val[1:-1]]
	if type(key) == str and '%' in key and key[1:-1] in core:
		key = core[key[1:-1]]

	return key, val

core = {'player_one' : genUID(), 'player_two' : genUID(), 'data' : []}

unit_object_one = genUID()
unit_object_two = genUID()
# Create the player object.

actions = {'player_one':
			[{'D_timeOffset' : 0.1, 'D_loop' : False, 'D_Executed' : False, 'action' : 'create', 'asset' : 'lobby'},
			 {'D_timeOffset' : 0.5, 'D_loop' : False, 'D_Executed' : False, 'action' : 'list', 'asset' : 'lobbys'},
			 {'D_timeOffset' : 0.5, 'D_loop' : False, 'D_Executed' : False, 'action' : 'join', 'asset' : '%lobby%', 'player_uid' : '%player_one%'},
			 {'D_timeOffset' : 0.1, 'D_loop' : False, 'D_Executed' : False, 'D_WaitFor' : {'action' : 'join', 'asset' : 'lobby'}, 'D_WaitFor_Count' : 3, 'action' : 'start', 'asset' : '%lobby%'},
			 {'D_timeOffset' : 1.5, 'D_loop' : False, 'D_Executed' : False, 'action' : 'start', 'asset' : '%lobby%'},

			 {'D_timeOffset' : 1, 'D_loop' : False, 'D_Executed' : False, 'action' : 'create', 'asset' : 'unit', 'unit_uid' : unit_object_one, 'position' : (10, 10), 'facing' : 0},
			 {'D_timeOffset' : 1, 'action' : 'face', 'asset' : 'unit', 'unit_uid' : unit_object_one, 'facing' : 0},
			#{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_one, 'from' : (10, 10), 'to' : (20, 10)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_one, 'from' : (10, 10), 'to' : (11, 10)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_one, 'from' : (11, 10), 'to' : (12, 10)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_one, 'from' : (12, 10), 'to' : (13, 10)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_one, 'from' : (13, 10), 'to' : (14, 10)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_one, 'from' : (14, 10), 'to' : (15, 10)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_one, 'from' : (15, 10), 'to' : (16, 10)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_one, 'from' : (16, 10), 'to' : (17, 10)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_one, 'from' : (17, 10), 'to' : (18, 10)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_one, 'from' : (18, 10), 'to' : (19, 10)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_one, 'from' : (19, 10), 'to' : (20, 10)},

			## == Attack
			{'action' : 'attack', 'asset' : 'unit', 'unit_uid' : unit_object_one, 'direction' : 180, 'position' : (21, 10)},

			 {'D_timeOffset' : 1, 'action' : 'face', 'asset' : 'unit', 'unit_uid' : unit_object_one, 'facing' : 180},
			#{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_one, 'from' : (20, 10), 'to' : (10, 10)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_one, 'from' : (20, 10), 'to' : (19, 10)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_one, 'from' : (19, 10), 'to' : (18, 10)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_one, 'from' : (18, 10), 'to' : (17, 10)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_one, 'from' : (17, 10), 'to' : (16, 10)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_one, 'from' : (16, 10), 'to' : (15, 10)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_one, 'from' : (15, 10), 'to' : (14, 10)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_one, 'from' : (14, 10), 'to' : (13, 10)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_one, 'from' : (13, 10), 'to' : (12, 10)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_one, 'from' : (12, 10), 'to' : (11, 10)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_one, 'from' : (11, 10), 'to' : (10, 10)}],

		  'player_two' : 
		  	[#{'D_timeOffset' : 1, 'D_loop' : False, 'D_Executed' : False, 'action' : 'list', 'asset' : 'lobbys'},
			 {'D_timeOffset' : 2, 'D_loop' : False, 'D_Executed' : False, 'action' : 'join', 'asset' : '%lobby%', 'player_uid' : '%player_two%'},
			 {'D_timeOffset' : 0.1, 'D_loop' : False, 'D_Executed' : False, 'D_WaitFor' : {'action' : 'start', 'asset' : 'game', 'lobby' : '%lobby%'}, 'action' : 'start', 'asset' : '%lobby%'},

			 {'D_timeOffset' : 1, 'D_loop' : False, 'D_Executed' : False, 'action' : 'create', 'asset' : 'unit', 'unit_uid' : unit_object_two, 'position' : (25, 10), 'facing' : 180},
			 {'D_timeOffset' : 1, 'action' : 'face', 'asset' : 'unit', 'unit_uid' : unit_object_two, 'facing' : 180},
			#{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_two, 'from' : (25, 10), 'to' : (21, 10)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_two, 'from' : (25, 10), 'to' : (24, 10)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_two, 'from' : (24, 10), 'to' : (23, 10)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_two, 'from' : (23, 10), 'to' : (22, 10)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_two, 'from' : (22, 10), 'to' : (21, 10)},
			## == Pause a little longer here in case of attack.
			 {'D_timeOffset' : 3, 'action' : 'face', 'asset' : 'unit', 'unit_uid' : unit_object_two, 'facing' : 270},
			#{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_two, 'from' : (21, 10), 'to' : (21, 15)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_two, 'from' : (21, 10), 'to' : (21, 11)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_two, 'from' : (21, 11), 'to' : (21, 12)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_two, 'from' : (21, 12), 'to' : (21, 13)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_two, 'from' : (21, 13), 'to' : (21, 14)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_two, 'from' : (21, 14), 'to' : (21, 15)},
			 {'D_timeOffset' : 1, 'action' : 'face', 'asset' : 'unit', 'unit_uid' : unit_object_two, 'facing' : 0},
			#{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_two, 'from' : (21, 15), 'to' : (25, 15)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_two, 'from' : (21, 15), 'to' : (22, 15)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_two, 'from' : (22, 15), 'to' : (23, 15)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_two, 'from' : (23, 15), 'to' : (24, 15)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_two, 'from' : (24, 15), 'to' : (25, 15)},
			 {'D_timeOffset' : 1, 'action' : 'face', 'asset' : 'unit', 'unit_uid' : unit_object_two, 'facing' : 90},
			#{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_two, 'from' : (25, 15), 'to' : (25, 10)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_two, 'from' : (25, 15), 'to' : (25, 14)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_two, 'from' : (25, 14), 'to' : (25, 13)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_two, 'from' : (25, 13), 'to' : (25, 12)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_two, 'from' : (25, 12), 'to' : (25, 11)},
			{'action' : 'move', 'asset' : 'unit', 'unit_uid' : unit_object_two, 'from' : (25, 11), 'to' : (25, 10)}]
		}

class player(Thread):
	def __init__(self, core, actions, player_uid):
		self.actions = actions
		self.player_uid = player_uid
		self.core = core
		self.r = reciever(core)
		Thread.__init__(self)
		self.start()

	def run(self):
		last_action = time()
		while 1:
			for action in self.actions:
				if not 'D_loop' in action:
					action['D_loop'] = True
					action['D_Executed'] = False
				if not 'D_timeOffset' in action:
					action['D_timeOffset'] = 0.25
					
				if action['D_loop'] is False and action['D_Executed'] is True: continue
				if action['D_loop'] is False: action['D_Executed'] = True

				if 'D_WaitFor' in action:
					triggered = False
					started = time()
					alerted = False
					while not triggered:
						if time()-started > 5 and not alerted:
							cleaned = {}
							for key, val in action['D_WaitFor'].items():
								key, val = convert(key, val)
								cleaned[key] = val
							print('The following trigger is running late: {} ({})'.format(cleaned, counter))
							alerted = True
						counter = 0
						for jdata in self.core['data']:
							all_found = True
							for key, val in action['D_WaitFor'].items():
								key, val = convert(key, val)
								if key in jdata and jdata[key] == val:
									pass
								else:
									all_found = False

							if all_found:
								counter += 1
								if not 'D_WaitFor_Count' in action or counter >= action['D_WaitFor_Count']:
									triggered = True
									print('Trigger met: {} ({})'.format(action, counter))
									print(self.core['data'])
									break
						sleep(0.025)
					if triggered:
						continue

				while time()-last_action < action['D_timeOffset']:
					sleep(0.01)

				cleaned = {}
				for key, val in list(action.items()):
					if 'D_' in key: continue

					#if type(val) == str and '%' in val:
					#	print('Inline modifying {} ({} in core: {})'.format(val, val[1:-1], val[1:-1] in core))
					#	if val[1:-1] in core:
					#		val = core[val[1:-1]]
					#if type(key) == str and '%' in key and key[1:-1] in core:
					#	key = core[key[1:-1]]
					key, val = convert(key, val, mute=False)
					
					cleaned[key] = val

				cleaned['player_uid'] = self.player_uid
				print('[Sending] {}'.format(cleaned))
				self.r.send(cleaned)
				last_action = time()

print('Initating player 1: {}'.format(core['player_one']))
print('Initating player 2: {}'.format(core['player_two']))
player(core, actions['player_one'], core['player_one'])
player(core, actions['player_two'], core['player_two'])