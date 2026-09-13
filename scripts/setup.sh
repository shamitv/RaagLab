#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"
if [[ ! -e .env ]]; then
  (umask 077; set -o noclobber; cat .env.example > .env)
  echo 'Created .env with local development defaults.'
else
  echo 'Preserved existing .env.'
fi
require_engine
compose config --quiet
echo 'Prerequisites ready. Start with: bash scripts/start.sh mock'
