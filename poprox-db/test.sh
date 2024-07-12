export POPROX_DB_PASSWORD=`cat db/password.txt`
export PG_PASSWORD=`cat db/password.txt`
docker compose up -d
sleep 5
pytest
docker compose down
