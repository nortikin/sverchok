Select Mesh Elements
====================

.. image:: https://user-images.githubusercontent.com/14288520/197348551-a2d5c2ae-f213-47e6-becc-7a02bc563e50.png
  :target: https://user-images.githubusercontent.com/14288520/197348551-a2d5c2ae-f213-47e6-becc-7a02bc563e50.png

Functionality
-------------

This node allows to select mesh elements (vertices, edges and faces) by their geometrical location, by one of supported criteria.

You can combine different criteria by applying several instances of this node and combining masks with Logic node.

Inputs
------

This node has the following inputs:

- **Vertices**
- **Edges**
- **Faces**
- **Direction**. Direction vector. Used in modes: **By side**, **By normal**, **By plane**, **By cylinder**. Exact meaning depends on selected mode.
- **Center**. Center or base point. Used in modes: **By sphere**, **By plane**, **By cylinder**, **By bounding box**.
- **Percent**. How many vertices to select. Used in modes: **By side**, **By normal**.
- **Radius**. Allowed distance from center, or line, or plane, to selected vertices. Used in modes: **By sphere**, **By plane**, **By cylinder**, **By bounding box**.

Parameters
----------

This node has the following parameters:

- **Mode**. Criteria type to apply. Supported criteria are:

  * **By side**. :ref:`Selects vertices that are located at one side of mesh<MODE_BY_SIDE>`. The side is specified by **Direction** input. So you can select "rightmost" vertices by passing (0, 0, 1) as Direction. Number of vertices to select is controlled by **Percent** input: 1% means select only "most rightmost" vertices, 99% means select "all but most leftmost". More exactly, this mode selects vertex V if `(Direction, V) >= max - Percent * (max - min)`, where `max` and `min` are maximum and minimum values of that scalar product amongst all vertices.
  * **By normal direction**. :ref:`Selects faces, that have normal vectors pointing in specified Direction<MODE_BY_NORMAL_DIRECTION>`. So you can select "faces looking to right". Number of faces to select is controlled by **Percent** input, similar to **By side** mode. More exactly, this mode selects face F if `(Direction, Normal(F)) >= max - Percent * (max - min)`, where `max` and `min` are maximum and minimum values of that scalar product amongst all vertices.
  * **By center and radius**. :ref:`Selects vertices, which are within Radius from specified Center<MODE_BY_CENTER_AND_RADIUS>`; in other words, it selects vertices that are located inside given sphere. More exactly, this mode selects vertex V if `Distance(V, Center) <= Radius`. This mode also supports passing many points to **Center** input; in this case, "Distance" is distance from vertex to the nearest "Center".
  * **By plane**. :ref:`Selects vertices, which are within Radius from specified plane<MODE_BY_PLANE>`. Plane is specified by providing normal vector (**Direction** input) and a point, belonging to that plane (**Center** input). For example, if you specify Direction = (0, 0, 1) and Center = (0, 0, 0), the plane will by OXY. More exactly, this mode selects vertex V if `Distance(V, Plane) <= Radius`.
  * **By cylinder**. :ref:`Selects vertices, which are within Radius from specified straight line<MODE_BY_CYLINDER>`. Line is specified by providing directing vector (**Direction** input) and a point, belonging to that line (**Center** input). For example, if you specify Direction = (0, 0, 1) and Center = (0, 0, 0), the line will by Z axis. More exactly, this mode selects vertex V if `Distance(V, Line) <= Radius`.
  * **By edge direction**. :ref:`Selects edges, which are nearly parallel to specified Direction vector<MODE_BY_EDGE_DIRECTION>`. Note that this mode considers edges as non-directed; as a result, you can change sign of all coordinates of **Direction** and it will not affect output. More exactly, this mode selects edge E if `Abs(Cos(Angle(E, Direction))) >= max - Percent * (max - min)`, where max and min are maximum and minimum values of that cosine.
  * **Normal pointing outside**. Selects faces, that have normal vectors pointing outside from specified **Center**. So you can select "faces looking outside". Number of faces to select is controlled by **Percent** input. More exactly, this mode selects face F if `Angle(Center(F) - Center, Normal(F)) >= max - Percent * (max - min)`, where max and min are maximum and minimum values of that angle.
  * **By bounding box**. :ref:`Selects vertices, that are within bounding box defined by points passed into Center input<MODE_BY_BOUNDING_BOX>`. **Radius** is interpreted as tolerance limit. For examples:

    - If one point `(0, 0, 0)` is passed, and Radius = 1, then the node will select all vertices that have `-1 <= X <= 1`, `-1 <= Y <= 1`, `-1 <= Z <= 1`.
    - If points `(0, 0, 0)`, `(1, 2, 3)` are passed, and Radius = 0.5, then the node will select all vertices that have `-0.5 <= X <= 1.5`, `-0.5 <= Y <= 2.5`, `-0.5 <= Z <= 3.5`.
