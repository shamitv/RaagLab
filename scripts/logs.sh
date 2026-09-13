#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"
require_env
require_engine
if [[ $# == 0 ]]; then
  compose logs --tail 200 api dispatcher worker-mock
elif [[ $# == 1 && "$1" =~ ^[[:xdigit:]]{8}-[[:xdigit:]]{4}-[[:xdigit:]]{4}-[[:xdigit:]]{4}-[[:xdigit:]]{12}$ ]]; then
  compose logs --no-color api dispatcher worker-mock | grep -F -- "$1" || {
    status=$?
    [[ $status == 1 ]] || exit "$status"
    echo 'No matching job logs. Generation is not delivered in foundation.'
  }
else
  fail 'Usage: bash scripts/logs.sh [job-uuid]'
fi
