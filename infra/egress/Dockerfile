ARG BASE_IMAGE=alpine:3.20
FROM ${BASE_IMAGE}
RUN apk add --no-cache tinyproxy=1.11.2-r0   # alpine 3.20 仓库版本，换 BASE_IMAGE 时同步更新
COPY tinyproxy.conf /etc/tinyproxy/tinyproxy.conf
COPY filter /etc/tinyproxy/filter
EXPOSE 8888
CMD ["tinyproxy","-d","-c","/etc/tinyproxy/tinyproxy.conf"]
