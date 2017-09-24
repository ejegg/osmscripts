#!/bin/bash
workdir=$(mktemp -d "${TMPDIR:-/tmp/}$(basename $0).XXXXXXXXXXXX")
osmosis --rx $1 --tf reject-relations --un --tt addArea.xml --wx "$workdir/norelation.osm"
cat "$workdir/norelation.osm" | ./invertIds.sed >> "$workdir/positiveparts.osm"
echo bogosm/merge_ways.py "$workdir/positiveparts.osm" $2
bogosm/merge_ways.py "$workdir/positiveparts.osm" $2
#rm -r $workdir
