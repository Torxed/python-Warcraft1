#import lzw # Was slightly broken spewing out "EOS" errors.
import sys
from struct import *
from time import sleep # DEBUG
from io import BytesIO
from os import mkdir
from os.path import isdir, isfile
import pyglet
from pyglet.gl import *
from collections import OrderedDict
from os.path import isfile
from math import *
from time import time
pyglet.options['audio'] = ('alsa', 'openal', 'silent')
key = pyglet.window.key

from config import conf

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

def lss_decompress(data, unCompressedFileLength):
	"""
	This is the most messy code ever written.
	But it does the job, and both this cred goes to:
		https://github.com/Wargus/war1gus/blob/master/war1tool.c#L1180
	"""
	buf = [ 0x00 for i in range(4096) ]
	fileData = [ None for i in range(unCompressedFileLength) ]
	compData = BytesIO(data)
	compData.seek(0)

	dp = 0
	bi = 0
	ep = dp + unCompressedFileLength

	while dp < ep:
		bflags = unpack('<B', compData.read(1))[0]
		for i in range(8):
			if bflags & 1:
				j = unpack('<B', compData.read(1))[0]
				
				#*dp++ = j;
				fileData[dp] = j
				dp += 1
				
				bi &= 0xFFF
				buf[bi] = j
				bi+=1
			else:
				o = unpack('<H', compData.read(2))[0]
				j = (o >> 12) + 3;
				o &= 0xFFF;
				while (j):
					o &= 0xFFF
					bi &= 0xFFF
					fileData[dp] = buf[o]
					dp += 1
					buf[bi] = buf[o]
					bi += 1
					o += 1
					if dp == ep:
						break
					j -= 1
			if dp == ep:
				break
			bflags >>= 1

	return b''.join([pack('<B', x) if type(x) == int else x for x in fileData])

class WAR_RESOURCE():
	def __init__(self, index, data, size):
		"""
		This is functionality all .war resources share.
		Mainly that they're compressed/uncompressed,
		they have a data-len(size) and extracted size (found in data).
		"""
		self.type = conf['sprites'][index]['type']

		self.size = size
		self.found_size = unpack('<I', data[:4])[0]
		self.compressed = True if self.found_size >> 24 == 0x20 else False
		self.extracted_size = self.found_size & 0x1FFFFFFF
		self.corrupted = False

		#print('[#{}]<Comp:{}> Packed Size: {}, Extracted size: {}'.format(index, self.compressed, size, self.extracted_size))
			
		data = data[4:] # Strips the header

		if self.compressed:
			#self.data = lzw_decompress(data)
			try:
				self.data = lss_decompress(data, self.extracted_size)
			except:
				print(index,'is corrupted')
				self.corrupted = True
				self.data = data
		else:
			self.data = data

		#if not self.corrupted:
		#	if not isdir('./dump/'+self.type):
		#		mkdir('./dump/'+self.type)

class WAR_PALETTE(WAR_RESOURCE):
	def __init__(self, index, data, size):
		super(WAR_PALETTE, self).__init__(index, data, size)
		self.shades = {'R' : b'', 'G': b'', 'B' : b''}

		try:
			for index in range(0, len(self.data), 3):
				RGB = unpack('<3B', self.data[index:index+3])
				self.shades['R'] += pack('<B', RGB[0])
				self.shades['G'] += pack('<B', RGB[1])
				self.shades['B'] += pack('<B', RGB[2])
		except:
			print(len(self.data), len(self.data)/3)
			self.corrupted = True

	def __getitem__(self, key):
		if key.upper() in self.shades:
			return self.shades[key.upper()]
		else:
			raise KeyError('{} is not in the color palette. Valid options: {}'.format(key, ', '.join([key for key in self.shades])))

	def __repr__(self):
		return str(self.shades)

class WAR_IMAGE(WAR_RESOURCE):
	def __init__(self, index, data, size):
		super(WAR_IMAGE, self).__init__(index, data, size)

	def to_png(self, palette, gamma_correction=2.5, supress_gamma=True):
		""" It's not actually a full fledged PNG.
		But sort of is. Just missing the header."""

		## == First four bytes, is the width and height.
		width = unpack('<H', self.data[0:2])[0]
		height = unpack('<H', self.data[2:4])[0]
		data = self.data[4:]

		## == The rest is palette-positions, not RGB colors.
		## == First, we create a solid image-placeholder with RGBA format.
		img = gen_solid_image(width, height)
		## == We create row placeholders,
		##    Mainly becase WAR images are calculated from top down
		##    but PNG/RGBA are bottom up format. So at the end, we'll do a
		##    reverse(rows) before building the image.
		rows = [b'']*height
		index = 0
		for y in range(height):
			for x in range(width):
				c8bit = unpack('<B', data[index:index+1])[0]
				try:
					r,g,b,a = palette['R'][c8bit], palette['G'][c8bit], palette['B'][c8bit], 255
				except:
					raise KeyError('Color {} not in palette: {}'.format((r,g,b,a), palette))

				if supress_gamma:
					rows[y] += pack('<4B', *(min(int(r*gamma_correction), 255), min(int(g*gamma_correction), 255), min(int(b*gamma_correction), 255), a))
				else:
					try:
						rows[y] += pack('<4B', *(int(r*gamma_correction), int(g*gamma_correction), int(b*gamma_correction), a))
					except:
						raise ValueError('Gamma {} to high.'.format((int(r*gamma_correction), int(g*gamma_correction), int(b*gamma_correction), a)))
				index += 1

		img.data = b''.join(rows[::-1])#new_data#[::-1]
		return img

