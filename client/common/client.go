package common

import (
	"net"
	"time"
	"os"
	"syscall"
	"os/signal"
	log "github.com/sirupsen/logrus"
)

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopLapse     time.Duration
	LoopPeriod    time.Duration
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

func genericBet(num int32) Bet {
	date := Date {
		year: 2022,
		month: 12,
		day: 18,
	}
	bet := Bet{
		name: "tom",
		surname: "smith",
		id: 123456789,
		birth: date,
		number: num,
	}
	return bet
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

		bet := genericBet(int32(msgID))
		err := long_write(c, ConstructMessageBet(bet))

		// msg, err := c.conn.read()
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
			break loop
		default:
		}
		// Wait a time between sending one message and the next one
		time.Sleep(c.config.LoopPeriod)
	}

	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}
