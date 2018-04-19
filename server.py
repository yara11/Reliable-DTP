from rdtp import Packet
import os
import time
import struct
from socket import *
from multiprocessing import Process, Manager
from timer import *

BUFFSIZE = 512
TIMEOUT = 5 # in seconds

# Creates a server-side socket that listens for client requests,
# and handles each in a child process with the given rdtp_fn
def server_listener(server_portno, window_size, seedvalue, plp, rdtp_fn):
	server_socket = socket(AF_INET, SOCK_DGRAM)
	#server_socket.bind(('192.168.147.1', server_portno))
	server_socket.bind((gethostbyname(gethostname()), server_portno))

	client_table = Manager().dict()

	print('started server ', gethostbyname(gethostname()), ' on port ', server_portno, '\n')

	while True:
		request_msg, client_address = server_socket.recvfrom(BUFFSIZE)
		
		request_msg = Packet.unpack(request_msg)

		# print('received', request_msg.print(), ' from ', client_address)
		# print('in parent  ', client_table)
		if request_msg.is_corrupted():
			continue
		#if client_address in client_table:
		if request_msg.is_ACK():
			# update client table
			client_table[client_address] = request_msg.seqno
			print('received ack ', request_msg.seqno, ' from ', client_address)
		# else: not mine

		else:
			file_name = request_msg.data
			print('received request ', file_name, ' from ', client_address)
			client_table[client_address] = None
			child = Process(target=rdtp_fn, args=(server_socket, window_size, seedvalue, plp, file_name, client_address, client_table))
			child.start()

	server_socket.close()



def stop_and_wait(server_socket, window_size, seedvalue, plp, file_name, client_address, client_table):
	
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
				# print('in child ', client_table)
				print('packet ', sndpkt.seqno, ' resent to ', client_address)
				now = time.time()
				future = now + TIMEOUT
				continue
			
			# if ACK received for this client, with this seq no
			if client_table[client_address] == sndpkt.seqno:
				print('packet ', sndpkt.seqno, ' received by ', client_address)
				break
	del client_table[client_address]

#GO BACK N ALGORITHM
def go_back_n (server_socket, window_size, seedvalue, plp, file_name, client_address, client_table):
	packet_timer = timer(TIMEOUT)
	base=1
	next_seq_num=1
	sequencenumbers = 2 * window_size

	packets = make_packets(file_name,list(range(1,sequencenumbers+1)))
	for sndpkt in packets:
		#if there is a space in window send packets
		if next_seq_num < base+window_size:
			server_socket.sendto(sndpkt.pack(), client_address)
			if base == next_seq_num:
				packet_timer.start_time()
			next_seq_num +=1

		#timeout for the first unacked packet
		#will send all unacked packets again
		if packet_timer.timer_timeout():
			print('TIMEOUT')
			packet_timer.start_time()
			for base in next_seq_num-1 :
				server_socket.sendto(sndpkt.pack(), client_address)

		#if the client recieved the packet and it is not corrupted
		if client_table[client_address] == sndpkt.seqno:
			print('packet ', sndpkt.seqno, ' received by ', client_address)
			base = client_table[client_address]+1
			if base == next_seq_num:
				packet_timer.stop_timer()
			else:
				packet_timer.start_time()





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
		packet = Packet(seqno, len(data)+8, 0, False, False, data)
		if stt_ind+data_size >= str_len:
			packet.islast = True
		packets.append(packet)
		# packet.print()
		# Packet.unpack(packet.pack()).print()
		stt_ind += data_size
		seqno = (seqno+1)%2

	return packets


#dummy_make_packets([0, 1])

print(gethostbyname(gethostname()))

server_listener(2050, 0, 0, 0, stop_and_wait)
