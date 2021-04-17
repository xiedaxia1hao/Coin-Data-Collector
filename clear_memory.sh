pkill -9 chrome;
pkill -9 python;
pkill -9 Xvfb;
sudo sh -c 'echo 3 >/proc/sys/vm/drop_caches';
