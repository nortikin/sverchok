Typography Viewer
=================


.. image:: https://user-images.githubusercontent.com/14288520/190365693-a37cff3d-edef-465d-be32-62669b9403e7.png
  :target: https://user-images.githubusercontent.com/14288520/190365693-a37cff3d-edef-465d-be32-62669b9403e7.png

.. image:: https://user-images.githubusercontent.com/14288520/190381347-4ed2a78b-acf3-4a44-8d53-ea9c7ac08bd7.png
  :target: https://user-images.githubusercontent.com/14288520/190381347-4ed2a78b-acf3-4a44-8d53-ea9c7ac08bd7.png

* Number-> :doc:`A Number </nodes/number/numbers>`

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

Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/190374351-00c3b1c8-4435-4942-8a4f-f1cce318120b.png
  :target: https://user-images.githubusercontent.com/14288520/190374351-00c3b1c8-4435-4942-8a4f-f1cce318120b.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* List->List Struct-> :doc:`List Levels </nodes/list_struct/levels>`
* Text-> :doc:`String Tools </nodes/text/string_tools>`

Further reading
---------------

it might be useful to search the Sverchok issue tracker for mentions and examples of of Typography Viewer.