# ------ this Dockerfile is a set of instructions that tells Docker how to build an image
# ------ image: frozen, complete snapshot of the entire app; not running yet
# ------ container: image that is actually running; can run multiple containers with same image

# to run the backend, need:
#    - docker build -t <app-name-backend> .
#    - docker run -p <local-port-(can customise which port preferred)>:<container-port-(must match CMD port which default 8000)> <app-name>

# alternatively, use docker-compose.yml file to run the full-stack completely
#    - docker-compose up --build

# docker hub - cloud registry like github where u can push or pull image (sharing publicly/privately)

# --------------------------------------------------------

FROM python:3.14.4-bookworm

RUN pip install uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync

COPY . .

ENTRYPOINT [ "uv", "run", "uvicorn" ]
CMD [ "--app-dir", "src", "--host", "0.0.0.0", "--port", "8001", "app:app" ]
