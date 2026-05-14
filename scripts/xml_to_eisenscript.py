
import sys
import argparse
from xml.etree import ElementTree

from sverchok.utils.modules.eisenscript.from_xml import xml_to_ast
from sverchok.utils.modules.eisenscript.serializer import ast_to_string

# Use only arguments which come after --
# ones which come earlier are intended for Blender itself, not for this script
argv = sys.argv
delimiter_idx = argv.index("--")
argv = argv[delimiter_idx+1:]

parser = argparse.ArgumentParser(description = "Translate Elfnor's Generative Art XML format to Eisenscript")
parser.add_argument('input', metavar="SCRIPT.XML", help = "Path to output XML file")
parser.add_argument('output', metavar="SCRIPT.ES", help = "Path to Eisenscript file")

args = parser.parse_args(argv)

with open(args.input) as inf:
    text = inf.read()
    xml = ElementTree.fromstring(text)
    prog = xml_to_ast(xml)
    with open(args.output, 'w') as outf:
        outf.write(ast_to_string(prog))

