Mesh Smoothed Surface Field
===========================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/b85cd338-7f80-4e59-9d3f-40dbd422b628
  :target: https://github.com/nortikin/sverchok/assets/14288520/b85cd338-7f80-4e59-9d3f-40dbd422b628

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node generates a Scalar Field, which has value of zero at some "key"
points of a given mesh, and value of 1 at the ends of normals of the mesh at
these points. Points to be considered as "key" can be mesh's vertices, middle
points of edges, and centers of faces. Between the described points, the field
is interpolated by use of RBF_ method. Depending on "smooth" parameter, the
generated field can be approximating rather than interpolating.

The field generated by this rule has it's iso-surface at zero level in a
general shape of the source mesh, but smoothed.

.. _RBF: http://www.scholarpedia.org/article/Radial_basis_function

.. image:: https://github.com/nortikin/sverchok/assets/14288520/62991279-9cd5-4e74-8485-ab8d26c3f764
  :target: https://github.com/nortikin/sverchok/assets/14288520/62991279-9cd5-4e74-8485-ab8d26c3f764

With real mesh you can get very funny results:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/4ec8fb67-478b-4fae-8d19-1ea25ea1b2ab
  :target: https://github.com/nortikin/sverchok/assets/14288520/4ec8fb67-478b-4fae-8d19-1ea25ea1b2ab

.. image:: https://github.com/nortikin/sverchok/assets/14288520/6243151d-c48d-4e82-9400-a4a81501e2e5
  :target: https://github.com/nortikin/sverchok/assets/14288520/6243151d-c48d-4e82-9400-a4a81501e2e5

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Surfaces-> :doc:`Marching Cubes </nodes/surface/marching_cubes>`
* Matrix-> :doc:`Matrix Apply to Mesh </nodes/matrix/apply_and_join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Get Objects Data </nodes/scene/get_objects_data>`

Inputs
------

This node has the following inputs:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/e14e3caf-6dca-4b45-adc8-f2bb7eea7c1e
  :target: https://github.com/nortikin/sverchok/assets/14288520/e14e3caf-6dca-4b45-adc8-f2bb7eea7c1e

* **Vertices**. The vertices of the source mesh. This input is mandatory.
* **Edges**. The edges of the source mesh.
* **Faces**. The faces of the source mesh. This input is mandatory.
* **Epsilon**. Epsilon parameter of used RBF function; it affects the shape of
  generated field. The default value is 1.0.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/7d57ca8d-9d24-495d-be72-02515b3b44b3
      :target: https://github.com/nortikin/sverchok/assets/14288520/7d57ca8d-9d24-495d-be72-02515b3b44b3

* **Smooth**. Smoothness parameter of used RBF function. If this is zero, then
  the field will have exactly the specified values in all provided points;
  otherwise, it will be only an approximating field. The default value is 0.0.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/3fa4fc26-7ec7-4943-8ce8-d37276a1b43d
      :target: https://github.com/nortikin/sverchok/assets/14288520/3fa4fc26-7ec7-4943-8ce8-d37276a1b43d

* **Scale**. This defines the distance along the normals of the mesh, at which
  the field should have the value of 1. The default value is 1.0.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/726dd2c7-9208-47eb-bd34-692dfe405f5e
      :target: https://github.com/nortikin/sverchok/assets/14288520/726dd2c7-9208-47eb-bd34-692dfe405f5e


Parameters
----------

This node has the following parameters:

* **Function**. The specific function used by the node. The available values are:

  * Multi Quadric

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/340e868d-f2c1-4ddb-a14c-8a1b53e625e7
      :target: https://github.com/nortikin/sverchok/assets/14288520/340e868d-f2c1-4ddb-a14c-8a1b53e625e7

  * Inverse

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/201acf74-1e27-4ebd-a783-e63316173164
      :target: https://github.com/nortikin/sverchok/assets/14288520/201acf74-1e27-4ebd-a783-e63316173164

  * Gaussian

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/f8eef86a-c74c-4e88-8b9c-f9944ca82c58
      :target: https://github.com/nortikin/sverchok/assets/14288520/f8eef86a-c74c-4e88-8b9c-f9944ca82c58

  * Cubic

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/9f6a5d7a-cb8c-48cc-a3e8-7bba4a8e8a2f
      :target: https://github.com/nortikin/sverchok/assets/14288520/9f6a5d7a-cb8c-48cc-a3e8-7bba4a8e8a2f

  * Quintic

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/789132e0-ec4e-478a-8e69-9b1b1a1aa1eb
      :target: https://github.com/nortikin/sverchok/assets/14288520/789132e0-ec4e-478a-8e69-9b1b1a1aa1eb

  * Thin Plate

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/f30460ac-78f3-4e12-9eb5-f70b1c929ed6
      :target: https://github.com/nortikin/sverchok/assets/14288520/f30460ac-78f3-4e12-9eb5-f70b1c929ed6

  The default function is Multi Quadric.

* **Use Vertices**. If checked, then the generated scalar field will have value
  of zero at locations of mesh's vertices. Checked by default.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/95a33bec-64db-474a-bb4d-05c16c84c099 
      :target: https://github.com/nortikin/sverchok/assets/14288520/95a33bec-64db-474a-bb4d-05c16c84c099

* **Use Edges**. If checked, then the generated scalar field will have value of
  zero at middle points of mesh's edges. Unchecked by default.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/2aa41903-a48f-472d-80a7-37b223798f14
      :target: https://github.com/nortikin/sverchok/assets/14288520/2aa41903-a48f-472d-80a7-37b223798f14

* **Use Faces**. If checked, then the generated scalar field will have value of
  zero at centers of mesh's faces. Unchecked by default.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/85bb38d7-570d-45e0-82a4-1360448a4377
      :target: https://github.com/nortikin/sverchok/assets/14288520/85bb38d7-570d-45e0-82a4-1360448a4377

Outputs
-------

This node has the following output:

* **Field**. The generated scalar field.

Example of Usage
----------------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/7821c460-8521-4b1a-8633-0b352fa434e8
  :target: https://github.com/nortikin/sverchok/assets/14288520/7821c460-8521-4b1a-8633-0b352fa434e8

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Surfaces-> :doc:`Marching Cubes </nodes/surface/marching_cubes>`
* Analyzers-> :ref:`Component Analyzer/Vertices/Matrix <VERTICES_MATRIX>`
* CAD-> :doc:`Inset Special </nodes/CAD/inset_special_mk2>`
* Modifiers->Modifier Change-> :doc:`Polygon to Edges </nodes/modifier_change/polygons_to_edges_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`


.. image:: https://github.com/nortikin/sverchok/assets/14288520/226a8aad-0384-4556-976e-0b442821474c
  :target: https://github.com/nortikin/sverchok/assets/14288520/226a8aad-0384-4556-976e-0b442821474c

---------

In combination with "Marching Cubes" node this can be used to generate a smoothened version of the source mesh:

.. image:: https://user-images.githubusercontent.com/284644/103563698-04322200-4edf-11eb-9dca-583aea877d80.png
  :target: https://user-images.githubusercontent.com/284644/103563698-04322200-4edf-11eb-9dca-583aea877d80.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Bounds: Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Surfaces-> :doc:`Marching Cubes </nodes/surface/marching_cubes>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`