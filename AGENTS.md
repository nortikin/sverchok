# Sverchok Developer Handover Document

## Project Overview

**Sverchok** is a powerful parametric geometry programming tool for Blender, enabling visual programming of geometry through nodes. It is an addon for Blender version 2.93 and above (currently tested with 5.1).

- **License**: GPL3
- **Current Version**: 1.4.0
- **Homepage**: https://nortikin.github.io/sverchok/
- **Documentation**: http://nortikin.github.io/sverchok/docs/main.html
- **GitHub**: https://github.com/nortikin/sverchok
- **Community**: Discord (https://discord.gg/pjHHhjJz8Z), Telegram (https://t.me/sverchok_3d)

## Technological Stack

- **Blender** (Python API - bpy)
- **Python** (3.x)
- **NumPy** (array operations)
- **Additional libraries**: scipy, geomdl, skimage, mcubes, circlify, cython, numba, numexpr, ezdxf, pyacvd, pySVCGAL, spyrrow, freecad

## Project Structure

**IMPORTANT**: Project, its root directory and its root module are called `sverchok`, not `sverzok` or anything else! Imports follow the pattern:
- `import sverchok.core` → `sverchok/core/__init__.py`
- `import sverchok.utils.curve.core` → `sverchok/utils/curve/core.py`
- `import sverchok.nodes.geometry.mesh` → `sverchok/nodes/geometry/mesh.py`

### Directory Organization

| Directory | Purpose |
|-----------|---------|
| `core/` | Core infrastructure: node tree, update system, sockets, handlers, events, group update system |
| `nodes/` | Node implementations organized by category (geometry, modifier, generator, etc.) |
| `old_nodes/` | Legacy nodes (deprecated but maintained for compatibility) |
| `utils/` | Utility modules: math, geometry, file I/O, visualization, testing helpers |
| `ui/` | User interface components: panels, menus, icons, theme management |
| `docs/` | Sphinx documentation sources and configuration |
| `tests/` | Automated test suites for various components |
| `menus/` | Menu presets and configurations (YAML format) |
| `presets/` | Node tree presets |
| `scripts/` | Build scripts and utilities |
| `profile_examples/` | Profile examples for testing |

### Key Files

| File | Purpose |
|------|---------|
| `__init__.py` | Main addon initialization, registration, version info |
| `node_tree.py` | Core node tree definitions |
| `data_structure.py` | Core data structures for Sverchok |
| `settings.py` | Add-on preferences and settings |
| `dependencies.py` | External library dependencies management |

## Core Architecture

### Module Loading

The addon uses a sophisticated module loading system:

1. **Root modules**: `dependencies`, `data_structure`, `node_tree`, `core`, `utils`, `ui`, `nodes`, `old_nodes`
2. **Core modules**: `sv_custom_exceptions`, `update_system`, `sockets`, `socket_data`, `handlers`, `events`, `node_group`, `tasks`, `group_update_system`, `event_system`

The `core/__init__.py` file contains the `init_architecture()` function that orchestrates module initialization.

### Registration System

Node modules are automatically discovered and registered in `nodes/__init__.py` via `automatic_collection()` which walks the directory tree.

### Node Categories

Nodes are organized into categories: geometry, modifier_change, modifier_make, generator, list, matrix, vector, scalar, scene, surface, curve, solid, text, old_nodes, special, spatial, sv_script.

## Development Guidelines

### Code Conventions

1. **Comments**: All comments must be in English
2. **Documentation**: Use docstrings for all functions and classes
3. **Error handling**: Use Sverchok's custom exceptions from `sv_custom_exceptions.py`
4. **Testing**: Write tests for new functionality

### Floating Point Precision

**CRITICAL**: Always account for floating point precision issues:
- Don't test for exact equality: `if x == 0.5` ❌
- Use tolerance-based comparisons: `if abs(x - 0.5) < tolerance` ✅

### Testing

```bash
# Run all tests
./run_tests.sh

# Run specific test module
./run_tests.sh test_module_name
```

Tests are located in the `tests/` directory. The testing framework uses `SverchokTestCase` from `sverchok.utils.testing`.

### Dependencies

See the [Dependencies wiki page](https://github.com/nortikin/sverchok/wiki/Dependencies) for installation instructions.

## Key Development Areas

### Core Components

1. **Update System** (`core/update_system.py`) - Controls node tree evaluation and updates
2. **Socket System** (`core/sockets.py`) - Data type definitions and conversions
3. **Event System** (`core/event_system.py`) - Handles Blender events and callbacks
4. **Group Update System** (`core/group_update_system.py`) - Manages node group updates

### Utility Modules

1. **Math & Geometry** (`utils/math.py`, `utils/geom.py`, `utils/linalg.py`)
2. **File I/O** (`utils/sv_json_import.py`, `utils/sv_json_export.py`, `utils/dxf.py`, `utils/svg.py`)
3. **Visualization** (`utils/sv_viewer_utils.py`, `utils/visualize_data_tree.py`)
4. **BMesh Operations** (`utils/sv_bmesh_utils.py`, `utils/blender_mesh.py`)
5. **NURBS** (`utils/nurbs_common.py`, `utils/sv_curve_utils.py`, `utils/curve/`)

### NURBS Architecture

Sverchok implements NURBS curve operations with support for two backends:

- **`SvGeomdlCurve`** (`utils/curve/nurbs.py`): Wrapper around the external `geomdl` library
- **`SvNativeNurbsCurve`** (`utils/curve/nurbs.py`): Native implementation with full control over operations

**Key Files:**
- `utils/curve/nurbs.py` - Core NURBS operations: knot insertion/removal, degree elevation, basis functions
- `utils/curve/knotvector.py` - Knot vector generation and validation
- `utils/curve/nurbs_solver.py` - NURBS curve fitting solver
- `utils/nurbs_common.py` - Common utilities and exceptions (`CantInsertKnotException`, `CantRemoveKnotException`)

**NURBS Features:**
- Support for both clamped (endpoint-fixed) and unclamped (free) curves
- Rational curves with weight support
- Knot insertion and removal with configurable tolerance
- Cumulative error tracking for multiple knot operations
- `if_possible=True/False` parameters for flexible error handling

**Testing:**
Comprehensive test suites in `tests/nurbs_tests.py` and `tests/nurbs_solver_tests.py`.

### UI Components

1. **Panels** (`ui/sv_panels.py`, `ui/sv_3d_panel.py`)
2. **Menus** (`ui/sv_extra_search.py`, `ui/nodeview_rclick_menu.py`)
3. **Icons** (`ui/sv_icons.py`)
4. **Theme** (`ui/sv_theme_apply.py`)

## Important Notes

### Module Import Path

The project uses a non-standard structure where the root directory IS the module:
```python
import sverchok.core        # → sverchok/core/__init__.py
import sverchok.utils.math  # → sverchok/utils/math.py
```

### Reload Event

Sverchok supports hot-reloading during development:
```python
reload_event = "import_sverchok" in locals()
```

### Logging

Configurable in preferences via `settings.py` - `SverchokPreferences` class:
- Log levels: DEBUG, INFO, WARNING, ERROR
- Log destinations: Buffer, file, console

### Theme System

Sverchok supports multiple themes (Default, Nipon Blossom, Grey, Darker, Gruvbox Light/Dark) with automatic application and custom color customization.

## Common Development Tasks

### Adding a New Node

1. Create a Python file in the appropriate category under `nodes/`
2. Implement the node class inheriting from `SverchokNode`
3. Define `sv_icon`, `bl_idname`, `bl_label`, `bl_description`
4. Implement `sv_get_inputs()`, `process_node()`, `sv_get_outputs()`
5. Nodes are auto-discovered via `automatic_collection()`

### Debugging

1. Enable debug logging in preferences
2. Use Blender's text editor to view logs
3. Check `pylint_errors.log` and `tests.log` for issues
4. Use `sv_stethoscope_helper.py` for socket data inspection

## Testing Framework

Tests use `SverchokTestCase` from `sverchok.utils.testing` providing:
- Temporary node tree context manager
- Data structure testing utilities
- Exception handling with Sverchok custom exceptions
- Logging utilities specific to testing

## Release Process

1. Update version in `__init__.py` (`bl_info` and `VERSION`)
2. Add changelog entry in `CHANGELOG.md`
3. Test with latest Blender version
4. Update documentation
5. Create release archive

## Contact and Support

- **Email**: sverchok-b3d@yandex.ru
- **GitHub Issues**: https://github.com/nortikin/sverchok/issues
- **Stack Exchange**: https://blender.stackexchange.com/questions/tagged/sverchok
- **Discord**: https://discord.gg/pjHHhjJz8Z
- **Telegram**: https://t.me/sverchok_3d

## Contributors

See GitHub contributors page. Major contributors include:
- Alexander Nedovizin (Cfyzzz)
- Nikita Gorodetskiy (Nikitron)
- Linus Yng (Ly29)
- Ilya Portnov (portnov)
- Eleanor Howick (elfnor)
- Deaglan McArdle (zeffii)
- Konstantin Vorobiew (Kosvor)

## Legacy Nodes

The `old_nodes/` directory contains deprecated nodes maintained for backward compatibility. When refactoring:
1. Keep old nodes functional
2. Create new versions in `nodes/` directory
3. Mark old nodes as deprecated in documentation

## Performance Considerations

1. Use NumPy vectorization where possible
2. Consider Numba JIT compilation for CPU-intensive operations
3. Use profiling tools to identify bottlenecks
4. Be mindful of memory usage with large datasets

## Documentation

Documentation is built using Sphinx (`docs/` directory, `./build_docs.sh`). Node documentation is auto-generated from docstrings.

## Git Workflow

- Main branch: `master`
- Issue tracking via GitHub
- Pull requests for contributions
- Continuous integration via GitHub Actions

## Troubleshooting

### Common Issues

1. **NameError: name 'nodes' is not defined** → Restart Blender
2. **Module not found errors** → Check PYTHONPATH and module structure
3. **Floating point precision issues** → Use tolerance-based comparisons
4. **Theme not applying** → Check theme settings and auto-apply preferences
5. **Node updates not happening** → Check update system and frame change mode

Enable developer mode in preferences for additional debugging tools.

---

*This document should be kept up to date as the project evolves.*
