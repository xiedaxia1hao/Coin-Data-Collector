while true; 

do 
	timeout 300 sh -c "venv/bin/python3 xx.py"; 
	echo "SLEEPING..."; 
	sleep 5; 
	pkill -9 chrome; 
	pkill -9 python; 
	pkill -9 Xvfb;
       	sudo sh -c 'echo 3 >/proc/sys/vm/drop_caches'	
	echo "PROCESSES KILLED AND MEMORY CLEARED! "; 
	sleep 5;  
done
