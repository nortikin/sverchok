:orphan:

Socket-aware node search
========================

Drag a socket link and release over empty space in a Sverchok node
editor, including while editing a nested group. Results identify the node, its operation where supported, and the exact
socket to connect. Choose a result to create and connect the configured node
at the drop location. Escape cancels the search.

Dragging from an output searches inputs; dragging from an unconnected input
searches outputs. Moving an existing input link retains Blender's normal
behavior. Normal direct connections use Blender's link operator, including
cable drawing and edge panning. Automatic search is enabled by default and can
be disabled with the ``Search on Link Drop`` preference. Manual search is also
available in the socket context menu.

`Watch: Create a Curve Mapper from an output <https://github.com/user-attachments/assets/3f230c0a-b7cf-4112-9708-731815be6126>`__

.. raw:: html

   <video controls preload="none" style="width: 100%; max-width: 960px;" aria-label="Create a Curve Mapper from an output">
     <source src="https://github.com/user-attachments/assets/3f230c0a-b7cf-4112-9708-731815be6126" type="video/mp4">
     <a href="https://github.com/user-attachments/assets/3f230c0a-b7cf-4112-9708-731815be6126">Watch the demonstration video.</a>
   </video>

`Watch: Create a number node by dragging backwards from an input <https://github.com/user-attachments/assets/0a5c3d28-f38e-49ea-bca8-779be15ad0a4>`__

.. raw:: html

   <video controls preload="none" style="width: 100%; max-width: 960px;" aria-label="Create a number node by dragging backwards from an input">
     <source src="https://github.com/user-attachments/assets/0a5c3d28-f38e-49ea-bca8-779be15ad0a4" type="video/mp4">
     <a href="https://github.com/user-attachments/assets/0a5c3d28-f38e-49ea-bca8-779be15ad0a4">Watch the demonstration video.</a>
   </video>

Preferences
-----------

Preferences > Add-ons > Sverchok > General > Other > ``Search on Link Drop``
changes automatic search immediately; save Blender preferences to retain it.
Manual ``Search and Connect...`` remains available from the socket menu.
Ctrl-drag and connected-input link moves keep Blender's normal behavior.
If any output socket is explicitly selected, automatic search defers to Blender
to preserve its read-only socket selection. Selecting nodes alone does not
disable automatic search.

New nodes and existing sockets
------------------------------

Normal queries search for new nodes. Start a query with ``<`` to search sockets
of existing nodes in the current tree. For example, ``bevel`` creates a Bevel
node, while ``<bevel`` searches existing instances. Tab switches modes without
discarding the query text. The footer identifies the current mode.

Existing results include the instance name and socket. Occupied inputs are
marked ``(Replace)``; selecting one explicitly replaces that input's connection.
Outputs can have several consumers, so a linked output is not a replacement.
Connections that would create a cycle are excluded. The chosen endpoint is
validated again before changing links. A changed/deleted endpoint is rejected.

`Watch: Use < to connect to an existing node <https://github.com/user-attachments/assets/2f383f0a-2c75-464a-bc27-d18d7aaf39cf>`__

.. raw:: html

   <video controls preload="none" style="width: 100%; max-width: 960px;" aria-label="Use &lt; to connect to an existing node">
     <source src="https://github.com/user-attachments/assets/2f383f0a-2c75-464a-bc27-d18d7aaf39cf" type="video/mp4">
     <a href="https://github.com/user-attachments/assets/2f383f0a-2c75-464a-bc27-d18d7aaf39cf">Watch the demonstration video.</a>
   </video>

Geometry bundles
----------------

For unambiguous geometry sockets, selecting Vertices, Edges or Polygons also
connects the other available channels shared by both nodes. Indicators such as
``V+E+P``, ``V+E`` and ``V+P`` show the planned bundle. This works in either
direction and when connecting existing nodes. Shift while confirming restricts
the operation to the selected socket.

Only the chosen input is replaced when marked ``(Replace)``. Occupied companion
inputs are preserved. A separate result marked ``(Replace V+E+P)`` (or the actual
available channels) explicitly replaces the whole geometry bundle. This extra
choice appears only when companion inputs are occupied. Its exact link plan is
validated again on confirmation; changes require repeating the search. Failed
connections restore the original links. Shift still connects the chosen socket
only, including for a whole-bundle replacement result. Mixed topology inputs such as ``edg_pol`` and ``PolyEdge``
prefer polygons when completing a bundle automatically; an explicitly chosen
Edges link is respected. Ambiguous geometry groups receive only the selected
link. Component Analyzer uses the inputs required by its operation: Edge Length
connects Vertices and Edges, not Faces.

`Watch: Connect Vertices, Edges and Polygons to a new Bevel node <https://github.com/user-attachments/assets/8162e0d3-123e-49e6-a749-1303e50d8fc7>`__

