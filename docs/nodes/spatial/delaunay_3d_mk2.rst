Delaunay 3D
===========

.. image:: https://user-images.githubusercontent.com/14288520/202203897-2d69a159-b90b-4150-ac8b-d63d63971d6d.png
  :target: https://user-images.githubusercontent.com/14288520/202203897-2d69a159-b90b-4150-ac8b-d63d63971d6d.png

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node generaets a Delaunay_ triangulation for a set of points in 3D space.

.. _Delaunay: https://en.wikipedia.org/wiki/Delaunay_triangulation

In many cases, Delaunay triangulation in 3D tends to generate almost flat
tetrahedrons on the boundary. This node can automatically skip generation of
such tetrahedrons.

.. image:: https://user-images.githubusercontent.com/14288520/202204616-f9bfbe0b-8852-4581-9810-ba063a7f603b.png
  :target: https://user-images.githubusercontent.com/14288520/202204616-f9bfbe0b-8852-4581-9810-ba063a7f603b.png

.. image:: https://user-images.githubusercontent.com/14288520/202203843-cbb301f8-0bb3-431b-a52d-3caa50e97a4c.gif
  :target: https://user-images.githubusercontent.com/14288520/202203843-cbb301f8-0bb3-431b-a52d-3caa50e97a4c.gif

Inputs
------

This node has the following inputs:

* **Vertices**. The vertices to generate Delaunay triangulation for. This input is mandatory.
* **PlanarThreshold**. This defines the threshold used to filter "too flat"
  tetrahedrons out. Smaller values of threshold mean more "almost flat"
  tetrahedrons will be generated. Set this to 0 to skip this filtering step and
  allow to generate any tetrahedrons. The default value is 0.0001.
* **EdgeThreshold**. This defines the threshold used to filter "too long"
  tetrahedrons out. Tetrahedrons which have one of their edges longer than
  value specified here will not be generated. Set this to 0 to skip this
  filtering step and allow to generate any tetrahedrons. The default value is 0
  (no filtering).

Parameters
----------

This node has the following parameter:

* **Join**. If checked, then the node will generate one mesh object, composed
  of all faces of all tetrahedrons (without duplicating vertices and faces).
  Otherwise, the node will generate a separate mesh object for each
  tetrahedron. Unchecked by default.

Outputs
-------

This node has the following outputs:

* **Vertices**. Vertices of the Delaunay triangulation.
* **Edges**. Edges of the Delaunay triangulation.
* **Faces**. Faces of the Delaunay triangulation.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/14288520/202234630-06b8cca7-31c7-424d-a27b-38232645b0c8.png
  :target: https://user-images.githubusercontent.com/14288520/202234630-06b8cca7-31c7-424d-a27b-38232645b0c8.png

* Spacial-> :doc:`Vector P Field </nodes/spatial/homogenous_vector_field>`
* Transform-> :doc:`Scale </nodes/transforms/scale_mk3>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Analyzers-> :doc:`Origins </nodes/analyzer/origins>`
* Analyzers-> :ref:`Component Analyzer/Faces/Center <FACES_CENTER>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* List->List Struct-> :doc:`List Levels </nodes/list_struct/levels>`
* Color-> :doc:`Color Ramp </nodes/color/color_ramp>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/202456423-a678eadd-7124-40fc-977d-fdc24a76b013.gif
  :target: https://user-images.githubusercontent.com/14288520/202456423-a678eadd-7124-40fc-977d-fdc24a76b013.gif

---------

.. image:: https://user-images.githubusercontent.com/14288520/202235904-aa9b6651-ac03-4860-978b-6957b4ad4b0e.png
  :target: https://user-images.githubusercontent.com/14288520/202235904-aa9b6651-ac03-4860-978b-6957b4ad4b0e.png

* Spacial-> :doc:`Vector P Field </nodes/spatial/homogenous_vector_field>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`