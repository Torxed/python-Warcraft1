import signal, os
from threading import Thread, enumerate as t_enum
from select import epoll, EPOLLIN
from time import sleep, time
from socket import *
from json import loads, dumps
from collections import OrderedDict
from base64 import b64encode

run = True
def sighandler(sig, frame):
	global run
	run = False
signal.signal(signal.SIGINT, sighandler)

def genUID():
	return b64encode(bytes(str(time()), 'UTF-8')+os.urandom(4)).decode('UTF-8')

DEBUG_GAME = genUID()
core = {'threading' : {'t_offload' : 0.0083},
		'games' : {},
		'positions' : {}}

class t(Thread):
	def __init__(self, globs):
		self.globs = globs
		self.alive = True
		self.events = []
		Thread.__init__(self)
		self.start()

	def sleep(self, ms=None):
		if not ms: ms = self.globs['threading']['t_offload']
		sleep(ms)

	def loop(self):
		self.sleep()

	def run(self):
		m = None
		for t in t_enum():
			if t.name == 'MainThread':
				m = t
				break

		while m and m.isAlive() and self.alive:
			self.loop()

class unit():
	def __init__(self, globs, x, y):
		self.globs = globs
		self.units = OrderedDict()
		self.x = x
		self.y = y
		self.hp = 100
		self.dmg = 0
		self.direction = 0
		self.dead = None

	def move(self, from_pos, to_pos):
		self.x, self.y = to_pos

		if not from_pos[0] in self.globs['positions'] and from_pos[1] not in self.globs['positions'][from_pos[0]]:
			print('[Movement] There wasn\'t a unix on this coordinate?')
			return {'action' : 'move', 'asset' : 'unit', 'status' : 'failed', 'reason' : 'There wasn\'t a unit in this position?'}

		x = to_pos[0]
		y = to_pos[1]

		if x in self.globs['positions'] and y in self.globs['positions'][x]:
			print('[Movement] A unit is already on this position')
			return {'action' : 'move', 'asset' : 'move', 'status' : 'failed', 'reason' : 'There\'s already a unit here?'}

		if not x in self.globs['positions']: self.globs['positions'][x] = {}
		if not y in self.globs['positions'][x]: self.globs['positions'][x][y] = {}

		self.globs['positions'][x][y] = self
		del(self.globs['positions'][from_pos[0]][from_pos[1]])
		if len(self.globs['positions'][from_pos[0]]) <= 0:
			del(self.globs['positions'][from_pos[0]])

class footman(unit):
	def __init__(self, globs, x, y):
		unit.__init__(self, globs, x, y)
		self.dmg = 20

class game(t):
	def __init__(self, globs, players={}):
		self.globs = globs
		self.players = players
		self.units = OrderedDict()
		self.sockets = {}

		t.__init__(self, globs)

	def player_add(self, player_uid):
		self.players[player_uid] = {'units' : OrderedDict()}

	def unit_add(self, player_uid, unit_uid, unit_type, x, y):
		self.units[unit_uid] = unit_type(self.globs, x, y)
		self.players[player_uid]['units'][unit_uid] = self.units[unit_uid]

		if not x in self.globs['positions']: self.globs['positions'][x] = {}
		if not y in self.globs['positions'][x]: self.globs['positions'][x][y] = {}
		self.globs['positions'][x][y] = self.units[unit_uid]

		if not x in self.globs['positions']:
			self.globs['positions'][x] = {}
		self.globs['positions'][x][y] = self.units[unit_uid]

	def unit_move(self, player_uid, unit_uid, from_pos, to_pos):
		if unit_uid in self.players[player_uid]['units']:
			return self.units[unit_uid].move(from_pos, to_pos)