.. raw:: html

   <video controls preload="none" style="width: 100%; max-width: 960px;" aria-label="Connect Vertices, Edges and Polygons to a new Bevel node">
     <source src="https://github.com/user-attachments/assets/8162e0d3-123e-49e6-a749-1303e50d8fc7" type="video/mp4">
     <a href="https://github.com/user-attachments/assets/8162e0d3-123e-49e6-a749-1303e50d8fc7">Watch the demonstration video.</a>
   </video>

`Watch: Connect only Vertices and Edges for Edge Length <https://github.com/user-attachments/assets/f7564f36-f3db-4b7a-86ef-d331d24fa6a1>`__

.. raw:: html

   <video controls preload="none" style="width: 100%; max-width: 960px;" aria-label="Connect only Vertices and Edges for Edge Length">
     <source src="https://github.com/user-attachments/assets/f7564f36-f3db-4b7a-86ef-d331d24fa6a1" type="video/mp4">
     <a href="https://github.com/user-attachments/assets/f7564f36-f3db-4b7a-86ef-d331d24fa6a1">Watch the demonstration video.</a>
   </video>

`Alternative recording: Edge Length <https://github.com/user-attachments/assets/43cf2792-f58b-4301-8710-849139b2687a>`__

Expanded operations
-------------------

Operations are read from each registered node's RNA enumeration. The catalogue
does not maintain a duplicate list of operation identifiers. Supported adapters:

.. list-table:: Operation properties
   :header-rows: 1
   :widths: 30 45 25

   * - Node
     - RNA node identifier
     - Property
   * - Scalar Math
     - ``SvScalarMathNodeMK4``
     - ``current_op``
   * - Vector Math
     - ``SvVectorMathNodeMK3``
     - ``current_op``
   * - Color Mix
     - ``SvColorMixNode``
     - ``current_op``
   * - Logic Functions
     - ``SvLogicNodeMK2``
     - ``function_name``
   * - List Math
     - ``ListFuncNode``
     - ``func_``
   * - Matrix Math
     - ``SvMatrixMathNode``
     - ``operation``
   * - Quaternion Math
     - ``SvQuaternionMathNode``
     - ``operation``
   * - Scalar Field Math
     - ``SvExScalarFieldMathNode``
     - ``operation``
   * - Vector Field Math
     - ``SvExVectorFieldMathNode``
     - ``operation``
   * - Strings Tools
     - ``SvStringsToolsNodeMK2``
     - ``current_op``

Component Analyzer additionally expands the component family and its operation.
Other registered nodes are indexed in their initial configuration until an
operation adapter is added. Secondary parameters such as list matching, matrix
Pre/Post order, precision and numeric defaults remain editable on the node;
they do not multiply catalogue entries.

`Watch: Search directly for Scalar Math Multiply <https://github.com/user-attachments/assets/c4345e36-c86e-42c8-b4ae-532da1e00c95>`__

.. raw:: html

   <video controls preload="none" style="width: 100%; max-width: 960px;" aria-label="Search directly for Scalar Math Multiply">
     <source src="https://github.com/user-attachments/assets/c4345e36-c86e-42c8-b4ae-532da1e00c95" type="video/mp4">
     <a href="https://github.com/user-attachments/assets/c4345e36-c86e-42c8-b4ae-532da1e00c95">Watch the demonstration video.</a>
   </video>

Search text and Triggers
------------------------

Results include muted Triggers on the right, read from the node's normal search
metadata. Hover over the result to read the full label and Triggers. Text search
accepts prefixes, common aliases (for example ``inverse``/``invert`` and
``average``/``mean``), and one-character typos in longer words. Exact matches rank
ahead of typo matches, followed by connection compatibility. Results continue to
arrive while indexing. Explicit keyboard navigation keeps the chosen result
stable; otherwise the best available match becomes active.

Groups and configured interfaces
--------------------------------

Existing group definitions in the current blend file appear as ``Group: Name``.
Their declared interfaces are inspected without executing the group. Groups
that would create recursive containment are excluded. Inside a group, searches
also offer its Group Input and Group Output interface sockets.

Nodes whose configured socket interface differs from the catalogue's operation
profiles appear as ``[instance name copy]`` templates. Only nodes in the current
edited tree are considered. Selecting a template creates a native duplicate,
using the node's usual copy hooks and configuration. This supports already
configured script nodes and adaptive list interfaces without editing those
nodes. Indexing a template reads sockets only; choosing a script template can
execute its normal copy hook. An unconfigured script has no interface to infer
and cannot be offered as a configured producer. Template discovery waits until
the default catalogue is ready. Changed/deleted groups or templates are rejected
before creating the new node.

Matching and generic list outputs
---------------------------------

