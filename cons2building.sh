#!/bin/bash
# list all the ConCodigo (building code) values that only appear once
# in a key.value file for osmosis tag-transform
grep ConCodigo $1 | sort | uniq -u | sed -e "s/.*k='//" -e "s/' v='/./" -e "s/'.*//" > simpleConCodigos
# extract the ways with those building codes
osmosis --rx $1 --tf reject-relations --wkv keyValueListFile=simpleConCodigos --un --wx simpleBuildings.osm
# transform the ways into buildings, keeping the levels and the construction code
osmosis --rx simpleBuildings.osm --tt file=simpleTransform.xml --wx simpleBuildingsTransformed.xml
