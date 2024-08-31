Viewer Draw Surface
===================

.. image:: https://user-images.githubusercontent.com/14288520/190859856-a96709c4-434f-444b-849a-09dfc89e1f26.png
  :target: https://user-images.githubusercontent.com/14288520/190859856-a96709c4-434f-444b-849a-09dfc89e1f26.png

Functionality
-------------

This node displays Surface objects in the 3D View, using opengl. The node is
intended to be a fast way to show you the result of your node tree. 

For NURBS and NURBS-like surfaces, the node can also additionally display
control points and control net edges. For non-NURBS curves, the node just does
not try to display these attributes.

This node is automatically created when you select "Connect Viewer Draw" from
right-click menu for nodes which have Surface output. Also this node pops up as a
"temporal viewer". when you perform control-click on such a node.

Inputs
------

This node has the following inputs:

* **Surface**. The surface object(s) to be displayed. This input is mandatory.
* **Resolution U**, **Resolution V**. Resolution to display the surface, along
  U and V parameters. The default value is 50.

Parameters
----------

This node has one main parameter:

* **Show**. The node displays something only when this parameter is enabled.

.. image:: https://user-images.githubusercontent.com/14288520/190235190-86138e03-8423-4b86-9d35-4337b25513f3.png
  :target: https://user-images.githubusercontent.com/14288520/190235190-86138e03-8423-4b86-9d35-4337b25513f3.png

Most parameters of this node are grouped in rows; for each type of
information this node can display, there are three parameters: whether to
display it, the color to be used, and point size / line width to be used.

The parameters of the node are (in this order):

* **Display Vertices**, **Vertices Color**, **Vertices Size**. Control display
  of points on the surface (number of points along U and V parameters are
  controlled by **Resolution U**, **Resolution V** inputs). Display of points
  is disabled by default.

.. image:: https://user-images.githubusercontent.com/14288520/190232504-7efd678d-60da-45e9-a8f9-3a00a68096b4.png
  :target: https://user-images.githubusercontent.com/14288520/190232504-7efd678d-60da-45e9-a8f9-3a00a68096b4.png

-------------

* **Display Edges**, **Edges Color**, **Edges Line Width**. Control display of
  edges on the curve (edges between points). Display of edges is disabled by
  default.

.. image:: https://user-images.githubusercontent.com/14288520/190232619-676b8cfd-839a-4c1f-9cc9-703b8d6b3bda.png
  :target: https://user-images.githubusercontent.com/14288520/190232619-676b8cfd-839a-4c1f-9cc9-703b8d6b3bda.png

-------------

* **Display Surface**, **Surface Color**. Control display of the surface
  itself. The surface is shown by default.

.. image:: https://user-images.githubusercontent.com/14288520/190233082-7627834b-cd18-476c-8abf-27be180c8705.png
  :target: https://user-images.githubusercontent.com/14288520/190233082-7627834b-cd18-476c-8abf-27be180c8705.png

-------------

* **Display Control Points**, **Control Points Color**, **Control Points
  Size**. Control display of surface's control points, for NURBS and NURBS-like
  surfaces. Control points are not shown by default.

.. image:: https://user-images.githubusercontent.com/14288520/190233234-3e638636-4945-4e31-8872-ccc45c0ddeaf.png
  :target: https://user-images.githubusercontent.com/14288520/190233234-3e638636-4945-4e31-8872-ccc45c0ddeaf.png

-------------

* **Display Control Net**, **Control Net Color**, **Control Net Line Width**.
  Control display of surface's control net (edges between control points), for
  NURBS and NURBS-like surfaces. Control net is not displayed by default.
* **Display Node Lines**, **Node Lines Color**, **Node Lines Width**. Conrtol
  display of node lines, i.e. isolines at U and V parameters according to node
  values of knotvectors along U and V parameter directions. Node lines are not
  displayed by default.

.. image:: https://user-images.githubusercontent.com/14288520/190234804-8789ca5c-d35a-46f3-9c6c-95cc440ce394.png
  :target: https://user-images.githubusercontent.com/14288520/190234804-8789ca5c-d35a-46f3-9c6c-95cc440ce394.png

* **Indicate Curvature**, **Minimum Curvature Color**, **Maximum Curvature
  Color**. Control indication of surface curvature. Colors control how places
  with minimum and maximum curvature value will be indicated on surface. Places
  with medium curvature values will be drawn with **Surface Color**, as usual.
  The **Type** dropdown is visible only when **Indicate Curvature** is checked,
  and it controls what type of curvature should be indicated:

  * **Gauss** - indicate Gauss curvature (product of minimum and maximum
    curvature). Places with positive Gaussian curvature are where the surface
    behaves like sphere. Places with negative Gaussian curvature are where the
    surface is like a saddle.
  * **Mean** - indicate mean curvature (sum of minimum and maximum curvature).
  * **Maximum** - indicate maximum curvature, i.e. the biggest of two principal
    curvature values.
  * **Minimum** - indicate minimum curvature, i.e. the smallest of two
    principal curvature values.
  * **Difference** - indicate difference between maximum and minimum curvature
    values. Places where difference is zero, i.e. maximum curvature equals
    minimum curvature, are umbillic points.

Operators
---------

This node has the following buttons:

* **BAKE**. Create mesh objects in Blender scene according to curves being displayed.
* **Align**. Zoom and position 3D view so that generated object is in the center.

Outputs
-------

This node has no outputs.

Example of Usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/189537929-2be26995-0cb3-4063-9531-8ca0f955e155.png
  :target: https://user-images.githubusercontent.com/284644/189537929-2be26995-0cb3-4063-9531-8ca0f955e155.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Transform-> :doc:`Randomize </nodes/transforms/randomize>`
* Surfaces->NURBS-> :doc:`Interpolate Nurbs Surface </nodes/surface/interpolate_nurbs_surface>`

Examples of surface curvature indication:

* Gaussian curvature:

.. image:: https://user-images.githubusercontent.com/284644/212495583-9f71e2c3-5fa5-410f-be9d-9b5c6c72b066.png
  :target: https://user-images.githubusercontent.com/284644/212495583-9f71e2c3-5fa5-410f-be9d-9b5c6c72b066.png

* Another surface with indicated Gaussian curvature:

.. image:: https://user-images.githubusercontent.com/284644/215551129-04652358-2704-4f6a-a069-d4f05a51158c.png
  :target: https://user-images.githubusercontent.com/284644/215551129-04652358-2704-4f6a-a069-d4f05a51158c.png

* Mean curvature:

.. image:: https://user-images.githubusercontent.com/284644/212495578-f719c92f-a503-4146-92bb-f474c2905753.png
  :target: https://user-images.githubusercontent.com/284644/212495578-f719c92f-a503-4146-92bb-f474c2905753.png

* Difference of two curvatures:

.. image:: https://user-images.githubusercontent.com/284644/212495582-cfae4468-8b65-4f78-9c55-6237e53a5e0a.png
  :target: https://user-images.githubusercontent.com/284644/212495582-cfae4468-8b65-4f78-9c55-6237e53a5e0a.png

