# How to use docker for SoapyIris

# FAILED! THE AVAHI DOESN'T WORK

# SEEMS NEED FUTHER STUDY

















## 1. install docker

these steps are from [this link](https://docs.docker.com/install/linux/docker-ce/ubuntu/)

```shell
sudo apt install apt-transport-https ca-certificates curl software-properties-common
# then add Docker’s official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
# then check fingerprint: 9DC8 5822 9FC7 DD38 854A E2D8 8D81 803C 0EBF CD88
sudo apt-key fingerprint 0EBFCD88

# add apt repository
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get update  # update index
sudo apt-get install docker-ce

# to test whether it's installed properly
sudo docker version

# if don't want 'sudo' to run docker, see instructions in the link above
```

## 2. run basic ubuntu 16.04 and build your own image

<font style='color: red; font-weight: bold;'>notice: </font>**If you are only interested in built image, please refer to [here][release] (read 3)**

ubuntu 16.04 is the recommended environment for running SoapySDR and SoapyIris

```shell
docker create --privileged -i --net="host" -v /var/run/avahi-daemon:/var/run/avahi-daemon ubuntu:16.04
```

this will create a container based on clean ubuntu 16.04, just like you have a barely new computer

```shell
docker ps -a
# then you will get a container which STATIS is 'Created', copy the Container ID
docker start <containerID>
# after that, run `docker ps -a` you will see a 'Up' state container
docker exec -it <containerID> /bin/bash
# this time you will get into the new "system"
```

notice that you are the root, but what's OK because in the docker you will not affect the host system.

```shell
# do some system update and install software
apt update
apt upgrade
apt install vim  # if you want to do some editing work on system, not necessary
# you can install other packages, that up to you!
```

then we start installing the SoapySDR

you can follow [the build guide](https://github.com/pothosware/SoapySDR/wiki/BuildGuide) because this document will **not** update with SoapySDR

```shell
apt-get install python3-dev cmake g++ libpython-dev python-numpy swig git
cd /root  # clone into here
git clone https://github.com/pothosware/SoapySDR.git
cd SoapySDR
mkdir build
cd build
cmake ..
make -j4
make install
ldconfig
SoapySDRUtil --info  # if you can see version here, success
```

next, install Soapy Remote

see [build guide](https://github.com/pothosware/SoapyRemote/wiki)

```shell
apt-get install avahi-daemon libavahi-client-dev  # used for device discovery
cd /root
git clone https://github.com/pothosware/SoapyRemote.git
cd SoapyRemote
mkdir build
cd build
cmake ..
make
make install
```

finally, install SoapyIris

```shell
cd /root
git clone https://github.com/skylarkwireless/sklk-soapyiris.git
cd sklk-soapyiris
mkdir build
cd build
cmake ..
make
make install
```

**So till now we have a **

now you can clone a [ArgosWebGui](https://github.com/wuyuepku/ArgosWebGui/settings)



## 3. run SoapySDR and ArgosWebGui

### get the docker image

here we have a built image with all dependencies and applications. You can download this from the GitHub.

[release]: https://github.com/wuyuepku/ArgosWebGui/releases	"Released Docker Images"

If you haven't built for your own (for the most cases), you can load the docker image to your system

```shell
docker load -i <the file you download>.tar
```

then you can call `docker image ls` to list all the image on your system.

If you have unused docker image, the system will not **delete** them until you call

```shell
docker rmi <dockerImageID>  # the image ID is from command `docker image ls`
```

### get ArgosWebGui

simply clone from GitHub `git clone https://github.com/wuyuepku/ArgosWebGui/`

because they are all python script, no build commands needed to run.

### create a docker container based on the image

if you have a docker image tagged `ArgosWebGui:<version>`, then you can do these command

```shell
docker create -i --net="host" -v <directory>:/root/ArgosWebGui ArgosWebGui:<version> 
# where <directory> is the ArgosWebGui folder you just clone from GitHub
#     it must be a absolute path !!!
# and <version> is the version you want in `docker image ls`
```

### start the container

then using `docker ps -a` you could see a container with STATUS of `Created` but not `Up`

```shell
docker start <containerID>  # container ID is in `docker ps -a`
```

this time you type `docker ps -a` and will see a `Up` state container

### login

next step is to login to the shell

```shell
docker exec -it <containerID> /bin/bash  # -it means interactive and tty
# exec is to run a command, in this case is "/bin/bash", and "-it" make sure you can use stdin & stdout to access
```

now you should see the root `/` of the container, which contains a folder `ArgosWebGui`

### run ArgosWebGui

Congratulations! all the dependencies are there

`cd ArgosWebGui` and use `python3 host.py`, then you could enjoy it!

