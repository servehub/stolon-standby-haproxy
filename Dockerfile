FROM haproxy:2.1.1

LABEL maintainer="Anton Markelov <a.markelov@unitedtraders.com>"

ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  python3 \
  python3-dev \
  python3-pip \
  python3-setuptools \
  supervisor \
  curl && \
  apt-get -y clean && \
  rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt

ENV STOLON_VERSION="0.16.0"

RUN curl -Lfs https://github.com/sorintlab/stolon/releases/download/v${STOLON_VERSION}/stolon-v${STOLON_VERSION}-linux-amd64.tar.gz \
      -o /tmp/stolon.tar.gz \
    && tar -xzf /tmp/stolon.tar.gz -C /tmp \
    && cp /tmp/stolon-v${STOLON_VERSION}-linux-amd64/bin/* /usr/bin/ \
    && rm -rf /tmp/stolon*

COPY docker/config.yml /app/config.yml

COPY docker/haproxy.cfg /usr/local/etc/haproxy/config.cfg
COPY docker/stolon_haproxy.j2 /app/stolon_haproxy.j2
RUN touch /usr/local/etc/haproxy/stolon-config.cfg

COPY docker/supervisord.conf /app/supervisord.conf

COPY src /app/src

EXPOSE 25433

CMD ["supervisord", "-c", "/app/supervisord.conf"]
