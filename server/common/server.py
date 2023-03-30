import socket
import logging
import signal
from common.protocol import get_ip
import multiprocessing as mp
from common.winners import proccess_winners
from common.bet_loader import bet_loader
from common.client_process import client_process

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
                new_p = mp.Process(target=client_process, args=(client_sock,bet_q,winner_q,))
                processes.append(new_p)
                new_p.start()
                contacted_agencies += 1
        
        p.join()
        proccess_winners(agency_queues)
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