FROM ubuntu:latest

RUN apt-get update && apt-get -y update

# Install python
RUN apt-get install -y build-essential python3.8 python3-pip python3-dev
RUN pip3 -q install pip --upgrade

# Make src directory to contain necessary items
RUN mkdir src
WORKDIR src
COPY . .

# Install requirements
RUN pip3 install -r requirements.txt \
    && python3 -m spacy download en_core_web_md

# Grant execution rights to python script to be run each day
RUN chmod +x /src/regular_article_pull.py

# Run script in unbuffered mode - feed stdout directly to docker logs
CMD ["python3", "-u", "regular_article_pull.py"]
# Remember to set db env variables when running
