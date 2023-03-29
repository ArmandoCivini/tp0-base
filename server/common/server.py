import socket
import logging
import signal
from common.protocol import read_bet
from common.utils import store_bets
BET_TYPES = b'\x01'

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
        while self.running:
            client_sock = self.__accept_new_connection()
            if client_sock: self.__handle_client_connection(client_sock)

    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            msg = client_sock.recv(1)
            if msg == BET_TYPES:
                bet = read_bet(client_sock)
                store_bets([bet])
                logging.info(f'action: apuesta_almacenada | result: success | dni: ${bet.document} | numero: ${bet.number}')
        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {e}")
        finally:
            client_sock.close()

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
        logging.info(f'action: close_server_socket | result: in_progress')
        self._server_socket.close()
        logging.info(f'action: close_server_socket | result: success')