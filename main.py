#import lzw # Was slightly broken spewing out "EOS" errors.
import pyglet
from pyglet.gl import *
from collections import OrderedDict
from os import urandom
from os.path import isfile
from math import *
from time import time
from threading import Thread
from time import time, sleep
from socket import *
from select import epoll, EPOLLIN # TODO: Replace epoll with select for MS Windows functionality
from json import loads, dumps
from socket import *
from base64 import b64encode

from ui.helpers import generic_sprite
from ui.elements import text_input, lobby, main_menu, gameUI

pyglet.options['audio'] = ('alsa', 'openal', 'silent')
key = pyglet.window.key

from config import conf
from warlib import *

__builtins__.__dict__['cosmic'] = {
	'pages' : {'main_menu' : {'batch' : pyglet.graphics.Batch(),
							  'layers' : {0 : pyglet.graphics.OrderedGroup(0),
										  1 : pyglet.graphics.OrderedGroup(1),
										  2 : pyglet.graphics.OrderedGroup(2),
										  3 : pyglet.graphics.OrderedGroup(3)},
							  'sprites' : {},
							  'subpages' : {}}
			   },
	'merge_pages' : {},
	'active_page' : 'main_menu',
	'quit' : False,
	'input_to' : None,
}

## == TODO:
#		Check the following palettes: 191, 194, 197

## == General credits:
# https://github.com/magical/nlzss/blob/master/lzss3.py#L36
# https://github.com/Wargus/war1gus/blob/master/war1tool.c
# https://github.com/plasticlogic/pldata/blob/master/lzss/python/pylzss.c
# https://github.com/Wargus/wargus
# https://github.com/Wargus/war1gus/blob/master/war1tool.c
# https://github.com/Wargus/stratagus/issues/198
# https://github.com/bradc6
# https://github.com/Stratagus/libwararch/blob/master/SampleSource/ExtractFile/main.cpp
# https://github.com/Stratagus/libwararch/blob/master/Source/WarArchive/WarArchive.cpp
# http://www.blizzardarchive.com/pub/Misc/Wc1Book_041215.pdf
# https://twitter.com/brad_c6
## == Image stuff:
# https://i.ytimg.com/vi/xzkhWZqVRcE/hqdefault.jpg
# http://www.libpng.org/pub/png/book/chapter08.html#png.ch08.div.5.1
# https://en.wikipedia.org/wiki/Indexed_color
# https://en.wikipedia.org/wiki/List_of_monochrome_and_RGB_palettes#3-3-2_bit_RGB

def getTexture(img_id):
	return game_data.images[img_id].to_png(game_data.colorPalettes[conf['colorMap'][img_id]])

#def genUID():
#	return hash(bytes(str(time()), 'UTF-8')+urandom(4))

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



def hash_dict(d):
	sorted_keys = sorted(list(d.keys()))
	keystruct = ''.join([str(key)+':'+str(d[key]) for key in sorted_keys])
	return b64encode(bytes(keystruct, 'UTF-8'))

class _network(Thread):
	def __init__(self, host='127.0.0.1', port=4433):
		Thread.__init__(self)
		self.poller = epoll()
		self.socket = socket()
		self.main_sock = self.socket.fileno()
		self.poller.register(self.main_sock, EPOLLIN)
		self.network_events = {}
		self.socket.connect((host, port))
		self.alive = True
		self.start()

	def reg_event(self, d, func):
		d_hash = hash_dict(d)
		if not d_hash in self.network_events:
			self.network_events[d_hash] = {'func' : func, 'dict' : d}

	def run(self):
		while self.alive and not cosmic['quit']:
			for fileno, event in self.poller.poll(0.25):
				if self.main_sock == fileno:
					data = self.socket.recv(8192)
					if len(data) == 0:
						print('Network died..')
						self.socket.close()
						break

					if type(data) == bytes:
						data = data.decode('UTF-8')
					data = loads(data)
					print('INC Data:', data)
					for d_hash in self.network_events:
						d = self.network_events[d_hash]['dict']
						if d.items() <= data.items():
							self.network_events[d_hash]['func'](data)
		self.socket.close()

	def send(self, data):
		if type(data) not in (str, bytes):
			data = dumps(data)

		self.socket.send(bytes(data, 'UTF-8'))

	def close(self):
		self.alive = False

try:
	__builtins__['network'] = None
	__builtins__['net_class'] = _network
except:
	__builtins__.__dict__['network'] = None
	__builtins__.__dict__['net_class'] = _network

