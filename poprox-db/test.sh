export POPROX_DB_PASSWORD=$(cat db/password.txt)
export PG_PASSWORD=$(cat db/password.txt)
export POPROX_DB_PORT=5435
docker compose up -d
sleep 5
pytest
docker compose down
