import signal, os
from threading import Thread, enumerate as t_enum
from select import epoll, EPOLLIN
from time import sleep, time
from socket import *
from json import loads, dumps

run = True
def sighandler(sig, frame):
	global run
	run = False
signal.signal(signal.SIGINT, sighandler)

def genUID():
	return hash(bytes(str(time()), 'UTF-8')+os.urandom(4))

DEBUG_GAME = genUID()
core = {'threading' : {'t_offload' : 0.0083},
		'games' : {DEBUG_GAME : {'timeline' : [], 'players' : {}}},
		'unit_types' : {'footmen' : {'hp' : 100, 'dmg' : 20}},
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

	def send(self, d):
		data = dumps(d)
		self.socket.send(bytes(data,'UTF-8'))

	def loop(self):
		for fileno, event in self.poller.poll(1):
			if not fileno == self.fileno: continue

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

			if 'action' in jdata:
				if jdata['action'] == 'list':
					if 'asset' in jdata and jdata['asset'] == 'lobbys':
						print('[Lobbys] Sending lobby info')
						self.send({'asset' : 'lobbys', 'result' : list(self.globs['games'].keys())})
						continue

				elif jdata['action'] == 'move':
					pass # Used to server-lag control

				elif jdata['action'] == 'position_update':
					## == A unit has moved
					from_x, from_y = jdata['from']
					x, y = jdata['to']

					if not from_x in self.globs['positions'] and y not in self.globs['positions'][x]:
						print('[Movement] There wasn\'t a unix on this coordinate?')
						self.send({'asset' : 'position_update', 'status' : 'failed', 'reason' : 'There wasn\'t a unit in this position?'})
						continue

					if x in self.globs['positions'] and y in self.globs['positions'][x]:
						print('[Movement] A unit is already on this position')
						self.send({'asset' : 'position_update', 'status' : 'failed', 'reason' : 'There\'s already a unit here?'})
						continue

					if not x in self.globs['positions']: self.globs['positions'][x] = {}
					if not y in self.globs['positions'][x]: self.globs['positions'][x][y] = {}

					self.globs['positions'][x][y] = self.globs['positions'][from_x][from_y]
					del(self.globs['positions'][from_x][from_y])

				elif jdata['action'] == 'join':
					player_uid = jdata['player_uid']
					self.game = jdata['asset']
					self.globs['games'][self.game]['players'][player_uid] = {'units' : {}}
					## == Joining a lobby
					pass

				elif jdata['action'] == 'start':
					## == Starting a lobby
					pass

				elif jdata['action'] == 'create':
					x, y = jdata['position']
					asset = jdata['asset']
					player_uid = jdata['player_uid']

					self.globs['games'][self.game]['players'][player_uid]['units'][asset] = self.globs['unit_types']['footmen']
					self.globs['games'][self.game]['players'][player_uid]['units'][asset]['x'] = x
					self.globs['games'][self.game]['players'][player_uid]['units'][asset]['y'] = y

					if not x in self.globs['positions']: self.globs['positions'][x] = {}
					self.globs['positions'][x][y] = self.globs['games'][self.game]['players'][player_uid]['units'][asset]

				elif jdata['action'] == 'attack':
					x, y = jdata['position']
					asset = jdata['asset']
					player_uid = jdata['player_uid']

					if not x in self.globs['positions'] and y not in self.globs['positions'][x]:
						self.send({'asset' : 'attack', 'status' : 'failed', 'reason' : 'no one there?'})
						continue

					## TODO: This breaks when another thread is for instance moving.
					target = self.globs['positions'][x][y]
					print('{} Attacked: {} @ {}x{} (hp: {})'.format(player_uid, target, x, y, target['hp']))

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
				print('{} has connected'.format(na))
				ns_fileno = ns.fileno()

				self.sockets[ns_fileno] = {'socket' : ns, 'address' : na, 't' : client(self.globs, self.poller, self.sockets, ns, ns_fileno, na)}
				self.poller.register(ns_fileno, EPOLLIN)
		self.sleep()

x = listener(core)
while run and len(t_enum()) >= 1:
	sleep(core['threading']['t_offload'])