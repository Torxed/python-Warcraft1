#import lzw # Was slightly broken spewing out "EOS" errors.
from time import sleep # DEBUG
import pyglet
from pyglet.gl import *
from collections import OrderedDict
from os.path import isfile
from math import *
from time import time
pyglet.options['audio'] = ('alsa', 'openal', 'silent')
key = pyglet.window.key

from config import conf
from warlib import *

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

# id:216_pal:217

# key = image_id, val = palette_id
image_map = {216 : 217,
			218 : 217,
			219 : 217,
			220 : 217, # 262?
			221 : 217, # 262?
			222 : 217, # 262?
			223 : 217, # 262?
			224 : 217, # 262?
			225 : 217, # 262?
			226 : 217, # 262?
			227 : 217, # 262?
			228 : 217, # 262?
			229 : 217, # 262?
			233 : 217, # 262?
			234 : 217,
			235 : 217, # 262?
			236 : 217, # 262?
			237 : 217, # 262?
			238 : 217,
			239 : 217,
			#233 : 217,
			#233 : 217,
			#233 : 217,
			#233 : 217,
			}

def gen_solid_image(width, height, color='#FF0000', alpha=255):
	if type(color) == str:
		c = color.lstrip("#")
		c = max(6-len(c),0)*"0" + c
		r = int(c[:2], 16)
		g = int(c[2:4], 16)
		b = int(c[4:], 16)
	else:
		r,g,b = color
	
	c = (r,g,b,alpha)
	return pyglet.image.SolidColorImagePattern(c).create_image(width, height)

class generic_sprite(pyglet.sprite.Sprite):
	def __init__(self, texture=None, width=None, height=None, color="#C2C2C2", alpha=int(255), x=None, y=None, moveable=False, batch=None, bind=None):
		
		if not width:
			width = 10
		if not height:
			height = 10

		if type(texture) == str:
			if not texture or not isfile(texture):
				#print('No texutre could be loaded for sprite, generating a blank one.')
				## If no texture was supplied, we will create one
				self.texture = gen_solid_image(int(width*conf['resolution'].scale()), int(height*conf['resolution'].scale()), color, alpha)
			else:
				self.texture = pyglet.image.load(texture)
		elif texture is None:
			self.texture = gen_solid_image(int(width*conf['resolution'].scale()), int(height*conf['resolution'].scale()), color, alpha)
		else:
			self.texture = texture

		super(generic_sprite, self).__init__(self.texture)
		self.batch = batch
		self.scale = conf['resolution'].scale()
		self.sprites = OrderedDict()

		if x:
			self.x = x
		else:
			self.x = 0
		if y:
			self.y = y
		else:
			self.y = 0

		self.moveable = moveable

		if bind:
			self.click = bind

	def set_batch(self, batch):
		self.batch = batch
		for sName, sObj in self.sprites.items():
			sObj.batch = batch

	def click(self, x, y):
		"""
		Usually click_check() is called followed up
		with a call to this function.
		Basically what this is, is that a click
		should occur within the object.
		Normally a class who inherits Spr() will create
		their own click() function but if none exists
		a default must be present.
		"""
		return True

	def mouse_inside(self, x, y, button=None):
		"""
		When called, we first iterate our sprites.
		If none of those returned a click, we'll
		check if we're inside ourselves.
		This is because some internal sprites might go
		outside of the object boundaries.
		"""
		for sname, sobj in self.sprites.items():
			check_sobj = sobj.mouse_inside(x, y, button)
			if check_sobj:
				return check_sobj

		if x > self.x and x < (self.x + self.width):
			if y > self.y and y < (self.y + self.height):
				return self

	def move(self, x, y):
		if self.moveable:
			self.x += x
			self.y += y
			for sprite in self.sprites:
				self.sprites[sprite].x += x
				self.sprites[sprite].y += y

	def update(self):
		pass

	def click(self, x, y):
		return True

	def _draw(self):
		self.draw()

def start_game(x, y):
	print('Starting the game')

class main_menu(generic_sprite):
	def __init__(self, batch=None):
		super(main_menu, self).__init__(width=conf['resolution'].width(), height=conf['resolution'].height(), alpha=0, batch=batch)

		self.sprites['background'] = generic_sprite(game_data.images[261].to_png(game_data.colorPalettes[260]), moveable=False)

		self.sprites['start_game'] = generic_sprite(game_data.images[239].to_png(game_data.colorPalettes[217]), bind=start_game)
		self.sprites['start_game'].x = conf['resolution'].width()/2 - self.sprites['start_game'].width/2
		self.sprites['start_game'].y = conf['resolution'].height()/2 - self.sprites['start_game'].height/2 - 10

		self.sprites['load_existing_game'] = generic_sprite(game_data.images[239].to_png(game_data.colorPalettes[217]), bind=start_game)
		self.sprites['load_existing_game'].x = conf['resolution'].width()/2 - self.sprites['load_existing_game'].width/2
		self.sprites['load_existing_game'].y = conf['resolution'].height()/2 - self.sprites['load_existing_game'].height/2 - 50

		self.sprites['replay_introduction'] = generic_sprite(game_data.images[239].to_png(game_data.colorPalettes[217]), bind=start_game)
		self.sprites['replay_introduction'].x = conf['resolution'].width()/2 - self.sprites['replay_introduction'].width/2
		self.sprites['replay_introduction'].y = conf['resolution'].height()/2 - self.sprites['replay_introduction'].height/2 - 90

		self.sprites['quit'] = generic_sprite(game_data.images[239].to_png(game_data.colorPalettes[217]), bind=start_game)
		self.sprites['quit'].x = conf['resolution'].width()/2 - self.sprites['quit'].width/2
		self.sprites['quit'].y = conf['resolution'].height()/2 - self.sprites['quit'].height/2 - 170

		#self.add_sprite('main_menu', 'background', generic_sprite(game_data.images[261].to_png(game_data.colorPalettes[260]), moveable=False)

