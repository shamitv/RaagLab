#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"
[[ $# == 0 ]] || fail 'Usage: bash scripts/stop.sh'
require_env
require_engine
compose down
echo 'Stopped. Database, broker and artifact volumes are preserved.'
