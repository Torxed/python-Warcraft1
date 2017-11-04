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

def ConvertPalette(data):
	for i in range(768): # PNG needs 0-256
		data[i] <<= 2

	return data

def ConvertImg(data):
	offset = 0
	width = unpack('<H', data[offset:offset+2])
	offset += 2
	height = unpack('<H', data[offset:offset+2])
	offset += 2

	image = [ data[i] for i in range(width*height) ]

	for i in range(width*height):
		if image[i] == 96:
			image[i] = 255

	return image

def ConvertImage(data):
	image = ConvertImg(data)
	ConvertPalette(image)

	#sprintf(buf, "%s/%s/%s.png", Dir, GRAPHIC_PATH, file);
	#CheckPath(buf);

	#ResizeImage(&image, w, h, 2 * w, 2 * h);
	#SavePNG(buf, image, 2 * w, 2 * h, palp, -1)

def lss2_decompress(data, unCompressedFileLength):
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

def lss_decompress(data, unCompressedFileLength):
	## == Allocate a bytes file that is equal to the extracted size.
	## == Also fill it with b'' as placeholders for when doing index overwrite later.
	fileData = [ None for i in range(unCompressedFileLength) ]
	## == Convert the data into a file object to handle read/jumpaheads
	compData = BytesIO(data)
	compData.seek(0)

	## == Current write position in the fileData
	currentWritePos = 0
	## == A look ahead index
	byteIndex = 0
	## == Create a lookup table for the decompression algo.
	lookAheadBuffer = [ 0x00 for i in range(4096) ]
	currentProcessingByte = 0

	DEBUG = 0

	while currentProcessingByte < unCompressedFileLength:
		byteFlags = unpack('<B', compData.read(1))[0] # 1 byte
		#print('Read byteFlags:', byteFlags)

		for x in range(8):
			if byteFlags & 1:
				dataByte = unpack('<B', compData.read(1))[0]
				#print('Writing at Position:', currentWritePos,'dataByte:', dataByte)

				fileData[currentWritePos] = dataByte
				currentWritePos += 1

				byteIndex &= 0xFFF
				lookAheadBuffer[byteIndex] = byteFlags
				byteIndex += 1
				currentProcessingByte += 1
			else:
				try:
					repeatByte = unpack('<H', compData.read(2))[0]
				except:
					print(len(data), unCompressedFileLength, currentProcessingByte)
					return data

				dataByte = (repeatByte >> 12) + 3 # Wtf is this 3 doing here?
				repeatByte &= 0xFFF


				while dataByte:
					repeatByte &= 0xFFF
					byteIndex &= 0xFFF
					fileData[currentWritePos] = lookAheadBuffer[repeatByte]
					currentWritePos += 1
					lookAheadBuffer[byteIndex] = lookAheadBuffer[repeatByte]
					repeatByte += 1
					byteIndex += 1

					currentProcessingByte += 1
					if currentProcessingByte == unCompressedFileLength:
						break

					dataByte -= 1
			if currentProcessingByte == unCompressedFileLength:
				break

		byteFlags >>= 1

	return b''.join([pack('<B', x) if type(x) == int else x for x in fileData])

def pad(b, l=4):
	return b+(b'\x00'*(l-len(b)))

