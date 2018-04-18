from rdtp import Packet
import os
import time
import struct
from socket import *

BUFFSIZE = 512
TIMEOUT = 5 # in seconds

client_table = {}

# Creates a server-side socket that listens for client requests,
# and handles each in a child process with the given rdtp_fn
def server_listener(server_portno, window_size, seedvalue, plp, rdtp_fn):
	server_socket = socket(AF_INET, SOCK_DGRAM)
	server_socket.bind((gethostbyname(gethostname()), server_portno))

	print('started server ', gethostbyname(gethostname()), ' on port ', server_portno)

	while True:
		request_msg, client_address = server_socket.recvfrom(BUFFSIZE)
		
		request_msg = Packet.unpack(request_msg)

		if request_msg.is_corrupted():
			continue
		if client_address in client_table:
			if request_msg.is_ACK():
				# update client table
				client_table = request_msg.seqno
			# else: not my bitch
		else:
			file_name = request_msg.data
			new_pid = os.fork()
			client_table[client_address] = None

			if new_pid == 0:
				rdtp_fn(server_socket, window_size, seedvalue, plp, file_name, client_address)
				del client_table[client_address]
				# kill this process
				os.kill(os.getpid(), SIGKILL)
	server_socket.close()



def stop_and_wait(server_socket, window_size, seedvalue, plp, file_name, client_address):
	
	packets = make_packets(file_name, [0, 1]) # stop and wait only needs 2 seq nos
	print('starting stop-and-wait...')
	print('sending ', file_name, 'to ', client_address)

	for sndpkt in packets:
		# send packet
		server_socket.sendto(sndpkt.pack(), client_address)
		print('packet ', sndpkt.seqno, ' sent to ', client_address)
		
		# start timer
		now = time.time()
		future = now + TIMEOUT
		
		# waiting for ACK
		while True:
			# if timeout, resend, restart timer
			if time.time() >= future:
				server_socket.sendto(sndpkt.pack(), client_address)
				print('packet ', sndpkt.seqno, ' resent to ', client_address)
				now = time.time()
				future = now + TIMEOUT
				continue
			
			# if ACK received for this client, with this seq no
			if client_table[client_address] == sndpkt.seqno:
				print('packet ', sndpkt.seqno, ' received by ', client_address)
				break
		

# reads file and returns list of (encoded) datagram packets
def make_packets(file_name, seq_nos):
	return dummy_make_packets(seq_nos)

def dummy_make_packets(seq_nos):
	str_dummy = 'The Quick Brown Fox Jumped Over The Lazy Dog.'
	str_len = len(str_dummy)
	data_size = 10
	stt_ind = 0
	seqno = 0

	packets = []
	
	while stt_ind < str_len:
		data = str_dummy[stt_ind:min(stt_ind+data_size, str_len)]
		packet = Packet(seqno, len(data)+8, 0, data)
		if stt_ind+data_size >= str_len:
			packet.islast = True
		packets.append(packet)
		packet.print()
		Packet.unpack(packet.pack()).print()
		stt_ind += data_size
		seqno = (seqno+1)%2

	return packets


#dummy_make_packets([0, 1])
server_listener(0, 0, 0, 0, stop_and_wait)
