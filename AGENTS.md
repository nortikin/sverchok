# Sverchok Developer Handover Document

## Project Overview

**Sverchok** is a parametric geometry programming tool for Blender,
enabling visual programming of geometry through nodes.

- **License**: GPL3
- **Current Version**: 1.4.0
- **Blender**: Works with Blender 5.1; CI tests run on Blender 4.5
- **GitHub**: <https://github.com/nortikin/sverchok>

## Technological Stack

- **Blender** (Python API - `bpy`)
- **Python** (3.x)
- **NumPy** (array operations)
- **Additional libraries**: scipy, geomdl, skimage, mcubes, circlify,
  cython, numba, numexpr, ezdxf, pyacvd, pySVCGAL, spyrrow, freecad

## Required Knowledge

Analytical geometry, linear algebra, NURBS mathematics, and Blender
Python API.

## Project Structure

**IMPORTANT**: Project, root directory, and root module are called
`sverchok`, not `sverzok`! Imports follow the pattern:

- `import sverchok.core` → `sverchok/core/__init__.py`
- `import sverchok.utils.curve.core` → `sverchok/utils/curve/core.py`
- `import sverchok.nodes.geometry.mesh` →
  `sverchok/nodes/geometry/mesh.py`

### Directory Organization

| Directory           | Purpose                                                                                       |
|---------------------|-----------------------------------------------------------------------------------------------|
| `core/`             | Core infrastructure: node tree, update system, sockets, handlers, events, group update system |
| `nodes/`            | Node implementations organized by category (subdirectories)                                   |
| `old_nodes/`        | Legacy nodes (deprecated but maintained for compatibility)                                    |
| `utils/`            | Utility modules: math, geometry, file I/O, visualization, testing helpers                     |
| `ui/`               | User interface components: panels, menus, icons, theme management                             |
| `docs/`             | Sphinx documentation sources and configuration                                                |
| `tests/`            | Automated test suites for various components                                                  |
| `menus/`            | Menu presets and configurations (YAML format)                                                 |
| `presets/`          | Node tree presets                                                                             |
| `profile_examples/` | Profile examples for testing                                                                  |

### Key Files

| File                | Purpose                                                               |
|---------------------|-----------------------------------------------------------------------|
| `__init__.py`       | Main addon initialization, registration, version info                 |
| `node_tree.py`      | Core node tree definitions; defines `SverchCustomTreeNode` base class |
| `data_structure.py` | Core data structures for Sverchok                                     |
| `settings.py`       | Add-on preferences and settings (`SverchokPreferences`)               |
| `dependencies.py`   | External library dependencies management                              |

## Core Architecture

### Module Loading

The addon uses a sophisticated module loading system in
`core/__init__.py`:

1.  **Root modules**: `dependencies`, `data_structure`, `node_tree`,
    `core`, `utils`, `ui`, `nodes`, `old_nodes`
2.  **Core modules**: `sv_custom_exceptions`, `update_system`,
    `sockets`, `socket_data`, `handlers`, `events`, `node_group`,
    `tasks`, `group_update_system`, `event_system`, `socket_conversions`

The `core/__init__.py` file contains the `init_architecture()` function
that orchestrates module initialization.

### Registration System

Node modules are automatically discovered and registered in
`nodes/__init__.py` via `automatic_collection()` which walks the
directory tree. Each subdirectory under `nodes/` becomes a node
category.

### Node Categories

Actual categories (subdirectories under `nodes/`):

`analyzer`, `CAD`, `color`, `curve`, `dictionary`, `dxf`, `exchange`,
`generator`, `generators_extended`, `layout`, `list_main`, `list_masks`,
`list_mutators`, `list_struct`, `logic`, `matrix`, `modifier_change`,
`modifier_make`, `network`, `number`, `object_nodes`, `pulga_physics`,
`quaternion`, `scene`, `script`, `solid`, `spatial`, `surface`, `text`,
`transforms`, `vector`, `viz`, `old_nodes`

Solid nodes use `sv_category` for sub-categorization (e.g.,
`"Solid Operators"`, `"Solid Inputs"`, `"Solid Outputs"`).

## Node Development

### Node Class Template

Every node is a Python class inheriting from both `SverchCustomTreeNode`
and `bpy.types.Node`:

``` python
import bpy
from sverchok.node_tree import SverchCustomTreeNode

class SvMyNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: My Node
    Tooltip: Short description shown in node search
    """
    bl_idname = 'SvMyNode'
    bl_label = 'My Node'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SOME_ICON'       # Custom icon from sverchok icons
    sv_dependencies = {'scipy'}     # Set or list of required dependencies
```

### Sockets

Inputs and outputs are created in `sv_init(self, context)` via
`self.inputs.new(SocketClass, "Name")` and
`self.outputs.new(SocketClass, "Name")`.

**Common socket types:**

