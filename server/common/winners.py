import logging
from common.protocol import BatchOrEnd
from common.utils import load_bets, has_won


def send_winners_to_processes(agency_queues, bet):
    #sends a winning bet through a winner_q
    agency_queues[bet.agency].put(BatchOrEnd([bet]))

def proccess_winners(agency_queues):
    #sends all winning bets to the corresponding winner_q
    logging.info("action: sending_winners | result: processing")
    [send_winners_to_processes(agency_queues, bet) for bet in load_bets() if has_won(bet)]
    logging.info("action: sending_winners | result: success")
    for agency in agency_queues:
        agency_queues[agency].put(BatchOrEnd(None, end=True))