- **Include partial selection**. Not available in **By normal** mode. All other modes select vertices first. This parameter controls either we need to select edges and faces that have **any** of vertices selected (Include partial = True), or only edges and faces that have **all** vertices selected (Include partial = False).

.. image:: https://user-images.githubusercontent.com/14288520/197355140-b84f32bf-79c1-45d5-a060-d301dc10f100.png
  :target: https://user-images.githubusercontent.com/14288520/197355140-b84f32bf-79c1-45d5-a060-d301dc10f100.png

- **Level**. Data nesting level to work with. Default (and minimum) value is 2,
  which means that the node's **Vertices** input will expect a list of lists of
  vertices, and the node will output list of lists of booleans; i.e. node will
  process a list of meshes, as most of nodes usually do. With **Level** of 3,
  the node will expect a list of lists of meshes, and output a list of lists of
  lists of booleans; and so on.

Outputs
-------

This node has the following outputs:

- **VerticesMask**. Mask for selected vertices.
- **EdgesMask**. Mask for selected edges. Please note that this mask relates to list of vertices provided at node input, not list of vertices selected by this node.
- **FacesMask**. Mask for selected faces. Please note that this mask relates to list of vertices provided at node input, not list of vertices selected by this node.

.. _MODE_BY_SIDE:

Mode - By Side
--------------

Selects vertices that are located at one side of mesh. The side is specified by **Direction** input. So you can select "rightmost" vertices by passing (0, 0, 1) as Direction. Number of vertices to select is controlled by **Percent** input: 1% means select only "most rightmost" vertices, 99% means select "all but most leftmost". More exactly, this mode selects vertex V if `(Direction, V) >= max - Percent * (max - min)`, where `max` and `min` are maximum and minimum values of that scalar product amongst all vertices.

.. image:: https://user-images.githubusercontent.com/14288520/197350451-1c209494-153e-4f82-9758-f4f22983fddc.png
  :target: https://user-images.githubusercontent.com/14288520/197350451-1c209494-153e-4f82-9758-f4f22983fddc.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Vector-> :doc:`Vector Polar Input </nodes/vector/vector_polar_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/197350918-26a4a94e-7ad8-4c59-a4d3-fb9356cfab21.gif
  :target: https://user-images.githubusercontent.com/14288520/197350918-26a4a94e-7ad8-4c59-a4d3-fb9356cfab21.gif

---------

.. image:: https://user-images.githubusercontent.com/14288520/197352357-a5133a0e-9556-45a9-8095-485b8595c5af.png
  :target: https://user-images.githubusercontent.com/14288520/197352357-a5133a0e-9556-45a9-8095-485b8595c5af.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator->Generators Extended :doc:`Torus Knot </nodes/generators_extended/torus_knot_mk2>`
* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Surfaces-> :doc:`Pipe Surface Along Curve </nodes/surface/pipe>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Vector-> :doc:`Vector Polar Input </nodes/vector/vector_polar_in>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/197351814-c5cc0ae0-b56e-4c19-ba36-197443bb0acb.gif
  :target: https://user-images.githubusercontent.com/14288520/197351814-c5cc0ae0-b56e-4c19-ba36-197443bb0acb.gif

.. _MODE_BY_NORMAL_DIRECTION:

Mode - By Normal Direction
--------------------------

Selects faces, that have normal vectors pointing in specified **Direction**. So you can select "faces looking to right". Number of faces to select is controlled by **Percent** input, similar to **By side** mode. More exactly, this mode selects face F if `(Direction, Normal(F)) >= max - Percent * (max - min)`, where `max` and `min` are maximum and minimum values of that scalar product amongst all vertices.

.. image:: https://user-images.githubusercontent.com/14288520/197353517-6383bd19-151c-4ab9-9601-e385bbd92e60.png
  :target: https://user-images.githubusercontent.com/14288520/197353517-6383bd19-151c-4ab9-9601-e385bbd92e60.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Analyzers-> :doc:`Origins </nodes/analyzer/origins>`
