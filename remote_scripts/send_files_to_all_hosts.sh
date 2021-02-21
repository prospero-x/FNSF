#!/usr/bin/env bash

LCPP_HOSTS_FILE=lcpp_hosts.txt
# Ignore #-style comments and blank lines
lcpp_hosts=$(grep -Ev '^$|#.*' $LCPP_HOSTS_FILE)

# SCP all local files matching a pattern to each host in hosts.txt. Destination
# dir must already exist on remote host.
#
# Example: ./send_files_to_all_hosts.sh check_status.sh mikhail-hpic-run


LOCAL_SRC_PATTERN="$1"

REMOTE_DEST_DIR="$2"

for host in $lcpp_hosts; do
    scp $LOCAL_SRC_PATTERN $host:$REMOTE_DEST_DIR
done
