"""
Verify that the modified index.yaml is parsed such that:
  - SvGroupTreeNode appears as a direct AddNode entry under the Group category.
  - The original SverchokGroupMenu is preserved as a nested CustomMenu (Group tools).

Run with:
    python experiments/test_group_in_index.py
"""
import os
import sys

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, repo_root)

from utils import yaml_parser  # type: ignore


def find_group_entry(data):
    for entry in data:
        if isinstance(entry, dict) and 'Group' in entry:
            return entry['Group']
    return None


def collect_strings_recursively(items):
    out = []
    if isinstance(items, list):
        for it in items:
            out.extend(collect_strings_recursively(it))
    elif isinstance(items, dict):
        for v in items.values():
            out.extend(collect_strings_recursively(v))
    elif isinstance(items, str):
        out.append(items)
    return out


def run(path):
    print(f"Checking {path}")
    data = yaml_parser.load(path)
    group = find_group_entry(data)
    assert group is not None, f"'Group' entry not found in {path}"
    flat = collect_strings_recursively(group)
    assert 'SvGroupTreeNode' in flat, (
        f"SvGroupTreeNode not found inside Group entry of {path}: {flat}")
    assert 'NODE_MT_SverchokGroupMenu' in flat, (
        f"NODE_MT_SverchokGroupMenu not preserved inside Group entry of {path}: {flat}")
    print(f"  OK: SvGroupTreeNode + NODE_MT_SverchokGroupMenu present")


if __name__ == '__main__':
    run(os.path.join(repo_root, 'index.yaml'))
    run(os.path.join(repo_root, 'menus', 'full_by_data_type.yaml'))
    run(os.path.join(repo_root, 'menus', 'full_by_operations.yaml'))
    print("All checks passed.")
