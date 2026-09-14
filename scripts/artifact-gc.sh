#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"
require_env
require_engine
compose run --rm worker-mock python -m museforge.maintenance "$@"
