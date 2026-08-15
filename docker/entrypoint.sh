#!/bin/sh
# The app builds its database from the catalog on first start
# (see keel.catalog.ensure_ready), so there is nothing to set up here.
set -e

exec "$@"