| Socket Class          | Purpose                                 |
|-----------------------|-----------------------------------------|
| `SvVerticesSocket`    | List of 3D vertices                     |
| `SvStringsSocket`     | Generic data (lists, integers, strings) |
| `SvMatrixSocket`      | Transformation matrices                 |
| `SvGeom2DSocket`      | 2D geometry (shapely)                   |
| `SvScalarFieldSocket` | Scalar field (SDF)                      |
| `SvVectorFieldSocket` | Vector field                            |

All custom sockets inherit from Blender’s `NodeSocket` via
`SvBaseSocket`.

### Data Processing & Data Flow

Sverchok uses a **batched data model**: data is always a **list of
lists** (or deeper nesting). Each outer list element = one “item” or
“batch”.

The `process_node(self)` method is the main entry point:

``` python
def process_node(self):
    # Check if any output is linked (early exit optimization)
    if not any(socket.is_linked for socket in self.outputs):
        return

    # Get input data — returns list of lists (batched)
    data_s = self.inputs['Data'].sv_get()

    # Use zip_long_repeat for parallel iteration over multiple inputs
    for data in zip_long_repeat(data_s, other_s):
        # ... process ...
        pass

    # Set output data
    self.outputs['Output'].sv_set(result)
```

**Key data utilities** (from `sverchok.data_structure`):

| Function                 | Purpose                                                   |
|--------------------------|-----------------------------------------------------------|
| `zip_long_repeat()`      | Parallel iteration; repeats last element of shorter lists |
| `ensure_nesting_level()` | Normalizes data nesting depth                             |
| `fullList()`             | Extends short lists to match a reference length           |

### Properties & UI

Use `bpy.props` for node parameters:

``` python
my_property : IntProperty(
    name="My Property",
    default=10,
    min=1,
    update=updateNode)
```

Draw buttons in the node panel:

``` python
def draw_buttons(self, context, layout):
    layout.prop(self, "my_property")

def draw_buttons_ext(self, context, layout):
    self.draw_buttons(context, layout)
    # Additional properties for the full panel
```

### Adding a New Node

1.  **Create the module**: `nodes/<category>/<name>.py`
2.  **Define the node class** — see Node Class Template above
3.  **Declare dependencies** via `sv_dependencies` if needed
4.  **Implement `sv_init()`, `process_node()`, and any UI methods**
5.  **Register/unregister** the class (or use
    `register_classes_factory`)
6.  **Add tests** in `tests/`
7.  Ensure the module is imported in the category’s `__init__.py`

Nodes are auto-discovered via `automatic_collection()` in
`nodes/__init__.py`.

## Development Practices

### Coding Conventions

1.  **Comments**: All comments must be in English
2.  **Documentation**: Use docstrings for all functions and classes
    (`Triggers:` for search, `Tooltip:` for hover)
3.  **Error handling**: Use Sverchok’s custom exceptions from
    `core/sv_custom_exceptions.py`
4.  **Testing**: Write tests for new functionality
5.  **Type hints**: Use where helpful
6.  **Focus**: Keep node classes focused — complex algorithms belong in
    `utils/`
7.  **License header**: Include the Sverchok GPL3 license header in new
    files
8.  **Icons**: Use `sv_icon` for custom icons; fall back to `bl_icon`
    for standard icons

### Floating Point Precision

**CRITICAL**: Always account for floating point precision issues:

- Don’t test for exact equality: `if x == 0.5` ❌
- Use tolerance-based comparisons: `if abs(x - 0.5) < tolerance` ✅

### Testing

``` bash
# Run all tests
./run_tests.sh

# Run specific test module
./run_tests.sh test_module_name
```

Tests are located in the `tests/` directory. The testing framework uses
`SverchokTestCase` from `sverchok.utils.testing`.

### Dependencies