Exact socket types rank first. Name hints distinguish edges, polygons, masks
and numbers where possible. Known directional conversions have lower priority.
Generic list inputs accept other data types. Adaptive data outputs of Join,
Item, Reverse and similar list nodes are also offered in reverse searches from
Force, Surface and other data sockets. Numeric/control outputs such as Length,
Index and Mask are not classified as generic list data outputs.

Matching uses metadata rather than socket values. It cannot guarantee that
data contents or nesting satisfy an operation. A generic output does not become
semantically "edges" merely because upstream data contains edges. Nodes can
still report normal calculation errors after connection. Link Search refreshes
the existing receiving node's sockets before calculation, so an upstream error
does not prevent List Join from adding its next free input.

`Watch: Build a Pulga force chain with List Join and reverse search <https://github.com/user-attachments/assets/e777a977-275c-4af2-9400-6cc75e51eb8b>`__

.. raw:: html

   <video controls preload="none" style="width: 100%; max-width: 960px;" aria-label="Build a Pulga force chain with List Join and reverse search">
     <source src="https://github.com/user-attachments/assets/e777a977-275c-4af2-9400-6cc75e51eb8b" type="video/mp4">
     <a href="https://github.com/user-attachments/assets/e777a977-275c-4af2-9400-6cc75e51eb8b">Watch the demonstration video.</a>
   </video>

Catalogue lifecycle
-------------------

With ``Search on Link Drop`` enabled, Sverchok warms the catalogue after enabling
the addon or opening a blend file. The work runs cooperatively on Blender's main
thread, yielding between operation variants. A single node constructor cannot
be interrupted and can exceed the timer's normal batch budget.

Disabling automatic link search prevents automatic warmup and pauses unfinished
automatic indexing on its next callback. No idle polling timer is kept alive.
An open manual ``Search and Connect...`` popup can still request compatible
results while the preference is off. Closing that manual popup pauses indexing
again. F3 > ``Sverchok: Rebuild Socket Search Catalogue`` is an explicit request
that finishes even when automatic link search is disabled.

A paused catalogue resumes on the next search after re-enabling the preference.
The menu opens immediately, receives compatible results as indexing progresses,
and uses the same selection interaction before and after the catalogue is ready.
Progress appears in the footer; there is no separate Connect step.

The catalogue, operation profiles and query caches are held in memory. There is
no persistent catalogue file in the repository or blend file. Finished indexing
unregisters its timer. Popup refresh/input timers stop when the popup closes.
The native-link observer still checks left-button presses in the node editor;
ordinary clicks use bulk RNA geometry reads before inspecting socket selection.
This is a per-click cost and needs no permanent spatial cache or graph watcher.

Probes use temporary, non-processing trees. The indexer copies settings and
socket descriptions, and does not call ``process()`` or read socket values.
Normal node constructors and property callbacks still run. Probe trees, their
queued tasks and caches, and newly created helper resources are cleaned before
returning to Blender's event loop. Configured templates are inspected through
their existing interfaces; choosing a template uses its normal copy hooks.

The node-menu registry is checked when searching. New node types invalidate the
catalogue; use the rebuild operator after editing an operation adapter. Opening
a blend file invalidates the descriptions, but starts warmup only when automatic
search is enabled.

Current scope
-------------

* Main Sverchok trees and nested Sverchok groups are supported. Groups come from
  definitions in the current blend file.
* Configured interfaces are offered as copies of current-tree instances. This
  does not enumerate every possible configuration or execute scripts to discover
  their sockets. Nodes without a configured instance still need an adapter.
* Nodes are placed at the drop point; use G to move them afterwards.
* Missing dependencies and failed probes are logged and skipped.
* The native socket hit test briefly toggles socket selection. Automatic search
  is bypassed when outputs are explicitly socket-selected, to preserve native
  dragging behavior.

Developer notes
---------------

Architecture
^^^^^^^^^^^^

Four runtime modules separate the responsibilities. ``ui/sv_link_search.py``
owns socket dragging, catalogue probes, creation and helper resources.
``ui/sv_link_search_popup.py`` owns the live menu and keyboard/mouse selection.
``utils/sv_link_search.py`` contains socket metadata, matching, query relevance
and operation adapters. ``utils/sv_link_search_extensions.py`` owns existing
endpoints, geometry bundles, groups and configured copies. Section comments
separate the responsibilities within each file. Calculation errors use Blender
reports and the console logger.

Adding an operation adapter normally changes only ``MODE_PROPERTIES`` and,
if necessary, ``configure_node()``. Individual node implementations do not need
modification. Reuse their existing RNA properties and socket update methods.

One operation enumeration
^^^^^^^^^^^^^^^^^^^^^^^^^

1. Inspect the registered node's ``bl_idname`` and the RNA enum that selects its
   operation. Use property identifiers, not translated UI labels.
