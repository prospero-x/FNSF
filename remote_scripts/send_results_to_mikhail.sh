#!/usr/bin/env bash


#
# This script is meant to be run after hPIC simulations are complete on various
# LCPP boxes, on the boxes themselves.
#
# It searches the directory "hpic_results" (usually at location
# "~/mikhail-hpic-runs/hpis_results" for all files matching a preset list of file
# patterns (i.e. a preset list of patterns of hPIC output files) and scp's them
# to mikhail's machine.
#


FILE_PATTERNS_OF_INTEREST=(
*IEAD_sp0.dat
)

# destination on mikhail's box
DEST_DIR=/home/xerxes/npre/research/FNSF/hpic_results

for SimDir in hpic_results/*; do
    ssh mikhail "mkdir -p $DEST_DIR/$SimDir"

    for pattern in ${FILE_PATTERNS_OF_INTEREST[*]}; do
        scp $SimDir/$pattern mikhail:$DEST_DIR/$SimDir
    done
done
