while ! sudo /local/scratch/contiki-ng//tunslip6 -t tun0 -a 127.0.0.1 aaaa::1/64 -p 60016
do
echo -n "Waiting... "
done
