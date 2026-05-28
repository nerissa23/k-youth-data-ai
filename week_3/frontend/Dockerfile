# ------ this Dockerfile is a set of instructions that tells Docker how to build an image
# ------ image: frozen, complete snapshot of the entire app; not running yet
# ------ container: image that is actually running; can run multiple containers with same image

# to run the frontend, need:
#    - docker build -t <app-name-frontend> .
#    - docker run -p <local-port-(can customise which port preferred)>:<container-port-(must match CMD port which default 8000)> <app-name>

# alternatively, use docker-compose.yml file to run the full-stack completely
#    - docker-compose up --build

# docker hub - cloud registry like github where u can push or pull image (sharing publicly/privately)

# --------------------------------------------------------

# 1. pull pre-built image from docker hub that alrdy has python installed, so we build on top of it
FROM python:3.14.4-bookworm

# 2. install uv first
RUN pip install uv

# 3. setup dependencies
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync

# 4. copy entire application code
COPY . .

# 5. be default runs: uv run uvicorn --app-dir src --host 0.0.0.0 app:app
# can customise CMD by running `docker run <app-name> <new-CMD>`
ENTRYPOINT [ "uv", "run", "uvicorn" ]
CMD [ "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000", "app:app" ]
