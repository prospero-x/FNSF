#!/usr/bin/env bash

# This script is meant to be run DURING hPIC simulations, ON LCPP boxes, in order
# to see which hPIC simulations are complete and which ones are still running.
# It's meant to be a more accurate representation than "$ htop" or
# "$ ps -ef | grep hpic | grep <MY_SIMULATION_PATTERNS>".
#
# It assumes that, before a particular hPIC simulation, a file named
# "simulation-start" was created in the particular hPIC simualtion subdirectory,
# containing a single line date time string in the format %Y-%m-%dT%H:%S-%Z.
# Similarlty, it assumes that ones an hPIC simulation is complete, a similar
# file named "simulation-complete" is created.


for SimID in hpic_results/*
do
    start=$(cat $SimID/simulation-start)
    end=$(cat $SimID/simulation-complete)
    python3 -c '''
import sys
from datetime import datetime

DEFAULT_DATE = datetime(1970,1,1,0,0,0)
start = end = DEFAULT_DATE

SimID = sys.argv[1].split("hpic_results/")[1]
if len(sys.argv) < 3:
    print(f"{SimID:35} not started!")
    sys.exit(0)

start = datetime.strptime(sys.argv[2], "%Y-%m-%dT%H:%M:%S-%Z")
if len(sys.argv) < 4:
    print(f"{SimID:35} still running")
    sys.exit(0)

end = datetime.strptime(sys.argv[3], "%Y-%m-%dT%H:%M:%S-%Z")

# Maybe the previous hPIC run failed, in which case "simulation-complete"
# MIGHT exist, but with a stale timestemp.
if end > start:
    print(f"{SimID:35} done (took {end - start})")
else:
    print(f"{SimID:35} still running")''' $SimID $start $end
 done

