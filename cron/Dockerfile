FROM ubuntu:latest

# Install cron
RUN apt-get update && apt-get -y update
RUN apt-get install cron

# Add crontab file in cron directory
ADD crontab /etc/cron.d/simple-cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/simple-cron

# Create logfile for debug
RUN touch /var/log/cron.log

# Run the command on container startup (this also helps keep container alive)
CMD cron && tail -f /var/log/cron.log 