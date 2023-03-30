import logging
from common.protocol import (send_finished_winner_message, 
                             send_won_message, read_protocol, 
                             write_confirm)

def client_process(client_sock, bet_q, winner_q, shutdown):
    #loops, receiving batches from client until it finishes
    #then, it receives winners from winner_q and sends them to the client
    finished_betting = False
    while not finished_betting and not shutdown.is_set():
        try:
            batch_or_end = read_protocol(client_sock)
            bet_q.put(batch_or_end)
            if batch_or_end.end:
                finished_betting = True
                break
        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {e}")
        finally:
            if not finished_betting:
                write_confirm(client_sock)
    
    while not shutdown.is_set():
        winner = winner_q.get()
        if winner.end:
            break
        send_won_message(winner.batch[0], client_sock)

    send_finished_winner_message(client_sock)
    return