from common.utils import Bet
import ipaddress

def long_read(skt, n):
    #avoids short read
    message = []
    while len(message) < n:
        message += skt.recv(n)
    return message

def read_string(skt):
    string_len = read_int8(skt)
    string = long_read(skt, string_len)
    return string

def read_int32(skt):
    return int.from_bytes(long_read(skt, 4), byteorder='big', signed=True)

def read_int16(skt):
    return int.from_bytes(long_read(skt, 2), byteorder='big', signed=True)

def read_int8(skt):
    return int.from_bytes(long_read(skt, 1), byteorder='big', signed=True)

def read_bet(skt):
    agency = int(ipaddress.ip_address(skt.getpeername()[0]))
    name = read_string(skt)
    surname = read_string(skt)
    id  = read_int32(skt)
    year = read_int16(skt)
    month = read_int8(skt)
    date = read_int8(skt)
    number = read_int32(skt)
    birth = f'{year}-{month}-{date}'
    return Bet(agency, name, surname, id, birth, number)#TODO get acency
    