class client(t):
	def __init__(self, globs, poller, sockets, socket, fileno, address):
		self.poller = poller
		self.sockets = sockets

		self.socket = socket
		self.fileno = fileno
		self.address = address
		self.connected = True

		self.game = None

		t.__init__(self, globs)

	def send(self, d, sock=None):
		if not sock: sock = self.socket
		data = dumps(d)
		sock.send(bytes(data,'UTF-8'))

	def loop(self):
		for fileno, event in self.poller.poll(1):
			if not fileno == self.fileno: continue

			print(event)
			data = self.socket.recv(8192)
			if len(data) == 0:
				print('{} has disconnected'.format(self.address))
				self.connected = False
				self.alive = False
				return

			try:
				jdata = loads(data.decode('UTF-8'))
				print('{} sent: {}'.format(':'.join([str(x) for x in self.address]), jdata))
			except Exception as e:
				print(e)
				continue

			if 'asset' in jdata:
				if jdata['asset'] == 'lobby':
					if 'action' in jdata:
						if jdata['action'] == 'list':
							print('[Lobbys] Sending lobby info')
							self.send({'action' : 'list', 'asset' : 'lobbys', 'result' : list(self.globs['games'].keys())})
							continue
						
						elif jdata['action'] == 'join':
							## == Joining a lobby
							player_uid = jdata['player_uid']
							self.game = jdata['asset']

							print('[JOIN] Player {} just sent join on game {}'.format(player_uid, self.game))
							self.globs['games'][self.game].player_add(player_uid)
							#for player in self.globs['games'][self.game].players:
							#	print('In game:', player)
							for fileno in self.sockets:
								if fileno == self.fileno: continue
								# if fileno in self.game.players:
								print('[JOIN::PUSH] On socket {}: {}'.format(fileno, {'action' : 'join', 'asset' : 'lobby', 'lobby' : DEBUG_GAME, 'player_uid' : player_uid}))
								self.send({'action' : 'join', 'asset' : 'lobby', 'lobby' : DEBUG_GAME, 'player_uid' : player_uid}, self.sockets[fileno]['socket'])

						elif jdata['action'] == 'start':
							## == Starting a lobby
							self.globs['games'][DEBUG_GAME]
							for fileno in self.sockets:
								#if fileno == self.fileno: continue
								self.send({'action' : 'start', 'asset' : 'game', 'lobby_uid' : DEBUG_GAME}, self.sockets[fileno]['socket'])

						elif jdata['action'] == 'create':
							self.globs['games'][DEBUG_GAME] = game(self.globs, owner=jdata['owner'])
							self.send({'action' : 'create', 'asset' : 'lobby', 'result' : {'lobby_uid' : DEBUG_GAME, 'title' : jdata['owner']+'\'s lobby.'}})


				elif jdata['asset'] == 'unit':
					if jdata['action'] == 'move':
						## == A unit has moved

						response = self.globs['games'][self.game].unit_move(jdata['player_uid'], jdata['unit_uid'], jdata['from'], jdata['to'])
						if response: self.send(response)
					elif jdata['action'] == 'create':
						x, y = jdata['position']
						unit_uid = jdata['unit_uid']
						player_uid = jdata['player_uid']

						self.globs['games'][self.game].player_add(player_uid)
						self.globs['games'][self.game].unit_add(player_uid, unit_uid, footman, x, y)

				
					elif jdata['action'] == 'attack':
						x, y = jdata['position']
						asset = jdata['asset']
						player_uid = jdata['player_uid']

						try:
							if not x in self.globs['positions'] and y not in self.globs['positions'][x]:
								self.send({'asset' : 'attack', 'status' : 'failed', 'reason' : 'no one there?'})
								continue
						except KeyError:
							self.send({'asset' : 'attack', 'status' : 'failed', 'reason' : 'no one there?'})
							continue

						## TODO: This breaks when another thread is for instance moving.
						target = self.globs['positions'][x][y]
						print('{} Attacked: {} @ {}x{} (hp: {})'.format(player_uid, target, x, y, target.hp))

		else:
			self.sleep() # 25ms or whatever is configured

class listener(t):
	def __init__(self, globs):
		self.i = 0
		self.sockets = {}
		self.poller = epoll()
		self.socket = socket()
		self.main_sock = self.socket.fileno()
		self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
		self.socket.bind(('', 4433))
		self.poller.register(self.main_sock)
		self.socket.listen(4)

		t.__init__(self, globs)

	def loop(self):
		for fileno, event in self.poller.poll(1):
			if self.main_sock == fileno:
				ns, na = self.socket.accept()
				print('{} has connected on fileno {}'.format(na, ns.fileno()))
				ns_fileno = ns.fileno()

				self.sockets[ns_fileno] = {'socket' : ns, 'fileno' : ns_fileno, 'address' : na, 't' : client(self.globs, self.poller, self.sockets, ns, ns_fileno, na)}
				self.poller.register(ns_fileno, EPOLLIN)
		self.sleep()

x = listener(core)
while run and len(t_enum()) >= 1:
	sleep(core['threading']['t_offload'])