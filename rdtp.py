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
        if not type(self.data) is bytes:
            self.data = self.data.encode()


    # TODO
    # def calc_checksum(self):
    #     return 0

    #def carry_around_add(a, b):
    #c = a + b
    #return (c & 0xffff) + (c >> 16)

    #def checksum(msg):
    #s = 0
    #for i in range(0, len(msg)-1, 2):
     #   w = msg[i] + msg[i+1] << 8
      #  s = carry_around_add(s, w)
    #return ~s & 0xffff


    def calc_checksum(self):
        data = self.data
        self.cksum = 0
        d_lenght = len(data)
        pointer =0
        while d_lenght > 1:
            # 16 bit number for the checksum
            # getting the ascki code for each character using ord() function
            self.cksum +=(data[pointer]+data[pointer+1])
            d_lenght -= 2
            pointer +=2
        if d_lenght:
            self.cksum += ord(data[pointer])
        # add up the carry 
        while(self.cksum >> 16) > 0:
             self.cksum = (self.cksum >> 16) + (self.cksum &0xffff)
        self.cksum+=self.cksum >> 16
        self.cksum = ~self.cksum
        self.cksum = self.cksum & 0xffff
        return self.cksum

    def is_corrupted(self):
        return self.cksum != self.calc_checksum()

    def is_ACK(self):
        return self.isACK

    def pack(self):
        return struct.pack(Packet.MSGFORMAT, self.seqno, self.pktlen, self.cksum, 
            self.isACK, self.islast, self.data)
    
    @staticmethod
    def unpack(pkt):
        unpacked_pkt = struct.unpack(Packet.MSGFORMAT, pkt)
        return Packet(unpacked_pkt[0], unpacked_pkt[1], unpacked_pkt[2], 
            unpacked_pkt[3], unpacked_pkt[4], unpacked_pkt[5])

    def pprint(self):
        print(vars(self))


# class AckPacket:
#     MSGFORMAT = '!LHH'
#     def __init__(self, seqno, pktlen, cksum):
#         self.pktlen = pktlen
#         self.cksum = cksum
#         self.seqno = seqno
    
#     # TODO
#     def calc_checksum(self):
#         self.cksum = 0

#     def pack(self):
#         return struct.pack(AckPacket.MSGFORMAT, self.seqno, self.pktlen, self.cksum)

#     @staticmethod
#     def unpack(pkt):
#         unpacked_pkt = struct.unpack(AckPacket.MSGFORMAT, pkt)
#         return AckPacket(unpacked_pkt[0], unpacked_pkt[1], unpacked_pkt[2])

#     def print(self):
#         pprint(vars(self))