class AnimatedSprite(generic_sprite):
	def __init__(self, war_data, palette, batch=None, x=10, y=10):
		self.war_data = war_data
		self.war_data.convert_frames(palette)
		
		super(AnimatedSprite, self).__init__(self.war_data.frames[0]['image'], width=war_data.max_width, height=war_data.max_height, alpha=0, batch=batch, x=x, y=y)
		self.palette = palette
		self.index = 0
		self.last_update = time()

	def update(self):
		if time() - self.last_update > 0.25:
			self.index += 1
			if self.index >= self.war_data.frameCount:
				self.index = 0
			self.texture = self.war_data.frames[self.index]['image']
			self.last_update = time()
#		self.frames[i] = {'width': width, 'height' : height, 'xOffset' : xoff, 'yOffset' : yoff, 'frameOffset' : frameOffset, 'data' : None}

class main(pyglet.window.Window):
	def __init__ (self, width=conf['resolution'].width(), height=conf['resolution'].height(), *args, **kwargs):
		super(main, self).__init__(width, height, *args, **kwargs)
		self.x, self.y = 0, 0

		self.sprites = OrderedDict()
		__builtins__.__dict__['game_data'] = WAR(sys.argv[1])
		self.pages = {'default' : {'batch' : pyglet.graphics.Batch(), 'sprites' : OrderedDict()}}
		self.pages['main_menu'] = {'batch' : pyglet.graphics.Batch(), 'sprites' : OrderedDict()}
		self.active_page = 'main_menu'
		self.active_sprites = OrderedDict()

		#self.add_sprite(page='main_menu', itemName='main_menu', obj=main_menu(batch=self.pages['main_menu']['batch']))
		self.add_sprite(page='main_menu', itemName='house', obj=AnimatedSprite(war_data=game_data.sprites[315], palette=game_data.colorPalettes[416], batch=self.pages['main_menu']['batch'], x=30, y=30))
		#self.add_sprite('main_menu', 'background', generic_sprite(game_data.images[261].to_png(game_data.colorPalettes[260]), moveable=False))
		
		#for image in game_data.images:
		#	self.add_sprite('main_menu', 'background', generic_sprite(game_data.images[261].to_png(game_data.colorPalettes[260]), moveable=False))
		self.input = ''	
		self.keymap = {key._0 : 0, key._1 : 1, key._2 : 2, key._3 : 3, key._4 : 4, key._5 : 5, key._6 : 6, key._7 : 7, key._8 : 8, key._9 : 9}

		self.keys = {}

		self.drag = False
		self.alive = 1

	def add_sprite(self, page, itemName, obj):
		if not page in self.pages:
			self.pages[page] = {'batch' : pyglet.graphics.Batch(), 'sprites' : OrderedDict()}

		obj.set_batch(self.pages[page]['batch'])
		self.pages[page]['sprites'][itemName] = obj
		self.sprites[itemName] = obj

	def on_draw(self):
		self.render()

	def on_close(self):
		self.alive = 0

	def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
		self.drag = True

		for name, obj in self.active_sprites.items():
			obj.move(dx, dy)
			break

	def on_key_release(self, symbol, modifiers):
		if symbol == key.LCTRL:
			self.active_sprites = OrderedDict()

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
			for sprite_name, sprite in self.pages[self.active_page]['sprites'].items():
				if sprite:
					#print('Clickchecking:', sprite, 'with button', button)
					sprite_obj = sprite.mouse_inside(x, y, button)
					if sprite_obj:
						self.active_sprites[sprite_name] = sprite_obj

	def on_key_press(self, symbol, modifiers):
		self.keys[symbol] = True

		if symbol == key.ESCAPE: # [ESC]
			self.alive = 0

		elif symbol in self.keymap:
			self.input += str(self.keymap[symbol])

		elif symbol == key.BACKSPACE:
			self.input = self.input[:-1]

		elif symbol == key.ENTER:
			if int(self.input) in game_data.images:
				print('Loading image:', int(self.input))
				for palette_id in game_data.colorPalettes.keys():
					if not game_data.colorPalettes[palette_id].corrupted:
						self.add_sprite('main_menu', 'id:{}_pal:{}'.format(self.input, palette_id), generic_sprite(game_data.images[int(self.input)].to_png(game_data.colorPalettes[palette_id]), moveable=True))
			else:
				print('Image {} not in resources.'.format(self.input))
			self.input = ''
		#elif symbol == key.LCTRL:

	def render(self):
		#t = timer()
		self.clear()

		for sName, sObj in self.pages[self.active_page]['sprites'].items():
			sObj.update()

		#for sprite_name, sprite_obj in self.sprites.items():
		#	sprite_obj._draw()
		self.pages[self.active_page]['batch'].draw()

		self.flip()

	def run(self):
		while self.alive == 1:
			self.render()

			# -----------> This is key <----------
			# This is what replaces pyglet.app.run()
			# but is required for the GUI to not freeze
			#
			event = self.dispatch_events()

x = main()
x.run()