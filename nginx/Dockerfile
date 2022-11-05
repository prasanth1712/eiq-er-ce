FROM nginx:1.23.1-alpine

COPY docker-entrypoint.sh /
RUN apk update && apk upgrade

RUN set -x ; \
  addgroup -g 82 -S www-data ; \
  adduser -u 82 -D -S -G www-data www-data && exit 0 ; exit 1

# Create nginx log directory
RUN mkdir -p /var/log/nginx/

# Remove sym links from nginx image
RUN rm /var/log/nginx/access.log
RUN rm /var/log/nginx/error.log

# Install logrotate
RUN apk update && apk add  logrotate

# Copy MyApp nginx config
#COPY nginx.conf /etc/nginx/nginx.conf

#Copy logrotate nginx configuration
COPY logrotate_nginx /etc/logrotate.d/
#COPY nginx.conf /etc/nginx/
#Copy cron job configuration
COPY cron_logrotate /etc/cron.d/

# Apply cron job
RUN /usr/bin/crontab /etc/cron.d/cron_logrotate

RUN chmod -R 644 /etc/logrotate.d/logrotate_nginx

# Start nginx and cron as a service
ENTRYPOINT ["sh","/docker-entrypoint.sh"]

