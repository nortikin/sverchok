"""
Reproduce the logic of `tests/ui_tests.py::UiTests::test_full_menu_presets`
without Blender to confirm the node sets are consistent across:
  - index.yaml
  - menus/full_by_data_type.yaml
  - menus/full_by_operations.yaml
"""
import os
import sys

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, repo_root)

from utils import yaml_parser  # type: ignore


def _load_node_names_from_menu(menu_path):
    def search_in_list(data):
        for item in data:
            if isinstance(item, str) and item != '---':
                yield item
            elif isinstance(item, dict):
                yield from search_in_dict(item)

    def search_in_dict(data):
        for key, value in data.items():
            if key in {'icon_name', 'extra_menu', 'operator', 'custom_menu'}:
                continue
            if isinstance(value, list):
                yield from search_in_list(value)

    def search_node_names(menu):
        for item in menu:
            if isinstance(item, dict):
                yield from search_in_dict(item)
            elif isinstance(item, list):
                yield from search_in_list(item)

    menu = yaml_parser.load(menu_path)
    return set(search_node_names(menu))


index_nodes = _load_node_names_from_menu(os.path.join(repo_root, 'index.yaml'))
data_type_nodes = _load_node_names_from_menu(os.path.join(repo_root, 'menus', 'full_by_data_type.yaml'))
operations_nodes = _load_node_names_from_menu(os.path.join(repo_root, 'menus', 'full_by_operations.yaml'))

print(f"index.yaml node count: {len(index_nodes)}")
print(f"full_by_data_type.yaml node count: {len(data_type_nodes)}")
print(f"full_by_operations.yaml node count: {len(operations_nodes)}")

print(f"\nSvGroupTreeNode in index.yaml: {'SvGroupTreeNode' in index_nodes}")
print(f"SvGroupTreeNode in full_by_data_type.yaml: {'SvGroupTreeNode' in data_type_nodes}")
print(f"SvGroupTreeNode in full_by_operations.yaml: {'SvGroupTreeNode' in operations_nodes}")

assert index_nodes == data_type_nodes, (
    f"index.yaml != full_by_data_type.yaml\n"
    f"only-in-index: {index_nodes - data_type_nodes}\n"
    f"only-in-data-type: {data_type_nodes - index_nodes}")
assert index_nodes == operations_nodes, (
    f"index.yaml != full_by_operations.yaml\n"
    f"only-in-index: {index_nodes - operations_nodes}\n"
    f"only-in-operations: {operations_nodes - index_nodes}")
assert 'SvGroupTreeNode' in index_nodes, "SvGroupTreeNode not registered in index.yaml"
print("\nAll preset-consistency checks passed.")
