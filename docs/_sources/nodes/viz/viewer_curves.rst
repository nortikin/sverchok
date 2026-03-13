Curve Viewer
============

.. image:: https://user-images.githubusercontent.com/14288520/190258815-66ddd5bc-b8b9-49fc-9863-9ea76efe8fb6.png
  :target: https://user-images.githubusercontent.com/14288520/190258815-66ddd5bc-b8b9-49fc-9863-9ea76efe8fb6.png

.. image:: https://user-images.githubusercontent.com/14288520/190258592-e193710e-01bd-4bdd-b3b0-40fec9fd3781.png
  :target: https://user-images.githubusercontent.com/14288520/190258592-e193710e-01bd-4bdd-b3b0-40fec9fd3781.png

Functionality
-------------

This node takes ``verts`` and ``edges`` and makes straight sections of Curve to represent them. Like a pipe, but without smooth transitions between pipes. Each edge is truly disjoint and the renderable geometry can overlap.

This is useful for quickly generating renderable lightweight geometry for scaffolding, beams, pillars, plynths, tubes, fences, neon signage.

.. image:: https://user-images.githubusercontent.com/619340/127735005-6eeafb79-a8df-4037-9594-8e651c0d3d01.png
    :target: https://user-images.githubusercontent.com/619340/127735005-6eeafb79-a8df-4037-9594-8e651c0d3d01.png

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Transform-> :doc:`Matrix Apply (verts) </nodes/transforms/apply>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* MUL X, YSINX X, ADD X: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`

---------

The node has a 2d and 3d mode, in 2D mode you can make interesting 2d booleans on the XY axis. The features are limited to what Blender offers.

.. image:: https://user-images.githubusercontent.com/619340/127735158-0f4a8341-dc04-4dac-a7b6-6546a2c5ceea.png
    :target: https://user-images.githubusercontent.com/619340/127735158-0f4a8341-dc04-4dac-a7b6-6546a2c5ceea.png

* Generator-> :doc:`Circle </nodes/generator/circle>`
* Number-> :doc:`Number Range </nodes/number/number_range>`

inputs
------

verts, edges, and matrix


output
------

directly into the scene, the node has no Object output socket. yet.

