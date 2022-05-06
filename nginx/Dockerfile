FROM nginx:1.21.4

COPY docker-entrypoint.sh /

# Create nginx log directory
RUN mkdir -p /var/log/nginx/

# Remove sym links from nginx image
RUN rm /var/log/nginx/access.log
RUN rm /var/log/nginx/error.log

# Install logrotate
RUN apt-get update && apt-get -y install logrotate

# Copy MyApp nginx config
#COPY nginx.conf /etc/nginx/nginx.conf

#Copy logrotate nginx configuration
COPY logrotate_nginx /etc/logrotate.d/

#Copy cron job configuration
COPY cron_logrotate /etc/cron.d/

# Apply cron job
RUN /usr/bin/crontab /etc/cron.d/cron_logrotate

RUN chmod -R 644 /etc/logrotate.d/logrotate_nginx

# Start nginx and cron as a service
ENTRYPOINT ["sh","/docker-entrypoint.sh"]
