#!/usr/bin/env bash

LCPP_HOSTS_FILE=lcpp_hosts.txt

#
# Execute command via SSH on all hosts in hosts.txt
#
# Example: $ ./run_cmd_on_all_hosts.sh cd mikhail-hpic-runs\;./check_status.sh

remote_command="$@"

# Ignore #-style comments and blank lines
lcpp_hosts=$(grep -Ev '^$|#.*' $LCPP_HOSTS_FILE)

for host in $lcpp_hosts; do
    ssh $host "$remote_command"
done
