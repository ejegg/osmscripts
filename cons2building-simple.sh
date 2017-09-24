#!/bin/bash
workdir=$(mktemp -d "${TMPDIR:-/tmp/}$(basename $0).XXXXXXXXXXXX")
# list all the ConCodigo (building code) values that only appear once
# in a key.value file for osmosis tag-transform
grep ConCodigo $1 | sort | uniq -u | sed -e "s/.*k='//" -e "s/' v='/./" -e "s/'.*//" > "$workdir/simpleConCodigos"
# extract the ways with those building codes
osmosis --rx $1 --tf reject-relations --wkv keyValueListFile="$workdir/simpleConCodigos" --un --wx "$workdir/simpleWays.osm"
# transform the ways into buildings, keeping the levels and the construction code
osmosis --rx "$workdir/simpleWays.osm" --tt file=simpleTransform.xml --wx -
#rm -r $workdir
