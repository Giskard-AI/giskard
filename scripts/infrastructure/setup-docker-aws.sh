# install docker from yum
sudo yum update -y
sudo yum install docker -y
sudo systemctl enable docker
sudo usermod -aG docker ec2-user

# install docker-compose
sudo curl -L https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# then copy the file giskard-docker-start.service into /usr/lib/systemd/system/ and enable it with 
sudo systemctl enable giskard-docker-start.service
