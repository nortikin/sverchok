========
Node API
========

This page has a claim to define all aspects of node creation. Brief introduction
to node creation is represented :doc:`on this page <contributing/add_new_node>`.

Code of new node should be created in separate file. The file should obtain
one of the available categories in ``nodes`` folder.

Usually structure of the file looks next:

.. code-block:: python

    # This file is part of project Sverchok. It's copyrighted by the contributors
    # recorded in the version control history of the file, available from
    # its original location https://github.com/nortikin/sverchok/commit/master
    #
    # SPDX-License-Identifier: GPL3
    # License-Filename: LICENSE

    import bpy

    class Node:
        ...

    def register():
        ...

    def unregister():
        ...


Class Definition
----------------

To create a node in Sverchok means to create a node class. Naming convention for
node classes is ``SV + name of the node + Node``

Standard Mix-ins for all node classes are
``sverchok.node_tree.SverchCustomTreeNode`` and ``bpy.types.Node``

Optional Mix-ins can be found over the next path ``sverchok.utils.nodes_mixins``

Node class documentation string serves to two purposes:

  1. Adding key words for searching
  2. Adding tool tip into add node menu

There are tow mandatory class variables:

  1. ``bl_idname`` it should repeat the name of the class
  2. ``bl_label`` it shows text (name of the node) in the header of the node

.. tip::
   Node label can be defined dynamically in ``draw_label`` method which
   should return a string.

Also the class can define optional ``bl_icon`` variable with a string of an
standard Blender icon for the node. To find all standard icons default Icon
Viewer add-on can be used.

It's possible to define custom icons in ``sv_icon``
variable. A custom icon should be stored in ``sverchok.ui.icons`` folder in png
format. The variable value should repeat the png file name without extension
and in upper case.

.. code-block:: python

    class SvSetMeshAttributeNode(SverchCustomTreeNode, bpy.types.Node):
        """
        Triggers: set mesh attribute
        Tooltip: It adds an attribute to a mesh
        """
        bl_idname = 'SvSetMeshAttributeNode'
        bl_label = 'Set mesh attribute'
        bl_icon = 'SORTALPHA'

        def draw_label(self):
            return "Label1" if self.prop else "Label2"


Creating Node Custom Properties
-------------------------------

Properties are created in standard way similar to other areas of Blender.
`Blender documentation <https://docs.blender.org/api/current/bpy.props.html>`_

After properties are added they can be used as node buttons or socket property.
Also they can be used for internal usage but it's usually better to use ID
properties instead.

.. note::
   Using node properties for displaying on sockets is deprecated. Usually
   sockets can define their own properties.

To make a node to react on property changes they should define update argument.
If not extra logic is required the argument can be define thus
``update=sverchok.data_structure.updateNode``. Also in case for example if after
property changing some sockets should appear it can be done in custom update
method of a node. The method expects to get the ``self`` and ``context``
parameters.

.. tip::
   Also there is direct method to update the node but it can't be passed as
   argument to the update parameter directly. Instead it's possible to use
   lambda expression:
   ``update=lambda self, context: self.process_node(context)``

.. code-block:: python

    class NodeClass:

        # ...

        def update_type(self, context):
            # some logic
            updateNode(self, context)

        some_mode: bpy.props.BoolProperty(update=updateNode)
        another_mode: bpy.props.BoolProperty(update=update_type)


Draft Properties
^^^^^^^^^^^^^^^^

Node can has draft properties which will be used instead of normal ones in
draft mode of a tree. Draft properties are defined in the same way as normal
ones. Also the node should use ``DraftMode`` mix-in, define
``draft_properties_mapping`` class variable with mapping between standard
properties and draft ones, and ``does_support_draft_mode`` method which should
return boolean value.

.. code-block:: python

    class NodeClass(sverchok.utils.nodes_mixins.DraftMode):

        # ...

        some_mode: bpy.props.BoolProperty(update=updateNode)
        some_mode_draft: bpy.props.BoolProperty(name='[D] Some Mode', update=updateNode)

        draft_properties_mapping = dict(some_mode = 'some_mode_draft')

        def does_support_draft_mode(self):
            return True


