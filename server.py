from rdtp import Packet
import os, sys
import time
import struct
from socket import *
import threading
from multiprocessing import Process, Manager
from timer import *
import random
# import enc_dec

BUFFSIZE = 512
HEADERSIZE = 10
TIMEOUT = 1 # in seconds
MYIP = '127.0.1.1'
OO = 1<<30 # infinity

# Creates a server-side socket that listens for client requests,
# and handles each in a child process with the given rdtp_fn
def server_listener(server_portno, window_size, seedvalue, plp, rdtp_fn):
    # assign seed value
    random.seed(seedvalue)

    server_socket = socket(AF_INET, SOCK_DGRAM)
    server_socket.bind((gethostbyname(gethostname()), server_portno))
    client_table = Manager().dict()

    print('started server ', gethostbyname(gethostname()), ' on port ', server_portno, '\n')

    while True:
        # receive message
        request_msg, client_address = server_socket.recvfrom(BUFFSIZE)
        request_msg = Packet.unpack(request_msg)

        # if request_msg.is_corrupted():
        #     print('received corrupted message from ', client_address)
        #     continue

        if request_msg.is_ACK(): # existing client ACK
            # if not lose_packet(plp): # no ACK packet loss
            # update client table
            if rdtp_fn == selective_repeat:
                key = client_address + (request_msg.seqno, )
                client_table[key] = True
            else:
                client_table[client_address] = request_msg.seqno
            print('received ack ', request_msg.seqno, ' from ', client_address)
            # else:
            #     print('ACK loss')

        else: # new client request
            file_name = request_msg.data
            print('received request ', file_name, ' from ', client_address)
            client_table[client_address] = None
            child = Process(target=rdtp_fn, args=(server_socket, window_size, plp, file_name, client_address, client_table))
            child.start()

    server_socket.close()



def stop_and_wait(server_socket, window_size, plp, file_name, client_address, client_table):
    
    packets = make_packets(file_name, 2) # stop and wait only needs 2 seq nos
    print('starting stop-and-wait...')
    print('sending ', file_name, 'to ', client_address)

    for sndpkt in packets:
        # send packet
        if not lose_packet(plp): # no packet loss
            server_socket.sendto(sndpkt.pack(), client_address)
            print('packet ', sndpkt.seqno, ' sent to ', client_address)
        # else:
        #     print('packet loss')
        
        # start timer
        packet_timer = timer(TIMEOUT)

        trials = 0

        # waiting for ACK
        while True:
            # in case client closed connection
            # client is declared unreachable after 10 trials
            if trials == 10:
                print('unable to reach client ', client_address)
                del client_table[client_address]
                return
            
            # if timeout, resend, restart timer
            if packet_timer.timer_timeout():
                trials +=1
                if not lose_packet(plp): #no packet loss
                    server_socket.sendto(sndpkt.pack(), client_address)
                    print('packet ', sndpkt.seqno, ' resent to ', client_address)
                # else:
                #     print('packet re-loss')
                # restart timer
                packet_timer.start_timer()
            
            # if ACK received for this client, with this seq no
            if client_table[client_address] == sndpkt.seqno:
                print('packet ', sndpkt.seqno, ' received by ', client_address)
                break
    # request served, remove status of this client
    del client_table[client_address]


#GO BACK N ALGORITHM
def go_back_n (server_socket, window_size, plp, file_name, client_address, client_table):
    
    packets = make_packets(file_name)
    
    # index of the base packet in the list
    base_ind=0
    # the next available sequence number
    next_seq_num=0
    # the maximum sequence number [0...max_seq_no-1]
    max_seq_no = len(packets)
    print(max_seq_no)
    
    # Start timer
    packet_timer = timer(TIMEOUT)
    trials = 0

    while base_ind < len(packets):

        # in case client close connection
        if trials == 5:
            print('unable to reach client ', client_address)
            del client_table[client_address]
            return

        # if there is a space in window, send packets
        if next_seq_num < max_seq_no and next_seq_num < packets[base_ind].seqno+window_size:
            # send packet
            if not lose_packet(plp): # no packet loss
                server_socket.sendto(packets[next_seq_num].pack(), client_address)
                print('packet ', next_seq_num, ' sent to ', client_address)
            # the base is sent, restart timer
            if next_seq_num == packets[base_ind].seqno:
                packet_timer.start_timer()
            next_seq_num = next_seq_num+1

        #ask yara how to if this is the last packet then stop this loop
        #if the client recieved the packet and it is not corrupted
        # if base ACK received, change base
        if client_table[client_address] == packets[base_ind].seqno:
            print('packet ', packets[base_ind].seqno, ' received by ', client_address)
            base_ind += 1
            if base_ind != next_seq_num:
                packet_timer.start_timer()
            else:
                trials = 0

        # timeout for the first unacked packet
        # will send all unacked packets again
        if packet_timer.timer_timeout():
            trials += 1
            print(trials, '. sending packet ', packets[base_ind].seqno, ' to ', client_address, ' timed-out')
            packet_timer.start_timer()
            next_seq_num = base_ind

    del client_table[client_address]



