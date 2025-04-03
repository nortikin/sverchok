***************
Adding new Node
***************

This page documents the essentials to make your own node for sverchok. We make several assumptions
about your Python knowledge - an affinity for Python is a prerequisite. If you suck at Python, you
will have a bad time trying to write nodes for sverchok (-- a hard truth). 

.. tip::
    If you don't know Python my advice to you is to read first all the shorter nodes, and take notes
    about parts you don't understand.
    As you read more, the notes you took on previous nodes will be about techniques that re-occur in other nodes.
    Once you notice some repetition of the techniques you can class them, and start to associate the code with a
    procedure. Humans learn by extracting patterns from the chaos, but you have to see enough new material to let
    your brain do the pattern matching.
    
    Also do any of the free python courses, and quit and move on from easy ones to harder ones.


To create a node:
=================

Creation of new node can be split into next steps.

#. Make a scripted node to test the idea.
#. Show your node to us in an issue or create branch or fork of master in github. If it
   is a huge complex job we can make you collaborator.
#. Create a file with the node code according this page in appropriate 
   folder ``..sverchok/nodes/whatever_existing_category/your_file.py``
#. Add node's ``bl_idname`` to ``sverchok/index.md`` file in an appropriate category.
#. Make a pull request.

This page will describe from which pats the code of a new node should consist using simple example of a node.
The whole code of the node can be downloaded from the link below.

:download:`Simple node code template <simple_node_template.py>`.

.. note::
    This documentation describe node structure which is used in most nodes in Sverchok.
    However there are other experimental approaches too. In the future more advanced approach
    may be born because current approach has
    `certain disadvantages <https://github.com/nortikin/sverchok/issues/3955>`_.

License
-------

Use next strings in the top of the node file::

    # This file is part of project Sverchok. It's copyrighted by the contributors
    # recorded in the version control history of the file, available from
    # its original location https://github.com/nortikin/sverchok/commit/master
    #
    # SPDX-License-Identifier: GPL3
    # License-Filename: LICENSE


Imports
-------

.. code-block:: python

    import bpy
    from mathutils import Vector
    from bpy.props import FloatProperty
    from sverchok.node_tree import SverchCustomTreeNode
    from sverchok.data_structure import updateNode

- You need to import ``bpy`` because we use always use ``bpy.types.Node`` and often use ``bpy.props``
- The Sverchok imports are needed for the availability of common Sverchok functions.

  - The ``updateNode`` is the function we add to a property to trigger updates when a slider is adjusted. 
  - ``SverchCustomTreeNode``'s definition can be found in 
    `node_tree.py <https://github.com/nortikin/sverchok/blob/master/node_tree.py>`_,
    it adds a ``poll`` and several utility functions to the node class.
- You are free to import any other useful module in that section.


Node Class
----------

.. code-block:: python

    class SvScaleVectorNode(SverchCustomTreeNode, bpy.types.Node):
        """
        Triggers: vector multiple scale
        Tooltip: This node multiply vector and some value
    
        Merely for illustration of node creation workflow
        """
        bl_idname = 'SvScaleVectorNode'  # should be add to `sverchok/index.md` file
        bl_label = 'Name shown in menu'
        bl_icon = 'GREASEPENCIL'

Class name
    A small (but significant) implementation detail of Sverchok is that name of the Node class should
    be identical to the ``bl_idname`` of the node class. This simplified a few things for development. This
    class name should start with a prefix ``Sv`` and contain only alphanumeric characters. Something like
    ``SvMyFirstNode`` would be fine. If you want to automatically make the node available upon startup then
    this classname must be added to the ``index.md`` file in the correct category.

Docstring
    **Triggers:** This should be very short (two or three words, not much more)
    to be used in :kbd:`Ctrl-Space` search menu.

    **Tooltip:** Longer description to be present as a tooltip in UI.

    More detailed description with technical information or historical notes goes after empty line.
    This is not shown anywhere in the UI.

bl_idname
    This is the unique identifier for a node type, like a post code for a home.

bl_label
    This is the name as it will appear in menus and on the node's header when it's first added to a
    node tree. Keep this short.

bl_icon
    This is used to display a node icon in the shift+A menu. There's also a ``sv_icon`` implemented 
    for custom icons (but for a different topic)

.. code-block:: python

    value: FloatProperty(name="My value", default=2, update=updateNode)
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "value")

Properties
    Each node can have properties which can be displayed in the its UI and used in its code.
    `Read more about properties <https://docs.blender.org/api/current/bpy.props.html>`_.

def draw_buttons
    This is where we add any custom UI (sliders/buttons/enumerators), this is like the ``draw`` function of a panel.
    This function can be called many times a second so avoid doing intense computation inside it. 
    This function is for nothing other than drawing the current state of the node, 
    it isn't for updating node properties.
    More information in the 
    `Blender documentation <https://docs.blender.org/api/current/bpy.types.UILayout.html>`_. 

.. code-block:: python

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvVerticesSocket', "Vertices")

def sv_init
    This function is used to setup the initial state of a node. This is where you add the default sockets
    and their properties. This is where we tell a socket to appear as a slider. To better get an idea of what
    it's used for do a search for this function in the Sverchok repository.

.. code-block:: python

    def process(self):
        # read input value
        input_vertices = self.inputs["Vertices"].sv_get(default=[])

        # vectorization code
        output_vertices = []
        for in_vert_list in input_vertices:  # object level
            out_vert_list = []

            for v in in_vert_list:  # value level

                # perform the node function
                out_vert_list.append((Vector(v) * self.value)[:])

            output_vertices.append(out_vert_list)

        # wright output value
        self.outputs["Vertices"].sv_set(output_vertices)

def process
    This function is called whenever the node is told to update. It's where we get the content of the 
    input sockets, and set the output of the output sockets. This function is sometimes big..and sometimes
    merely a few lines - you should look at existing nodes to get a feel for what to put in there.

    First line of the process method read data from the input socket with name *Vertices*.
    If the socket is not connected the input data will be an empty list.
    Expecting format of vertices is next::

        [[[x, y, z],   <- object 1, vector 1
          [x, y, z]],  <- object 1, vector 2

         [[x, y, z],   <- object 2, vector 1
          [x, y, z]]]  <- object 2, vector 2
    
    To understand the Sverchok data structure read :doc:`this tutorial <../tutorials/nesting>`.

    Next step is unroll the vertices data structure, perform operation on single
    vertices and wrap the result back. Last string assign the result to output socket.


Register node class
-------------------

.. code-block:: python

    def register():
        bpy.utils.register_class(SvScaleVectorNode)


    def unregister():
        bpy.utils.unregister_class(SvScaleVectorNode)

All node classes should be registered so Blender could be able to use them. 
``register`` function is called when the add-on is enabled, 
``unregister`` when you hit :kbd:`f8` (or execute `script.reload` in Python
console editor) or disable Sverchok.


.. warning::

    Fixing existing nodes is not the same as create new ones. Existing node can be used in some layouts
    and new changes should not break them. It's possible to add new logic to an existing node
    but don't do next:
    
    #. Change ``bl_idname`` of a node
    #. Remove or rename sockets (use labels for socket renaming)
    #. Adding new socket in between existing sockets. We prefer that you add sockets behind the last
       existing socket for either ``self.inputs`` or ``self.outputs``. This is the rule only if access
       to sockets is made by their indexes.
    #. There are other reserved property names see the bpy.types.Node baseclass in Blender docs and
       Sverchok's custom node mixin class. (this is true and when new node is created)
