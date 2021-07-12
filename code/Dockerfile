FROM ubuntu:latest

RUN apt-get update && apt-get -y update

# Install python
RUN apt-get install -y build-essential python3.6 python3-pip python3-dev
RUN pip3 -q install pip --upgrade

# Make src directory to contain necessary items
RUN mkdir src
WORKDIR src
COPY . .

# Install requirements
RUN pip3 install -r requirements.txt

# Add python script to be run each day and grant execution rights
ADD regular_article_pull.py /regular_article_pull.py
RUN chmod +x /regular_article_pull.py



# Remember to set db env variables when running
