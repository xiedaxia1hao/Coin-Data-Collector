for i in  `seq 1 15`; do timeout 300 sh -c "venv/bin/python3.7 xx.py"; echo "SLEEPING..."; sleep 5; pkill -9 chrome; pkill -9 python; echo "PROCESSES KILLED! "; sleep 5;  done