2. Add the property name to ``MODE_PROPERTIES`` in
   ``utils/sv_link_search.py``. For example::

       MODE_PROPERTIES = {
           # Existing adapters ...
           'SvExampleNode': 'operation',
       }

3. ``operation_variants()`` reads identifiers and human-readable names through
   ``enum_options()``. It yields immutable pairs of settings and search labels::

       ((('operation', 'ADD'),), 'Add')

4. Check the node's layout after applying the settings. Setting a property to
   its default may leave sockets unchanged unless its update method is called
   explicitly. Add a case to ``configure_node()`` when normalization is needed.

Configuration and socket normalization
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Apply settings in the same order used when probing. Use the node's existing
structural methods; these may hide sockets, replace their types or change names.
For example::

    # Methods without a context parameter:
    node.update_sockets()

    # RNA-style callbacks with a context parameter:
    node.update_sockets(None)

The new Matrix, Quaternion and Strings Tools adapters use the first form.
Scalar/Vector Field Math use the second. Component Analyzer has its own
``update_mode(None)`` normalization. Never assume all methods share a signature.

List Math has static sockets. Its original operation callback now updates its
label and schedules calculation without calling a nonexistent socket updater.
No class monkeypatch is installed by the adapter.

Both probing and creation call ``configure_node()`` before describing/finding
the target socket. This is essential for operations that change output type:
Quaternion Dot returns a number, Vector Field Norm returns a scalar field, and
Strings Tools To Number returns a number instead of text.

Nested or dependent modes
^^^^^^^^^^^^^^^^^^^^^^^^^

Use a dedicated branch in ``operation_variants()`` when a node has a parent
mode and a dependent operation. Store every required setting, in dependency
order. Component Analyzer is the existing example::

    ((('mode', 'Edges'), ('edge_mode', 'Length')), 'Edges > Length')

For a genuinely dependent enum, set the parent on the temporary probe before
reading the child's allowed choices. Do not enumerate every enum/boolean on a
node: display options, list matching and unrelated parameters create a large
Cartesian product without improving socket search.

Probe invariants
^^^^^^^^^^^^^^^^

* Keep all ``bpy`` access on the main thread. The timer budget is cooperative;
  yield between variants rather than running Blender data access in workers.
* Never call ``process()``, ``sv_get()`` or evaluate a user tree for indexing.
* Store plain settings and socket metadata, not temporary node/socket RNA.
* Include only sockets passing ``socket_available()`` after configuration.
* Recreate the same settings before resolving a chosen socket. Match identifier,
  then position/name/type, and cancel if the intended socket no longer exists.
* Respect the temporary-tree cleanup in ``_index_tree()``. A new adapter must
  not leave helper nodes, groups, update caches or queued probe tasks behind.
* Keep the menu's physical-row mapping. Blender may retain old button operator
  properties after filtering; using the original global index recreates the
  stale-selection bug fixed by ``_choice_index()``.
* When extending reverse creation, retain the explicit receiving-node update
  after ``init_tree()`` ends. Socket layout updates must precede tree evaluation.

Tests and review
^^^^^^^^^^^^^^^^

The native event suite also exercises Blender's real socket hit test before
opening search menus. It checks inputs, outputs and collapsed nodes, preserves
node/socket selection, and defers when an output is already selected. This
covers the bulk RNA geometry path used by the drag observer, as well as the
separate search-menu interaction. The workflow runs the unit and native suites
with Blender 4.5.10 and 5.1.0; its result must be checked on the actual PR branch.

The isolated suite includes matching, all operation profiles, forward/reverse
creation, group recursion and interface changes, configured templates, explicit
bundle replacement and restoration after failure. Run from the repository::

    blender -b --factory-startup --python-exit-code 1 --python tests/link_search_tests.py

Native popup tests exercise filtered mouse choices, typo ranking, whole-bundle
replacement, groups, configured interfaces, Escape and one-step undo::

    blender --factory-startup --enable-event-simulate --python-exit-code 1 --python tests/link_search_gui.py

The native test writes ``link-search-gui.json`` (override the destination with
``LINK_SEARCH_GUI_RESULT``); require its ``ok`` value to be true. Disable the
first-run splash before running unattended. The dedicated ``Link Search`` GitHub
Actions workflow runs both suites with pinned Blender 4.5 and 5.1 builds under
Xvfb and retains the logs. Local results do not imply that remote CI has run.

For each additional adapter, test the default operation, a different operation,
a return to the default, unary/binary signatures and type-changing outputs.
Check forward and reverse creation, a real mouse choice after filtering, Escape
and one-step undo. Verify that an upstream calculation error cannot prevent a
receiving multi-input node from adding its next free socket. Force a catalogue
rebuild and confirm that unsupported socket directions/types remain excluded.
