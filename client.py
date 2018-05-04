from rdtp import Packet
from socket import *
import time
from multiprocessing import Process

BUFFSIZE = 512

def client_init(server_ip, server_portno, client_portno, file_name, window_size, rdtp_fn):
	rdtp_fn(server_ip, server_portno, client_portno, file_name, window_size)

def stop_and_wait(server_ip, server_portno, client_portno, file_name, window_size):
	client_socket = socket(AF_INET, SOCK_DGRAM)
	rcv_data = []

	# TODO: calc checksum
	request_pkt = Packet(1, len(file_name)+8, 0, False, False, file_name)
	msg = 'hi plz work'
	client_socket.sendto(request_pkt.pack(), (server_ip, server_portno))
	# client_socket.sendto(msg.encode(), (server_ip, server_portno))
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
			# TODO: CREATE CLEANER ACK PACKAGE - THIS IS NOT RELIABLE
			sndpkt = Packet(rcvpkt.seqno, 8, 0, True) # send ACK
			client_socket.sendto(sndpkt.pack(), (server_ip, server_portno))
			print('sent ACK ', sndpkt.seqno, ' to ', (server_ip, server_portno))
			seqno = (seqno+1)%2
			if rcvpkt.islast == True:
				break

		else:# resend packet/ack
			client_socket.sendto(sndpkt.pack(), (server_ip, server_portno))
			print('resent ACK ', sndpkt.seqno, ' to ', (server_ip, server_portno))
		
	print(rcv_data)
	client_socket.close()

def go_back_n (server_ip, server_portno, client_portno, file_name, window_size):
	client_socket = socket(AF_INET, SOCK_DGRAM)
	rcv_data = []

	request_pkt = Packet(1, len(file_name) + 8, 0, False, False, file_name)
	client_socket.sendto(request_pkt.pack(), (server_ip, server_portno))
	sndpkt = request_pkt
	seqno = 1

	while True:
		rcvpkt, server_address = client_socket.recvfrom(BUFFSIZE)
		rcvpkt = Packet.unpack(rcvpkt)

		if not rcvpkt.is_corrupted() and rcvpkt.seqno == seqno:
			rcv_data.append(rcvpkt.data) # extract, deliver
			print('received packet ', seqno, ' from ', (server_ip, server_portno))
			sndpkt = Packet(rcvpkt.seqno, 8, 0, True)  # send ACK
			client_socket.sendto(sndpkt.pack(), (server_ip, server_portno))
			print('sent ACK ', sndpkt.seqno, ' to ', (server_ip, server_portno))

			#ask yara about this
			seqno = seqno + 1
			if rcvpkt.islast == True:
				break
		else :
			print ("dublicate packet")
	print(rcv_data)
	client_socket.close()

def selective_repeat (server_ip, server_portno, client_portno, file_name, window_size):
	client_socket = socket(AF_INET, SOCK_DGRAM)
	rcv_data = []

	request_pkt = Packet(1, len(file_name) + 8, 0, False, False, file_name)
	client_socket.sendto(request_pkt.pack(), (server_ip, server_portno))

	seqno = 1
	rcv_base = 1

	while True:
		rcvpkt, server_address = client_socket.recvfrom(BUFFSIZE)
		rcvpkt = Packet.unpack(rcvpkt)

		#packet is not corrupted and between base and base+windowsize-1
		if not rcvpkt.is_corrupted() and rcv_base <= rcvpkt.seqno and rcvpkt.seqno <= (rcv_base+window_size-1) :
			#print and send ACK
			print('received packet ', rcvpkt.seqno, ' from ', (server_ip, server_portno))
			sndpkt = Packet(rcvpkt.seqno, 8, 0, True)  # send ACK
			client_socket.sendto(sndpkt.pack(), (server_ip, server_portno))
			print('sent ACK ', sndpkt.seqno, ' to ', (server_ip, server_portno))

			#Buffer packet is it is not base packet and mark it as acked
			if rcvpkt.seqno != rcv_base :
				rcv_data.insert(rcvpkt.seqno-1,rcvpkt.data)
				print("--------------->")
				# mark packed as acked
				request_pkt.isACK == True
			#if it is base packet or it is already acked deliver it , increase base
			elif rcvpkt.seqno == rcv_base or request_pkt.isACK:
				rcv_data.append(rcvpkt.data)
				if rcvpkt.seqno == rcv_base:
					rcv_base+=1
			#if it is last packet break
			if rcvpkt.islast == True:
				break
		#dublicate packets just resend ACK
		# leh byd5ol hena ??????????
		elif ((rcv_base-window_size) < rcvpkt.seqno )and (rcvpkt.seqno <= (rcv_base-1)):
			sndpkt = Packet(rcvpkt.seqno, 8, 0, True)  # send ACK
			client_socket.sendto(sndpkt.pack(), (server_ip, server_portno))
			print("8888888888888888")

	print(rcv_data)
	client_socket.close()



client_init('127.0.1.1', 1028, 1025, '', 0, stop_and_wait)
# x = Process(target=client_init, args=('127.0.1.1', 2050, 1025, '', 4, selective_repeat))
# y = Process(target=client_init, args=('127.0.1.1', 2050, 1026, '', 4, selective_repeat))

# x.start()
# y.start()
