import sys, pyglet
from struct import *
from io import BytesIO
from os import mkdir
from os.path import isdir, isfile
from collections import OrderedDict

from config import conf

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
		self.width = 0
		self.height = 0

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

class WAR_TILES(WAR_RESOURCE):
	def __init__(self, index, data, size):
		WAR_RESOURCE.__init__(self, index, data, size)
		self.numOfTiles = self.extracted_size / 8 # 8?
		self.data = data
		#print('Tile len:', index, len(data), len(data)/2, len(data)/8, len(data)/16)
		self.size = size
		self.tiles_per_row = 16 # 16? 8*2?
		self.width = 8#self.tiles_per_row * 16 # 16? is 16 the known width/height of a tile?
		self.height = 8#self.tiles_per_row * 16 # 16? #((self.numOfTiles + self.tiles_per_row - 1) / self.tiles_per_row) * 16 # 16?

	def DecodeMiniTile(self, img, palette, gamma_correction=conf['gamma_correction'], supress_gamma=True):#, flip_x, flip_y):
		flip = [7,6,5,4,3,2,1,0,8]

		print(len(self.data), len(self.data)/3)
		print([img])
		print(len(palette['R']), len(palette['G']), len(palette['B']))

		png = [c for c in img]
		for c in img:
			for y in range(8):
				for x in range(8):
					c8bit = unpack('<B', self.data[y * 8 + x])[0]-1
					print('Color:', c8bit)
					print(len(palette['R']))
					print(palette['R'][c8bit])
					print(palette['G'][c8bit])
					print(palette['B'][c8bit])
					r,g,b,a = unpack('B', palette['R'][c8bit])[0], unpack('B', palette['G'][c8bit])[0], unpack('B', palette['B'][c8bit])[0], 255
				
					if supress_gamma:
						png[y * self.width + x] = pack('<4B', *(min(int(r*gamma_correction), 255), min(int(g*gamma_correction), 255), min(int(b*gamma_correction), 255), a))
					else:
						try:
							png[y * self.width + x] = pack('<4B', *(int(r*gamma_correction), int(g*gamma_correction), int(b*gamma_correction), a))
						except:
							raise ValueError('Gamma {} to high.'.format((int(r*gamma_correction), int(g*gamma_correction), int(b*gamma_correction), a)))

		return ''.join(png) #TODO: Fix this for py3

	def to_png(self, tile_set, palette, gamma_correction=conf['gamma_correction'], supress_gamma=True):

		img = gen_solid_image(self.width, self.height)
		print('Generating {}x{} size image'.format(self.width, self.height))
		#print([img.data])

		#for i in range(self.tiles_per_row):
		#mp = tile_set[i*8]
		#	for y in range(2):
		#		for x in range(2):
		#offset = unpack('B', tile_set[x+y*2])[0]
		#img.data = self.DecodeMiniTile(img.data, x+(i%self.tiles_per_row), y + (i/self.tiles_per_row) * 2)#, (offset&0xFFFC) << 1, offset & 2, offset & 1)
		img.data = self.DecodeMiniTile(img.data, palette)#, (offset&0xFFFC) << 1, offset & 2, offset & 1)

		return img
		#print([img.data])
		#conf['sprites'][189] = {'type' : 'tile_set', 'data' : None, 'description' : "Summer 1"}
		#conf['sprites'][190] = {'type' : 'tiles', 'data' : None, 'description' : "Summer 2"}

class WAR_TILESET(WAR_RESOURCE):
	def __init__(self, index, data, size):
		WAR_RESOURCE.__init__(self, index, data, size)

	def __getitem__(self, index):
		return self.data[index]


