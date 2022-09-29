# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import sys
from os.path import join, dirname
from os import makedirs

try:
    import pdoc
except ImportError:
    pdoc = None

ROOT_MODULES = ['sverchok.utils', 'sverchok.ui']

def recursive_htmls(mod, parent=None):
    yield mod, mod.url(relative_to=None), mod.html()
    for submod in mod.submodules():
        yield from recursive_htmls(submod, parent=mod)

def generate_api_documentation(root_directory):
    if pdoc is None:
        raise Exception("pdoc3 package is required in order to generate documentation")
    print("Parsing modules...")
    context = pdoc.Context()
    modules = [pdoc.Module(mod, context=context) for mod in ROOT_MODULES]
    pdoc.link_inheritance(context)
    for mod in modules:
        for mod, mod_url, mod_html in recursive_htmls(mod):
            makedirs(join(root_directory, dirname(mod_url)), exist_ok=True)
            print(f"Writing module {mod.name} => {mod_url} documentation...")
            with open(join(root_directory, mod_url), 'w') as f:
                f.write(mod_html)
    print("Done")