See the [Dependencies wiki
page](https://github.com/nortikin/sverchok/wiki/Dependencies) for
installation instructions.

### Common Pitfalls

1.  **Missing dependency check**: Always check if a dependency is `None`
    before using it
2.  **Data nesting**: Use `ensure_nesting_level()` when input data may
    have varying nesting depths
3.  **Early exit**: Always check
    `any(socket.is_linked for socket in self.outputs)` at the start of
    `process_node()`
4.  **Socket naming**: Use descriptive socket names that match Sverchok
    conventions
5.  **Icon naming**: Custom icons use the pattern `sv_<name>.png` in the
    `ui/icons/` directory

## Key Development Areas

### Core Components

| File                           | Purpose                                   |
|--------------------------------|-------------------------------------------|
| `core/update_system.py`        | Controls node tree evaluation and updates |
| `core/sockets.py`              | Data type definitions and conversions     |
| `core/socket_conversions.py`   | Socket type conversion logic              |
| `core/socket_data.py`          | Socket data handling                      |
| `core/event_system.py`         | Handles Blender events and callbacks      |
| `core/group_update_system.py`  | Manages node group updates                |
| `core/node_group.py`           | Node group implementation                 |
| `core/handlers.py`             | Blender event handlers                    |
| `core/events.py`               | Event definitions                         |
| `core/tasks.py`                | Task management                           |
| `core/sv_custom_exceptions.py` | Custom exceptions                         |

### Utility Modules

| Category                    | Key Files                                                                                                                                                        |
|-----------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Math & Geometry**         | `utils/math.py`, `utils/geom.py`, `utils/linalg.py`, `utils/geom_2d/`                                                                                            |
| **Field-based generation**  | `utils/field/` (attractor, differential, frame_along_curve, image, probe, rbf, scalar, vector, vector_operations, vector_primitives, voronoi)                    |
| **NURBS**                   | `utils/curve/` (nurbs.py, knotvector.py, nurbs_solver.py, nurbs_algorithms.py, bezier.py, biarc.py, catmull_rom.py, splines.py, splprep.py, algorithms.py, etc.) |
| **NURBS Exceptions**        | `CantInsertKnotException`, `CantRemoveKnotException` in `utils/curve/nurbs.py`                                                                                   |
| **File I/O**                | `utils/sv_json_import.py`, `utils/sv_json_export.py`, `utils/dxf.py`, `utils/svg.py`, `utils/ifc.py`                                                             |
| **Visualization**           | `utils/sv_viewer_utils.py`, `utils/visualize_data_tree.py`                                                                                                       |
| **BMesh**                   | `utils/sv_bmesh_utils.py`, `utils/blender_mesh.py`                                                                                                               |
| **Other**                   | `utils/handle_blender_data.py`, `utils/listutils.py`, `utils/dictionary.py`, `utils/kdtree.py`, `utils/bvh_tree.py`, `utils/avl_tree.py`                         |
| **CAD / Exchange / Layout** | `utils/exchange/`, `utils/CAD/`, `utils/layout/`, `utils/network/`, `utils/pulga_physics_core.py`                                                                |

### NURBS Architecture

Sverchok implements NURBS curve operations with two backends (both
inherit from `SvNurbsCurve` in `utils/curve/nurbs.py`):

- **`SvGeomdlCurve`** — Wrapper around the external `geomdl` library
- **`SvNativeNurbsCurve`** — Native implementation with full control
  over operations

**Features:**

- Support for both clamped (endpoint-fixed) and unclamped (free) curves
- Rational curves with weight support
- Knot insertion and removal with configurable tolerance
- Cumulative error tracking for multiple knot operations
- `if_possible=True/False` parameters for flexible error handling

**Testing:** `tests/nurbs_tests.py` and `tests/nurbs_solver_tests.py`.

### UI Components

| File                           | Purpose                                                                                 |
|-------------------------------|------------------------------------------------------------------------------------------|
| `ui/sv_panels.py`             | Main UI panels                                                                           |
| `ui/sv_3d_panel.py`           | 3D view panel                                                                            |
| `ui/sv_extra_search.py`       | Node search                                                                              |
| `ui/nodeview_rclick_menu.py`  | Right-click menu                                                                         |
| `ui/sv_icons.py`              | Custom icons                                                                             |
| `ui/sv_theme_apply.py`        | Theme application                                                                        |
| `ui/bgl_callback_3dview.py`   | 3D view drawing                                                                          |
| `ui/bgl_callback_nodeview.py` | Node view drawing                                                                        |
| `ui/testing_panel.py`         | Testing utilities panel                                                                  |
| `ui/themes/`                  | Theme XML files (`Sverchok_light_3.xml`, `Sverchok_light_4.xml`, `Sverchok_light_5.xml`) |

## Important Notes

### Reload Event

Sverchok supports hot-reloading during development:

``` python
reload_event = "import_sverchok" in locals()
```

### Logging

Configurable in preferences via `settings.py` — `SverchokPreferences`
class:

- Log levels: DEBUG, INFO, WARNING, ERROR
- Log destinations: Buffer, file, console

### Theme System

Themes: `Sverchok_light_3`, `Sverchok_light_4`, `Sverchok_light_5` (per
Blender version). Themes are auto-applied. Custom colors can be set in
preferences.

## Legacy Nodes

The `old_nodes/` directory contains deprecated nodes maintained for
backward compatibility. When refactoring:

1.  Keep old nodes functional
2.  Create new versions in `nodes/` directory
3.  Mark old nodes as deprecated in documentation

## Documentation

Documentation is built using Sphinx (`docs/` directory,
`./build_docs.sh`).

## Quick Reference: Key Imports

``` python
# Always needed for nodes
import bpy
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, fullList

# For properties
from bpy.props import FloatProperty, IntProperty, EnumProperty, BoolProperty, StringProperty

# For math
import numpy as np
from mathutils import Matrix, Vector

# For testing
from sverchok.utils.testing import SverchokTestCase
```