class AnimatedSprite(generic_sprite):
	def __init__(self, war_data, palette, batch=None, x=10, y=10):
		self.war_data = war_data
		self.war_data.convert_frames(palette)
		
		super(AnimatedSprite, self).__init__(self.war_data.frames[0]['image'], width=war_data.width, height=war_data.height, alpha=0, batch=batch, x=x, y=y)
		self.palette = palette
		self.index = 0
		self.last_update = time()

	def update(self):
		if time() - self.last_update > 0.25:
			print('Updating', self.war_data.frameCount)
			self.index += 1
			if self.index >= self.war_data.frameCount:
				self.index = 0
			self.texture = self.war_data.frames[self.index]['image']
			self.image = self.texture
			#print(self.texture)
			self.last_update = time()
#		self.frames[i] = {'width': width, 'height' : height, 'xOffset' : xoff, 'yOffset' : yoff, 'frameOffset' : frameOffset, 'data' : None}

class HumanWarrior(AnimatedSprite):
	def __init__(self, batch=None, x=10, y=10):
		img_id = 279
		AnimatedSprite.__init__(self, war_data=game_data.sprites[img_id], palette=game_data.colorPalettes[conf['colorMap'][img_id]], batch=batch, x=x, y=y)
		self.img_id = img_id

		self.frames = {'walk' : {'up' : [0, 15, 30, 45, 60], 'upright' : [1, 16, 31, 46, 61], 'right' : [2, 17, 32, 47, 62], 'downright' : [3, 18, 33, 48, 63], 'down' : [4, 19, 34, 49, 64]},
						'attack' : {'up' : [5, 20, 35, 50, 65], 'upright' : [6, 21, 36, 51, 66], 'right' : [7, 22, 37, 52, 67], 'downright' : [8, 23, 38, 53, 68], 'down' : [9, 24, 39, 54, 69]},
						'dying' : {'upright' : [10, 11, 25, 26, 40, 41, 55, 56, 70, 71], 'downright' : [12, 13, 14, 27, 28, 29, 42, 43, 44, 57, 58, 59, 72, 73, 74]}
					  }
		self.action = 'walk'
		self.direction = 'up'
		self.index = 0

	def update(self):
		if time() - self.last_update > 0.25:
			self.index += 1
			if self.index >= len(self.frames[self.action][self.direction])-1:
				self.index = 0
			self.texture = self.war_data.frames[self.frames[self.action][self.direction][self.index]]['image']
			self.image = self.texture
			self.last_update = time()

class OrcGrunt(AnimatedSprite):
	def __init__(self, batch=None, x=10, y=10):
		img_id = 280
		AnimatedSprite.__init__(self, war_data=game_data.sprites[img_id], palette=game_data.colorPalettes[conf['colorMap'][img_id]], batch=batch, x=x, y=y)
		self.img_id = img_id

		self.frames = {'walk' : {'up' : [0, 15, 30, 45, 60], 'upright' : [1, 16, 31, 46, 61], 'right' : [2, 17, 32, 47, 62], 'downright' : [3, 18, 33, 48, 63], 'down' : [4, 19, 34, 49, 64]},
						'attack' : {'up' : [5, 20, 35, 50, 65], 'upright' : [6, 21, 36, 51, 66], 'right' : [7, 22, 37, 52, 67], 'downright' : [8, 23, 38, 53, 68], 'down' : [9, 24, 39, 54, 69]},
						'dying' : {'upright' : [10, 11, 25, 26, 40, 41, 55, 56, 70, 71], 'downright' : [12, 13, 14, 27, 28, 29, 42, 43, 44, 57, 58, 59, 72, 73, 74]}
					  }
		self.action = 'walk'
		self.direction = 'up'
		self.index = 0

	def update(self):
		if time() - self.last_update > 0.25:
			self.index += 1
			if self.index >= len(self.frames[self.action][self.direction])-1:
				self.index = 0
			self.texture = self.war_data.frames[self.frames[self.action][self.direction][self.index]]['image']
			self.image = self.texture
			self.last_update = time()

class Tile(generic_sprite):
	def __init__(self, tile_id, batch=None, x=10, y=10):
		self.war_data = game_data.tiles[tile_id]
		print('Decoding {} with palette {}'.format(tile_id, tile_id-2))
		img = self.war_data.to_png(game_data.tile_sets[tile_id-1], game_data.colorPalettes[tile_id-2])
		#self.war_data.convert_frames(palette)
		print(img)
		generic_sprite.__init__(self, img, width=self.war_data.width, height=self.war_data.height, alpha=0, batch=batch)
		self.x = x
		self.y = y