class WAR_SPRITE(WAR_RESOURCE):
	def __init__(self, index, data, size):
		WAR_RESOURCE.__init__(self, index, data, size)
		self.frames = OrderedDict()

		# B - size 1
		# H - size 2
		# I - size 4
		# Q - size 8
		# n - size 16

		# The .SPR Format
		# Sprite sheet files start with a 2 byte integer telling the number of frames inside the file,
		# followed by the sprite dimensions as 1 byte width and height.

		# Next is a list of all frames, starting with their y and x offset, followed by width and height, each as 1 byte value.

		# Last comes the offset of the frame inside the file, stored as 4 byte integer.
		# If the width times height is greater than the difference between this and the next
		# offset, then the frame is compressed as specified below. Else it is to be read as a usual
		# indexed 256 color bitmap.
		# 	2.4.1 Sprite Decompression
		# 	Sprites of the Mac version are often compressed with an RLE method. Only transparency
		# 	is compressed and the compression is linewise.
		# 	Lines are assembled by reading them blockwise, where each block starts with a single
		# 	byte Head, that gives further instructions:
		# 	* 0x00 -> EndOfLine
		# 	* 0xFF -> EndOfFrame
		# 	* 0x80 & Head = 0 -> Head-many uncompressed pixels follow
		# 	* 0x80 & Head != 0 -> ((0x7F & Head) + 1)-many transparent pixels

		offset = 0
		self.frameCount = unpack('<H', self.data[offset:offset+2])[0]
		offset += calcsize('<H')

		self.width = unpack('B', self.data[offset:offset+1])[0]
		offset += 1
		self.height = unpack('B', self.data[offset:offset+1])[0]
		offset += 1

		#print('Frames:', self.frameCount)
		#print('Size:', self.max_width, self.max_height)

		for i in range(self.frameCount):
			xoff = unpack('B', self.data[offset:offset+1])[0]
			yoff = unpack('B', self.data[offset+1:offset+2])[0]
			width = unpack('B', self.data[offset+2:offset+3])[0]
			height = unpack('B', self.data[offset+3:offset+4])[0]
			frameOffset = unpack('<i', self.data[offset+4:offset+8])[0]
			offset += 8 # Each image description block is 8 bytes.
			self.frames[i] = {'width': width, 'height' : height, 'xOffset' : xoff, 'yOffset' : yoff, 'frameOffset' : frameOffset, 'data' : None}

			#print('Index:{} xOff:{} yOff:{} width:{} height:{} frameOffset:{} endPos:{}'.format(index, xoff, yoff, width, height, frameOffset, frameOffset+(width*height)))
			if frameOffset < 0:
				frameOffset &= 0x7FFFFFFF
				width += 256
				self.frames[i]['frameOffset'] = frameOffset
				self.frames[i]['width'] = width

			rows = [b'']*height
			index = 0
			for y in range(height):
				for x in range(width):
					#c8bit = unpack('<B', self.data[frameOffset+index:frameOffset+index+1])[0]
					rows[y] = rows[y] + self.data[frameOffset+index:frameOffset+index+1]
					index += 1

			self.frames[i]['data'] = rows

	def convert_frames(self, palette, gamma_correction=conf['gamma_correction'], supress_gamma=True):
		for index in self.frames:
			self.frames[index]['image'] = self.to_png(index, palette, gamma_correction, supress_gamma)

	def to_png(self, frame, palette, gamma_correction=conf['gamma_correction'], supress_gamma=True):
		""" It's not actually a full fledged PNG.
		But sort of is. Just missing the header."""

		## == The rest is palette-positions, not RGB colors.
		## == First, we create a solid image-placeholder with RGBA format.
		img = gen_solid_image(self.frames[frame]['width'], self.frames[frame]['height'])
		## == We create row placeholders,
		##    Mainly becase WAR images are calculated from top down
		##    but PNG/RGBA are bottom up format. So at the end, we'll do a
		##    reverse(rows) before building the image.
		rows = [b'']*self.frames[frame]['height']
		index = 0
		for y in range(self.frames[frame]['height']):
			for x in range(self.frames[frame]['width']):
				c8bit = unpack('B', self.frames[frame]['data'][y][x])[0] #unpack('<B', self.frames[frame][index:index+1])[0]
				try:
					r,g,b,a = unpack('B', palette['R'][c8bit])[0], unpack('B', palette['G'][c8bit])[0], unpack('B', palette['B'][c8bit])[0], 255
				except:
					raise KeyError('Color {} not in palette: {}'.format(c8bit, palette))

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

