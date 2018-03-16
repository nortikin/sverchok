# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import os
from pathlib import Path

from sverchok.utils.sv_update_utils import sv_get_local_path


def get_examples_paths():
    sv_path = os.path.dirname(sv_get_local_path()[0])
    paths = {}
    dataset_root = Path(sv_path)
    analyzer_path = dataset_root / 'json_examples'
    for listed_path in analyzer_path.iterdir():
        if listed_path.is_dir():
            paths[listed_path.name] = str(listed_path)

    return paths


examples_paths = get_examples_paths()
