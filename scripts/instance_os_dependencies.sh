#!/usr/bin/env bash

# Update package lists
sudo yum update -y

# Install Python3 and pip
sudo yum install -y python3 python3-pip

# Install Nginx
sudo amazon-linux-extras enable nginx1
sudo yum install -y nginx

# Install virtualenv using pip
sudo pip3 install virtualenv
