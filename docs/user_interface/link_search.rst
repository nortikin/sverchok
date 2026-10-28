:orphan:

Socket-aware node search (experimental)
======================================

Drag a socket link and release over empty space in the main Sverchok node
editor. Search results identify a node, its operation (where supported), and
the exact socket that will be connected. Choosing a result creates and connects
the configured node at the drop location. Press Escape to cancel the search.

Dragging from an output searches inputs; dragging from an unconnected input
searches outputs. Existing connected-input link moves and Ctrl-drag retain
Blender's normal behavior. Normal connections to existing sockets still use
Blender's link operator, including its cable drawing and edge panning.

Expanded operations
-------------------

The initial adapters expose Scalar Math, Vector Math, Logic Functions,
Color Mix, and Component Analyzer (vertices, edges, faces and their operations).
Operation choices are read from the nodes' own RNA enums. Other available nodes
are indexed in their initial configuration without changes to their code.

Matching
--------

Exact socket types are ranked first. Generic list inputs accept other socket
types; for example, a vector output can connect to List Mask's data input.
A central set of name hints distinguishes Edges, Faces/Polygons, Mask, and
numeric parameters where possible. Known incompatible topology hints are
excluded. Some known directional type conversions are offered with lower
priority. Unknown names keep broader suggestions.

This is a metadata filter, not a guarantee that the data's nesting or contents
will satisfy a node. It does not read socket values, process trees, or propagate
semantic information through existing links. A generic output therefore remains
generic even if the upstream data represents edges.

Catalogue lifecycle
-------------------

The catalogue is generated automatically after enabling Sverchok, one node type
per timer tick, and held in memory. If a search starts before indexing finishes,
the status bar reports progress; Escape cancels that pending search. Normal node
creation and property callbacks run in temporary, non-processing trees; these
and any new helper groups are removed before returning to Blender's event loop.

The menu registry is checked when searching, so newly available node types
invalidate the catalogue. F3 > "Sverchok: Rebuild Socket Search Catalogue" forces
rebuilding. Opening a blend file also invalidates it. Nothing is written as a
persistent catalogue in the repository or in blend files.

Limitations of version 1
------------------------

* Main Sverchok trees only; nested group editing is not supported yet.
* Only initially available sockets are indexed for nodes without an adapter.
  Script-defined interfaces and configured group instances need separate support.
* Ctrl-drag is not intercepted. A connected input drag remains a disconnect/move.
* Created nodes are placed at the drop point; use G to move them afterwards.
* Unavailable dependencies are skipped. Indexing failures are logged and skipped.
* Native socket hit-testing briefly toggles socket selection. Blender can clear
  a previously selected output on the same node; links and node selection are
  preserved by the probe.

Implementation and checks
-------------------------

``ui/sv_link_search.py`` is loaded through Sverchok's existing UI-module discovery.
``utils/sv_link_search.py`` contains matching rules and operation adapters.
``tests/link_search_tests.py`` includes matching and Blender creation tests.
No existing node source file needs modification.
