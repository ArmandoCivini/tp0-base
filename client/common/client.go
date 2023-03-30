package common

import (
	"net"
	"time"
	"os"
	"syscall"
	"os/signal"
	log "github.com/sirupsen/logrus"
)

type ProtocolConfig struct {
	BET_TYPE int8
	FINISHED_TYPE int8
	OKEY_TYPE int8
	WINNER_TYPE int8
	FINISHED_WINNERS_TYPE int8
}
// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopLapse     time.Duration
	LoopPeriod    time.Duration
	BatchSize     int
	Protocol 	  ProtocolConfig
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	conn   net.Conn
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config: config,
	}
	return client
}

func DestroyClient(c *Client, betReader *BetReader) {
	c.conn.Close()
	DestroyBetReader(betReader)
}

func long_write(c *Client,message []byte) error {
	bytes_writen := 0
	for bytes_writen < len(message) {
		n, err := c.conn.Write(message[bytes_writen:])
		if err != nil {
			return err
		}
		bytes_writen += n
	}
	return nil
}

func long_read(c *Client, n int) ([]byte, error) {
	bytes_read := 0
	message := make([]byte, n)
	for n > bytes_read {
		n_read, err := c.conn.Read(message[bytes_read:])
		if err != nil {
			return nil, err
		}
		bytes_read += n_read
	}
	return message, nil
}


// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Fatalf(
	        "action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
	}
	c.conn = conn
	return nil
}

func readBets(betReader *BetReader, batchSize int) ([]Bet, bool) {
	bets := readNBets(betReader, batchSize)
	if bets == nil {
		log.Errorf("action: error reading bets | result: fail")
	}
	if len(bets) < batchSize {
		log.Infof("action: end of file | result: fail | bets read: %v",
		len(bets),
		)
		return bets, true
	}
	return bets, false
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {
	sigtermChannel := make(chan os.Signal, 1)
	signal.Notify(sigtermChannel, os.Interrupt, syscall.SIGTERM)
	betReader := NewBetReader()
	sentAll := false
	bets := make([]Bet, 0)
	c.createClientSocket()

	for !sentAll {

		bets, sentAll = readBets(betReader, c.config.BatchSize)
		if bets == nil {
			continue
		}

		// send bets to the server
		err := long_write(c, ConstructMessageBatch(bets, c.config.Protocol.BET_TYPE))
		if err != nil {
			log.Errorf("action: error sending bets | result: fail")
			continue
		}

		// receive confirmation from the server
		msg, err := long_read(c, 1)
		if err != nil {
			log.Errorf("action: error reading confirmation | result: fail")
		} else if msg[0] != byte(c.config.Protocol.OKEY_TYPE) {
			log.Errorf("action: error didnt confirm | result: fail")
		} else {	
			log.Infof("action: batch_successfull | result: success | client_id: %v",
			c.config.ID,
			)
		}

		select { // check for interrupt signal
		case <-sigtermChannel:
			log.Infof("action: signal_received | result: success | client_id: %v", c.config.ID)
			DestroyClient(c, betReader)
			break
		default:
		}
	}

	finishedMessage := make([]byte, 1)
	finishedMessage[0] = byte(c.config.Protocol.FINISHED_TYPE)
	err := long_write(c, finishedMessage)
	if err != nil {
		log.Errorf("action: error writing finish message | result: fail")
	}

	winners := readWinners(c)
	if winners == nil {
		log.Errorf("action: failed to get winners | result: fail")
		return
	}

	log.Infof("action: consulta_ganadores | result: success | cant_ganadores: %v", len(winners))

	DestroyClient(c, betReader)
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}

func readWinners(c *Client) []int32 {
	winners := make([]int32, 0)
	msg, err := long_read(c, 1)
	if err != nil {
		return nil
	}
	for msg[0] == byte(c.config.Protocol.WINNER_TYPE) {
		winnerIdBytes, err := long_read(c, 4)
		if err != nil {
			return nil
		} else {
			winnerId := bytesToInt32(winnerIdBytes)
			log.Infof("action: received winner | result: success | DNI: %v", winnerId)
			winners = append(winners, winnerId)
		}
		msg, err = long_read(c, 1)
		if err != nil {
			return nil
		}
	}

	if msg[0] == byte(c.config.Protocol.FINISHED_WINNERS_TYPE) {
		return winners
	}
	return nil
}
