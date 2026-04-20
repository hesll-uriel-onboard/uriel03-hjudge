FROM ghcr.io/flaresolverr/flaresolverr:latest

USER root
RUN apt-get update && apt-get install -y git gcc libpq-dev make curl
RUN curl -LsSf https://astral.sh/uv/install.sh | UV_INSTALL_DIR=/usr/local/bin sh

RUN useradd -m hjudge
WORKDIR /home/hjudge
RUN git clone https://github.com/hesll-uriel-onboard/uriel03-hjudge.git tmp && mv tmp/* tmp/.* . 2>/dev/null || true && rm -rf tmp
RUN uv sync

COPY docker/start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 8000
CMD ["/start.sh"]
