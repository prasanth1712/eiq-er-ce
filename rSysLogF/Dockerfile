FROM alpine:3.15
MAINTAINER John Rowley <johnrowleyster@gmail.com>

RUN apk add --no-cache rsyslog bash
COPY ./rsyslogd.conf /etc/rsyslogd.conf

EXPOSE 514/tcp 514/udp
ENTRYPOINT ["rsyslogd", "-n", "-f", "/etc/rsyslogd.conf"]
