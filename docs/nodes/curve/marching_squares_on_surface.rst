Marching Squares on Surface
===========================

.. image:: https://user-images.githubusercontent.com/14288520/209465511-338c7076-3c26-4106-bdca-36bc5a8db283.png
  :target: https://user-images.githubusercontent.com/14288520/209465511-338c7076-3c26-4106-bdca-36bc5a8db283.png

Dependencies
------------

This node requires SkImage_ library to work.

.. _SkImage: https://scikit-image.org/

Functionality
-------------

This node uses Marching Squares_ algorithm to find iso-lines of a scalar field
on an arbitrary surface, i.e. lines for which the value of scalar field equals
to the given value at each point. The lines are generated as mesh - vertices
and edges. You can use one of interpoolation nodes to build Curve objects from
them.

.. _Squares: https://en.wikipedia.org/wiki/Marching_squares

.. image:: https://user-images.githubusercontent.com/14288520/209466874-7456e36b-9b90-44ae-994a-f8216ac87345.png
  :target: https://user-images.githubusercontent.com/14288520/209466874-7456e36b-9b90-44ae-994a-f8216ac87345.png

Inputs
------

This node has the following inputs:

* **Field**. Scalar field to generate iso-lines for. This input is mandatory.

.. image:: https://user-images.githubusercontent.com/14288520/209467485-6a6d7c4e-db29-4c5c-879d-50234ba3d025.png
  :target: https://user-images.githubusercontent.com/14288520/209467485-6a6d7c4e-db29-4c5c-879d-50234ba3d025.png

* **Surface**. The surface to draw iso-lines on. This input is mandatory.

.. image:: https://user-images.githubusercontent.com/14288520/209468044-c5e6ef77-e135-4a12-829c-ed20111056a6.png
  :target: https://user-images.githubusercontent.com/14288520/209468044-c5e6ef77-e135-4a12-829c-ed20111056a6.png

* **Value**. The value of scalar field, for which to generate iso-lines. The
  default value is 1.0.

.. image:: https://user-images.githubusercontent.com/14288520/209468136-e27b8450-aecb-4905-9cff-c40868f8c8d6.png
  :target: https://user-images.githubusercontent.com/14288520/209468136-e27b8450-aecb-4905-9cff-c40868f8c8d6.png

* **SamplesU**, **SamplesV**. Number of samples along U and V parameter of the
  surface, correspondingly. This defines the resolution of curves: the bigger
  isvalue, the more vertices will the node generate, and the more precise the
  curves will be. But higher resolutioln requires more computation time. The
  default value is 50 for both inputs.

.. image:: https://user-images.githubusercontent.com/14288520/209472279-1d451e4d-ae49-4286-bb8d-ef28462af018.png
  :target: https://user-images.githubusercontent.com/14288520/209472279-1d451e4d-ae49-4286-bb8d-ef28462af018.png

Parameters
----------

This node has the following parameters:

* **Join by surface**. If checked, then mesh objects generated for each
  separate contour on one surface will be merged into one mesh object.
  Otherwise, separate mesh object will be generated for each contour. Checked
  by default.
* **Connect boundary**. If checked, the node will connect pieces of the same
  curve, that was split because it was cut by the boundary of the surface.
  Otherwise, several separate pieces will be generated in such case. Note that
  this node can not currently detect if the surface is closed to glue parts of
  contours at different sides of the surface. Checked by default. 

.. image:: https://user-images.githubusercontent.com/14288520/209476502-77ebe3aa-bba9-4742-a9eb-6b1c70699b32.png
  :target: https://user-images.githubusercontent.com/14288520/209476502-77ebe3aa-bba9-4742-a9eb-6b1c70699b32.png

Outputs
-------

This node has the following outputs:

* **Vertices**. Generated iso-curves vertices in 3D space.
* **Edges**. Edges connecting iso-curve vertices.
* **UVVertices**. Points in surface's U/V space, corresponding to generated
  iso-curve vertices.

Examples of usage
-----------------

.. image:: https://user-images.githubusercontent.com/14288520/209476926-ad0c2122-376d-4b67-b7c5-4867407f96bd.png
  :target: https://user-images.githubusercontent.com/14288520/209476926-ad0c2122-376d-4b67-b7c5-4867407f96bd.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Surfaces-> :doc:`Plane (Surface) </nodes/surface/plane>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Fields-> :doc:`Attractor Field </nodes/field/attractor_field_mk2>`
* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* MUL: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Color-> :doc:`Color Ramp </nodes/color/color_ramp>`
* Scene-> :doc:`Frame Info </nodes/scene/frame_info_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/209477146-d5d43aa0-addf-43ae-810f-4c63ab2c9321.gif
  :target: https://user-images.githubusercontent.com/14288520/209477146-d5d43aa0-addf-43ae-810f-4c63ab2c9321.gif

---------

Find iso-curves of attractor field on a cylindrical surface:

https://gist.github.com/10ddbe4d04655dc8a1553c9b7fb68ee8

.. image:: https://user-images.githubusercontent.com/14288520/209477585-43439ece-2b69-4bbf-bfb4-342d8447050a.png
  :target: https://user-images.githubusercontent.com/14288520/209477585-43439ece-2b69-4bbf-bfb4-342d8447050a.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Curves-> :doc:`Circle (Curve) </nodes/curve/curve_circle>`
* Surfaces-> :doc:`Extrude Curve Along Vector </nodes/surface/extrude_vector>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Fields-> :doc:`Attractor Field </nodes/field/attractor_field_mk2>`
* Modifiers->Modifier Change-> :doc:`Merge by Distance </nodes/modifier_change/merge_by_distance>`
* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Matrix Multiply: Matrix-> :doc:`Matrix Math </nodes/matrix/matrix_math>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Color-> :doc:`Color Ramp </nodes/color/color_ramp>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/209477781-8a7c7a4d-afe6-4792-9006-949665a5e3c4.gif
  :target: https://user-images.githubusercontent.com/14288520/209477781-8a7c7a4d-afe6-4792-9006-949665a5e3c4.gif

---------

Another example with multiple surfaces (old image):

.. image:: https://user-images.githubusercontent.com/284644/87062516-91453880-c226-11ea-9df8-8903de6d2ae2.png

Restore with new nodes:

https://gist.github.com/f177b018f8871cad33dab532cbcd9ac3

.. image:: https://user-images.githubusercontent.com/14288520/209480860-e1329d38-c3fd-44d1-a97f-913c000771e2.png
  :target: https://user-images.githubusercontent.com/14288520/209480860-e1329d38-c3fd-44d1-a97f-913c000771e2.png

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Curves-> :doc:`Circle (Curve) </nodes/curve/curve_circle>`
* Curves-> :doc:`Surface Boundary </nodes/curve/surface_boundary>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Surfaces-> :doc:`Extrude Curve Along Vector </nodes/surface/extrude_vector>`
* Surfaces-> :doc:`Tesselate & Trim Surface </nodes/surface/tessellate_trim>`
* Fields-> :doc:`Attractor Field </nodes/field/attractor_field_mk2>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`