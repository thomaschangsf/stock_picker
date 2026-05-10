FROM alpine:3.19

RUN apk add --no-cache squid

COPY squid.conf /etc/squid/squid.conf

RUN mkdir -p /var/cache/squid /var/log/squid \
    && chown -R squid:squid /var/cache/squid /var/log/squid \
    && rm -f /var/cache/squid/squid.pid /var/run/squid.pid \
    && squid -k parse -f /etc/squid/squid.conf

# Memory-only config: no `squid -z` required at runtime.
CMD ["sh", "-c", "mkdir -p /var/cache/squid /var/log/squid && chown -R squid:squid /var/cache/squid /var/log/squid && rm -f /var/cache/squid/squid.pid /var/run/squid.pid && exec squid -N -f /etc/squid/squid.conf"]
