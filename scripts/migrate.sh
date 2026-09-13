#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"
require_env
require_engine
compose up -d --wait db
compose run --rm --build migrate
