from common.utils import store_bets

def bet_loader(bet_q, number_of_agencies, shutdown):
    #gets bets from bet_q and stores them
    #finishes when all client processes have sent an end message
    finished_agencies = 0

    while finished_agencies < number_of_agencies and not shutdown.is_set():
        batch = bet_q.get()
        if batch.end:
            finished_agencies += 1
            continue
        store_bets(batch.batch)
    return