#!/usr/bin/env bash

LCPP_HOSTS_FILE=lcpp_hosts.txt
# Ignore #-style comments and blank lines
lcpp_hosts=$(grep -Ev '^$|#.*' $LCPP_HOSTS_FILE)

# For each LCPP host, SCP all local scripts intended to be run on that host
# to that host. Destination dir must already exist on remote host.
#
# Example: ./send_files_to_all_hosts.sh mikhail-hpic-run


REMOTE_DEST_DIR="$1"

_SEND_TO_ALL=(
    check_status.sh
    send_results_to_mikhail.sh
)

for host in $lcpp_hosts; do
    scp generated/*$host.sh $host:$REMOTE_DEST_DIR
    for file in ${_SEND_TO_ALL[*]}; do
        scp $file $host:$REMOTE_DEST_DIR
    done
done

