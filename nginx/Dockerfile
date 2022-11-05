FROM node:14.21.0-alpine3.16 as build
RUN npm install -g @angular/cli@13.2.3
RUN npm install -g gzipper@3.7.0
WORKDIR /app
COPY ./plgx-angular-ui .
RUN npm install
RUN ng build --prod --stats-json
RUN gzipper --verbose ../dist


FROM nginx:1.23.1-alpine

COPY build/nginx/docker-entrypoint.sh /

RUN set -x ; \
  addgroup -g 82 -S www-data ; \
  adduser -u 82 -D -S -G www-data www-data && exit 0 ; exit 1

# Create nginx log directory
RUN mkdir -p /var/log/nginx/

# Install logrotate
RUN apk update && apk add  logrotate

# Copy MyApp nginx config
COPY nginx/nginx.conf /etc/nginx/nginx.conf

#Copy logrotate nginx configuration
COPY nginx/logrotate_nginx /etc/logrotate.d/

#Copy cron job configuration
COPY nginx/cron_logrotate /etc/cron.d/

# Apply cron job
RUN /usr/bin/crontab /etc/cron.d/cron_logrotate

RUN chmod -R 644 /etc/logrotate.d/logrotate_nginx

COPY --from=build /dist /dist
COPY ./resources /resources

# Start nginx and cron as a service
ENTRYPOINT ["sh","/docker-entrypoint.sh"]

