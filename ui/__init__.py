from pathlib import Path


def module_names():
    """Returns module names in the ui folder"""
    for child in Path(__file__).parent.iterdir():
        if child.name.startswith('_'):
            continue
        if child.stem == 'nodeview_keymaps':
            continue
        if child.suffix == '.py':
            yield child.stem
    yield 'nodeview_keymaps'  # should be registered last