def selective_repeat (server_socket, window_size, plp, file_name, client_address, client_table):
    packets = make_packets(file_name)
    base_ind = 0
    next_seq_num = 0

    # contains events for threads awaiting acks
    ack_events = {}
    acknowledged = {}

    while base_ind < len(packets):
        # if there is a space in window send packets and start its timer
        if next_seq_num < min(len(packets), packets[base_ind].seqno + window_size):
            
            pkt_event = threading.Event()
            ack_events[next_seq_num] = pkt_event
            acknowledged[next_seq_num] = False

            # new thread to handle this packet, awaits on pkt_event
            pkt_thread = threading.Thread(name='pkt '+str(next_seq_num)+' mgr',target=sr_packet_manager, 
                args=(server_socket, client_address, packets[next_seq_num], plp, pkt_event, ))
            pkt_thread.start()

            next_seq_num += 1

        # stop threads awaiting acked packets
        for eventseqno in ack_events.keys():
            client_table_key = client_address + (eventseqno, )
            if client_table_key in client_table:
                ack_events[eventseqno].set()
                acknowledged[eventseqno] = True
                del client_table[client_table_key]

        # filter out set (non-waiting) events
        # instead of using del ack_events[client_table_key] because it will cause sync issues
        ack_events = {k: v for k, v in ack_events.items() if not v.isSet() }

        # move window as much as necessary
        while base_ind < len(acknowledged) and acknowledged[base_ind] == True:
            base_ind += 1

    del client_table[client_address]

def sr_packet_manager(server_socket, client_address, sndpkt, plp, event):
    while not event.isSet():
        if not lose_packet(plp):
            server_socket.sendto(sndpkt.pack(), client_address)
            print('packet ', sndpkt.seqno, ' sent to ', client_address)
        print(client_address, ' lost packet ', sndpkt.seqno)
        event_is_set = event.wait(TIMEOUT)
    print('packet ', sndpkt.seqno, ' received by ', client_address)


# (Packet loss simulation)
# decides to lose or keep a packet based on PLP
# returns true = lose packet, false = keep packet
def lose_packet(plp):
    return random.random() < plp

# reads file and returns list of (encoded) datagram packets
# max seq no is seqnos-1 (infinity by default, 2 for stop-and-wait, otherwise unhandled)
def make_packets(file_name, seqnos=OO):

    file_name=file_name.decode().replace('\n', '')
    # file_name = enc_dec.encryptMain(file_name)

    # read file as string 
    with open(file_name, 'rb') as myfile:
        data = myfile.read()
        data_len = len(data)
        seqno = 0
        stt_ind = 0
        # max number of bytes in packet
        max_len = BUFFSIZE - HEADERSIZE

        packets = []

        # divide into packets of size BUFFSIZE
        while stt_ind < data_len:
            pkt_data = data[stt_ind:min(stt_ind+max_len, data_len)]
            # TODO: checksum
            packet = Packet(seqno, len(pkt_data)+HEADERSIZE, 0, False, False, pkt_data)
            packet.calc_checksum()
            # last packet has is_last set
            if stt_ind+max_len >= data_len:
                packet.islast = True
            # add to packets list
            packets.append(packet)
            # next batch
            stt_ind += max_len
            seqno = (seqno+1)%seqnos

        return packets

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print('python3 usage: server.py',
            ' <protocol: stop-and-wait, go-back-n, selective-repeat> <input filename>')
    else: # assuming correct format of input filename :)
        filehandler = open(sys.argv[2], 'r')
        server_args = filehandler.readlines()
        filehandler.close()
        protocol_name = sys.argv[1]
        if protocol_name == 'stop-and-wait':
            server_listener(int(server_args[0]), int(server_args[1]), 
                float(server_args[2]), float(server_args[3]), stop_and_wait)
        elif protocol_name == 'go-back-n':
            server_listener(int(server_args[0]), int(server_args[1]), 
                float(server_args[2]), float(server_args[3]), go_back_n)
        elif protocol_name == 'selective-repeat':
            server_listener(int(server_args[0]), int(server_args[1]), 
                float(server_args[2]), float(server_args[3]), selective_repeat)
        else:
            print('unknown protocol: ', sys.argv[1])




# def dummy_make_packets(seqnos):
#     str_dummy = 'The Quick Brown Fox Jumped Over The Lazy Dog.'
#     str_len = len(str_dummy)
#     data_size = 10
#     stt_ind = 0
#     seqno = 0

#     packets = []
    
#     while stt_ind < str_len:
#         data = str_dummy[stt_ind:min(stt_ind+data_size, str_len)]
#         packet = Packet(seqno, len(data)+HEADERSIZE, 0, False, False, data)
#         if stt_ind+data_size >= str_len:
#             packet.islast = True
#         packets.append(packet)
#         # packet.print()
#         # Packet.unpack(packet.pack()).print()
#         stt_ind += data_size
#         seqno = (seqno+1)%seqnos

#     return packets

#print(gethostbyname(gethostname()))

# server_listener(1028, 0, 0, 0.2, stop_and_wait)
# server_listener(1028, 4, 0, 0.2, go_back_n)
# server_listener(1028, 4, 0, 0.2, selective_repeat)
