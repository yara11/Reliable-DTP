import os
import time
import struct
from socket import *

BUFFSIZE = 512
TIMEOUT = 20 # in seconds

# Creates a server-side socket that listens for client requests,
# and handles each in a child process with the given rdtp_fn
def server_listener(server_portno, window_size, seedvalue, plp, rdtp_fn):
	server_socket = socket(AF_INET, SOCK_DGRAM)
	server_socket.bind('', server_portno)
	while True:
		request_msg, client_address = server_socket.recvfrom(BUFFSIZE)
		# get filename from message

		new_pid = os.fork()
		if new_pid == 0:
			rdtp_fn(server_portno, window_size, seedvalue, plp, file_name, client_address)



def stop_and_wait(server_portno, window_size, seedvalue, plp, file_name, client_address):
	server_socket = socket(AF_INET, SOCK_DGRAM)
	# server_socket.bind('', server_portno)
	packets = make_packets(file_name, [0, 1]) # stop and wait only needs 2 seq nos
	for sndpkt in packets:
		# send packet
		server_socket.sendto(sndpkt, client_address)
		
		# start timer
		now = time.time()
		future = now + TIMEOUT
		
		while True:
			# if timeout, resend, restart timer
			if time.time() == future:
				server_socket.sendto(sndpkt, client_address)
				now = time.time()
				future = now + TIMEOUT
				continue
			
			rcvpkt, client_address = server_socket.recvfrom(BUFFSIZE)
			# isAck and has same seq no. && not corrupt, done
			# if :
			# 	break


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
		chksum = 0
		datalen = len(data)
		packet = struct.pack('!HHL'+str(datalen)+'s', chksum, datalen+4, seqno, data.encode())
		packets.append(packet)
		# print(struct.unpack('!HHL'+str(datalen)+'s', packet))
		stt_ind += data_size
		seqno = (seqno+1)%2

	return packets

dummy_make_packets([0, 1])
