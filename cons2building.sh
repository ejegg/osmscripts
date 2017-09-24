#!/bin/bash
workdir=$(mktemp -d "${TMPDIR:-/tmp/}$(basename $0).XXXXXXXXXXXX")
osmosis --rx $1 --un --tt addArea.xml --wx "$workdir/witharea.osm"
cat "$workdir/witharea.osm" | ./invertIds.sed >> "$workdir/positiveparts.osm"
bogosm/merge_ways.py "$workdir/positiveparts.osm" $2
rm -r $workdir
