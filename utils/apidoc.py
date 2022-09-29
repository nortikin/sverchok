# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import sys
from os.path import join, dirname
from os import makedirs

from sverchok.utils.logging import getLogger

try:
    import pdoc
except ImportError:
    pdoc = None

ROOT_MODULES = ['sverchok.data_structure', 'sverchok.node_tree', 'sverchok.core', 'sverchok.utils', 'sverchok.ui']

def recursive_htmls(mod, parent=None):
    yield mod, mod.url(relative_to=None), mod.html()
    for submod in mod.submodules():
        yield from recursive_htmls(submod, parent=mod)

def generate_api_documentation(root_directory, logger=None):
    if pdoc is None:
        raise Exception("pdoc3 package is required in order to generate documentation")
    if logger is None:
        logger = getLogger()
    logger.info("Start generating API documentation")
    context = pdoc.Context()
    modules = [pdoc.Module(mod, context=context) for mod in ROOT_MODULES]
    pdoc.link_inheritance(context)
    for mod in modules:
        for mod, mod_url, mod_html in recursive_htmls(mod):
            makedirs(join(root_directory, dirname(mod_url)), exist_ok=True)
            logger.info(f"Writing module documentation: {mod_url}")
            with open(join(root_directory, mod_url), 'w') as f:
                f.write(mod_html)
    logger.info("API documentation generation done.")

if __name__ == "__main__":
    try:
        argv = sys.argv
        argv = argv[argv.index("--")+1:]
        if argv:
            output_directory = argv[0]
        else:
            output_directory = "./api_documentation"
        generate_api_documentation(output_directory)
        sys.exit(0)
    except Exception as e:
        print(e)
        sys.exit(1)
