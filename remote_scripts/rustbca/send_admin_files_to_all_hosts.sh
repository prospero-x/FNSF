#!/usr/bin/env bash

LCPP_HOSTS_FILE=lcpp_hosts.txt
# Ignore #-style comments and blank lines
lcpp_hosts=$(grep -Ev '^$|#.*' $LCPP_HOSTS_FILE)

# For each LCPP host, SCP all local scripts intended to be run on that host
# to that host. Destination dir must already exist on remote host.
#
# Example: ./send_files_to_all_hosts.sh mikhail-hpic-run


REMOTE_DEST_DIR="$1"

if [ -z $REMOTE_DEST_DIR ]; then
    echo usage: ./send_files_to_all_hosts.sh \<DESTINATION_DIRECTORY\>
    exit 1
fi

_SEND_TO_ALL=(
   #rustbca/launcher.sh
   #rustbca/send_results_to_mikhail.sh
   rustbca/check_status.sh
   #rustbca/find_missing.sh
)

for host in $lcpp_hosts; do
    # Send the Cargo.toml file with the host-specific path to the RustBCA
    # installation directory so we can run rustbca simulations from
    # wherever we want
    sed "s/LCPP_BOX_USERNAME/$host/g" rustbca/Cargo.toml.template > tmp.toml
    scp tmp.toml $host:$REMOTE_DEST_DIR/Cargo.toml
    rm tmp.toml

    for file in ${_SEND_TO_ALL[*]}; do
        scp $file $host:$REMOTE_DEST_DIR
    done
done

