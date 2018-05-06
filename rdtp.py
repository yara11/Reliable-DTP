import struct
from pprint import pprint

# Packet(seqno, 8, cksum, True) returns ACK packet
class Packet:
	MSGFORMAT = '!LHHBB502s'
	ACKSTR = 'ACK'

	def __init__(self, seqno, pktlen, cksum, isACK=False, islast=False, data=''):
		self.seqno = seqno
		self.pktlen = pktlen
		self.cksum = cksum
		self.data = data[0:pktlen-10]
		self.islast = islast
		self.isACK = isACK

	# TODO
	def calc_checksum(self):
		return 0
	# def calc_checksum(self):
	# 	data = self.data
	# 	self.cksum = 0
	# 	d_lenght = len(data)
	# 	pointer =0
	# 	while d_lenght > 1:
	# 		# 16 bit number for the checksum
	# 		# getting the ascki code for each character using ord() function
	# 		self.cksum +=(ord(data[pointer])+ord(data[pointer+1]))
	# 		d_lenght -= 2
	# 		pointer +=2
	# 	if d_lenght:
	# 		self.cksum += ord(data[pointer])
	# 	#overflow
	# 	self.cksum = (self.cksum >> 16) + (self.cksum &0xffff)
	# 	# one's complement
	# 	result = (~self.cksum) & 0xffff
	# 	result += (self.cksum)
	# 	self.cksum = result
	# 	return result

	def is_corrupted(self):
		return self.cksum != self.calc_checksum()

	def is_ACK(self):
		return self.isACK

	def pack(self):
		return struct.pack(Packet.MSGFORMAT, self.seqno, self.pktlen, self.cksum, self.isACK, self.islast, self.data.encode())
	
	@staticmethod
	def unpack(pkt):
		unpacked_pkt = struct.unpack(Packet.MSGFORMAT, pkt)
		return Packet(unpacked_pkt[0], unpacked_pkt[1], unpacked_pkt[2], unpacked_pkt[3], unpacked_pkt[4], unpacked_pkt[5].decode())

	def pprint(self):
		print(vars(self))


# class AckPacket:
# 	MSGFORMAT = '!LHH'
# 	def __init__(self, seqno, pktlen, cksum):
# 		self.pktlen = pktlen
# 		self.cksum = cksum
# 		self.seqno = seqno
	
# 	# TODO
# 	def calc_checksum(self):
# 		self.cksum = 0

# 	def pack(self):
# 		return struct.pack(AckPacket.MSGFORMAT, self.seqno, self.pktlen, self.cksum)

# 	@staticmethod
# 	def unpack(pkt):
# 		unpacked_pkt = struct.unpack(AckPacket.MSGFORMAT, pkt)
# 		return AckPacket(unpacked_pkt[0], unpacked_pkt[1], unpacked_pkt[2])

# 	def print(self):
# 		pprint(vars(self))