* Vector-> :doc:`Vector Polar Input </nodes/vector/vector_polar_in>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/197353693-1e6c029d-ebe3-4e4d-8161-383055683415.gif
  :target: https://user-images.githubusercontent.com/14288520/197353693-1e6c029d-ebe3-4e4d-8161-383055683415.gif

---------

.. image:: https://user-images.githubusercontent.com/14288520/197354223-637bf456-cb3b-458d-b1b6-250205a4ac0c.png
  :target: https://user-images.githubusercontent.com/14288520/197354223-637bf456-cb3b-458d-b1b6-250205a4ac0c.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`Torus </nodes/generator/torus_mk2>`
* Analyzers-> :doc:`Origins </nodes/analyzer/origins>`
* Vector-> :doc:`Vector Polar Input </nodes/vector/vector_polar_in>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/197354299-304aefc1-9374-4c83-ac3b-8de4b8f0a747.gif
  :target: https://user-images.githubusercontent.com/14288520/197354299-304aefc1-9374-4c83-ac3b-8de4b8f0a747.gif

.. _MODE_BY_CENTER_AND_RADIUS:

Mode - By Center and Radius
---------------------------

Selects vertices, which are within Radius from specified **Center**; in other words, it selects vertices that are located inside given sphere. More exactly, this mode selects vertex V if `Distance(V, Center) <= Radius`. This mode also supports passing many points to **Center** input; in this case, "Distance" is distance from vertex to the nearest "Center".

.. image:: https://user-images.githubusercontent.com/14288520/197355447-89fc4aac-8178-4175-ba5a-150d53ff5bc4.png
  :target: https://user-images.githubusercontent.com/14288520/197355447-89fc4aac-8178-4175-ba5a-150d53ff5bc4.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Sphere </nodes/generator/sphere>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/197355253-a631e319-ddd9-4b08-b8d5-f160cc80eafa.gif
  :target: https://user-images.githubusercontent.com/14288520/197355253-a631e319-ddd9-4b08-b8d5-f160cc80eafa.gif

.. _MODE_BY_PLANE:

Mode - By Plane
---------------

Selects vertices, which are within **Radius** from specified plane. Plane is specified by providing normal vector (**Direction** input) and a point, belonging to that plane (**Center** input). For example, if you specify Direction = (0, 0, 1) and Center = (0, 0, 0), the plane will by OXY. More exactly, this mode selects vertex V if `Distance(V, Plane) <= Radius`.

.. image:: https://user-images.githubusercontent.com/14288520/197356952-2ecd3971-f8ef-4014-8b1f-483e3d219a68.png
  :target: https://user-images.githubusercontent.com/14288520/197356952-2ecd3971-f8ef-4014-8b1f-483e3d219a68.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix Apply to Mesh </nodes/matrix/apply_and_join>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/197357111-a954f4e4-c227-4046-874a-079a5db99b7f.gif
  :target: https://user-images.githubusercontent.com/14288520/197357111-a954f4e4-c227-4046-874a-079a5db99b7f.gif

.. _MODE_BY_CYLINDER:

Mode - By Cylinder
------------------

Selects vertices, which are within **Radius** from specified straight line. Line is specified by providing directing vector (**Direction** input) and a point, belonging to that line (**Center** input). For example, if you specify Direction = (0, 0, 1) and Center = (0, 0, 0), the line will by Z axis. More exactly, this mode selects vertex V if `Distance(V, Line) <= Radius`.

.. image:: https://user-images.githubusercontent.com/14288520/197360789-4dc49b05-0015-48e0-a6e8-4f7d6bab110a.png
  :target: https://user-images.githubusercontent.com/14288520/197360789-4dc49b05-0015-48e0-a6e8-4f7d6bab110a.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator-> :doc:`Cylinder </nodes/generator/cylinder_mk2>`
* Transform-> :doc:`Matrix Apply (verts) </nodes/transforms/apply>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Matrix-> :doc:`Matrix Apply to Mesh </nodes/matrix/apply_and_join>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/197360940-336f925f-f0f3-42f4-9a56-197f7d5b68d4.gif
  :target: https://user-images.githubusercontent.com/14288520/197360940-336f925f-f0f3-42f4-9a56-197f7d5b68d4.gif

.. _MODE_BY_EDGE_DIRECTION:

Mode - By Edge Direction
------------------------

Selects edges, which are nearly parallel to specified **Direction** vector. Note that this mode considers edges as non-directed; as a result, you can change sign of all coordinates of **Direction** and it will not affect output. More exactly, this mode selects edge E if `Abs(Cos(Angle(E, Direction))) >= max - Percent * (max - min)`, where max and min are maximum and minimum values of that cosine.

