#scp -i '~/.ssh/microkey.pem' /home/lapis/Documents/DSI/projects/okc/src/okc_account_credentials ubuntu@ec2-18-223-169-63.us-east-2.compute.amazonaws.com:/home/ubuntu/OkCupid/src
   
#scp -i '~/.ssh/microkey.pem' /home/lapis/Documents/DSI/projects/okc/src/chromedriver ubuntu@ec2-18-223-169-63.us-east-2.compute.amazonaws.com:/home/ubuntu/OkCupid/src 
  

https://repo.anaconda.com/archive/Anaconda3-2019.10-Linux-x86_64.sh

bash Anaconda3-2019.10-Linux-x86_64.sh -b


sudo apt-get update

sudo apt-get install \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common
    
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

sudo apt-key fingerprint 0EBFCD88

sudo apt-get update

sudo apt-get install docker-ce docker-ce-cli containerd.io

sudo apt-get install docker-ce=5:19.03.5~3-0~ubuntu-bionic docker-ce-cli=5:19.03.5~3-0~ubuntu-bionic containerd.io


sudo docker run --name mongoserver -p 27017:27017 -v "$PWD":/home/data -d mongo

sudo docker exec -it mongoserver mongo 
use okc
db.createCollection('users')
db.createCollection('usernames')
db.createCollection('scrapers')
exit

export PATH=~/anaconda3/bin:$PATH
conda install -y pymongo
conda install -y selenium


