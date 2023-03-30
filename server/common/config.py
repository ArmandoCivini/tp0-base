
def declare_config(config_params):
    global BET_TYPE
    global FINISHED_TYPE
    global CONFIRM_TYPE
    global WINNER_TYPE
    global FINISHED_WINNERS_TYPE
    BET_TYPE = config_params["bet_type"].to_bytes(1, byteorder='big', signed=True)
    FINISHED_TYPE = config_params["finished_type"].to_bytes(1, byteorder='big', signed=True)
    CONFIRM_TYPE = config_params["confirm_type"].to_bytes(1, byteorder='big', signed=True)
    WINNER_TYPE = config_params["winner_type"].to_bytes(1, byteorder='big', signed=True)
    FINISHED_WINNERS_TYPE = config_params["finished_winners_type"].to_bytes(1, byteorder='big', signed=True)