# these scripts are used for ssh

server:

add " echo 'psw' | sudo -s 'path/server_setup.sh' " in /etc/rc.local

client:

ssh: run client_ssh.sh 
html: http://192.168.1.10/rxdata/?url=log.jpg&format=image
      http://192.168.1.10/rxdata/?url=log.html&format=txt
