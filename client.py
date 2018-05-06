from rdtp import Packet
from socket import *
import time, sys
from multiprocessing import Process
import enc_dec

BUFFSIZE = 512
HEADERSIZE = 10
OO = 1 << 30

def client_init(server_ip, server_portno, client_portno, file_name, window_size, rdtp_fn):
    client_socket = socket(AF_INET, SOCK_DGRAM)
    client_socket.bind(('', client_portno))
    rdtp_fn(client_socket, server_ip, server_portno, client_portno, file_name, window_size)

def stop_and_wait(client_socket, server_ip, server_portno, client_portno, file_name, window_size):
    rcv_data = []

    # TODO: calc checksum

    # Create request and send to server
    request_pkt = Packet(1, len(file_name)+HEADERSIZE, 0, False, False, file_name)
    request_pkt.calc_checksum()
    client_socket.sendto(request_pkt.pack(), (server_ip, server_portno))
    
    print('requested ', file_name, ' from ', (server_ip, server_portno))

    sndpkt = request_pkt
    seqno = 0

    while True:
        rcvpkt, server_address = client_socket.recvfrom(BUFFSIZE)
        rcvpkt = Packet.unpack(rcvpkt)

        if not rcvpkt.is_corrupted() and rcvpkt.seqno == seqno:
            # extract, deliver
            rcv_data.append(rcvpkt.data)
            print('received packet ', seqno, ' from ', (server_ip, server_portno))
            
            # send ACK
            sndpkt = Packet(rcvpkt.seqno, 8, 0, True)
            client_socket.sendto(sndpkt.pack(), (server_ip, server_portno))
            print('sent ACK ', sndpkt.seqno, ' to ', (server_ip, server_portno))
            
            seqno = (seqno+1)%2
            if rcvpkt.islast == True:
                break

        else: # resend packet/ack
            client_socket.sendto(sndpkt.pack(), (server_ip, server_portno))
            print('resent ACK ', sndpkt.seqno, ' to ', (server_ip, server_portno))
        
    reassemble_file(file_name, rcv_data)
    client_socket.close()

def go_back_n (client_socket, server_ip, server_portno, client_portno, file_name, window_size):
    client_socket = socket(AF_INET, SOCK_DGRAM)
    rcv_data = []

    # send request
    request_pkt = Packet(0, len(file_name)+HEADERSIZE, 0, False, False, file_name)
    client_socket.sendto(request_pkt.pack(), (server_ip, server_portno))

    print('requested ', file_name, ' from ', (server_ip, server_portno))

    sndpkt = request_pkt
    seqno = 0

    while True:
        # receive packet
        rcvpkt, server_address = client_socket.recvfrom(BUFFSIZE)
        rcvpkt = Packet.unpack(rcvpkt)

        if not rcvpkt.is_corrupted() and rcvpkt.seqno == seqno:
            # extract, deliver
            rcv_data.append(rcvpkt.data)
            print('received packet ', seqno, ' from ', (server_ip, server_portno))
            # send ACK
            sndpkt = Packet(rcvpkt.seqno, 8, 0, True)
            client_socket.sendto(sndpkt.pack(), (server_ip, server_portno))
            print('sent ACK ', sndpkt.seqno, ' to ', (server_ip, server_portno))

            # should be % max_seq_no
            seqno = seqno + 1
            if rcvpkt.islast == True:
                break
        # else :
            # print ('duplicate or corrupt packet ignored')
    reassemble_file(file_name, rcv_data)
    client_socket.close()

def selective_repeat (client_socket, server_ip, server_portno, client_portno, file_name, window_size):
    client_socket = socket(AF_INET, SOCK_DGRAM)
    buffered = {}
    delivered = {}

    request_pkt = Packet(0, len(file_name)+HEADERSIZE, 0, False, False, file_name)
    client_socket.sendto(request_pkt.pack(), (server_ip, server_portno))

    seqno = 0
    rcv_base = 0
    pkts_num = OO

    while rcv_base < pkts_num: # break if all packets delivered

        rcvpkt, server_address = client_socket.recvfrom(BUFFSIZE)
        rcvpkt = Packet.unpack(rcvpkt)

        # packet is not corrupted and between base and base+windowsize-1
        if not rcvpkt.is_corrupted() and rcvpkt.seqno >= rcv_base and rcvpkt.seqno <= rcv_base+window_size-1 :
            # print and send ACK
            print('received packet ', rcvpkt.seqno, ' from ', (server_ip, server_portno))
            sndpkt = Packet(rcvpkt.seqno, 8, 0, True)  # send ACK
            client_socket.sendto(sndpkt.pack(), (server_ip, server_portno))
            print('sent ACK ', sndpkt.seqno, ' to ', (server_ip, server_portno))
            
            # buffer packet
            buffered[rcvpkt.seqno] = rcvpkt

            # mark the last packet
            if rcvpkt.islast == True:
                pkts_num = rcvpkt.seqno+1

        elif not rcvpkt.is_corrupted() and rcvpkt.seqno >= rcv_base-window_size and rcvpkt.seqno <= rcv_base-1:
            sndpkt = Packet(rcvpkt.seqno, 8, 0, True)  # send ACK
            client_socket.sendto(sndpkt.pack(), (server_ip, server_portno))

        # deliver in-order packets
        while rcv_base in buffered:
            rcv_base += 1
    
    rcv_list = []
    for i in range(0, pkts_num):
    	rcv_list.append(buffered[i].data)
    
    reassemble_file(file_name, rcv_list,client_portno)
    client_socket.close()


def reassemble_file(file_name, list, client_portno):
    file_name.replace('\n', '')
    file_name = str(client_portno)+file_name
    fh = open(file_name, "wb")
    for piece in list:
        fh.write(piece)
    fh.close()
    new_filename = 'dec_'+file_name+file_name
    enc_dec.decryptMain(file_name, new_filename) 
    print('file ', file_name, ' received successfully as ', new_filename)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print('python3 usage: client.py',
            ' <protocol: stop-and-wait, go-back-n, selective-repeat> <input filename>')
    else: # assuming correct format of input filename :)
        filehandler = open(sys.argv[2], 'r')
        client_args = filehandler.readlines()
        filehandler.close()
        protocol_name = sys.argv[1]
        if protocol_name == 'stop-and-wait':
            client_init(client_args[0], int(client_args[1]), int(client_args[2]), 
                client_args[3], int(client_args[4]), stop_and_wait)
        elif protocol_name == 'go-back-n':
            client_init(client_args[0], int(client_args[1]), int(client_args[2]), 
                client_args[3], int(client_args[4]), go_back_n)
        elif protocol_name == 'selective-repeat':
            client_init(client_args[0], int(client_args[1]), int(client_args[2]), 
                client_args[3], int(client_args[4]), selective_repeat)
        else:
            print('unknown protocol: ', sys.argv[1])

# x = Process(target=client_init, args=('127.0.1.1', 1028, 1025, '', 4, selective_repeat))
# y = Process(target=client_init, args=('127.0.1.1', 1028, 1026, '', 4, selective_repeat))

# x.start()
# y.start()

# x.join()
# y.join()
