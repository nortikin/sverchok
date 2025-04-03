===================
Copy Modifiers Node
===================

.. figure:: https://user-images.githubusercontent.com/28003269/163018172-7911e4a4-acd3-4cd5-a09f-1b436c9de088.png
    :align: right
    :figwidth: 200px

Functionality
-------------

The node performs similar operation to standard Blender Copy Modifiers operation.
It takes two set of objects and apply modifiers from one set to another.
It is useful for example in case when you want to assign Remesh or Subdivide modifiers
to Sverchok objects.

.. raw:: html

   <video width="700" controls>
     <source src="https://user-images.githubusercontent.com/28003269/163026163-a8762f52-b6f2-4dcd-b95e-760da3af033a.mp4" type="video/mp4">
   Your browser does not support the video tag.
   </video>

Inputs
------

**Object To** - Objects to whom to apply modifiers

**Object From** - Objects from which get modifiers

Outputs
-------

**Object** - Objects with assigned modifiers

Examples
--------

Assign Remesh modifier

.. image:: https://user-images.githubusercontent.com/28003269/163020246-317c00e5-dd15-4caa-8c14-3c98ca633ae5.png
   :width: 700 px
