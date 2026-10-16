#!/bin/sh
# Container entrypoint: apply pending database migrations, then run the
# container's command with it as PID 1.
#
# Deployed code and the database schema must never drift (e.g. Render running
# new code against an un-migrated Neon database); migrating here guarantees
# the schema matches the image before any request is served.
#
# Set RUN_MIGRATIONS=false to skip (the Compose `migrate` service does its own
# `alembic upgrade head` so backend containers can start migration-free).
set -e

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    echo "[entrypoint] alembic upgrade head"
    alembic upgrade head
fi

exec "$@"
