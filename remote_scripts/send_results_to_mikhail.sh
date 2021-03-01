#!/usr/bin/env bash


#
# This script is meant to be run after hPIC simulations are complete on various
# LCPP boxes, on the boxes themselves.
#
# It searches the directory "hpic_results" (usually at location
# "~/mikhail-hpic-runs/hpis_results" for all files matching a preset list of
# file patterns (i.e. a preset list of patterns of hPIC output files) and scp's
# them to mikhail's machine.
#
# REQUIRED SETUP: this script requires the ability to SSH from an LCPP box to
# mikhail's Ubuntu desktop without a password. SSH access to mikhail's box
# requires a reverse ssh tunnel, which can be configured EACH time I ssh into
# an LCPP box by adding "RemoteForward" to the stanza for each LCPP box
# in mikhail's ~/.ssh/config (one stanza for each LCPP box should already
# exist):
#
# Host pc85
#    HostName lcpp-pc85.npre.illinois.edu
#    User pc85
#    RemoteForward 12345 localhost:22
#
# NEXT: the LCPP box must be configured to ssh to port 12345 instead of 22. On
# each LCPP box, add this to ~/.ssh/config:
#
# Host mikhail
#    Hostname localhost
#    User xerxes
#    Port 12345
#
# FINALLY: in order to ssh from an LCPP box into mikhail's box without a
# password, the LCPP box's public ssh key must be in mikhail's
# ~/.ssh/authorized_keys



FILE_PATTERNS_OF_INTEREST=(
*IEAD_sp0.dat
hpic.log
)

# destination on mikhail's box
DEST_DIR=/home/xerxes/npre/research/FNSF

for SimDir in hpic_results/*; do
    ssh mikhail "mkdir -p $DEST_DIR/$SimDir"
    for pattern in ${FILE_PATTERNS_OF_INTEREST[*]}; do
        scp $SimDir/$pattern mikhail:$DEST_DIR/$SimDir
    done
done
