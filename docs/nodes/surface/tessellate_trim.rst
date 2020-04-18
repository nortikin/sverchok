Tessellate & Trim Surface
=========================

Functionality
-------------

This node "visualizes" the Surface object (turns it into a mesh), by drawing a carthesian (rectangular) grid on it and then cutting (trimming) that grid with the specified Curve object.

The provided trimming curve is supposed to be planar (flat), and be defined in the surface's U/V coordinates frame.

Note that this node is supported since Blender 2.81 only. It will not work in Blender 2.80.

Inputs
------

This node has the following inputs:

* **Surface**. The surface to tessellate. This input is mandatory.
* **TrimCurve**. The curve used to trim the surface. This input is mandatory.
* **SamplesU**. The number of tessellation samples along the surface's U direction. The default value is 25.
* **SamplesV**. The number of tessellation samples along the surface's V direction. The default value is 25.
* **SamplesT**. The number of points to evaluate the trimming curve at. The default value is 100.

Parameters
----------

This node has the following parameters:

* **Curve plane**. The coordinate plane in which the trimming curve is lying.
  The available options are XY, YZ and XZ. The third coordinate is just
  ignored. For example, if XY is selected, then X coordinates of the curve's
  points will be used as surface's U parameter, and Y coordinates of the
  curve's points will be used as surface's V parameter. The default option is
  XY.
* **Cropping mode**. This defines which part of the surface to output:

   * **Inner** - generate the part of the surface which is inside the trimming curve;
   * **Outer** - generate the part of the surface which is outside of the
     trimming curve (make a surface with a hole in it).

   The default option is Inner.

* **Accuracy**. This parameter is available in the node's N panel only. This defines the precision of the calculation. The default value is 5. Usually you do not have to change this value.

Outputs
-------

This node has the following outputs:

* **Vertices**. The vertices of the tessellated surface.
* **Faces**. The faces of the tessellated surface.

Examples of usage
-----------------

Trim some (formula-generated) surface with a circle:

.. image:: https://user-images.githubusercontent.com/284644/79388812-72b50580-7f87-11ea-9eab-2fd205b632d8.png

Cut a circular hole in the surface:

.. image:: https://user-images.githubusercontent.com/284644/79388815-73e63280-7f87-11ea-9bc9-de200fce3c59.png

