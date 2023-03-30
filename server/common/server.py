import socket
import logging
import signal
from common.protocol import read_batch, long_write, get_ip
from common.utils import store_bets, load_bets, has_won
from time import sleep

BET_TYPE = b'\x01'
FINISHED_TYPE = b'\x02'
CONFIRM_TYPE = b'\x03'
WINNER_TYPE = b'\x05'
FINISHED_WINNERS_TYPE = b'\x06'
NUMBER_OF_AGENCIES = 2

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self.running = True
        self.waiting_clients = {}
        signal.signal(signal.SIGTERM, self.graceful_shutdown)

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        # the server
        while self.running and len(self.waiting_clients) < NUMBER_OF_AGENCIES:
            client_sock = self.__accept_new_connection()
            if client_sock: self.__handle_client_connection(client_sock)
        
        if not self.running:
            return
        
        
        bets = load_bets()
        for bet in bets:
            if has_won(bet):
                logging.info(f'action: WINNER | result: success | dni: ${bet.document} | numero: ${bet.number}')
                self.send_won_message(bet)
        
        self.send_finished_winners_message()



    def send_won_message(self, bet):
        skt = self.waiting_clients[bet.agency]
        message = bytearray()
        message += WINNER_TYPE
        message += int(bet.document).to_bytes(4, byteorder='big', signed=True)
        long_write(skt, message)


    def send_finished_winners_message(self):
        for agency in self.waiting_clients:
            skt = self.waiting_clients[agency]
            long_write(skt, FINISHED_WINNERS_TYPE)


    def __handle_client_connection(self, client_sock):
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
                    store_bets(batch)
                    logging.info(f'action: batch_almacenad0 | result: success')
                elif msg == FINISHED_TYPE:
                    finished_betting = True
                    logging.info(f'action: ended_bets | result: success | id: {get_ip(client_sock)}')
            except OSError as e:
                logging.error("action: receive_message | result: fail | error: {e}")
            finally:
                if not finished_betting:
                    long_write(client_sock, CONFIRM_TYPE)

        self.waiting_clients[get_ip(client_sock)] = client_sock

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
        for client in self.waiting_clients:
            client.close()
        self._server_socket.close()
        logging.info(f'action: closing_sockets | result: success')

    def __del__(self):
        for client in self.waiting_clients:
            self.waiting_clients[client].close()
        self._server_socket.close()