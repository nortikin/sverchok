
import sys
import argparse

from sverchok.utils.modules.eisenscript.to_xml import eisenscript_to_xml, xml_to_string

# Use only arguments which come after --
# ones which come earlier are intended for Blender itself, not for this script
argv = sys.argv
delimiter_idx = argv.index("--")
argv = argv[delimiter_idx+1:]

parser = argparse.ArgumentParser(description = "Translate Eisenscript to Elfnor's Generative Art XML format")
parser.add_argument('script', metavar="SCRIPT.ES", help = "Path to Eisenscript file")
parser.add_argument('output', metavar="SCRIPT.XML", help = "Path to output XML file")

args = parser.parse_args(argv)

eisencsript_path = args.script

with open(args.script) as inf:
    text = inf.read()
    xml = eisenscript_to_xml(text)
    with open(args.output, 'w') as outf:
        outf.write(xml_to_string(xml))
