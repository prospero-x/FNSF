#!/usr/bin/env bash

DATA_DIR=solps_data

function clean_data {

	# The data sent by Jeremy has a strange format. We first
	# need to replace white spaces with columns, being careful
	# to only replace two or more white spaces, since some column
	# names contain a single white space. The result is close to
	# what we want, but it still contains either a column or a
	# space on the first character of every line, so we chop that off.

	# 
	# TODO: ask Jeremy to provide a CSV next time
	rawdatafile=$1
	datalabel=$2

	sed  's/  \+/,/g' $rawdatafile | cut -c2- > $DATA_DIR/cleaned/$datalabel.csv
}

rawdatafile=$1
datalabel=$(echo $1 | awk 'BEGIN{FS="/"} {print $NF}' | cut -d. -f1)

mkdir -p $DATADIR/cleaned

# Step 1: clean data
clean_data $rawdatafile $datalabel
