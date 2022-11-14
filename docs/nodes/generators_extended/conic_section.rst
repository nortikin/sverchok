Conic Sections
==============

.. image:: https://user-images.githubusercontent.com/14288520/191024304-42fbb161-7e21-4937-b632-fd8b1ff8d60a.png
  :target: https://user-images.githubusercontent.com/14288520/191024304-42fbb161-7e21-4937-b632-fd8b1ff8d60a.png

.. image:: https://user-images.githubusercontent.com/14288520/191024313-4ef6ba13-f6ca-47e7-9917-f6c0ffbfaa5d.png
  :target: https://user-images.githubusercontent.com/14288520/191024313-4ef6ba13-f6ca-47e7-9917-f6c0ffbfaa5d.png

Functionality
-------------

This node generates conic sections_ by definition: by generating an (endless)
cone, (endless) plane and calculating their intersection. As we know, the
intersection may be an ellipse, a parabola or a hyperbola:

.. image:: https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Conic_sections_with_plane.svg/1920px-Conic_sections_with_plane.svg.png

A cone_ may be defined by either

* A point (which is called apex or vertex), axis direction vector and an angle between generatrix and axis;
* Or an apex, axis direction vector and a generatrix direction vector.

A plane is defined by a point and a normal vector.

.. _sections: https://en.wikipedia.org/wiki/Conic_section
.. _cone: https://en.wikipedia.org/wiki/Cone

Inputs
------

This node has the following inputs:

- **ConeApex**. An apex point of the cone. The default value is `(0, 0, 0)`.
- **ConeDirection**. Cone axis direction vector. The default value is `(0, 0, 1)`.
- **Count**. Count of generatrices to generate. This defines the maximum number
  of vertices this node can generate. Actual number of vertices may be fewer,
  because some generatrices may not intersect the specified plane. The default
  value is 16.
- **Generatrix**. Cone generatrix direction vector. This input is available
  only if cone definition mode parameter is set to **Generatrix**. The default
  value is `(0, 1, 1)`.
- **ConeAngle**. An angle between cone axis and it's generatrix. This input is
  available only if cone definition mode parameter is set to **Angle**. The
  default value is `pi/6`.
- **Max Distance**. Maximum distance between cone apex and generated vertices.
  Vertices that are farther from apex will not be generated. The default value
  is 100.
- **PlanePoint**. A point lying on a plane (used to define the plane). The
  default value is `(0, 0, 1)`.
- **PlaneDirection**. A normal vector of a plane (used to define the plane).
  The default value is `(0, 0, 1)`.

Parameters
----------

This node has the following parameters:

- **Define Cone**. Specifies the way of defining the cone. Available values are
  **Angle** and **Generatrix**. The default value is **Angle**.
- **Even Distribution**. If checked, then generated vertices will be evenly
  distributed across the generated curve. Otherwise, positions of generated
  vertices will be defined by intersections of the cone generatrices and the
  specified plane. Unchecked by default.
- **Interpolation Mode**. Defines the way of interpolating vertices location in
  case when **Even Distribution** parameter is checked. Available values are
  **Linear** and **Cubic**. The default value is **Linear**.

Outputs
-------

The node has the following outputs:

- **Vertices**. The vertices of the output curve.
- **Edges**. The edges of the output curve.
- **BranchMask**. Mask values defining to which curve branch does the curve
  vertex belong. This is useful for hyperbolas only. For other curves, this
  output will contain all 0s or all 1s.
- **SideMask**. Mask values defining to which side of the curve does the vertex
  belong ("right" or "left"). For cases when sides of the curve can not be
  distinguished (for circles, for example), this output will contain all 1s.

Examples of Usage
-----------------

Classic parabola is defined by a cone and a plane which is parallel to cone's generatrix:

.. image:: https://user-images.githubusercontent.com/14288520/191026502-3dcb987b-e96a-464c-8136-87d45c748c6c.png
  :target: https://user-images.githubusercontent.com/14288520/191026502-3dcb987b-e96a-464c-8136-87d45c748c6c.png

* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

The same parabola but with "even distribution" turned on:

.. image:: https://user-images.githubusercontent.com/14288520/191027131-efbe2d50-5b75-4ce5-8204-c380ed9f6cbd.png
  :target: https://user-images.githubusercontent.com/14288520/191027131-efbe2d50-5b75-4ce5-8204-c380ed9f6cbd.png

* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Classic ellipse is defined by a cone and a plane which intersects the cone at some random angle:

.. image:: https://user-images.githubusercontent.com/14288520/191028981-25da9d63-21dc-4529-84b7-e40fa6f45254.png
  :target: https://user-images.githubusercontent.com/14288520/191028981-25da9d63-21dc-4529-84b7-e40fa6f45254.png

* Curves-> :doc:`Curve Segment </nodes/curve/curve_segment>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

One can generate a series of curves by intersecting one cone with a series of planes at different angles:

.. image:: https://user-images.githubusercontent.com/14288520/191033693-9ddaca46-614c-45b4-b038-e153e4230006.png
  :target: https://user-images.githubusercontent.com/14288520/191033693-9ddaca46-614c-45b4-b038-e153e4230006.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Vector-> :doc:`Vector Polar Input </nodes/vector/vector_polar_in>`
* Vector-> :doc:`Vector Rewire </nodes/vector/vector_rewire>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

One can generate a hyperbola (2-branched curve) and then use it to generate 1-sheet hyperboloid

.. image:: https://user-images.githubusercontent.com/14288520/191035609-4353b6d8-f1f8-4c60-8cb6-f9b5ba25103f.png
  :target: https://user-images.githubusercontent.com/14288520/191035609-4353b6d8-f1f8-4c60-8cb6-f9b5ba25103f.png

* Modifiers->Modifier Change-> :doc:`Mask Vertices </nodes/modifier_change/vertices_mask>`
* CAD-> :doc:`Lathe </nodes/modifier_make/lathe>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

or 2-sheet hyperboloid

.. image:: https://user-images.githubusercontent.com/14288520/191035963-1cb09de2-dc4f-426a-b70a-faa3ad1dc263.png
  :target: https://user-images.githubusercontent.com/14288520/191035963-1cb09de2-dc4f-426a-b70a-faa3ad1dc263.png

* Modifiers->Modifier Change-> :doc:`Mask Vertices </nodes/modifier_change/vertices_mask>`
* CAD-> :doc:`Lathe </nodes/modifier_make/lathe>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

There are more examples `in the original thread <https://github.com/nortikin/sverchok/pull/2636>`_.