class WAR_RESOURCE():
	def __init__(self, index, data, size):
		self.size = size
		self.found_size = unpack('<I', data[:4])[0]
		#print(bin(self.data_len)[2:])
		#self.compressed = True if bin(self.data_len)[2:][3] == '1' else False
		self.compressed = True if self.found_size >> 24 == 0x20 else False
		self.extracted_size = self.found_size & 0x1FFFFFFF
		self.corrupted = False

		if index == 473:
			print('[#{}]<Comp:{}> Packed Size: {}, Extracted size: {}'.format(index, self.compressed, size, self.extracted_size))
			
		data = data[4:] # Strips the header
		#self.compressed = compressed

		self.IMG, self.CUR, self.SPR = 0, 1, 2

		if self.compressed:
			#if index == 473:
			#self.data = lzw_decompress(data)
			#try:
			self.data = lss2_decompress(data, self.extracted_size)
			#except:
			#	print(index,'is corrupted')
			#	self.corrupted = True
			#	self.data = data
		else:
			print(index,'is not compressed')
			self.data = data


		self.type = conf['sprites'][index]['type']
		if not self.corrupted:
			if not isdir('./dump/'+self.type):
				mkdir('./dump/'+self.type)
		
			#with open('./dump/'+self.type+'/'+str(index)+'.'+self.type, 'wb') as fh:
			#	fh.write(self.data)

		#print('\nSelf data:',self.data)
		#print('\nData:', data)

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
		## == The header+data looks like this:
		##
		##        4 bytes  |   1 byte       3 bytes
		##    | ---------- | ------------------------ |
		##    [ Archive ID | Nr of files | compressed ]
		##    [  f_1 start |  f_2 start  | f_3 start  ] * ammount of files
		##

		# B - size 1
		# H - size 2
		# I - size 4
		# Q - size 8
		# n - size 16

		## 473 == wav, and should play fine.
		# Extracting Entity #473
		# Entity #473 has offset: 1621169 uncompressed Size: 51244
		# Allocating unCompressedFile data size: 51244

		## == Known first offset: 2340 //2344 according to shit appl
		## == Known comressed len: 16830

		# Deleting currentArchiveFileStream
		# Deleting vector fileOffsets
		# Opening file war1.war
		# Magic Number: 24 Number of Entities: 583 Type: 0
		# File #0  has data Offset: 2340
		# File #1  has data Offset: 19174
		# File #2  has data Offset: 35429
		# File #3  has data Offset: 51377
		# File #4  has data Offset: 66937
		# File #5  has data Offset: 78300
		# File #6  has data Offset: 92159
		# File #7  has data Offset: 94991
		# File #8  has data Offset: 98207
		# File #9  has data Offset: 102641

		# Extracting Entity #0
		# Entity #0 has offset: 2340 uncompressed Size: 25272
		# Allocating unCompressedFile data size: 25272
		# Read byteFlags: �
		# Writing at Position: 0 dataByte: 70
		# Writing at Position: 1 dataByte: 79
		# Writing at Position: 2 dataByte: 82
		# Writing at Position: 3 dataByte: 77
		# Writing at Position: 4 dataByte: 0
		# Writing at Position: 5 dataByte: 0
		# Writing at Position: 6 dataByte: 0
		# Writing at Position: 7 dataByte: 14
		# Writing at Position: 8 dataByte: 88
		# Writing at Position: 9 dataByte: 68


		header_bytes = self.data[0:self.header_size]

		self.id = unpack('<I', header_bytes[:4])[0]
		self.num_o_files = unpack('<I', header_bytes[4:])[0] # The first byte is num of files.
		#self.lz = True if unpack('<I', pad(entries[1:]))[0]==2 else False # the 3 last bytes are meta.
		#self.retail = True if self.id == 24 else False
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

		#print('Offsets:', self.offsets)

	def read_file_table(self):
		#if not self.lz:
		#	raise ValueError('Can not handle uncompressed file headers atm in filetable.')
		#	meta = unpack('<I', self.data[8:9])[0]
		#	data_pos = meta%4096
		#else:
#			for index, data_start in enumerate(self.offsets):

		## == Data start is the offset stored in offsets[x].
		##    And we find the end of the data by checking the next offset.
		##    Since we know the data can't be longer than the next position in offsets.
		for i in range(len(self.offsets)):
			data_start = self.offsets[i]
			if data_start == -1:
				print('Placeholder...')
				continue # It's a placeholder.

			if i+1 == len(self.offsets):
				data_stop = len(self.data)
			else:
				data_stop = self.offsets[i+1]

			#print(data_start, data_stop)
			#if i == 473:
			self.objects[i] = WAR_RESOURCE(i, self.data[data_start:data_stop], size=data_stop-data_start)
			#else:
			#	continue


			if not self.objects[i].type in self.contains:
				self.contains[self.objects[i].type] = 0
			self.contains[self.objects[i].type] += 1

		for key, val in self.contains.items():
			print(' -',key,' (' + str(val) + ' of them)')

			#index = 0
			#pos = 8
			#pos = self.data.find(b'\x20\x00')
			#print(self.data[pos-100:pos+100])

#			while pos < len(self.data):
#				meta = unpack('<h', self.data[pos:pos+2])[0]
#				numbytes = meta//4096
#				offset = meta%4096
#
#				#print('Offset:', meta)
#				#print('numbytes:', numbytes)
#				#print('Offset:', offset)
#
#				pos += 2 + numbytes + offset
#				#sleep(0.25)
#				index += 1
#

			#nmeta = unpack('<h', self.data[10+offset+numbytes:10+offset+numbytes+2])[0]
			#umbytes = nmeta//4096
			#offset = nmeta%4096
			
			#print('Offset:', nmeta)
			#print('numbytes:', numbytes)
			#print('Offset:', offset)

			#data = self.data[11+offset:11+offset+numbytes]

			#with open('debug.bin', 'wb') as fh:
			#	fh.write(data)


import sys
archive = WAR(sys.argv[1])
#archive = WAR('../wc1/WARCRAFT_1/DATA/DATA.WAR')
#archive = WAR('../wc1/WARCRAFT_1/DATA/TITLE.WAR')
#print('Archive ID:', archive.id)
#print('Num files:', archive.num_o_files)
#print('Compressed:', archive.lz)

#print('Files:', list(archive.objects.keys()))
#print('Contains:', archive.contains)