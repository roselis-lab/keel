#!/bin/sh
# Build the database from the catalog, then run whatever command was passed.
# Both steps are idempotent, so restarts are safe.
set -e

alembic upgrade head
keel seed

exec "$@"
