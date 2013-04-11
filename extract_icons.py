#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import collections
import json
import os
import re

import lxml.cssselect
import lxml.etree


NS = {
    'svg': 'http://www.w3.org/2000/svg'
}
SVG_DOCTYPE = '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">'


parser = argparse.ArgumentParser()
parser.add_argument('svg_source',
                    help="The glyphicons.svg file to extract the icons from")
parser.add_argument('bounding_boxes',
                    help="A JSON file with bounding box values for each glyphicon (generated by get_bounding_boxes.js)")
parser.add_argument('extraction_dir',
                    help="The directory to which icons should be extracted")


def make_pretty_id_mapping(glyphicons):
    # First pass is a simple 'prettification', but this is not guaranteed to give unique results.
    def prettify_id(g_id):
        pretty_id = g_id.lower().replace('_x34_', '4').replace('_x5f_', '-').replace('_', ' ').strip()
        terminating_number_match = re.search(r'[ \-]*([\d]+)$', pretty_id)
        if terminating_number_match:
            pretty_id = pretty_id[:terminating_number_match.start()]
        return pretty_id
    pretty_ids = dict((x.attrib['id'], prettify_id(x.attrib['id'])) for x in glyphicons)

    # Then we just disambiguate between g_ids that prettify to the same pretty_id.
    unambig_pretty_ids = pretty_ids.copy()
    pretty_id_counters = collections.defaultdict(int)
    for g_id, pretty_id in pretty_ids.items():
        if pretty_id_counters[pretty_id] != 0:
            unambig_pretty_ids[g_id] = '%s-%d' % (pretty_id, pretty_id_counters[pretty_id])
        pretty_id_counters[pretty_id] += 1
    return unambig_pretty_ids


def main():
    args = parser.parse_args()
    with open(args.svg_source) as source_file:
        svg = lxml.etree.parse(source_file)
    if not os.path.isdir(args.extraction_dir):
        os.makedirs(args.extraction_dir)
    with open(args.bounding_boxes) as bbox_file:
        bounding_boxes = dict(json.load(bbox_file))

    glyphicons = lxml.cssselect.CSSSelector('svg|g#glyphicons > svg|g',
                                            namespaces=NS)(svg)

    pretty_ids = make_pretty_id_mapping(glyphicons)
    get_root_clone = lambda: lxml.etree.Element('svg',
                                                attrib=svg.getroot().attrib,
                                                nsmap=svg.getroot().nsmap)

    for glyphicon in glyphicons:
        pretty_id = pretty_ids[glyphicon.attrib['id']]
        bbox = bounding_boxes[glyphicon.attrib['id']]
        svg_root = get_root_clone()
        del svg_root.attrib['viewBox']
        del svg_root.attrib['enable-background']
        svg_root.attrib['width'] = repr(bbox['width'])
        svg_root.attrib['height'] = repr(bbox['height'])
        glyphicon.attrib['transform'] = 'translate(-%r,-%r)' % (bbox['x'], bbox['y'])
        svg_root.append(glyphicon)
        doc = lxml.etree.ElementTree(element=svg_root)
        doc_src = lxml.etree.tostring(doc, xml_declaration=True, doctype=SVG_DOCTYPE, encoding='utf-8')
        with open(os.path.join(args.extraction_dir, pretty_id + '.svg'), 'wb') as doc_fp:
            doc_fp.write(doc_src)


if __name__ == '__main__':
    main()