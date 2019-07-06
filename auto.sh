#!/bin/sh

cp -p main.py reference.time

./main.py &
PID=$!

while true ; do
  if [ main.py -nt reference.time ]; then
    cp -p main.py reference.time
    kill $PID
    ./main.py &
    PID=$!
  fi
  sleep 1
done



  
