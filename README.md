# docker-examples

Small, copy-pasteable Docker setups I keep coming back to. Every file here runs.
No "hello world in 400 lines" nonsense.

I built this because I got tired of re-deriving the same multistage Python build
and the same postgres+redis compose file on every new project, and because half
the blog posts out there ship a Dockerfile that rebuilds your dependencies on
every single line change.

## What's in here

```
Dockerfile.multistage          # python:3.12-slim -> wheels -> slim runtime
flask/app.py                   # tiny real Flask app (health + a counter in redis)
flask/Dockerfile               # the build for the flask example
docker-compose.nginx.yml       # nginx reverse proxy in front of the flask app
docker-compose.postgres-redis.yml
redis/docker-compose.yml       # just redis, for local dev
prometheus/prometheus.yml      # scrape config
mysql/init.sql                 # schema + seed data
docs/tips.md                   # the stuff I wish someone told me earlier
```

## Quick start

The flask app:

```bash
cd flask
docker build -t flask-demo:dev .
docker run --rm -p 8000:8000 flask-demo:dev
curl localhost:8000/health
# {"status":"ok"}
```

Nginx + app (the app talks to redis, so bring both up):

```bash
docker compose -f docker-compose.nginx.yml up --build
curl -s localhost:8080/ | head
```

Postgres + redis:

```bash
docker compose -f docker-compose.postgres-redis.yml up -d
docker compose -f docker-compose.postgres-redis.yml exec postgres \
  psql -U app -d app -c '\dt'
```

MySQL with seed data:

```bash
docker run --rm -d --name mysql-demo \
  -e MYSQL_ROOT_PASSWORD=devroot -e MYSQL_DATABASE=shop \
  -v "$PWD/mysql/init.sql:/docker-entrypoint-initdb.d/init.sql:ro" \
  -p 3306:3306 mysql:8.0
```

## Sample output

`docker images` after a rebuild where only `app.py` changed:

```
REPOSITORY   TAG   IMAGE ID       CREATED         SIZE
flask-demo   dev   a1b2c3d4e5f6   6 seconds ago   61.4MB
```

That 61MB and the "6 seconds" are the whole point of the multistage file.
Before I split the builder stage out it was 1.02GB and took 40s.

## Gotchas

- **`Error response from daemon: Ports are not available: bind: address already in use`**
  Something on your host already has 5432 (usually a local postgres you forgot
  about). Change the host side: `"5433:5432"`.
- **`permission denied while trying to connect to the Docker daemon socket`**
  You're not in the `docker` group. `sudo usermod -aG docker "$USER"` then log
  out and back in. Rebooting the daemon is not enough.
- Compose v2 is `docker compose`, not `docker-compose`. The old python binary is
  dead as of 2024. If a script of mine says `docker-compose`, that's the old one.
- On macOS, bind mounts from `$HOME/Desktop` etc. are slow through the VM
  filesystem. Put volumes under `/tmp` or use named volumes.

## Notes

Tested on Docker Engine 26.1 and Compose v2.24, mostly on Ubuntu 22.04 and macOS
14 (arm64). The `platform: linux/amd64` line in a couple of the compose files is
there because I develop on an M2 and one of the images had no arm build. YMMV on
Windows — the volume paths in `docs/tips.md` are POSIX.

Nothing here is production-hardened. It's the "get a real stack running on my
laptop in 30 seconds" tier.
