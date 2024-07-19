# to use this file `source init_poprox_dev.sh`
# this can be called from any folder (adjust the path as needed when sourcing the file)
# you may find it useful to set up an alias.

pushd "$(dirname "${BASH_SOURCE[0]}")"

export POPROX_DB_PASSWORD=$(cat db/password.txt)
export PG_PASSWORD=$(cat db/password.txt)
export POPROX_DB_USER='postgres'
export POPROX_DB_HOST='127.0.0.1'
export POPROX_DB_PORT='5433'
export POPROX_DB_NAME='poprox'

docker compose up -d --wait

sleep 60

cd ../poprox-db
alembic upgrade heads

# TODO: add dummy data to alembic

popd
