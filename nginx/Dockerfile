FROM node:14.21.0-alpine3.16 as build
RUN npm install -g @angular/cli@13.2.3
RUN npm install -g gzipper@3.7.0
WORKDIR /app
COPY ./plgx-angular-ui .
RUN npm install
RUN ng build --prod --stats-json
RUN gzipper --verbose ../dist


FROM nginx:1.23.1-alpine

COPY /nginx/docker-entrypoint.sh /
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
COPY /nginx/logrotate_nginx /etc/logrotate.d/
COPY /nginx/nginx.conf /etc/nginx/
#Copy cron job configuration
COPY /nginx/cron_logrotate /etc/cron.d/

# Apply cron job
RUN /usr/bin/crontab /etc/cron.d/cron_logrotate

RUN chmod -R 644 /etc/logrotate.d/logrotate_nginx

COPY ./resources /resources
COPY --from=build /dist /dist


# Start nginx and cron as a service
ENTRYPOINT ["sh","/docker-entrypoint.sh"]

