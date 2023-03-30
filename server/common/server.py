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
NUMBER_OF_AGENCIES = 2

class BatchOrEnd:
    def __init__(self, batch, end=False, socket=None):
        self.batch = batch
        self.end = end
        self.socket = socket

def bet_loader(bet_q):
    finished_agencies = 0
    waiting_clients = {}

    while finished_agencies < NUMBER_OF_AGENCIES:
        batch = bet_q.get()
        if batch.end:
            waiting_clients[get_ip(batch.socket)] = batch.socket
            finished_agencies += 1
            continue
        store_bets(batch.batch)

    bets = load_bets()
    for bet in bets:
        if has_won(bet):
            logging.info(f'action: WINNER | result: success | dni: ${bet.document} | numero: ${bet.number}')
            send_won_message(bet, waiting_clients[bet.agency])
    
    send_finished_winners_message(waiting_clients)

def send_won_message(bet, skt):
    message = bytearray()
    message += WINNER_TYPE
    message += int(bet.document).to_bytes(4, byteorder='big', signed=True)
    long_write(skt, message)


def send_finished_winners_message(waiting_clients):
    for agency in waiting_clients:
        skt = waiting_clients[agency]
        long_write(skt, FINISHED_WINNERS_TYPE)
        skt.close()

def handle_client_connection(client_sock, bet_q):
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
                # store_bets(batch)
                logging.info(f'action: batch_almacenad0 | result: success')
            elif msg == FINISHED_TYPE:
                finished_betting = True
                logging.info(f'action: ended_bets | result: success | id: {get_ip(client_sock)}')
                bet_q.put(BatchOrEnd(None, end=True, socket=client_sock))
                return
        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {e}")
        finally:
            if not finished_betting:
                long_write(client_sock, CONFIRM_TYPE)

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
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
        bet_q = mp.Manager().Queue()
        p = mp.Process(target=bet_loader, args=(bet_q,))
        p.start()
        contacted_agencies = 0
        processes = []
        while self.running and contacted_agencies < NUMBER_OF_AGENCIES:
            client_sock = self.__accept_new_connection()
            if client_sock:  
                new_p = mp.Process(target=handle_client_connection, args=(client_sock,bet_q,))
                processes.append(new_p)
                new_p.start()
                contacted_agencies += 1
        
        for new_p in processes:
            new_p.join()
        p.join()
        # logging.info(f'FIN')
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