class main(pyglet.window.Window):#								 conf['resolution'].height()
	def __init__ (self, width=conf['resolution'].width(), height=conf['resolution'].height(), *args, **kwargs):
		super(main, self).__init__(width, height, *args, **kwargs)
		self.set_location(conf['position']['x'], conf['position']['y'])
		self.x, self.y = 0, 0

		self.sprites = OrderedDict()
		__builtins__.__dict__['game_data'] = WAR(sys.argv[1])

		#self.pages = {'default' : {'batch' : pyglet.graphics.Batch(), 'sprites' : OrderedDict()}}
		#self.pages['main_menu'] = {'batch' : pyglet.graphics.Batch(), 'sprites' : OrderedDict()}
		#self.pages['main_ui'] = {'batch' : pyglet.graphics.Batch(), 'sprites' : OrderedDict()}

		#cosmic['active_page'] = 'main_menu' #'main_menu'
		self.active_sprites = OrderedDict()

		self.add_sprite(page='main_menu', itemName='main_menu', obj=main_menu(batch=cosmic['pages']['main_menu']['batch']))
		#self.add_sprite(page='main_menu', itemName='house', obj=AnimatedSprite(war_data=game_data.sprites[315], palette=game_data.colorPalettes[416], batch=self.pages['main_menu']['batch'], x=30, y=30))
		
		## Test sprites
		#self.add_sprite(page='main_ui', itemName='frame', obj=gameUI(race='human', batch=self.pages['main_ui']['batch']))
		#self.add_sprite(page='main_ui', itemName='Warrior', obj=HumanWarrior(batch=self.pages['main_ui']['batch'], x=200, y=200))
		#self.add_sprite(page='main_ui', itemName='Orc', obj=OrcGrunt(batch=self.pages['main_ui']['batch'], x=350, y=200))

		#self.add_sprite(page='main_ui', itemName='Grass', obj=Tile(193, batch=self.pages['main_ui']['batch'], x=300, y=250))
		#self.add_sprite('main_menu', 'background', generic_sprite(game_data.images[261].to_png(game_data.colorPalettes[260]), moveable=False))
		
		#for image in game_data.images:
		#	self.add_sprite('main_menu', 'background', generic_sprite(game_data.images[261].to_png(game_data.colorPalettes[260]), moveable=False))
		self.input = ''	
		self.keymap = {key._0 : 0, key._1 : 1, key._2 : 2, key._3 : 3, key._4 : 4, key._5 : 5, key._6 : 6, key._7 : 7, key._8 : 8, key._9 : 9}

		self.keys = {}
		# DEBUG:
		self.combos = {}

		self.drag = False
		self.alive = 1

	def add_sprite(self, page, itemName, obj):
		if not page in cosmic['pages']:
			cosmic['pages'][page] = {'batch' : pyglet.graphics.Batch(), 'sprites' : OrderedDict(), 'layers' : {}, 'subpages' : {}}

		obj.set_batch(cosmic['pages'][page]['batch'])
		cosmic['pages'][page]['sprites'][itemName] = obj
		self.sprites[itemName] = obj

	def flush_sprites(self, page=None):
		if not page: page = cosmic['active_page']

		for obj in cosmic['pages'][page]['sprites']:
			cosmic['pages'][page]['sprites'][obj].delete()
			del cosmic['pages'][page]['sprites'][obj]
		#for obj in self.pages[page]['batch']
		#self.pages[page] = {'batch' : pyglet.graphics.Batch(), 'sprites' : OrderedDict()}		

	def on_draw(self):
		self.render()

	def on_close(self):
		self.alive = 0

	def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
		self.drag = True

		for name, obj in self.active_sprites.items():
			obj.move(dx, dy)

	def on_key_release(self, symbol, modifiers):
		if symbol == key.LCTRL:
			self.active_sprites = OrderedDict()

		print(cosmic['input_to'])
		try:
			if cosmic['input_to']:
				cosmic['input_to'].text += chr(symbol)
				cosmic['input_to'].changed = True
				cosmic['input_to'].update()
		except:
			pass

		try:
			del self.keys[symbol]
		except:
			pass

	def on_mouse_release(self, x, y, button, modifiers):
		if button == 1:
			for sName, sObj in self.active_sprites.items():
				sObj.click(x, y)
			if not key.LCTRL in self.keys:
				self.active_sprites = OrderedDict()

	def on_mouse_press(self, x, y, button, modifiers):
		if button == 1:
			print('Checking all sprites in', cosmic['active_page'])
			print(cosmic['pages'][cosmic['active_page']]['sprites'])
			for sprite_name, sprite in cosmic['pages'][cosmic['active_page']]['sprites'].items():
				if sprite:
					#print('Clickchecking:', sprite, 'with button', button)
					sprite_obj = sprite.mouse_inside(x, y, button)
					if sprite_obj:
						self.active_sprites[sprite_name] = sprite_obj
						if 'id' in sprite_name and 'pal' in sprite_name:
							_id, _pal = [int(x.split(':')[1]) for x in sprite_name.split('_')]
							self.combos[_id] = _pal
							for i in range(_id, max(list(game_data.images.keys()))):
								if i == _id: continue
								if _id in game_data.images and i in game_data.images:
									self.load_image(i)
									break
								elif _id in game_data.sprites and i in game_data.sprites:
									self.load_sprite(i)
									break

	## == DEBUG FEATURES:
	##    Used to load images and sprites with all palette combinations
	def load_image(self, index):
		print('Loading Image:', int(index))
		self.flush_sprites()
		x = 0
		y = 0
		for palette_id in game_data.colorPalettes.keys():
			if not game_data.colorPalettes[palette_id].corrupted:
				self.add_sprite('main_menu', 'id:{}_pal:{}'.format(index, palette_id), generic_sprite(game_data.images[index].to_png(game_data.colorPalettes[palette_id]), moveable=True, x=x, y=y))
				x += (game_data.images[index].width * conf['resolution'].scale()) + 5
				if x+(game_data.images[index].width * conf['resolution'].scale()) > self.width:
					x = 0
					y += (game_data.images[int(index)].height*conf['resolution'].scale())+5

	def load_sprite(self, index):
		print('Loading Sprite:', int(index))
		self.flush_sprites()
		x = 0
		y = 0
		for palette_id in game_data.colorPalettes.keys():
			if not game_data.colorPalettes[palette_id].corrupted:
				self.add_sprite(page='main_menu', itemName='id:{}_pal:{}'.format(index, palette_id), obj=AnimatedSprite(war_data=game_data.sprites[index], palette=game_data.colorPalettes[palette_id], batch=cosmic['pages']['main_menu']['batch'], x=x, y=y))
				x += (game_data.sprites[index].width * conf['resolution'].scale()) + 5
				if x+(game_data.sprites[index].width * conf['resolution'].scale()) > self.width:
					x = 0
					y += (game_data.sprites[int(index)].height*conf['resolution'].scale())+5

	def on_key_press(self, symbol, modifiers):
		self.keys[symbol] = True

		if symbol == key.ESCAPE: # [ESC]
			with open('images.conf', 'w') as fh:
				fh.write("conf['images'] = {}\n")
				for _id in self.combos:
					fh.write("conf[{}] = {}\n".format(_id, self.combos[_id]))

			self.alive = 0

		elif symbol in self.keymap:
			self.input += str(self.keymap[symbol])

		elif symbol == key.BACKSPACE:
			self.input = self.input[:-1]

		elif symbol == key.RIGHT:
			for sName, sObj in cosmic['pages'][cosmic['active_page']]['sprites'].items():
				sObj.update()

		elif symbol == key.ENTER:
			if len(self.input):
				inp = int(self.input)
				if inp in game_data.images:
					self.load_image(inp)
				elif inp in game_data.sprites:
					self.load_sprite(inp)
			else:
				print('Obj {} not in resources.'.format(self.input))

				print('Iamges:', ', '.join([str(i) for i in sorted(list(game_data.images.keys()))]))
				print('Sprites:', ', '.join([str(i) for i in sorted(list(game_data.sprites.keys()))]))
			self.input = ''
		#elif symbol == key.LCTRL:

	def on_move(self, x, y, *args, **kwargs):
		print(x, y, args)

	def render(self):
		#t = timer()
		self.clear()

		## Move sprite from a thread friendly place,
		## into the main thread's graphical context by initating the objects from the main resource.
		for page in list(cosmic['merge_pages'].keys()):
			cosmic['pages'][page] = cosmic['merge_pages'][page]

			cosmic['pages'][page]['batch'] = pyglet.graphics.Batch()
			for layer in cosmic['pages'][page]['layers']:
				cosmic['pages'][page]['layers'][layer] = pyglet.graphics.OrderedGroup(layer)

			print('{} contains:'.format(page))
			print(cosmic['pages'][page]['sprites'])
			for sprite in cosmic['pages'][page]['sprites']:
				print('Sprite {}:'.format(sprite))
				print(cosmic['pages'][page]['sprites'])
				func = cosmic['pages'][page]['sprites'][sprite][0]
				params = cosmic['pages'][page]['sprites'][sprite][1]

				if 'batch' in params:
					params['batch'] = cosmic['pages'][params['batch']]['batch']

				cosmic['pages'][page]['sprites'][sprite] = func(**params)

			del(cosmic['merge_pages'][page])

		## TODO: Uncomment this when auto-updates are ready
		for sName, sObj in cosmic['pages'][cosmic['active_page']]['sprites'].items():
			sObj.update()

		#for sprite_name, sprite_obj in self.sprites.items():
		#	sprite_obj._draw()
		cosmic['pages'][cosmic['active_page']]['batch'].draw()

		self.flip()

	def run(self):
		while self.alive == 1 and cosmic['quit'] is False:
			self.render()

			# -----------> This is key <----------
			# This is what replaces pyglet.app.run()
			# but is required for the GUI to not freeze
			#
			event = self.dispatch_events()
		cosmic['quit'] = True

x = main()
x.run()