Enum Properties
^^^^^^^^^^^^^^^

Enums are created in the same way as in other Blender UI parts. In case Enums
are generated dynamically they always should be stored somewhere in Python
memory. There are `known cases`_ when Blender crash during rendering when UI
expose dynamic enums which does not store their content.

.. _known cases: https://github.com/nortikin/sverchok/issues/4316

Enum items can have custom icons. Custom icons should be stored in
``sverchok.ui.icons`` folder. To use custom icons ``ui.sv_icons.custom_icon``
function should be used. It expects name of the file in upper case without
extension and returns index of the icon.


Dynamic Properties
^^^^^^^^^^^^^^^^^^

There are several nodes which generate dynamic properties - List Levels and
Switcher nodes. Dynamic properties are properties which are generated
dependently on the size of input data. Best way to generate dynamic properties
is to use PropertyGroups together with Collection properties. Displaying
such properties is possible with for loop inside UI code. Right place to upgrade
properties is ``process`` method.

.. warning::

   Dynamic properties should always store changed by user values even if they
   are not displayed anymore. Otherwise it will lead to degradation of node
   tree "code". Whenever properties will be removed and restored a user always
   should repeat his choice what is quite unexpected.

   Also in future generation of properties inside ``process`` method should
   move to some another method because ``process`` method should become an
   abstract method.


Creating Node Buttons
---------------------

There are 4 places where node can show its properties:

  1. Node interface
  2. Node tab of the Property panel of the Node editor
  3. Tool tab of the Property panel of the 3d View port editor
  4. Context menu

Node interface is appropriate place for adding properties which are used
regularly during work with a node tree. They should be defined in
``draw_buttons`` method which expects ``context`` and ``layout`` arguments.

Property panel of the Node editor is good place for showing properties which
are rarely changed or should be changed only once. Its possible to do in
``draw_buttons_ext`` method which expects ``context`` and ``layout`` arguments.

.. code-block:: python

    class Node:
        value: IntProperty()
        mode: BoolProperty()

        def draw_buttons(self, context, layout):
            layout.prop(self, "value")

        def draw_buttons_ext(self, context, layout):
            layout.prop(self, "mode")


There are some nodes which properties are useful to have in 3D Viewport editor.
Node with such properties should use ``utils.nodes_mixins.Show3DProperties``
mix-in. UI code should be placed in ``draw_buttons_3dpanel`` method. It expects
``layout`` argument and ``in_menu`` optional argument which is False by default.
UI should obtain only one string. It's possible to show UI on several lines but
in this case ``utils.node_mixins.Popup3DMenu`` operator should be used. The
operators calls the same ``draw_buttons_3dpanel`` method but with ``in_menu``
argument as True.

.. code-block:: python

    class Node(Show3DProperties):

        def draw_buttons_3dpanel(self, layout, in_menu=None):
            if not in_menu:
                menu = layout.row(align=True).operator('node.popup_3d_menu', text=f'Show: "{self.label or self.name}"')
                menu.tree_name = self.id_data.name
                menu.node_name = self.name
            else:
                row.prop(self, 'mode1')
                row.prop(self, 'mode2')


Also optionally nodes can show their properties in context menu. Node should
override ``rclick_menu`` method which expects ``context`` and ``layout``
arguments.


Node Sockets
------------

Node sockets are created in ``sv_init`` method. ``new`` method of input and
output collections of sockets should be used. It expects name of a socket type
and name socket itself. These names are shown in UI and also usually are used
as identifiers. Whole list of available socket types can be found in
``core.sockets`` module. The new method returns newly created socket which
can be used for setting its extra parameters.

Usually sockets expose their default parameters. By default they are switched
off. The proper way to make to show its property is to assign True value to
``use_prop`` attribute of the socket. Default value can be changed in
``default_property`` attribute.

``SvStringsSocket`` type has two types of default values. Current type stored
in ``default_property_type`` attribute which can receive either 'float' or
'int' values. Default values are stored in ``default_float_property`` and
``default_int_property`` attributes.

.. code-block:: python

    class Node:
        def sv_init(self, context):
            socket = self.inputs.new('SvStringsSocket', "Size")
            socket.use_prop = True
            socket.default_float_property = 1.0
            self.outputs.new('SvVerticesSocket', "Verts")

