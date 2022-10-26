FROM alpine:3.16
MAINTAINER John Rowley <johnrowleyster@gmail.com>

RUN apk add --no-cache rsyslog bash
COPY ./rsyslogd.conf /etc/rsyslogd.conf
RUN mkdir /src/
COPY ./docker-entrypoint.sh /src/docker-entrypoint.sh

EXPOSE 514/tcp 514/udp
RUN chmod a+x /src/docker-entrypoint.sh

ENTRYPOINT ["sh","/src/docker-entrypoint.sh"]
