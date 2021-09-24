
# in first window run in /hw1 dir
# ./hw1.out 1024 2000

# test WRQ
# in second window run in /test dir
# tftp -4 -v -m binary localhost 1025 -c put wrq.txt

# test RRQ
# in second window run in /test dir
# tftp -4 -v -m binary localhost 1025 -c get rrq.txt

# ---- automate (not working) ----
#command='hw1.out 1025 2000'
#xfce4-terminal --tab --command $'bash -c "${command} ; exec bash"'
#tftp -4 -v -m binary localhost 1025 -c put blob.txt

.././hw1.out 15000 20000&
pid=$!

if [ $1 = "rrq" ]; then
    tftp -4 -v -m binary localhost 15000 -c get student_long.txt
elif [ $1 = "wrq" ]; then
    tftp -4 -v -m binary localhost 15000 -c put student_long_remote.txt
fi

kill $pid