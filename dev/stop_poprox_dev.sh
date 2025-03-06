# to use this file `source init_poprox_dev.sh`
# this can be called from any folder (adjust the path as needed when sourcing the file)
# you may find it useful to set up an alias.

script_dir="${0:A:h}"
pushd "$script_dir"

docker compose down

popd
