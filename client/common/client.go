package common

import (
	"net"
	"time"
	"os"
	"syscall"
	"os/signal"
	log "github.com/sirupsen/logrus"
)

const OKEY_TYPE = 0x03

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopLapse     time.Duration
	LoopPeriod    time.Duration
	BatchSize     int
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

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {
	// autoincremental msgID to identify every message sent
	msgID := 1
	sigtermChannel := make(chan os.Signal, 1)
	signal.Notify(sigtermChannel, os.Interrupt, syscall.SIGTERM)
	betReader := NewBetReader()
	// sentAll := false

loop:
	// Send messages if the loopLapse threshold has not been surpassed

	for timeout := time.After(c.config.LoopLapse); ; {
		select {
		case <-timeout:
	        log.Infof("action: timeout_detected | result: success | client_id: %v",
                c.config.ID,
            )
			break loop
		default:
		}

		// Create the connection the server in every loop iteration. Send an
		c.createClientSocket()

		// read bets from the file
		bets := readNBets(betReader, c.config.BatchSize) //TODO: check for nil and EOF
		if bets == nil {
			//TODO: log read error
		}
		if len(bets) < c.config.BatchSize {
			// sentAll = true
		}

		// send bets to the server
		err := long_write(c, ConstructMessageBatch(bets))
		if err != nil {
			//TODO: log write error
		}

		// receive confirmation from the server
		msg, err := long_read(c, 1)
		if err != nil {
			//TODO: log read error
		}
		if msg[0] != OKEY_TYPE {
			//TODO: log server error
		}
		msgID++
		c.conn.Close()

		if err != nil {
			log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v",
                c.config.ID,
				err,
			)
			return
		}
		log.Infof("action: receive_message | result: success | client_id: %v | msg: %v",
            c.config.ID,
            1, //msg,
        )

		select { // check for interrupt signal
		case <-sigtermChannel:
			log.Infof("action: signal_received | result: success | client_id: %v", c.config.ID)
			DestroyBetReader(betReader)
			break loop
		default:
		}
		// Wait a time between sending one message and the next one
		time.Sleep(c.config.LoopPeriod)
	}
	DestroyBetReader(betReader)
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}
