Texture Viewer Lite
===================

.. image:: https://cloud.githubusercontent.com/assets/22656834/25429102/51cdf852-2a91-11e7-86ac-7b373d4bc97a.png

Functionality
-------------

This node allows viewing a list of scalar values and Vectors as a texture, very useful
to display data from fractal, noise nodes and others, before outputting to a viewer_draw_mk2.

Uses OpenGl calls to display the data. This is a very stripped down version of the :doc:`Texture Viewer </nodes/viz/viewer_texture>` * node.

https://github.com/nortikin/sverchok/pull/1585

Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/190501138-44d2f1b2-d780-4cca-b52f-c20c7484325d.png
  :target: https://user-images.githubusercontent.com/14288520/190501138-44d2f1b2-d780-4cca-b52f-c20c7484325d.png

* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`