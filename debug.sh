osascript -e 'tell application "Terminal" to do script "ssh -t mininet@192.168.21.100 '"'"'./combined1.py 192.168.11.0'"'"'; exit; "'
osascript -e 'tell application "Terminal" to do script "ssh -t mininet@192.168.22.100 '"'"'./combined1.py 192.168.12.0'"'"'; exit; "'
osascript -e 'tell application "Terminal" to do script "ssh -t mininet@192.168.23.100 '"'"'./combined1.py 192.168.13.0'"'"'; exit; "'
osascript -e 'tell application "Terminal" to do script "ssh -t mininet@192.168.24.100 '"'"'./combined1.py 192.168.14.0'"'"'; exit; "'