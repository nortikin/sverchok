# you may supply a list of `directory/node_name.py` to ignore
# this is about the only manual thing in this file.
import os
from os.path import dirname
from os.path import basename
from collections import defaultdict

ignore_list = {}
ignore_list['analyzer'] = ['bvh_raycast', 'bvh_overlap', 'bvh_nearest']
ignore_list['basic_data'] = ['create_bvh_tree']

nodes_dict = defaultdict(list)

# def path_iterator(path_name):
#     for fp in os.listdir(path_name):
#         if fp.lower().endswith(".py"):
#             if not fp == '__init__.py':
#                 yield fp

directory = dirname(__file__)
# for i in path_iterator(directory):
#     print(i)
def automatic_collection():
    for subdir, dirs, files in os.walk(directory):
        current_dir = basename(subdir)
        if current_dir == '__pycache__':
            continue
        for file in files:
            if file == '__init__.py':
                continue
            if file.endswith('dict'):
                continue
            nodes_dict[current_dir].append(file[:-3])

    # may not be used, but can be.
    return nodes_dict

automatic_collection()