Empty out
==============

.. image:: https://user-images.githubusercontent.com/14288520/190487281-8477d806-c5af-4a69-b7f3-f8998ab53f22.png
  :target: https://user-images.githubusercontent.com/14288520/190487281-8477d806-c5af-4a69-b7f3-f8998ab53f22.png

Functionality
-------------

Making an Empty in scene from matrix in sverchok

Inputs
------

The most versatile input is Matrix (scale, rotation and location information), 
but the node accepts vectors as input too, vectors will only pass location information.

Parameters
----------

+-------------+-----------------------------------------------------------------------------------+
| Feature     | info                                                                              |
+=============+===================================================================================+
| Base name   | Name for new Empty objects                                                        |
+-------------+-----------------------------------------------------------------------------------+

Limitations
-----------

The node will read the first matrix or vector from the input stream, and use that to transform
or place the empty.

There is no mode to output multiple matrices if the input contains more than one.


Outputs
-------

Object - Emptys

Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/190487670-608066e3-4fb0-4b19-a85e-c5c4aa6a5f08.png
  :target: https://user-images.githubusercontent.com/14288520/190487670-608066e3-4fb0-4b19-a85e-c5c4aa6a5f08.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Transform-> :doc:`Randomize </nodes/transforms/randomize>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

Spy camera for Sphere fit center output:

.. image:: https://user-images.githubusercontent.com/14288520/197333285-3dceffda-ddc1-47ba-88cf-447267ce8459.png
  :target: https://user-images.githubusercontent.com/14288520/197333285-3dceffda-ddc1-47ba-88cf-447267ce8459.png

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator-> :doc:`Sphere </nodes/generator/sphere>`
* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`
* Analyzers-> :doc:`Sphere fit </nodes/analyzer/sphere_approx>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/197333322-816f3841-e55b-4952-a426-9a0511538c24.gif
  :target: https://user-images.githubusercontent.com/14288520/197333322-816f3841-e55b-4952-a426-9a0511538c24.gif

See limitations.