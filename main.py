#import lzw # Was slightly broken spewing out "EOS" errors.
from struct import *
from time import sleep # DEBUG
from io import BytesIO
from os import mkdir
from os.path import isdir, isfile

from config import conf

# https://github.com/magical/nlzss/blob/master/lzss3.py#L36
# https://github.com/Wargus/war1gus/blob/master/war1tool.c
# https://github.com/plasticlogic/pldata/blob/master/lzss/python/pylzss.c
# https://github.com/Wargus/wargus
# https://github.com/Wargus/war1gus/blob/master/war1tool.c
# https://github.com/Wargus/stratagus/issues/198
# https://github.com/bradc6
# https://github.com/Stratagus/libwararch/blob/master/SampleSource/ExtractFile/main.cpp
# https://github.com/Stratagus/libwararch/blob/master/Source/WarArchive/WarArchive.cpp

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
		self.size = size
		self.found_size = unpack('<I', data[:4])[0]
		self.compressed = True if self.found_size >> 24 == 0x20 else False
		self.extracted_size = self.found_size & 0x1FFFFFFF
		self.corrupted = False

		if index == 473:
			print('[#{}]<Comp:{}> Packed Size: {}, Extracted size: {}'.format(index, self.compressed, size, self.extracted_size))
			
		data = data[4:] # Strips the header

		self.IMG, self.CUR, self.SPR = 0, 1, 2

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


		self.type = conf['sprites'][index]['type']
		if not self.corrupted:
			if not isdir('./dump/'+self.type):
				mkdir('./dump/'+self.type)
		
			#with open('./dump/'+self.type+'/'+str(index)+'.'+self.type, 'wb') as fh:
			#	fh.write(self.data)

class WAR():
	def __init__(self, WAR_FILE):
		self.archive = WAR_FILE
		with open(self.archive, 'rb') as fh:
			self.data = fh.read()

		self.id = 0
		self.num_o_files = 0
		self.lz = False
		self.objects = {}
		self.contains = {}
		self.header_size = 8

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

			self.objects[i] = WAR_RESOURCE(i, self.data[data_start:data_stop], size=data_stop-data_start)

			if not self.objects[i].type in self.contains:
				self.contains[self.objects[i].type] = 0
			self.contains[self.objects[i].type] += 1

		for key, val in self.contains.items():
			print(' -',key,' (' + str(val) + ' of them)')


import sys
archive = WAR(sys.argv[1])