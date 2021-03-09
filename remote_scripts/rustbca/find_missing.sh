#!/usr/bin/env bash

for simdir in SBE*/**; do
    if [ ! -f $simdir/sputtered.output ]; then
        echo $simdir
    fi
done
