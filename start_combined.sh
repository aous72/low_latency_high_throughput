echo starting 192.168.14.0
ssh mininet@192.168.24.100 'screen -d -m ./combined1.py 192.168.14.0' &
echo starting 192.168.13.0
ssh mininet@192.168.23.100 'screen -d -m ./combined1.py 192.168.13.0' &
echo starting 192.168.12.0
ssh mininet@192.168.22.100 'screen -d -m ./combined1.py 192.168.12.0' &
echo starting 192.168.11.0
ssh mininet@192.168.21.100 'screen -d -m ./combined1.py 192.168.11.0' &
