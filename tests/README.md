Fuse testing
========

Build
-----
	apt-get install libacl1-dev git
	git clone https://github.com/billziss-gh/secfs.test.git
	make

Tests cases
-----
	./bench_10000_10M.sh
	./bench_1000_100M.sh
	./bench_100_1000M.sh
	./bench_random.sh

	python fsrand.py /mnt/user/up2p/fuse/mountpoint/ -c 1000 -v

	./fs_racer.sh 60 /mnt/user/up2p/fuse/mountpoint/

	./fsstress -d /mnt/user/up2p/fuse/mountpoint/ -l 2 -n 100000 -p 4 -r -X -v

	./bonnie++ -x 60 -d /mnt/user/up2p/fuse/mountpoint/ -u root

	./iozone -R -b /shared/tests/bench_u02_test.xls -r 8k -s 10m -t 1 -F /mnt/user/up2p/fuse/mountpoint/testing

	./iozone -R -b /shared/test/bench_u01_test.xls -r 8k -s 100m -l 2 -u 10

	./iozone -l 2 -u 2 -r 16k -s 512M -F /mnt/user/up2p/fuse/mountpoint/t1 /mnt/user/up2p/fuse/mountpoint/t2

