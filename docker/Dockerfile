FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

RUN apt update && apt install -y git gcc libpq-dev make
RUN ln -sf /usr/local/bin/uv /usr/bin/uv
RUN useradd -m hjudge
WORKDIR /home/hjudge
RUN git clone https://github.com/hesll-uriel-onboard/uriel03-hjudge.git tmp && mv tmp/* tmp/.* . 2>/dev/null || true && rm -rf tmp
RUN uv sync
EXPOSE 8000
CMD [ "uv", "run", "litestar", "--app", "hjudge.app:app", "run", "--host", "0.0.0.0" ]
