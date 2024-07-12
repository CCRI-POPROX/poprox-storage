. ../poprox-db/.env.prod
pg_dump -h $POPROX_DB_HOST --port $POPROX_DB_PORT --user $POPROX_DB_USER $POPROX_DB_NAME  --no-owner --exclude-table-data *account* --exclude-table-data clicks --exclude-table-data newsletters --exclude-table-data subscriptions --exclude-table-data expt_allocations > dump.sql
