package common

import (
	"encoding/binary"
)

const MAX_STRING_LEN = 127
const BET_TYPE = 0x01

type Date struct {
	year int16
	month int8
	day int8
}

type Bet struct {
	name string
	surname string
	id int32
	birth Date
	number int32
}

func addStringToMessage(message []byte, str string) []byte {
	strLen := len(str)
	message = append(message, byte(strLen))
	message = append(message, str...)
	return message
}

func addInt32ToMessage(message []byte, number int32) []byte {
	bytes := make([]byte, 4)
	binary.BigEndian.PutUint32(bytes, uint32(number))
	message = append(message, bytes...)
	return message
}

func addInt16ToMessage(message []byte, number int16) []byte {
	bytes := make([]byte, 2)
	binary.BigEndian.PutUint16(bytes, uint16(number))
	message = append(message, bytes...)
	return message
}

func bytesToInt32(bytes []byte) int32 {
	return int32(binary.BigEndian.Uint32(bytes))
}

func ConstructMessageBatch(bets []Bet) []byte {
	message := make([]byte, 2)
	message[0] = BET_TYPE //bet type message code
	message[1] = uint8(len(bets)) //bet type message code
	for _, bet := range bets {
		message = append(message, ConstructMessageBet(bet)...)
	}
	return message
}

func ConstructMessageBet(bet Bet) []byte {
	message := make([]byte, 0)
	if len(bet.name) > MAX_STRING_LEN || len(bet.surname) > MAX_STRING_LEN {
		return nil
	}
	message = addStringToMessage(message, bet.name)
	message = addStringToMessage(message, bet.surname)
	message = addInt32ToMessage(message, bet.id)
	message = addInt16ToMessage(message, bet.birth.year)
	message = append(message, byte(bet.birth.month))
	message = append(message, byte(bet.birth.day))
	message = addInt32ToMessage(message, bet.number)
	return message
}