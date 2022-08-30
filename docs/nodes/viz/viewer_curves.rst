Curve Viewer
============

Functionality
-------------

This node takes ``verts`` and ``edges`` and makes straight sections of Curve to represent them. Like a pipe, but without smooth transitions between pipes. Each edge is truly disjoint and the renderable geometry can overlap.

This is useful for quickly generating renderable lightweight geometry for scaffolding, beams, pillars, plynths, tubes, fences, neon signage.

.. image:: https://user-images.githubusercontent.com/619340/127735005-6eeafb79-a8df-4037-9594-8e651c0d3d01.png

The node has a 2d and 3d mode, in 2D mode you can make interesting 2d booleans on the XY axis. The features are limited to what Blender offers.

.. image:: https://user-images.githubusercontent.com/619340/127735158-0f4a8341-dc04-4dac-a7b6-6546a2c5ceea.png

inputs
------

verts, edges, and matrix


output
------

directly into the scene, the node has no Object output socket. yet.