class WAR():
	def __init__(self, WAR_FILE):
		self.archive = WAR_FILE
		with open(self.archive, 'rb') as fh:
			self.data = fh.read()

		self.id = 0
		self.num_o_files = 0
		self.lz = False
		self.contains = {}
		self.header_size = 8

		self.objects = {}
		self.color_palette = {}
		self.images = {}

		self.header = self.parse_header()
		self.read_file_table()


	def parse_header(self):
		## == /doc/war_header.png

		# B - size 1
		# H - size 2
		# I - size 4
		# Q - size 8
		# n - size 16

		header_bytes = self.data[0:self.header_size]

		self.id = unpack('<I', header_bytes[:4])[0]
		## == There's two ways people do this:
		##    First is that 4 bytes == num of files.
		##    The other using <H (2 bytes) as numOfFiles and
		##    The remainder two bytes as a magic number (?)
		self.num_o_files = unpack('<I', header_bytes[4:])[0] # The first byte is num of files.
		self.retail = True if self.id == 24 else False

		print('Archive:', self.archive)
		print('Archive ID:', self.id,'[Retail]' if self.retail else '[Demo]')
		print('Num o files:', self.num_o_files)

		self.offsets = []
		bytesize = calcsize('<I') # This is the size of each offset-position value.
		for i in range(self.num_o_files):
			offset = unpack('<I', self.data[self.header_size+(bytesize*i):self.header_size+(bytesize*i)+bytesize])[0]
			## == If the offset is 0000 or FFFF it means it's a placeholder.
			##    Mainly these orriginates from DEMO or Pre-release versions of the game.
			##    But we still need to deal with them just in case.
			if offset == 0 or offset == 4294967295:
				offset = -1

			if i == 473:
				print('File #{} has offset {}'.format(i, offset))
			self.offsets.append(offset)

	def read_file_table(self):
		for i in range(len(self.offsets)):
			data_start = self.offsets[i]
			if data_start == -1:
				print('Placeholder...')
				continue # It's a placeholder.
						 # Typically only happens in demo versions.

			if i+1 == len(self.offsets):
				data_stop = len(self.data)
			else:
				data_stop = self.offsets[i+1]

			#self.objects[i] = WAR_RESOURCE(i, self.data[data_start:data_stop], size=data_stop-data_start)
			if conf['sprites'][i]['type'] == 'palette':
				self.color_palette[i] = WAR_PALETTE(i, self.data[data_start:data_stop], size=data_stop-data_start)
				self.objects[i] = self.color_palette[i]

			elif conf['sprites'][i]['type'] == 'image':
				self.images[i] = WAR_IMAGE(i, self.data[data_start:data_stop], size=data_stop-data_start)
				self.objects[i] = self.images[i]

			#else:
			#	self.objects[i] = WAR_RESOURCE(i, self.data[data_start:data_stop], size=data_stop-data_start)

			## == Counter of objects
			if i in self.objects:
				if not self.objects[i].type in self.contains:
					self.contains[self.objects[i].type] = 0
				self.contains[self.objects[i].type] += 1

		for key, val in self.contains.items():
			print(' -',key,' (' + str(val) + ' of them)')

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
	def __init__(self, texture=None, width=None, height=None, color="#C2C2C2", alpha=int(255), x=None, y=None, moveable=False, batch=None):
		if type(texture) == str:
			if not texture or not isfile(texture):
				#print('No texutre could be loaded for sprite, generating a blank one.')
				## If no texture was supplied, we will create one
				if not width:
					width = 10
				if not height:
					height = 10
				self.texture = gfx_helpers.gen_solid_image(width*_UPSCALE_, height*_UPSCALE_, color, alpha)
			else:
				self.texture = pyglet.image.load(texture)
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

class main(pyglet.window.Window):
	def __init__ (self, width=conf['resolution'].width(), height=conf['resolution'].height(), *args, **kwargs):
		super(main, self).__init__(width, height, *args, **kwargs)
		self.x, self.y = 0, 0

		self.sprites = OrderedDict()
		self.game_data = WAR(sys.argv[1])
		self.pages = {'default' : {'batch' : pyglet.graphics.Batch(), 'sprites' : {}}}
		self.pages['main_menu'] = {'batch' : pyglet.graphics.Batch(), 'sprites' : {}}
		self.active_page = 'main_menu'
		self.active_sprites = OrderedDict()

		#self.add_sprite('main_menu', 'background', generic_sprite(self.game_data.images[261].to_png(self.game_data.color_palette[260]), moveable=False))
		
		#for image in self.game_data.images:
		#	self.add_sprite('main_menu', 'background', generic_sprite(self.game_data.images[261].to_png(self.game_data.color_palette[260]), moveable=False))
		self.input = ''	
		self.keymap = {key._0 : 0, key._1 : 1, key._2 : 2, key._3 : 3, key._4 : 4, key._5 : 5, key._6 : 6, key._7 : 7, key._8 : 8, key._9 : 9}

		self.keys = {}

		self.drag = False
		self.alive = 1

	def add_sprite(self, page, title, obj):
		if not page in self.pages:
			self.pages[page] = {'batch' : pyglet.graphics.Batch(), 'sprites' : {}}

		obj.batch = self.pages[page]['batch']
		self.pages[page]['sprites'][title] = obj
		self.sprites[title] = obj

	def on_draw(self):
		self.render()

	def on_close(self):
		self.alive = 0

	def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
		self.drag = True

		for name, obj in self.active_sprites.items():
			print('Moving',name)
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
			if int(self.input) in self.game_data.images:
				print('Loading image:', int(self.input))
				for palette_id in self.game_data.color_palette.keys():
					if not self.game_data.color_palette[palette_id].corrupted:
						self.add_sprite('main_menu', '{}_{}'.format(self.input, palette_id), generic_sprite(self.game_data.images[int(self.input)].to_png(self.game_data.color_palette[palette_id]), moveable=True))
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