"""
Simulate (without bpy) the parsing logic of `Category.from_config` from
sverchok/ui/nodeview_space_menu.py for the Group entry, to confirm that:

  - The Group entry parses to a Category whose draw_data contains an
    `AddNode('SvGroupTreeNode')` item.
  - The Group entry also contains a CustomMenu wrapping
    NODE_MT_SverchokGroupMenu (preserving existing UX).

The simulation is sufficient to demonstrate that the search infrastructure
(which iterates AddNode items returned by `walk_categories`) will now find
SvGroupTreeNode via search terms like "group", "monad", "sub tree".
"""
import os
import sys

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, repo_root)

from utils import yaml_parser  # type: ignore


# --- Tiny re-implementation of detection helpers from nodeview_space_menu --- #

def is_operator_config(elem):
    if not isinstance(elem, dict):
        return False
    inner = list(elem.values())[0]
    if not isinstance(inner, list):
        return False
    for prop in inner:
        if isinstance(prop, dict):
            prop_name = list(prop.keys())[0]
            if prop_name.lower() == 'operator':
                return True
    return False


def is_custom_menu_config(elem):
    if not isinstance(elem, dict):
        return False
    inner = list(elem.values())[0]
    if not isinstance(inner, list):
        return False
    for prop in inner:
        if isinstance(prop, dict):
            prop_name = list(prop.keys())[0]
            if prop_name.lower() == 'custom_menu':
                return True
    return False


def parse_category(name, conf):
    """Returns a list of (kind, value) describing parsed children."""
    parsed = []
    for elem in conf:
        if isinstance(elem, dict):
            if is_operator_config(elem):
                parsed.append(('Operator', list(elem.keys())[0]))
                continue
            if is_custom_menu_config(elem):
                # find the custom_menu name
                inner = list(elem.values())[0]
                menu_name = None
                for prop in inner:
                    if isinstance(prop, dict) and 'custom_menu' in prop:
                        menu_name = prop['custom_menu']
                        break
                parsed.append(('CustomMenu', menu_name))
                continue
            # nested sub-category
            sub_name = list(elem.keys())[0]
            sub_value = list(elem.values())[0]
            if isinstance(sub_value, list):
                parsed.append(('Category', (sub_name, parse_category(sub_name, sub_value))))
            elif isinstance(sub_value, str):
                # category property like icon_name, extra_menu — ignored here
                continue
        elif isinstance(elem, str):
            if all(c == '-' for c in elem):
                parsed.append(('Separator', None))
            else:
                parsed.append(('AddNode', elem))
    return parsed


def find_group_section(data):
    for entry in data:
        if isinstance(entry, dict) and 'Group' in entry:
            return entry['Group']
    return None


def walk_addnodes(parsed):
    for kind, value in parsed:
        if kind == 'AddNode':
            yield value
        elif kind == 'Category':
            _, sub_parsed = value
            yield from walk_addnodes(sub_parsed)


def run(path):
    print(f"Checking {path}")
    data = yaml_parser.load(path)
    section = find_group_section(data)
    assert section is not None, f"Group section missing in {path}"
    parsed = parse_category('Group', section)

    add_nodes = list(walk_addnodes(parsed))
    custom_menus = [v for k, v in parsed if k == 'CustomMenu']
    nested_custom_menus = [
        cm for k, v in parsed if k == 'Category'
        for ck, cm in v[1] if ck == 'CustomMenu'
    ]
    all_custom_menus = custom_menus + nested_custom_menus

    print(f"  AddNodes:     {add_nodes}")
    print(f"  CustomMenus:  {all_custom_menus}")

    assert 'SvGroupTreeNode' in add_nodes, (
        f"SvGroupTreeNode not registered as AddNode under Group: {parsed}")
    assert 'NODE_MT_SverchokGroupMenu' in all_custom_menus, (
        f"SverchokGroupMenu not preserved under Group: {parsed}")
    print("  OK")


if __name__ == '__main__':
    run(os.path.join(repo_root, 'index.yaml'))
    run(os.path.join(repo_root, 'menus', 'full_by_data_type.yaml'))
    run(os.path.join(repo_root, 'menus', 'full_by_operations.yaml'))
    print("All simulation checks passed.")
