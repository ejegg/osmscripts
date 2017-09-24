#!/usr/bin/python
from __future__ import print_function
import osmium
import shapely.wkb
import shapely.ops
import shapely.geometry
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
    node_index = -1
    nodes = {}
    way_index = -1

    def merge_building_parts(self, input_file, output_file):
        wm = BogotaReader()
        wm.apply_file(input_file)
        codigos = wm.buildingParts.keys()
        with open(output_file, "w") as fp:
            xml = OSMWriter(fp=fp)
            for k in codigos:
                shapely_shapes = []
                for part in wm.buildingParts[k]:
                    shapely_shape = shapely.wkb.loads(part['shape'], hex=True)
                    shapely_shapes.append(shapely_shape)
                    self.write_shape(
                        xml,
                        shapely_shape,
                        {
                            'building:part': 'yes',
                            'building:levels': part['levels'],
                            'ref:BOG:ConCodigo': k
                        }
                    )
                # write the full building out
                max_levels = max(map(
                    lambda part: part['levels'],
                    wm.buildingParts[k]
                ))
                summed = shapely.ops.cascaded_union(shapely_shapes)
                self.write_shape(
                    xml,
                    summed,
                    {
                        'building': 'yes',
                        'building:levels': max_levels,
                        'ref:BOG:ConCodigo': k
                    }
                )

            xml.close()

    def write_shape(self, xml, shape, tags):
        """ Write a shapely shape as an OSM way
        :type xml: OSMWriter
        :type shape: shapely.geometry.BaseGeometry
        :type tags: dict
        """
        node_ids = []

        if hasattr(shape, 'exterior'):
            coords = shape.exterior.coords
        elif hasattr(shape, 'boundary') and hasattr(shape.boundary, 'geoms'):
            first_exterior = shape.boundary.geoms[0]
            coords = first_exterior.coords
        else:
            raise RuntimeError(
                "Can't deal with shape type {0}".format(
                    type(shape)
                ))

        for point in coords:
            node_id = self.write_point(xml, point)
            node_ids.append(node_id)
        xml.way(self.way_index, tags, node_ids)
        self.way_index -= 1

    def write_point(self, xml, point):
        """ Write a point as an OSM node, avoiding duplication
        :type xml: OSMWriter
        :type point: float[]
        """
        key = "{0}|{1}".format(point[1], point[0])
        if key not in self.nodes:
            xml.node(self.node_index, point[1], point[0])
            self.nodes[key] = self.node_index
            self.node_index -= 1
        return self.nodes[key]


BogotaMerger().merge_building_parts(sys.argv[1], sys.argv[2])
