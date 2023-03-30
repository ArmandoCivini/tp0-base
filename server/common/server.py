import socket
import logging
import signal
from common.protocol import read_batch, long_write, get_ip
from common.utils import store_bets, load_bets, has_won
import multiprocessing as mp

BET_TYPE = b'\x01'
FINISHED_TYPE = b'\x02'
CONFIRM_TYPE = b'\x03'
WINNER_TYPE = b'\x05'
FINISHED_WINNERS_TYPE = b'\x06'

class BatchOrEnd:
    def __init__(self, batch, end=False):
        self.batch = batch
        self.end = end

def bet_loader(bet_q, number_of_agencies):
    finished_agencies = 0

    while finished_agencies < number_of_agencies:
        batch = bet_q.get()
        if batch.end:
            finished_agencies += 1
            continue
        store_bets(batch.batch)
    return

def send_won_message(bet, skt):
    message = bytearray()
    message += WINNER_TYPE
    message += int(bet.document).to_bytes(4, byteorder='big', signed=True)
    long_write(skt, message)

def send_finished_winner_message(skt):
    long_write(skt, FINISHED_WINNERS_TYPE)
    skt.close()

def send_winners_to_processes(agency_queues, bet):
    logging.info("sending winner")
    agency_queues[bet.agency].put(BatchOrEnd([bet]))


def send_finished_winners_message(waiting_clients):
    for agency in waiting_clients:
        skt = waiting_clients[agency]
        long_write(skt, FINISHED_WINNERS_TYPE)
        skt.close()

def handle_client_connection(client_sock, bet_q, winner_q):
    """
    Read message from a specific client socket and closes the socket

    If a problem arises in the communication with the client, the
    client socket will also be closed
    """
    finished_betting = False
    while not finished_betting:
        try:
            msg = client_sock.recv(1)
            if msg == BET_TYPE:
                batch = read_batch(client_sock)
                bet_q.put(BatchOrEnd(batch))
                # logging.info(f'action: batch_almacenad0 | result: success')
            elif msg == FINISHED_TYPE:
                finished_betting = True
                logging.info(f'action: ended_bets | result: success | id: {get_ip(client_sock)}')
                bet_q.put(BatchOrEnd(None, end=True))
                break
        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {e}")
        finally:
            if not finished_betting:
                long_write(client_sock, CONFIRM_TYPE)
    
    while True:
        logging.info("waiting for winner")
        winner = winner_q.get()
        if winner.end:
            break
        send_won_message(winner.batch[0], client_sock)

    send_finished_winner_message(client_sock)
    return

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self.listen_backlog = listen_backlog
        self.running = True
        signal.signal(signal.SIGTERM, self.graceful_shutdown)

    

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        # the server
        manager = mp.Manager()
        bet_q = manager.Queue()
        p = mp.Process(target=bet_loader, args=(bet_q,self.listen_backlog,))
        p.start()
        contacted_agencies = 0
        processes = []
        agency_queues = {}
        while self.running and contacted_agencies < self.listen_backlog:
            client_sock = self.__accept_new_connection()
            if client_sock:  
                winner_q = manager.Queue()
                agency_queues[get_ip(client_sock)] = winner_q
                new_p = mp.Process(target=handle_client_connection, args=(client_sock,bet_q,winner_q,))
                processes.append(new_p)
                new_p.start()
                contacted_agencies += 1
        
        p.join()
        logging.info("action: sending_winners | result: processing")
        [send_winners_to_processes(agency_queues, bet) for bet in load_bets() if has_won(bet)]
        logging.info("action: sending_winners | result: success")
        for agency in agency_queues:
            agency_queues[agency].put(BatchOrEnd(None, end=True))
        for new_p in processes:
            new_p.join()
        logging.info("action: End of server | result: success")
        return


    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        try:
            c, addr = self._server_socket.accept()
        except OSError as e:
            if self.running:
                logging.error(f'action: accept_connections | result: fail | error: {e}')
            return None
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c

    def graceful_shutdown(self, signum, frame):
        """
        Graceful shutdown of the server
        """
        self.running = False
        logging.info(f'action: closing_sockets | result: in_progress')
        self._server_socket.close()
        logging.info(f'action: closing_sockets | result: success')

    def __del__(self):
        self._server_socket.close()