#!/usr/bin/env bash

DATA_DIR=solps_data

function format_data_files {

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

	sed  's/  \+/,/g' $rawdatafile | cut -c2- > $DATA_DIR/formatted/$datalabel.csv
}

rawdatafile=$1
datalabel=$(echo $1 | awk 'BEGIN{FS="/"} {print $NF}' | cut -d. -f1)

if [ $# -eq 0 ]; then
	echo usage: format_data_file.sh \<RAW_DATAFILE\>
	exit -1
fi

mkdir -p $DATA_DIR/formatted

format_data_files $rawdatafile $datalabel