Dynamic Sockets
^^^^^^^^^^^^^^^

Dynamic sockets are shown only on certain conditions. There are 3 categories
of them:

  1. Socket is shown if a node has certain properties.
  2. Socket is shown if other socket is connected.
  3. Socket is shown if node has appropriate input data.

There are many ways to show / hide sockets. First of all it's possible ot use
Blender standard API for adding and removing sockets. Most resent nodes use
``hide_safe`` attribute of sockets. Disadvantage of this method is tha sockets
are not really deleted and can be shown with `Ctrl+h` by user. The proper
way now is to use standard Blender ``enabled`` attribute.

When type of a socket should be changed it's possible to use
``data_structure.changable_sockets`` function or ``replace_socket`` method of a
socket. First function changes type of output sockets dependently on type of
a socket connected to input one. With the method you have to define new
type of a socket by yourself.

.. warning::
   Change type of a socket is tricky part. Because it's related with removing,
   adding, moving sockets and links in a tree. Also it can be quite inefficient
   because Blender does not expose API which would allow to search connected
   neighbour sockets efficiently. But usually it's not a bottle neck in such
   cases.

To generate sockets upon changes of node properties is possible in ``update``
method of properties.

To generate sockets upon changes in node connections is possible in
``sv_update`` method of nodes. This method can be called quite intensively so
it's wise to expense resources carefully.

To generate sockets upon changes of input data of a node was quite controversial
idea. Now it's only used in Dictionary output node. The problem is that this can
easily lead to losses of user connections what breaks node setups. For example
in Geometry Nodes project there was a decision that sockets should be
independent to data layer. So to generate such nodes is not recommended now.
If there is now way but to have this functionality possible solution could be
to add a button to a node which would recreate sockets explicitly.

.. code-block:: python

    class Node:
        def mode_update(self, context):
            self.inputs['Value'].enabled = self.mode
            self.process_node()

        mode: BoolProperty(update=mode_update)

        def sv_init(self, context):
            self.inputs.new('SvStringsSocket', "Value").use_prop = True
            self.outputs.new('SvStringsSocket', "Value")

        def sv_update(self)
            data_structure.changable_sockets(self, "Value", ["Value"])

Socket Properties
^^^^^^^^^^^^^^^^^

label
  Expects a string which is used instead of a socket name in UI.

use_prop
  Expects boolean value. If true the socket will display its default property.

custom_draw
  Expects name of a method of the node of the socket. If defined the method
  will be used draw UI elements for the socket.

  .. code-block:: python

     class Node:
         def custom_draw_socket(self, socket, context, layout):
             layout.prop(self, "node_property")


