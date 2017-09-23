#!/usr/bin/python
from __future__ import print_function
import osmium
import shapely.wkb
import shapely.ops
from pprint import pprint
import sys
from osmwriter import OSMWriter


wkbfab = osmium.geom.WKBFactory()


class BogotaReader(osmium.SimpleHandler):
    def __init__(self):
        osmium.SimpleHandler.__init__(self)
        self.buildingParts = {}

    def area(self, a):
        if 'ConCodigo' not in a.tags:
            return
        con_codigo = a.tags['ConCodigo']

        wkbshape = wkbfab.create_multipolygon(a)
        if con_codigo not in self.buildingParts:
            self.buildingParts[con_codigo] = []
        self.buildingParts[con_codigo].append({
            'shape': wkbshape,
            'levels': a.tags['ConNPisos'],
        })


class BogotaMerger:
    def merge_building_parts(self, input_file, output_file):
        wm = BogotaReader()
        wm.apply_file(input_file)
        codigos = wm.buildingParts.keys()
        nodeidx = -1
        with open(output_file, "w") as fp:
            xml = OSMWriter(fp=fp)
            for k in codigos:
                shapely_shapes = list(map(
                    lambda part: shapely.wkb.loads(part['shape'], hex=True),
                    wm.buildingParts[k]
                ))
                max_levels = max(map(
                    lambda part: part['levels'],
                    wm.buildingParts[k]
                ))
                summed = shapely.ops.cascaded_union(shapely_shapes)
                nodeids = []
                for point in summed.exterior.coords:
                    xml.node(nodeidx, point[1], point[0])
                    nodeids.append(nodeidx)
                    nodeidx -= 1
                # write the full building out
                xml.way(
                    -1,
                    {
                        'building': 'yes',
                        'levels': max_levels,
                        'ref:BOG:ConCodigo': k
                    },
                    nodeids
                )
            xml.close()


BogotaMerger().merge_building_parts(sys.argv[1], sys.argv[2])