.. image:: https://user-images.githubusercontent.com/14288520/197361794-ad1c0708-6689-4af0-b7fd-495aaff7f5c2.png
  :target: https://user-images.githubusercontent.com/14288520/197361794-ad1c0708-6689-4af0-b7fd-495aaff7f5c2.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator->Generator Extended-> :doc:`Polygon Grid </nodes/generators_extended/polygon_grid>`
* Vector-> :doc:`Vector Polar Input </nodes/vector/vector_polar_in>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/197361869-193cf2fb-8d56-4975-84bc-679f5e9a2b1c.gif
  :target: https://user-images.githubusercontent.com/14288520/197361869-193cf2fb-8d56-4975-84bc-679f5e9a2b1c.gif

.. _MODE_BY_BOUNDING_BOX:

Mode - By Bounding Box
----------------------

Selects vertices, that are within bounding box defined by points passed into **Center** input. **Radius** is interpreted as tolerance limit.

.. image:: https://user-images.githubusercontent.com/14288520/197362690-52d369de-29e4-42d6-950e-db25b75edca8.png
  :target: https://user-images.githubusercontent.com/14288520/197362690-52d369de-29e4-42d6-950e-db25b75edca8.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator-> :doc:`Torus </nodes/generator/torus_mk2>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* MUL: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/197362774-5ec0b49a-66bc-49dd-a795-1c72022e4cbe.gif
  :target: https://user-images.githubusercontent.com/14288520/197362774-5ec0b49a-66bc-49dd-a795-1c72022e4cbe.gif

Examples of usage
-----------------

Select rightmost vertices:

.. image:: https://cloud.githubusercontent.com/assets/284644/23761326/aa0cacf6-051c-11e7-8dae-1848bc0e81cd.png
  :target: https://cloud.githubusercontent.com/assets/284644/23761326/aa0cacf6-051c-11e7-8dae-1848bc0e81cd.png

Select faces looking to right:

.. image:: https://cloud.githubusercontent.com/assets/284644/23761372/cc0950b6-051c-11e7-9c57-4b76a91c2e5d.png
  :target: https://cloud.githubusercontent.com/assets/284644/23761372/cc0950b6-051c-11e7-9c57-4b76a91c2e5d.png

Select vertices within sphere:

.. image:: https://cloud.githubusercontent.com/assets/284644/23761537/5106db9e-051d-11e7-81e8-2fca30c02b18.png
  :target: https://cloud.githubusercontent.com/assets/284644/23761537/5106db9e-051d-11e7-81e8-2fca30c02b18.png

Using multiple centers:

See also: Analyzers-> :doc:`KDT Closest Verts </nodes/analyzer/kd_tree_MK2>`

.. image:: https://cloud.githubusercontent.com/assets/284644/24580675/b5206da8-172d-11e7-9aa3-2c345712c899.png
  :target: https://cloud.githubusercontent.com/assets/284644/24580675/b5206da8-172d-11e7-9aa3-2c345712c899.png


Select vertices near OYZ plane:

.. image:: https://cloud.githubusercontent.com/assets/284644/23756618/7036cf88-050e-11e7-9619-b0d748d03d20.png
  :target: https://cloud.githubusercontent.com/assets/284644/23756618/7036cf88-050e-11e7-9619-b0d748d03d20.png

Select vertices near vertical line:

.. image:: https://cloud.githubusercontent.com/assets/284644/23756638/81324d3a-050e-11e7-89c2-e2016557aa47.png
  :target: https://cloud.githubusercontent.com/assets/284644/23756638/81324d3a-050e-11e7-89c2-e2016557aa47.png

Bevel only edges that are parallel to Z axis:

.. image:: https://cloud.githubusercontent.com/assets/284644/23831501/fcebffee-074c-11e7-8e15-de759d67588c.png
  :target: https://cloud.githubusercontent.com/assets/284644/23831501/fcebffee-074c-11e7-8e15-de759d67588c.png

Select faces that are looking outside:

.. image:: https://cloud.githubusercontent.com/assets/284644/23831280/62e48816-0748-11e7-887f-b9223dbbf939.png
  :target: https://cloud.githubusercontent.com/assets/284644/23831280/62e48816-0748-11e7-887f-b9223dbbf939.png

Select faces by bounding box:

.. image:: https://cloud.githubusercontent.com/assets/284644/24332028/248a1026-1261-11e7-8886-f7a0f88ecb60.png
  :target: https://cloud.githubusercontent.com/assets/284644/24332028/248a1026-1261-11e7-8886-f7a0f88ecb60.png

