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
    ways = {}
    relation_index = -1

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
        if hasattr(shape, 'geoms'):
            shape = shape.geoms[0]
        if len(shape.interiors) == 0:
            # simple case, just write a way
            self.write_way(xml, shape.exterior.coords, tags)
        else:
            # need to write a relation
            exterior_id = self.write_way(xml, shape.exterior.coords, {})
            members = [['way', exterior_id, 'outer']]
            for inner in shape.interiors:
                interior_id = self.write_way(xml, inner.coords, {})
                members.append(['way', interior_id, 'inner'])
            xml.relation(
                self.relation_index,
                tags,
                members
            )
            self.relation_index -= 1

    def write_way(self, xml, coords, tags):
        """
        :type xml: OSMWriter
        :type coords: float[][]
        :type tags: dict
        :return: int
        """
        node_ids = []
        for point in coords:
            node_id = self.write_point(xml, point)
            node_ids.append(node_id)
        node_ids = self.normalize_node_list(node_ids)
        key = ','.join(str(nid) for nid in node_ids)
        if key not in self.ways:
            xml.way(self.way_index, tags, node_ids)
            self.ways[key] = self.way_index
            self.way_index -= 1
        return self.ways[key]

    def write_point(self, xml, point):
        """
        Write a point as an OSM node, avoiding duplication
        :type xml: OSMWriter
        :type point: float[]
        :return int
        """
        key = "{0}|{1}".format(point[1], point[0])
        if key not in self.nodes:
            xml.node(self.node_index, point[1], point[0])
            self.nodes[key] = self.node_index
            self.node_index -= 1
        return self.nodes[key]

    @staticmethod
    def normalize_node_list(node_ids):
        """
        Normalize the node list so we don't repeat ways. Take the duplicated
        last id off the end, then rotate the list till it starts with the
        maximum id. Finally, restore the last element.
        """
        max_id = max(node_ids)
        if node_ids[0] == max_id:
            return node_ids
        node_ids = node_ids[0:-1]
        while node_ids[0] != max_id:
            node_ids.append(node_ids.pop(0))
        node_ids.append(node_ids[0])
        return node_ids


BogotaMerger().merge_building_parts(sys.argv[1], sys.argv[2])
