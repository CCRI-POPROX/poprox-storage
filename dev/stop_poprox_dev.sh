# to use this file `source init_poprox_dev.sh`
# this can be called from any folder (adjust the path as needed when sourcing the file)
# you may find it useful to set up an alias.

pushd "$(dirname "${BASH_SOURCE[0]}")"

docker compose down

popd
