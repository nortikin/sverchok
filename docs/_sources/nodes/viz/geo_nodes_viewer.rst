Geo Nodes Viewer
================

Functionality
-------------

The node generates object with given mesh and applies given Geometry Nodes
modifier. The use case of this node is to create efficient viewers with help of
Geometry Nodes. Currently it can replace more than tens of nodes which generate
mesh, curves or instances (see `Examples`_ section).

.. note::
   Usually add-on developers use Blender Python API to generate different
   types of data blocks. But for the last several years Geometry Nodes became
   much more powerful than Blender API mean while the API remained unchanged.
   So instead of hardcoding and improving existing viewers it's a logical step
   to delegate this to users. Using this node is much more efficient and
   flexible than existing users except Mesh Viewer because they share the same
   code to generate objects.

When a Geometry Nodes node group is assigned to the node it generates extra
sockets for each extra input of the node group. If the generated sockets are
not connected they pass single value otherwise they pass a field of values if
possible. The domain of field can be selected by a property drawn on a connected
socket (only for Vertices, Values and Colors). If, after assigning a node group,
its input sockets were changed the node input sockets can be updated by a button
drawn near the name of the tree.

.. important::
   Important thing to remember is that only real data is vertices, edges and
   faces. Everything else is just attributes of this elements or single values.
   It means if you want to pass certain amount of data it should be controlled
   by number of vertices, edges or faces. You can't create an object by the node
   and copy it into certain position because number of passed positions is
   limited either by the number of vertices or edges or faces. See the
   `Examples`_ the way of how to achieve this.

The node adds Geometry Nodes modifier to generated geometry. It's possible to
add more modifiers to the object. But if the name of modifier will be changed
the node wont be able to distinguish it and will create a new one.

.. It's impossible to use Custom properties on Geometry Nodes modifiers because
.. they are cleared up whenever interface of the node group is updated.

Category
--------

Viz -> Geo Nodes Viewer

Inputs
------

- Verts
- Edges
- Faces
- arbitrary inputs

Parameters
----------

Live Update
  The node only works when the option is on.

Show Objects
  Similar to Hide in Viewport option in the Outliner.

Select Objects
  To make objects selectable.

Render Objects
  Similar to Disable in Renders option in th Outliner.

Base Data Name
  Base name for generated objects.

Modifier
  Geometry Nodes modifier to assign to generated objects

Fast Mesh Update
  It tries to update mesh in fast way. It can't update mesh properly in
  some conner cases. So it should be disabled.

Buttons
-------

Random Name
  Generate random for Base Data Name property

Select
  Select generated objects

Bake
  When node is deleted it is deleted with generated mesh. Use bake button to
  save the output of the node. It will generate copy of objects disconnected
  of the node. The same can be done with Bake All operator.

Add new Geometry Nodes tree (shown when tree is not chosen)
  It asks name of a tree and create instance of Geometry Nodes tree.

Update Node Sockets (shown if there is GN tree)
  It generates or removes node input sockets according to input sockets of the
  Geometry Nodes node group. Should be called when the node group inputs were
  changed.

  .. note::
     Update socket is optional step. If node input sockets does not match to
     GN tree inputs they will be just ignored. So it's possible add extra
     inputs to GN tree and all nodes which already use the tree will continue
     to work even if new inputs are not presented in the inputs of the nodes.

Edit Geometry Nodes Tree (shown if there is GN tree)
  Switches current Sverchok tree editor to Geometry Nodes editor to edit the
  tree of the node. You can use ``Tab`` button similar to how to edit group
  nodes.

  .. note::
     When you finished with editing of Geometry Nodes tree you can return back
     to Sverchok by pressing dedicated button in right top corner of the tree
     editor.

     .. image:: https://user-images.githubusercontent.com/28003269/206369211-eee956cb-5300-412f-abe5-2fe311d444b5.png

Outputs
-------

- Objects

Examples
--------

.. figure:: https://user-images.githubusercontent.com/28003269/193779986-37096119-7ccc-4f1f-9fc2-31e46de38b54.png
   :width: 700px

   Using the node as a Mesh Viewer

.. figure:: https://user-images.githubusercontent.com/28003269/193781623-5bce566f-1bf3-4cc7-8830-3eee85099de8.png
   :width: 700px

   Recreating logic of current Curve Viewer node

.. figure:: https://user-images.githubusercontent.com/28003269/193784538-eb88831a-2e3e-4957-8fc5-03e94947c480.png
   :width: 700px

   Polyline viewer. Extra properties can be added in GN tree optionally.

.. figure:: https://user-images.githubusercontent.com/28003269/193793969-0ba2eb45-1587-4d96-9858-ae50ed6ecd92.png
   :width: 700px

   Typography Viewer.

.. figure:: https://user-images.githubusercontent.com/28003269/193798678-df1ba9e9-569a-4a3e-bd69-2911f8b67372.png
   :width: 700px

   Skin Masher Viewer.

.. figure:: https://user-images.githubusercontent.com/28003269/193799291-010ca655-8faf-4e8c-8ac6-4b33876bf2bd.png
   :width: 700px

   The Geometry Node group of Skin Masher Viewer also can be used for generating
   Metaballs. It does not generate exectly metaballs but the result looks close.

.. figure:: https://user-images.githubusercontent.com/28003269/193802557-d8187b64-9132-41fe-b0ea-8c3b015e4882.png
   :width: 700px

   Bezier and NURBS Curve Out Viewers.

.. figure:: https://user-images.githubusercontent.com/28003269/193803850-5ded8fe4-db2c-420e-9b9e-e0fda144bb08.png
   :width: 700px

   NURBS Surface Out Viewer.

.. figure:: https://user-images.githubusercontent.com/28003269/193820713-d664c769-6701-4473-8c71-e5d125f03df7.png
   :width: 700px

   Object Instancer node. Unlink original node Geo Nodes Viewer does not
   generate extra objects and all meshes are generated in single object. This
   is much more efficient approach.

.. figure:: https://user-images.githubusercontent.com/28003269/193822290-dcaa388d-7ec0-46f9-b254-3a4f08d3a01b.png
   :width: 700px

   Dupli Instanser node.
