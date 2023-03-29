package common

import (
    "encoding/csv"
    "io"
    log "github.com/sirupsen/logrus"
    "os"
	"strings"
	"strconv"
)

const BET_FILE_PATH = "./data/agency.csv"

type BetReader struct {
	file *os.File
}

func NewBetReader() *BetReader {
	file, err := os.Open(BET_FILE_PATH)
	if err != nil {
		log.Fatal(err)
	}
	return &BetReader{file: file}
}

func DestroyBetReader(betreader *BetReader) {
	betreader.file.Close()
}

func stringToInt32(str string) int32 {
	num, err := strconv.Atoi(str)
	if err != nil {
		log.Fatal(err)
	}
	return int32(num)
}

func stringToInt16(str string) int16 {
	num, err := strconv.Atoi(str)
	if err != nil {
		log.Fatal(err)
	}
	return int16(num)
}

func stringToInt8(str string) int8 {
	num, err := strconv.Atoi(str)
	if err != nil {
		log.Fatal(err)
	}
	return int8(num)
}


func readNBets(betreader *BetReader, n int) []Bet {
	bets := make([]Bet, 0)

    // read csv values using csv.Reader
    csvReader := csv.NewReader(betreader.file)
    for len(bets) < n {
        rec, err := csvReader.Read()
        if err == io.EOF {
            return bets
        }
        if err != nil {
            return nil
        }
        // do something with read line
		if len(rec) != 5 {
			log.Infof("action: invalid_bet | result: fail | value: %v",
				rec,
			)
			continue
		}
		date_str := strings.Split(rec[3], "-")
		date := Date {
			year: stringToInt16(date_str[0]),
			month: stringToInt8(date_str[1]),
			day: stringToInt8(date_str[2]),
		}
		bet := Bet{
			name: rec[0],
			surname: rec[1],
			id: stringToInt32(rec[2]),
			birth: date,
			number: stringToInt32(rec[4]),
		}
        bets = append(bets, bet)
    }
	return bets
}