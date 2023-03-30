from common.utils import Bet
import ipaddress
import datetime
import logging

BET_TYPE = b'\x01'
FINISHED_TYPE = b'\x02'
CONFIRM_TYPE = b'\x03'
WINNER_TYPE = b'\x05'
FINISHED_WINNERS_TYPE = b'\x06'

class BatchOrEnd:
    def __init__(self, batch, end=False):
        self.batch = batch
        self.end = end

def get_ip(skt):
    return int(ipaddress.ip_address(skt.getpeername()[0]))

def long_read(skt, n):
    #avoids short read
    message = []
    while len(message) < n:
        message += skt.recv(n)
    return message

def long_write(skt, message):
    #avoids short write
    while len(message) > 0:
        n = skt.send(message)
        message = message[n:]
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
    #reads one bet from the socket
    agency = get_ip(skt)
    name = read_string(skt)
    surname = read_string(skt)
    id  = read_int32(skt)
    year = read_int16(skt)
    month = read_int8(skt)
    date = read_int8(skt)
    number = read_int32(skt)
    birth = datetime.date(year, month, date).isoformat()
    return Bet(agency, name, surname, id, birth, number)

def read_batch(skt):
    #reads a batch of bets from the socket
    batch_len = read_int8(skt)
    batch = []
    for i in range(batch_len):
        batch.append(read_bet(skt))
    return batch

def send_won_message(bet, skt):
    #informs client of winner bet
    message = bytearray()
    message += WINNER_TYPE
    message += int(bet.document).to_bytes(4, byteorder='big', signed=True)
    long_write(skt, message)

def send_finished_winner_message(skt):
    #informs client that all winners have been sent
    long_write(skt, FINISHED_WINNERS_TYPE)
    skt.close()

def read_protocol(skt):
    msg = skt.recv(1)
    if msg == BET_TYPE:
        batch = read_batch(skt)
        logging.info(f'action: batch_almacenad0 | result: success')
        return BatchOrEnd(batch)
    elif msg == FINISHED_TYPE:
        logging.info(f'action: ended_bets | result: success | id: {get_ip(skt)}')
        return BatchOrEnd(None, end=True)
    
def write_confirm(skt):
    #sends a confirmation message to the client that the batch has been received
    long_write(skt, CONFIRM_TYPE)
    