class WAR_PALETTE(WAR_RESOURCE):
	def __init__(self, index, data, size):
		WAR_RESOURCE.__init__(self, index, data, size)
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

	#def __repr__(self):
	#	return str(self.shades)

class WAR_IMAGE(WAR_RESOURCE):
	def __init__(self, index, data, size):
		WAR_RESOURCE.__init__(self, index, data, size)

	def to_png(self, palette, gamma_correction=conf['gamma_correction'], supress_gamma=True):
		""" It's not actually a full fledged PNG.
		But sort of is. Just missing the header."""

		## == First four bytes, is the width and height.
		self.width = unpack('<H', self.data[0:2])[0]
		self.height = unpack('<H', self.data[2:4])[0]
		data = self.data[4:]

		## == The rest is palette-positions, not RGB colors.
		## == First, we create a solid image-placeholder with RGBA format.
		img = gen_solid_image(self.width, self.height)
		## == We create row placeholders,
		##    Mainly becase WAR images are calculated from top down
		##    but PNG/RGBA are bottom up format. So at the end, we'll do a
		##    reverse(rows) before building the image.
		rows = [b'']*self.height
		index = 0
		for y in range(self.height):
			for x in range(self.width):
				c8bit = unpack('<B', data[index:index+1])[0]

				try:
					# Python 3
					r,g,b,a = palette['R'][c8bit], palette['G'][c8bit], palette['B'][c8bit], 255
				except:
					try:
						# Python 2
						r,g,b,a = unpack('B', palette['R'][c8bit])[0], unpack('B', palette['G'][c8bit])[0], unpack('B', palette['B'][c8bit])[0], 255
					except:
						raise KeyError('Color {} not in palette: {}'.format(c8bit, palette))

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
		self.colorPalettes = {}
		self.images = {}
		self.sprites = {}
		self.tiles = {}
		self.tile_sets = {}

		self.header = self.parse_header()
		self.read_file_table()

	def __repr__(self, *args, **kwargs):
		return str(self.objects)

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
				self.colorPalettes[i] = WAR_PALETTE(i, self.data[data_start:data_stop], size=data_stop-data_start)
				self.objects[i] = self.colorPalettes[i]

			elif conf['sprites'][i]['type'] == 'image':
				self.images[i] = WAR_IMAGE(i, self.data[data_start:data_stop], size=data_stop-data_start)
				self.objects[i] = self.images[i]

			elif conf['sprites'][i]['type'] == 'sprite':
				self.sprites[i] = WAR_SPRITE(i, self.data[data_start:data_stop], size=data_stop-data_start)
				self.objects[i] = self.sprites[i]

			elif conf['sprites'][i]['type'] == 'tiles':
				self.tiles[i] = WAR_TILES(i, self.data[data_start:data_stop], size=data_stop-data_start)
				self.objects[i] = self.tiles[i]

			elif conf['sprites'][i]['type'] == 'tile_set':
				self.tile_sets[i] = WAR_TILESET(i, self.data[data_start:data_stop], size=data_stop-data_start)
				self.objects[i] = self.tile_sets[i]

			#else:
			#	self.objects[i] = WAR_RESOURCE(i, self.data[data_start:data_stop], size=data_stop-data_start)

			## == Counter of objects
			if i in self.objects:
				if not self.objects[i].type in self.contains:
					self.contains[self.objects[i].type] = 0
				self.contains[self.objects[i].type] += 1

		for key, val in self.contains.items():
			print(' -',key,' (' + str(val) + ' of them)')