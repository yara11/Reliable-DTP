import sys
import struct
from pprint import pprint

class Packet:
	MSGFORMAT = '!LHH500s'

	def __init__(self, seqno, pktlen, cksum, data=''):
		self.seqno = seqno
		self.pktlen = pktlen
		self.cksum = cksum
		self.data = data[0:pktlen-8]

	# TODO
	def calc_checksum(self):
		self.cksum = 0

	def pack(self):
		return struct.pack(Packet.MSGFORMAT, self.seqno, self.pktlen, self.cksum, self.data.encode())
	
	@staticmethod
	def unpack(pkt):
		unpacked_pkt = struct.unpack(Packet.MSGFORMAT, pkt)
		return Packet(unpacked_pkt[0], unpacked_pkt[1], unpacked_pkt[2], unpacked_pkt[3].decode())

	def print(self):
		pprint(vars(self))


class AckPacket:
	MSGFORMAT = '!LHH'
	def __init__(self, seqno, pktlen, cksum):
		self.pktlen = pktlen
		self.cksum = cksum
		self.seqno = seqno
	
	# TODO
	def calc_checksum(self):
		self.cksum = 0

	def pack(self):
		return struct.pack(AckPacket.MSGFORMAT, self.seqno, self.pktlen, self.cksum)

	@staticmethod
	def unpack(pkt):
		unpacked_pkt = struct.unpack(AckPacket.MSGFORMAT, pkt)
		return AckPacket(unpacked_pkt[0], unpacked_pkt[1], unpacked_pkt[2])

	def print(self):
		pprint(vars(self))
