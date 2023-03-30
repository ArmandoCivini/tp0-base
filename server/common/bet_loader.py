from common.utils import store_bets

def bet_loader(bet_q, number_of_agencies, shutdown):
    finished_agencies = 0

    while finished_agencies < number_of_agencies and not shutdown.is_set():
        batch = bet_q.get()
        if batch.end:
            finished_agencies += 1
            continue
        store_bets(batch.batch)
    return