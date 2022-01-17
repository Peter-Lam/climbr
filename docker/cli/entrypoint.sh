#!/bin/bash
# A startup script for the climbr cli container 
echo "Starting container: climbr_cli"
# poetry config virtualenvs.create false
poetry install --no-interaction --no-ansi
tail -f /workspace/logs/cli/climbr.log
echo "Container sucefully started: climbr_cli"
