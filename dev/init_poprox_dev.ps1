# to use this file `.\init_poprox_dev.ps1`
# this can be called from any folder (adjust the path as needed when sourcing the file)
# you may find it useful to set up an alias.

# Save the current directory and navigate to the script's directory
Push-Location -Path (Split-Path -Path $MyInvocation.MyCommand.Definition -Parent)

# Read database passwords
$global:POPROX_DB_PASSWORD = Get-Content -Path "db\password.txt"
$global:PG_PASSWORD = Get-Content -Path "db\password.txt"
$global:POPROX_DB_USER = 'postgres'
$global:POPROX_DB_HOST = '127.0.0.1'
$global:POPROX_DB_PORT = '5433'
$global:POPROX_DB_NAME = 'poprox'

# Start Docker containers
docker compose up -d --wait

# Move to the `poprox-db` folder
Set-Location -Path "../poprox-db"

# Run Alembic migrations
alembic upgrade heads

# TODO: add dummy data to alembic

# Return to the original directory
Pop-Location
