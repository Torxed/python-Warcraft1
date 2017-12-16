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

def getTexture(img_id):
	return game_data.images[img_id].to_png(game_data.colorPalettes[conf['colorMap'][img_id]])

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

		if x > self.x and x < (self.x + (self.texture.width*conf['resolution'].scale())):
			if y > self.y and y < (self.y + (self.texture.height*conf['resolution'].scale())):
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

class gameUI(generic_sprite):
	def __init__(self, race, batch=None):
		super(gameUI, self).__init__(width=conf['resolution'].width(), height=conf['resolution'].height(), alpha=0, batch=batch)

		self.race = race

		self.layers = OrderedDict()
		self.layers['base'] = pyglet.graphics.Batch()

		self.sprites['minimap'] = generic_sprite(getTexture(conf['ui'][self.race]['sidebars']['left']['minimap']['empty']), bind=start_game)
		self.sprites['minimap'].x = 0
		self.sprites['minimap'].y = conf['resolution'].height() - self.sprites['minimap'].height

		self.sprites['left_bar'] = generic_sprite(getTexture(conf['ui'][self.race]['sidebars']['left']['normal']), bind=start_game)
		self.sprites['left_bar'].x = 0
		self.sprites['left_bar'].y = conf['resolution'].height() - self.sprites['minimap'].height - self.sprites['left_bar'].height

		self.sprites['top_bar'] = generic_sprite(getTexture(conf['ui'][self.race]['sidebars']['top']['normal']), bind=start_game)
		self.sprites['top_bar'].x = self.sprites['minimap'].width
		self.sprites['top_bar'].y = conf['resolution'].height() - self.sprites['top_bar'].height

		self.sprites['right_bar'] = generic_sprite(getTexture(conf['ui'][self.race]['sidebars']['right']['normal']), bind=start_game)
		self.sprites['right_bar'].x = self.sprites['minimap'].width + self.sprites['top_bar'].width
		self.sprites['right_bar'].y = conf['resolution'].height() - self.sprites['right_bar'].height

		self.sprites['bottom_bar'] = generic_sprite(getTexture(conf['ui'][self.race]['sidebars']['bottom']['normal']), bind=start_game)
		self.sprites['bottom_bar'].x = self.sprites['minimap'].width
		self.sprites['bottom_bar'].y = 0

		# grass = tile_set 189 & 190

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
		self.x, self.y = 0, 0

		self.sprites = OrderedDict()
		__builtins__.__dict__['game_data'] = WAR(sys.argv[1])
		self.pages = {'default' : {'batch' : pyglet.graphics.Batch(), 'sprites' : OrderedDict()}}
		self.pages['main_menu'] = {'batch' : pyglet.graphics.Batch(), 'sprites' : OrderedDict()}
		self.pages['main_ui'] = {'batch' : pyglet.graphics.Batch(), 'sprites' : OrderedDict()}

		self.active_page = 'main_ui' #'main_menu'
		self.active_sprites = OrderedDict()

		#self.add_sprite(page='main_menu', itemName='main_menu', obj=main_menu(batch=self.pages['main_menu']['batch']))
		#self.add_sprite(page='main_menu', itemName='house', obj=AnimatedSprite(war_data=game_data.sprites[315], palette=game_data.colorPalettes[416], batch=self.pages['main_menu']['batch'], x=30, y=30))
		self.add_sprite(page='main_ui', itemName='frame', obj=gameUI(race='human', batch=self.pages['main_ui']['batch']))
		self.add_sprite(page='main_ui', itemName='Warrior', obj=HumanWarrior(batch=self.pages['main_ui']['batch'], x=200, y=200))
		self.add_sprite(page='main_ui', itemName='Orc', obj=OrcGrunt(batch=self.pages['main_ui']['batch'], x=350, y=200))

		self.add_sprite(page='main_ui', itemName='Grass', obj=Tile(193, batch=self.pages['main_ui']['batch'], x=300, y=250))
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
		if not page in self.pages:
			self.pages[page] = {'batch' : pyglet.graphics.Batch(), 'sprites' : OrderedDict()}

		obj.set_batch(self.pages[page]['batch'])
		self.pages[page]['sprites'][itemName] = obj
		self.sprites[itemName] = obj

	def flush_sprites(self, page=None):
		if not page: page = self.active_page

		for obj in self.pages[page]['sprites']:
			self.pages[page]['sprites'][obj].delete()
			del self.pages[page]['sprites'][obj]
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
				self.add_sprite(page='main_menu', itemName='id:{}_pal:{}'.format(index, palette_id), obj=AnimatedSprite(war_data=game_data.sprites[index], palette=game_data.colorPalettes[palette_id], batch=self.pages['main_menu']['batch'], x=x, y=y))
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
			for sName, sObj in self.pages[self.active_page]['sprites'].items():
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

	def render(self):
		#t = timer()
		self.clear()

		## TODO: Uncomment this when auto-updates are ready
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