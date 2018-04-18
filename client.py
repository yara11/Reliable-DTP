from rdtp import Packet
from socket import *
import time

BUFFSIZE = 512

def client_side_guy(server_ip, server_portno, client_portno, file_name, window_size, rdtp_fn):
	rdtp_fn(server_ip, server_portno, client_portno, file_name, window_size)

def stop_and_wait(server_ip, server_portno, client_portno, file_name, window_size):
	client_socket = socket(AF_INET, SOCK_DGRAM)
	rcv_data = []

	# TODO: calc checksum
	request_pkt = Packet(1, len(file_name)+8, 0, file_name)
	client_socket.sendto(request_pkt.pack(), (server_ip, server_portno))
	print('requested ', file_name, ' from ', (server_ip, server_portno))

	sndpkt = request_pkt
	seqno = 0
	while True:
		# TODO: TIMEOUT

		rcvpkt, server_address = client_socket.recvfrom(BUFFSIZE)
		rcvpkt = Packet.unpack(rcvpkt)

		if not rcvpkt.is_corrupted() and rcvpkt.seqno == seqno:
			rcv_data.append(rcvpkt.data) # extract, deliver
			print('received packet ', seqno, ' from ', (server_ip, server_portno))
			seqno = (seqno+1)%2
			# TODO: CREATE CLEANER ACK PACKAGE - THIS IS NOT RELIABLE
			sndpkt = Packet(seqno, 8, 0, Packet.ACKSTR) # send ACK
			client_socket.sendto(sndpkt.pack(), (server_ip, server_portno))
			print('sent ACK ', seqno, ' to ', (server_ip, server_portno))
			if rcvpkt.islast == True:
				break

		else:# resend packet/ack
			client_socket.sendto(sndpkt.pack(), (server_ip, server_portno))
			print('resent ACK ', seqno, ' to ', (server_ip, server_portno))
		

	client_socket.close()

client_side_guy('127.0.1.1', 0, 1025, '', 0, stop_and_wait)
