Solidify
========

.. image:: https://user-images.githubusercontent.com/14288520/201440855-0564d90d-6654-42d9-980c-2f856b57d4f0.png
  :target: https://user-images.githubusercontent.com/14288520/201440855-0564d90d-6654-42d9-980c-2f856b57d4f0.png

Extrudes a mesh along its normal. Used usually to get a thick mesh from a planar mesh.

.. image:: https://user-images.githubusercontent.com/14288520/201441550-c1a3bb63-693d-48b3-a8f1-8144296f4c12.png
  :target: https://user-images.githubusercontent.com/14288520/201441550-c1a3bb63-693d-48b3-a8f1-8144296f4c12.png

Inputs
------


* **Vertices**: Mesh Vertices (mandatory)
* **Edges**: Mesh Edges (optional, if you want to output edges makes the algorithm faster)
* **Polygons**: Mesh Polygons (mandatory)
* **Thickness**: Distance to extrude

.. image:: https://user-images.githubusercontent.com/14288520/201442046-b93db529-8e17-47b7-995b-82acf469f27c.gif
  :target: https://user-images.githubusercontent.com/14288520/201442046-b93db529-8e17-47b7-995b-82acf469f27c.gif

* **Offset**: Relative offset from original mesh [-1.0; 1.0]

.. image:: https://user-images.githubusercontent.com/14288520/201442148-7ef38073-ee87-48a1-98ed-6a247687a0db.gif
  :target: https://user-images.githubusercontent.com/14288520/201442148-7ef38073-ee87-48a1-98ed-6a247687a0db.gif

Options
-------

* **Even**: adjust thickness in sharp corners to have a even thickness.

.. image:: https://user-images.githubusercontent.com/14288520/201442415-7e840cc4-af94-43b0-b4ee-0cf93c715832.gif
  :target: https://user-images.githubusercontent.com/14288520/201442415-7e840cc4-af94-43b0-b4ee-0cf93c715832.gif

* **Implementation**: Algorithm used to compute.

  - Sverchok: Faster all with more options
  - Blender: Old method, left because it may differ in some corner cases

Outputs
-------

* **Vertices**, **Edges**, **Polygons**: Modified mesh
* **New Pols**: New opposite polygons (in the same order as the originals)
* **Rim Pols**: Side Polygons created in the boundaries of the mesh
* **Pols Group**: Outputs a list to mask polygons from the modified mesh,

  - 0 = Original Polygon
  - 1 = New Polygon
  - 2 = Rim Polygon

* **New Verts Mask**: To split old vertices form new vertices

.. image:: https://user-images.githubusercontent.com/14288520/201444252-0c1d3bef-78c5-4527-8870-32c3ae2cb30e.png
  :target: https://user-images.githubusercontent.com/14288520/201444252-0c1d3bef-78c5-4527-8870-32c3ae2cb30e.png

* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

Examples
--------

Using variable thickness:

.. image:: https://user-images.githubusercontent.com/14288520/201444780-ff1a1ac7-c6ec-4215-8638-6f40bd38db81.png
  :target: https://user-images.githubusercontent.com/14288520/201444780-ff1a1ac7-c6ec-4215-8638-6f40bd38db81.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Vector-> :doc:`Vector Noise </nodes/vector/noise_mk3>`
* Number-> :doc:`Map Range </nodes/number/range_map>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Splitting Data: New Vertices in white, Old vertices in black, New Polys in grey, Rim Polys in white...

.. image:: https://user-images.githubusercontent.com/14288520/201445261-ebbee6d5-8e1a-4f85-a9fa-f05123d5efcd.png
  :target: https://user-images.githubusercontent.com/14288520/201445261-ebbee6d5-8e1a-4f85-a9fa-f05123d5efcd.png

* Generator-> :doc:`Cylinder </nodes/generator/cylinder_mk2>`
* DIV: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`