#import lzw # Was slightly broken spewing out "EOS" errors.
from struct import *
from time import sleep # DEBUG

from config import conf

# unpack('hhl', '\x00\x01\x00\x02\x00\x00\x00\x03')
# The main difference is that Warcraft II, megatiles are 32x32 (made of 16 8x8 Minitiles) whereas War1 is 16x16 (4 8x8 minitiles).

## == Not yet modified to handle bytes data.
##    https://rosettacode.org/wiki/LZW_compression#Python
#def lzw_compress(uncompressed):
#	"""Compress a string to a list of output symbols."""
#
#	# Build the dictionary.
#	dict_size = 256
#	dictionary = dict((chr(i), i) for i in xrange(dict_size))
#	# in Python 3: dictionary = {chr(i): i for i in range(dict_size)}
#
#	w = ""
#	result = []
#	for c in uncompressed:
#		wc = w + c
#		if wc in dictionary:
#			w = wc
#		else:
#			result.append(dictionary[w])
#			# Add wc to the dictionary.
#			dictionary[wc] = dict_size
#			dict_size += 1
#			w = c
#
#	# Output the code for w.
#	if w:
#		result.append(dictionary[w])
#	return result

def lzw_decompress(compressed):
	"""Decompress a list of output ks to a string."""
	from io import BytesIO
 
	# Build the dictionary.
	dict_size = 256
	dictionary = dict((bytes([i]), bytes([i])) for i in range(dict_size))
 
	# use StringIO, otherwise this becomes O(N^2)
	# due to string concatenation in a loop
	result = BytesIO()
	w = bytes([compressed[0]])
	result.write(w)
	for k in compressed[1:]:
		k = bytes([k])
		if k in dictionary:
			entry = dictionary[k]
		elif k == dict_size:
			entry = w + w[0]
		else:
			raise ValueError('Bad compressed k: %s' % k)
		result.write(entry)
 
		# Add w+entry[0] to the dictionary.
		dictionary[dict_size] = w + bytes([entry[0]])
		dict_size += 1
 
		w = entry
	return result.getvalue()

def pad(b, l=4):
	return b+(b'\x00'*(l-len(b)))

# B - size 1
# H - size 2
# I - size 4
# Q - size 8
# n - size 16
class WAR_RESOURCE():
	def __init__(self, index, data, compressed):
		#print(data)
		#else:
		#	print(data[:len(THUNK)])
		align = data[2] # 3:d byte
		self.data_len = unpack('<H', data[:2])[0] + (align << 16)
		self.compressed = True if data[3] != b'\x00' else False
		#self.compressed = compressed

		self.IMG, self.CUR, self.SPR = 0, 1, 2

		if self.compressed:
			self.data = lzw_decompress(data[3:])
		else:
			self.data = data[3:]

			#try:
			#	for b in lzw.decompress(data[3:]):
			#		decompData += b
			#except ValueError:
			#	return None
			#except TypeError:
			#	return None

			#print(decompData)

		self.type = conf['sprites'][index]['type']
		#if self.type == 'image':
		#	print(self.data)
		if self.type == 'wave' and len(self.data) < 3000:
			with open('test.wav', 'wb') as fh:
				print()
				print(data)
				print(self.data)
				print()
				fh.write(self.data)

		#self.detect_dataType()

	#def detect_dataType(self):
		#print()
		# .IMG ?
		#width = unpack('<H', self.data[:2])[0]
		#height = unpack('<H', self.data[2:4])[0]
		#print('W x H:', (width, height))
		#if width < 800 and height < 600:
		#	return self.IMG

		# .SPR ?
		#frames = unpack('<H', self.data[:2])[0]
		#print('Frames:', frames)
		#if frames < 100:
		#	return self.SPR
	#	pass

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

		header_bytes = self.data[:8] # Out of our 8 byte header

		#archive_id =  # the first 4 are the archive ID only
		#entries =  # And this will be the nr_of_files+compressed bytes.

		self.id = unpack('<I', header_bytes[:4])[0]
		self.num_o_files = unpack('<I', header_bytes[4:])[0] # The first byte is num of files.
		#self.lz = True if unpack('<I', pad(entries[1:]))[0]==2 else False # the 3 last bytes are meta.
		#self.retail = True if self.id == 24 else False
		self.lz = True
		self.retail = True

		print('Archive:', self.archive)
		print('Archive ID:', self.id,'[Retail]' if self.retail else '[Demo]')
		print('Num o files:', self.num_o_files)
		print('Is compressed:', self.lz)

		self.offsets = []
		bytesize = 4
		for i in range(self.num_o_files):
			self.offsets.append(unpack('<I', self.data[bytesize+(bytesize*i):bytesize+(bytesize*i)+bytesize])[0])

		#print('Offsets:', self.offsets)

	def read_file_table(self):
		#if not self.lz:
		#	raise ValueError('Can not handle uncompressed file headers atm in filetable.')
		#	meta = unpack('<I', self.data[8:9])[0]
		#	data_pos = meta%4096
		#else:
#			for index, data_start in enumerate(self.offsets):
		for i in range(len(self.offsets)):
			data_start = self.offsets[i]
			if i+1 == len(self.offsets):
				data_stop = len(self.data)
			else:
				data_stop = self.offsets[i+1]

			#print(data_start, data_stop)
			self.objects[i] = WAR_RESOURCE(i, self.data[data_start:data_stop], compressed=self.lz)

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


archive = WAR('../wc1/WARCRAFT_1/DATA/DATA.WAR')
#archive = WAR('../wc1/WARCRAFT_1/DATA/TITLE.WAR')
#print('Archive ID:', archive.id)
#print('Num files:', archive.num_o_files)
#print('Compressed:', archive.lz)

#print('Files:', list(archive.objects.keys()))
#print('Contains:', archive.contains)