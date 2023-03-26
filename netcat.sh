#!/bin/bash
IP=$(awk -F "=" '/SERVER_IP/ {print $2}' server/config.ini)
PORT=$(awk -F "=" '/SERVER_PORT/ {print $2}' server/config.ini)
echo "initializing netcat container"
docker run --rm -d -it --name netcat --net tp0_testing_net alpine:latest 1> /dev/null
echo "sending message to server"
message_reply=$(docker exec netcat sh -c "echo 'hello world' | nc $IP $PORT")
if [ "$message_reply" = "hello world" ]; then
    echo "Message received"
    echo "Test passed"
else
    echo "Test failed"
fi
docker rm -f netcat 1> /dev/null