quick_link_to_node
  Expects a sting of node `bl_idname``. This will add an operator which can
  create quick link to the given node.

link_menu_handler
  Expects a sting of class name defined inside node of the socket. This only
  works whe displaying quick links is in multiple values mode. In the class
  its possible to define extra nodes for connections. This is analog of
  creating nodes during dragging a link from a socket in Blender 3.1.

  .. code-block:: python
     class Node:
         class MenuHandler:
             @classmethod
             def get_items(cls, socket, context):
                 """Return list of extra options for the menu"""
                 return [('KEY', "Name", "Description"), ]

             @classmethod
             def on_selected(cls, tree, node, socket, key, context):
                 """In this method the node should be created and linked to the socket"""
                 if key == 'KEY':
                     print("Hello world!")

prop_name
  Expects name of a node property to display in UI of the socket.

  .. warning::
     This is deprecated way to display default properties for sockets. Use
     ``use_prop`` attribute instead.

object_kinds (SvObjectSocket)
  Expects string value of object type to socket to display as possible choice.
  Its also possible to pass several types which should be separate by only
  comma: ‘MESH,CURVE,SURFACE,META,FONT,VOLUME,EMPTY,CAMERA,LIGHT’

expanded (SvVerticesSocket, SvQuaternionSocket, SvColorSocket)
  Expects boolean value. It's responsible for the way of the socket to display
  the socket value.

Socket Vectorization Properties
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Vectorization system is on
:ref:`experimental stage <experimental_vectorization>`

is_mandatory
  Expects boolean value. If True the node can't perform its function without
  data from the socket.

nesting_level
  Expects integer value. Describes the expected shape of input data.

  * 3 for vectors lists (Default for Vertices Socket)
  * 2 for number lists (Default)
  * 1 for single item

default_mode
  Expects one of the next stings:

  * 'NONE' to leave empty
  * 'EMPTY_LIST' for [[]] (Default)
  * 'MATRIX' for Matrix()
  * 'MASK' for [[True]]

pre_processing
  Expects one of the next stings:

  * 'ONE_ITEM' for values like the number of subdivision (one value per object).
    It will match one value per object independently if the list is [[1,2]]
    or [[1],[2]]. In case of more complex inputs no preprocessing will be made.
  * 'NONE' not doing any preprocessing. (Default)


Business logic
--------------

The main work of the node is happening inside ``process`` method which does
not expect any arguments.

The whole process can be split into 3 steps:

  1. Extract data from sockets.
  2. Handle the data.
  3. Record result into output sockets.

.. note::
   In future it is planned to convert the method into abstract one. In this case
   a node will get parameters via some arguments.

For reading data from sockets their ``sv_get`` method can be used.
It has tow important parameters. ``default`` parameter expects any
data which will be returned in case if input socket does not have any external
data. ``deepcopy`` parameter expects False value if input data is not modified
by the node. The node can work quite more efficient if deepcopy is False. But
if a node do modify the data the parameter should be with default value,
otherwise other nodes which use the same data will get unexpected results.

.. note::
   Many nodes on this stage also do such optimization as checking connection of
   their output sockets and if they are not connected cancel their father
   execution. Really it's not recommended in new nodes. The right place for
   such optimization is execution system.

After handling input data ``sv_set`` method of sockets can be used for
saving result. It expects only one parameter - data.

.. code-block:: python

    class Node:
        def process(self):
            data = self.inputs['My Socket'].sv_get(default=[], deepcopy=False)

            result = handle_data(data)

            self.outputs['My Socket'].sv_set(result)

.. important::
   Sometimes node does not have enough data to perform its function in this case
   it should pass available data to output sockets unmodified. It's important
   because the whole node tree will stop working otherwise.

Data vectorization
^^^^^^^^^^^^^^^^^^

All nodes should be designed in a way that they can handle not only one object
but multiple of them. That is called vectorization in Sverchok. For example if
a node works with vertices of an object it should handle list of list of
vertices.

It can happen that some input data has one number of objects and another
input data has another number of objects. In this case a node should perform
data matching operation. Usually it means that data with shorter number of
objects should repeat them to match them to number of objects of the longest
data. Repeating objects usually happens in two ways.

  1. Last object fills all missing ones. For example: ``[1, 2, 3]`` will be
     converted into ``[1, 2, 3, 3 ,3 ,3]`` if number of required objects is 6.
  2. Objects start to repeat from start of a list (cycling). For example:
     ``[1, 2, 3]`` will be converted into ``[1, 2, 3, 1, 2, 3]`` if number of
     required objects is 6.

Usually number of objects is determined by the longest input data. Sometimes
the number can be limited by some particular input in case it does not have
sense to repeat it.

There are helping functions / generators to perform data matching in
``data_structure`` module. Generators are preferable before functions.

.. code-block:: python

    class Node:
        def process(self):
            params = [s.sv_get(deepcopy=False, default=[[]]) for s in self.inputs]
            max_len = max(map(len, params))
            out = []
            for _, v, e, f, fd, m, t, d  in zip(range(max_len), *make_repeaters(params)):
                out.append(handle_data(v, f, t, d, e, fd, m))

            out_verts, out_edges, out_faces, out_face_data, out_mask = zip(*out)
            self.outputs['Verts'].sv_set(out_verts)
            self.outputs['Edges'].sv_set(out_edges)
            self.outputs['Faces'].sv_set(out_faces)
            self.outputs['Face data'].sv_set(out_face_data)
            self.outputs['Mask'].sv_set(out_mask)

.. _experimental_vectorization:

.. note::
   There are two experimental approaches to automatize data matching. One can
   be found in ``utils.nodes_mixins.recursive_nodes`` and another in
   ``utils.vectorize`` modules. Both of them can handle not only list of
   objects but and nested to each other lists of objects with arbitrary
   nestedness and shape. It leads to two disadvantages:

     1. It make the code difficult to understand, to support and to debug.
        Even for user its more difficult to handle data with complex shape.
     2. Vectorization itself is very expensive thing because it uses pure
        Python loops. And such complex vectorization system is even more
        expensive.

   Also any vectorization can be performed with loop nodes which can create
   more clear representation data handling. So this modules should prove first
   which problems they are going to solve which can't be tackled in another way
   and so they can't be recommended for use for now.

.. note::
   In future vectorization should leve the nodes area and arrive to execution
   system. In this case nodes only have to add information to sockets to give to
   execution system to now how to match data.

Data structure
^^^^^^^^^^^^^^

Sverchok can operate on vide variation of data structures. The most important
one is mesh data structure. Sverchok uses *Face-vertex* representation of them.
Representation is a simple list of vertices, and a set of edges and polygons
that point to the vertices they use.

.. note::
   Usually list of vertices, edges and polygons ary ordinary Python lists.
   Vertices can be represented as numpy arrays. If a node is generator it can
   have an option in which format to output vertices. If a node has vertices as
   an input it should output them in the same format in which they came.

   For edges and polygons it was decided not to use numpy arrays due little
   performance benefit and in case of n-gons it's not trivial how to store and
   handle them as numpy arrays.

.. code-block:: python

    # simple triangle
    vertices = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
    edges = [(0, 1), (1, 2), (0, 2)]
    polygons = [[0, 1, 2], ]

For vertices there is ``SvVerticesSocket`` socket type. For edges and faces
there is ``SvStringsSocket`` socket type. The last one is also used for lists
of numbers (floats, integers).

For storing mesh attributes Sverchok uses simple numbers or more complex data
as colors, texts and vectors. Such lists should store values per mesh element.
Color data passes via ``SvColorSocket``, number via ``SvStringsSocket``, strings
via ``SvTextSocket``.

For orienting meshes in space Blender Matrix and Quaternions are used.
Historically they has next format - ``[matrix, matrix, ...]`` but this format
can move only whole mesh. For this reason some nodes also support such format -
``[[matrix, matrix, ...], [matrix, ...]]``. In this cases matrix can be used
for moving separate elements of a mesh. Socket types for them are
``SvMatrixSocket`` and ``SvQuaternionSocket``.

Sverchok has family of mathematical objects such as Curves, Surfaces,
Feilds, Solids. All of them, except Solids, are defined as Python classes.
Solids are used from FreeCAD library. They all have dedicated to them sockets
in the ``core.sockets`` module.

Also there are some other data structures as Blender objects, File paths, svg,
Pulga forces, Dictionaries.

.. note::
   Dictionary has rather experimental stage and should prove in which area
   they can be used efficiently.

BMesh data structure
^^^^^^^^^^^^^^^^^^^^

For performing operations over geometry it's possible to create you own
algorithms. But also Blender has a library of some basic geometry operations.
This library uses special BMesh data structure. It's similar to Half-edge
data structure. To convert data from Sverchok format to BMesh and vice versa
there is ``utils.sv_bmesh_utils`` module.


Node Registration
-----------------

After a node was created it should be registered to appear in Blender interface.
It can be done in function with ``register`` name in the same module with node
class. This function will be called whenever the add-on is enabled. For the
class registration standard Blender function is used.

.. code-block:: python

    class Node:
        ...

    def register():
        bpy.utils.register_class(Node)

Also node should be placed in some existing category by adding its ``bl_idname``
to the ``index.md`` file.

When the add-on is disabled or reloaded its classes should be unregister. To
unregister a node is possible in function with name ``unregister`` in the same
module with Node class.

Also node with node should go documentation file in ``docs.nodes`` folder.

.. todo node tests


Animation
---------


Viewer Nodes
------------


Noes With Dependencies
----------------------


JSON Import / Export
--------------------


Upgrade Node
------------

.. todo context menu
