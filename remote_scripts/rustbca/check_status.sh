#!/usr/bin/env bash

# Is rust running?
running_status=""
if [ ! -z "$(pgrep -f "rustBCA SBE")" ]; then
    running_status="(RustBCA currently running)"
fi

# Count the number of completed simulations (or running)
complete=$(find . -name sputtered.output | wc -l)
total_simulations=$(find . -name *input.toml | wc -l)

printf "$(whoami): $complete/$total_simulations running or complete $running_status\n"
