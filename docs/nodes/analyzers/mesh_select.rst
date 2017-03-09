Select mesh elements by location
================================

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
- **Center**. Center or base point. Used in modes: **By sphere**, **By plane**, **By cylinder**.
- **Percent**. How many vertices to select. Used in modes: **By side**, **By normal**.
- **Radius**. Allowed distance from center, or line, or plane, to selected vertices. Used in modes: **By sphere**, **By plane**, **By cylinder**.

Parameters
----------

This node has the following parameters:

- **Mode**. Criteria type to apply. Supported criterias are:

  * **By side**. Selects vertices that are located at one side of mesh. The side is specified by **Direction** input. So you can select "rightmost" vertices by passing (0, 0, 1) as Direction. Number of vertices to select is controlled by **Percent** input: 1% means select only "most rightmost" vertices, 99% means select "all but most leftmost". More exactly, this mode selects vertex V if `(Direction, V) >= max - Percent * (max - min)`, where `max` and `min` are maximum and minimum values of that scalar product amongst all vertices.
  * **By normal direction**. Selects faces, that have normal vectors pointing in specified **Direction**. So you can select "faces looking to right". Number of faces to select is controlled by **Percent** input, similar to **By side** mode. More exactly, this mode selects face F if `(Direction, Normal(F)) >= max - Percent * (max - min)`, where `max` and `min` are maximum and minimum values of that scalar product amongst all vertices.
  * **By center and radius**. Selects vertices, which are within **Radius** from specified **Center**; in other words, it selects vertices that are located inside given sphere. More exactly, this mode selects vertex V if `Distance(V, Center) <= Radius`.
  * **By plane**. Selects vertices, which are within **Radius** from specified plane. Plane is specified by providing normal vector (**Direction** input) and a point, belonging to that plane (**Center** input). For example, if you specify Direction = (0, 0, 1) and Center = (0, 0, 0), the plane will by OXY. More exactly, this mode selects vertex V if `Distance(V, Plane) <= Radius`.
  * **By cylinder**. Selects vertices, which are within **Radius** from specified straight line. Line is specified by providing directing vector (**Direction** input) and a point, belonging to that line (**Center** input). For example, if you specify Direction = (0, 0, 1) and Center = (0, 0, 0), the line will by Z axis. More exactly, this mode selects vertex V if `Distance(V, Line) <= Radius`.

- **Include partial selection**. Not available in **By normal** mode. All other modes select vertices first. This parameter controls either we need to select edges and faces that have **any** of vertices selected (Include partial = True), or only edges and faces that have **all** vertices selected (Include partial = False).

Outputs
-------

This node has the following outputs:

- **VerticesMask**. Mask for selected vertices.
- **EdgesMask**. Mask for selected edges. Please note that this mask relates to list of vertices provided at node input, not list of vertices selected by this node.
- **FacesMask**. Mask for selected faces. Please note that this mask relates to list of vertices provided at node input, not list of vertices selected by this node.


Examples of usage
-----------------

Select rightmost vertices:

.. image:: https://cloud.githubusercontent.com/assets/284644/23761326/aa0cacf6-051c-11e7-8dae-1848bc0e81cd.png

Select faces looking to right:

.. image:: https://cloud.githubusercontent.com/assets/284644/23761372/cc0950b6-051c-11e7-9c57-4b76a91c2e5d.png

Select vertices within sphere:

.. image:: https://cloud.githubusercontent.com/assets/284644/23761537/5106db9e-051d-11e7-81e8-2fca30c02b18.png

Select vertices near OYZ plane:

.. image:: https://cloud.githubusercontent.com/assets/284644/23756618/7036cf88-050e-11e7-9619-b0d748d03d20.png

Select vertices near vertical line:

.. image:: https://cloud.githubusercontent.com/assets/284644/23756638/81324d3a-050e-11e7-89c2-e2016557aa47.png

