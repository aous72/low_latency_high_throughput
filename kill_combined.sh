ssh mininet@192.168.21.100 'sudo kill -SIGKILL $(ps -aux | grep '"'"'python ./combined1.py'"'"' | awk '"'"'{print $2}'"'"')' &
ssh mininet@192.168.22.100 'sudo kill -SIGKILL $(ps -aux | grep '"'"'python ./combined1.py'"'"' | awk '"'"'{print $2}'"'"')' &
ssh mininet@192.168.23.100 'sudo kill -SIGKILL $(ps -aux | grep '"'"'python ./combined1.py'"'"' | awk '"'"'{print $2}'"'"')' &
ssh mininet@192.168.24.100 'sudo kill -SIGKILL $(ps -aux | grep '"'"'python ./combined1.py'"'"' | awk '"'"'{print $2}'"'"')' &
