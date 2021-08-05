Typography Viewer
=================


.. image:: https://user-images.githubusercontent.com/619340/127733727-0d8299e7-ab20-4a33-b3ff-923276f09f5c.png


Functionality
-------------

The Blender Font (Text) object has many features, this node hopes to allow the user to create renderable Text. Convenience is paid for by only making a subset of features available. This might change in the future.

Each element of Text can be positioned using a Matrix. If you want to place individual Glyphs/letters arbitrarily in 3d/2d space then you must split the incoming text by letter. The String Tools node is very useful for this, and the List Item node is also commonly used.

Basic properties
----------------

Some configuration features are in the options dropdown (the precise arrangement of these UI elements will likely change):

.. image:: https://user-images.githubusercontent.com/619340/127733963-9ba1da4e-e3ac-4b6d-838e-3ef5315d3c8e.png


Inputs
------

a ``Text`` socket and a ``Matrix`` socket

Outputs
-------

A Blender Text object directly into the scene.

Caution
-------

You do not want to manually edit the product of this node, that would break the procedural nature of the node. Manual editing after creation can result in undefined behaviour and is likely overwritten as soon as you update the Sverchok node tree again by moving upstream sliders etc.


Further reading
---------------

it might be useful to search the Sverchok issue tracker for mentions and examples of of Typography Viewer.