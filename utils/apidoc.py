# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
import traceback
"""
Tools to generate Sverchok API documentation in HTML format.

When this module is run from command line instead of being imported, it
provides command-line interface to generate documentation. Please run it with
`--help` command-line argument to see usage information.
"""

from os.path import join, dirname
from os import makedirs

from sverchok.utils.sv_logging import get_logger

try:
    import pdoc
except ImportError:
    pdoc = None

DEFAULT_MODULES = [
        'sverchok.data_structure',
        'sverchok.node_tree',
        'sverchok.dependencies',
        'sverchok.core',
        'sverchok.utils']

def recursive_htmls(mod, parent=None):
    """
    Recursively list python modules and their documentation in HTML format.

    Yields:
        tuples: (pdoc.Module object, HTML documentation)
    """
    yield mod, mod.url(relative_to=None), mod.html()
    for submod in mod.submodules():
        yield from recursive_htmls(submod, parent=mod)

def generate_api_documentation(root_directory, root_modules=None, logger=None):
    """
    Generate Python API documentation by use of pdoc3 package, in HTML format.

    Args:
        root_directory: root directory to write HTML files into - string.
        root_modules: list of module names to be documented. All submodules of
            these will be documented as well.
    """
    if pdoc is None:
        raise Exception("pdoc3 package is required in order to generate documentation")
    if logger is None:
        logger = get_logger()
    if not root_modules:
        root_modules = DEFAULT_MODULES
    logger.info(f"Start generating API documentation in {root_directory}")
    context = pdoc.Context()
    modules = [pdoc.Module(mod, context=context) for mod in root_modules]
    pdoc.link_inheritance(context)
    for mod in modules:
        for mod, mod_url, mod_html in recursive_htmls(mod):
            makedirs(join(root_directory, dirname(mod_url)), exist_ok=True)
            logger.info(f"Writing module documentation: {mod_url}")
            with open(join(root_directory, mod_url), 'w') as f:
                f.write(mod_html)
    logger.info("API documentation generation done.")

if __name__ == "__main__":
    import sys
    import argparse
    try:
        parser = argparse.ArgumentParser(description = "Generate Sverchok API documentation in HTML format")
        parser.add_argument('-o', '--output', metavar='DIRECTORY', default='./api_documentation', help="Path to output directory")
        parser.add_argument('-m', '--modules', nargs='*', metavar='SVERCHOK.MODULE', help="Module(s) or package(s) to be documented")

        argv = sys.argv
        argv = argv[argv.index("--")+1:]

        args = parser.parse_args(argv)
        generate_api_documentation(args.output, args.modules)
        sys.exit(0)
    except Exception as e:
        print(e)
        traceback.print_exc()
        sys.exit(1)

