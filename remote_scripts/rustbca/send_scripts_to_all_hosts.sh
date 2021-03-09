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

cd ../rustbca_simulations
for host in $lcpp_hosts; do
    for input_file in $(find . -name *$host-input.toml); do
        SBE=$(echo $input_file | cut -d/ -f2)
        SimID=$(echo $input_file | cut -d/ -f3)
        if [ $input_file != "./SBE_1eV/outer_sop_plus_0.304m_from_spnNe+3/pc201-input.toml" ]; then
            continue
        fi
        ssh $host bash -c "'if [ -f $REMOTE_DEST_DIR/$SBE/$SimID ];then rm $REMOTE_DEST_DIR/$SBE/$SimID; fi'"
        ssh $host mkdir -p $REMOTE_DEST_DIR/$SBE/$SimID
        scp $input_file $host:$REMOTE_DEST_DIR/$SBE/$SimID
    done
done

