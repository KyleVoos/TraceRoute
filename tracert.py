import sys
import socket
import time
import os
import struct
import select
import binascii


def checksum(string):
    csum = 0
    countTo = (len(string) // 2) * 2

    count = 0
    while count < countTo:
        thisVal = string[count + 1] * 256 + string[count]
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2
    if countTo < len(string):
        csum = csum + string[- 1]
        csum = csum & 0xffffffff
    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer


def buildPacket():
    check_sum = 0
    Id = os.getpid() & 0xffff
    header = struct.pack("bbHHh", 8, 0, check_sum, Id, 1)
    data = struct.pack("d", time.time())
    check_sum = checksum(header + data)
    if sys.platform == 'darwin':
        check_sum = socket.htons(check_sum) & 0xffff
    else:
        check_sum = socket.htons(check_sum)
    header = struct.pack("bbHHh", 8, 0, check_sum, Id, 1)
    data = struct.pack("d", time.time())
    packet = header + data
    return packet


def getRoute(hostname):
    port = 33343
    max_hops = 30
    num_tries = 3
    upd = socket.getprotobyname('udp')
    timeout = 2

    for ttl in range(1, max_hops):
        for num_sent in range(1, num_tries):
            destination_address = socket.gethostbyname(hostname)
            icmp = socket.getprotobyname('icmp')
            send_sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
            send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
            send_sock.settimeout(2)
            try:
                d = buildPacket()
                send_sock.sendto(d, (destination_address, 0))
                t = time.time()
                startedSelect = time.time()
#                whatReady = select.select([send_sock], [], [], timeout)
                howLongInSelect = (time.time() - startedSelect)

                # if whatReady[0] == []:
                #     print("*\t*\t*\tRequest timed out")

                receive_packet, addr = send_sock.recvfrom(1024)
                print(addr)
                time_received = time.time()
                time_left = timeout - howLongInSelect

                if time_left <= 0:
                    print("*\t*\t*\tRequest timed out")

            except socket.timeout:
                continue

            else:
                icmp_header = receive_packet[20:28]
                request_type, code, checksum, packetID, sequence = struct.unpack("bbhhh", icmp_header)

                if request_type == 11:
                    bytes = struct.calcsize("d")
                    time_sent = struct.unpack("d", receive_packet[28:28 + bytes])[0]
                    print(" %d rtt=%.0f ms %s" & (ttl, (time_received - t) * 1000, addr[0]))
                elif request_type == 3:
                    bytes = struct.calcsize("d")
                    time_sent = struct.unpack("d", receive_packet[28:28 + bytes])[0]
                    print(" %d rtt=%.0f ms %s" & (ttl, (time_received - t) * 1000, addr[0]))
                elif request_type == 0:
                    bytes = struct.calcsize("d")
                    time_sent = struct.unpack("d", receive_packet[28:28 + bytes])[0]
                    print(" %d rtt=%.0f ms %s" & (ttl, (time_received - time_sent) * 1000, addr[0]))
                    return
                else:
                    print("error")
                    break
            finally:
                send_sock.close()


getRoute(sys.argv[1])
