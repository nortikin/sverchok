Voronoi Sphere
==============

.. image:: https://user-images.githubusercontent.com/14288520/202409878-c87ed16b-e69c-4197-9f24-1a046f4b9e5e.png
  :target: https://user-images.githubusercontent.com/14288520/202409878-c87ed16b-e69c-4197-9f24-1a046f4b9e5e.png

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node generates a Voronoi_ diagram for set of points (sites) on a spherical
surface. If provided vertices are not lying on a sphere, they will be projected
to the sphere first.

.. _Voronoi: https://en.wikipedia.org/wiki/Voronoi_diagram

Inputs
------

This node has the following inputs:

* **Vertices**. The vertices to generate a Voronoi diagram for. This input is
  mandatory.
* **Center**. The sphere center. The default value is ``(0, 0, 0)``.
* **Radius**. The sphere radius. The default value is 1.0.

Outputs
-------

This node has the following outputs:

* **Vertices**. Vertices of the generated Voronoi diagram.
* **Edges**. Edges of the generated diagram.
* **Faces**. Faces of the generated diagram.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/87226285-38071180-c3ac-11ea-84c7-a875e4980e08.png
  :target: https://user-images.githubusercontent.com/284644/87226285-38071180-c3ac-11ea-84c7-a875e4980e08.png

* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/202413761-90444865-5203-42a1-943b-71405bec8d4e.png
  :target: https://user-images.githubusercontent.com/14288520/202413761-90444865-5203-42a1-943b-71405bec8d4e.png

* Spacial-> :doc:`Vector P Field </nodes/spatial/homogenous_vector_field>`
* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/202414553-340928fe-6163-44f6-81a5-1fc72ee8bd13.gif
  :target: https://user-images.githubusercontent.com/14288520/202414553-340928fe-6163-44f6-81a5-1fc72ee8bd13.gif