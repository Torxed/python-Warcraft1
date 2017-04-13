from struct import *
from time import sleep # DEBUG

# unpack('hhl', '\x00\x01\x00\x02\x00\x00\x00\x03')
# The main difference is that Warcraft II, megatiles are 32x32 (made of 16 8x8 Minitiles) whereas War1 is 16x16 (4 8x8 minitiles).


def pad(b, l=4):
	return b+(b'\x00'*(l-len(b)))

class WAR():
	def __init__(self, WAR_FILE):
		self.archive = WAR_FILE
		with open(self.archive, 'rb') as fh:
			self.data = fh.read()

		self.id = 0
		self.num_o_files = 0
		self.lz = False
		self.objects = {}

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

		archive_id = header_bytes[:4] # the first 4 are the archive ID only
		entries = header_bytes[4:] # And this will be the nr_of_files+compressed bytes.

		self.id = unpack('<I', archive_id)[0]
		self.num_o_files = unpack('<B', bytes([entries[0]]))[0] # The first byte is num of files.
		self.lz = True if unpack('<I', pad(entries[1:]))[0]==2 else False # the 3 last bytes are meta.

		self.offsets = []
		bytesize = 4
		for i in range(self.num_o_files):
			self.offsets.append(unpack('<I', self.data[bytesize+(bytesize*i):bytesize+(bytesize*i)+bytesize])[0])

	def read_file_table(self):
		if not self.lz:
			meta = unpack('<I', self.data[8:9])[0]
			data_pos = meta%4096
		else:
#			for index, data_start in enumerate(self.offsets):
			for i in range(len(self.offsets)):
				data_start = self.offsets[i]
				if i+1 == len(self.offsets):
					data_stop = len(self.data)
				else:
					data_stop = self.offsets[i+1]

				self.objects[i] = self.data[data_start:data_stop]

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


archive = WAR('./WARCRAFT_1/DATA/DATA.WAR')
print('Archive ID:', archive.id)
print('Num files:', archive.num_o_files)
print('Compressed:', archive.lz)

print('Files:', list(archive.objects.keys()))