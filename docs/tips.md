# Docker stuff I keep re-learning the hard way

Notes to self. Most of these cost me at least 20 minutes the first time.

## Layer caching: order your COPYs

Docker caches a layer until something it depends on changes. If you do this:

```dockerfile
COPY . .
RUN pip install -r requirements.txt
```

then *every* source edit invalidates the `pip install` layer and you wait 40s
for deps you already had. Copy the lockfile first, install, then copy the rest:

```dockerfile
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
```

Deps are now cached until `requirements.txt` actually changes.

## .dockerignore is not optional

Without it, `COPY . .` drags `.git`, `node_modules`, `.venv`, and whatever junk
is in your working tree into the build context. The build gets slow before the
build even starts, because the whole context is shipped to the daemon. A
`.git` directory alone can be hundreds of MB.

You can see context size in the first line of a build:
`=> [internal] load build context`.

## Don't run as root

Default user is root. If your process gets popped, the attacker is root *in the
container*, which is a much shorter path to the host than people think. Add:

```dockerfile
RUN useradd --create-home --uid 10001 appuser
USER appuser
```

Watch out: files created by root earlier in the build may not be writable by
`appuser`. Use `COPY --chown=appuser:appuser` for app files.

## Image size: alpine is not always smaller

`python:3.12-alpine` looks great until pip tries to build a wheel and there's no
glibc. You end up `apk add build-base` and the image balloons, plus musl causes
weird runtime bugs. `python:3.12-slim` (debian) is usually the safer small base
for Python. For a Go binary, `FROM scratch` or `distroless` is genuinely tiny.

Check what is actually big with:

```bash
docker history --no-trunc <image>
# or, nicer:
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  wagoodman/dive:latest <image>
```

## Volume pitfalls

- **Named volume vs bind mount.** Named volumes (`pgdata:/var/lib/postgresql/data`)
  are managed by docker and survive `down`. Bind mounts (`./data:/data`) map a
  host path and are what you want for editing config live.
- **A named volume masks the image's directory.** If the image seeded
  `/var/lib/postgresql/data` and you mount an empty named volume there, you get
  the empty volume, not the seeded data. This is why postgres "loses" its init.
- **Editing init.sql does nothing on restart.** Init scripts run only when the
  data dir is empty. `docker compose down -v` (note the `-v`) to wipe volumes.
- **macOS bind mounts are slow.** Going through the VM filesystem, a `node_modules`
  on a bind mount can be 10x slower. Use a named volume for deps and bind-mount
  only your source.

## `docker compose down` does not delete volumes

`down` removes containers and networks. Volumes stay. That's usually good
(your dev DB survives) and occasionally surprising. `down -v` removes them too.
I have typed `down` when I meant `down -v` more times than I care to admit.

## Healthchecks + depends_on

`depends_on` alone only waits for the container to *start*, not to be *ready*.
A postgres container is "started" seconds before it accepts connections. Use:

```yaml
depends_on:
  postgres:
    condition: service_healthy
```

with a `healthcheck` on the postgres service. Otherwise your app crash-loops on
first boot and you blame the app.

## Cleanup commands worth aliasing

```bash
docker system df                 # how much space docker is eating
docker system prune -af          # remove stopped containers, unused images
docker volume prune              # unused volumes (careful: this deletes data)
docker image prune -a            # dangling + unused images
```

I have recovered >30GB from `docker system prune -af` on a laptop more than once.
