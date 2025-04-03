Voronoi on Solid
================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/d9691d7f-2d19-4ed5-a64b-b89ce488bbae
  :target: https://github.com/nortikin/sverchok/assets/14288520/d9691d7f-2d19-4ed5-a64b-b89ce488bbae

Dependencies
------------

This node requires both SciPy_ and FreeCAD_ libraries to work.

.. _SciPy: https://scipy.org/
.. _FreeCAD: ../../solids.rst

Functionality
-------------

This node creates Voronoi diagram on a given Solid object. The result can be
output as either series of fragments of the shell of Solid object (series of
faces), or as a series of solid bodies.

**Note**: this node uses FreeCAD's functionality of solid boolean operations
internally. This functionality is known to be **slow** when working with objects
defined by NURBS surfaces, especially when there are a lot of sites used. Also
please be warned that this functionality is known to cause Blender crashes on
some setups.

.. image:: https://user-images.githubusercontent.com/14288520/202863312-ef965247-efac-4f98-9b62-127bc0a03f32.png
  :target: https://user-images.githubusercontent.com/14288520/202863312-ef965247-efac-4f98-9b62-127bc0a03f32.png

Inputs
------

This node has the following inputs:

* **Solid**. The solid object, on which the Voronoi diagram is to be generated.
  This input is mandatory.

.. image:: https://user-images.githubusercontent.com/14288520/202748963-647952f5-744d-4db6-b538-6b4c0f454d39.png
  :target: https://user-images.githubusercontent.com/14288520/202748963-647952f5-744d-4db6-b538-6b4c0f454d39.png

* **Sites**. List of points, for which Voronoi diagram is to be generated. This
  input is mandatory.

.. image:: https://user-images.githubusercontent.com/14288520/202750050-afdaeee2-0b86-4d41-af5f-d025cc5f467e.png
  :target: https://user-images.githubusercontent.com/14288520/202750050-afdaeee2-0b86-4d41-af5f-d025cc5f467e.png

* **Inset**. Percentage of space to leave between generated Voronoi regions.
  Zero means the object will be fully covered by generated regions. Maximum
  value is 1.0. The default value is 0.1. This input can consume either a
  single value per object, or a list of values per object - one value per site.
  In the later case, each value will be used for corresponding cell.  

.. image:: https://user-images.githubusercontent.com/14288520/202751076-960737db-e8e0-4d71-aed8-0f2773f0facb.png
  :target: https://user-images.githubusercontent.com/14288520/202751076-960737db-e8e0-4d71-aed8-0f2773f0facb.png

.. image:: https://user-images.githubusercontent.com/14288520/202864166-e3317496-d617-496f-8dc7-8033a77c6578.png
  :target: https://user-images.githubusercontent.com/14288520/202864166-e3317496-d617-496f-8dc7-8033a77c6578.png

* Spatial-> :doc:`Populate Solid </nodes/spatial/populate_solid>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* List->List Struct-> :doc:`List Levels </nodes/list_struct/levels>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

Parameters
----------

This node has the following parameters:

* **Mode**. The available options are available:

  * **Surface**. The node will split the surface (shell) of the solid body into
    regions of Voronoi diagram.
  * **Volume**. The node will split the volume of the solid body into regions
    of Voronoi diagram.

  The default value is **Surface**.

.. image:: https://user-images.githubusercontent.com/14288520/202751663-1e7af390-77e7-42ff-844f-010403538b8f.png
  :target: https://user-images.githubusercontent.com/14288520/202751663-1e7af390-77e7-42ff-844f-010403538b8f.png

* **Flat output**. If checked, output single flat list of fragments for all
  output solids. Otherwise, output a separate list of fragments for each solid.
  Checked by default.
* **Accuracy**. This parameter is available in the N panel only. Precision of
  calculations (number of digits after decimal point). The default value is 6.

.. image:: https://user-images.githubusercontent.com/14288520/202752114-c940ad55-3e56-40dc-a55e-4f9b4992700e.png
  :target: https://user-images.githubusercontent.com/14288520/202752114-c940ad55-3e56-40dc-a55e-4f9b4992700e.png

Outputs
-------

This node has the following outputs:

* **InnerSolid**. Solid objects (or their shells, if **Surface** mode is used)
  calculated as regions of Voronoi diagram.
* **OuterSolid**. Solid object, representing the part of volume or shell, which
  is left between the regions of Voronoi diagram. This object will be empty if
  **Inset** input is set to zero.

Examples of usage
-----------------

Inner solids with **Surface** mode:

.. image:: https://user-images.githubusercontent.com/14288520/202754852-bfdbd502-ec68-4484-983c-de288e4c2dd6.png
  :target: https://user-images.githubusercontent.com/14288520/202754852-bfdbd502-ec68-4484-983c-de288e4c2dd6.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Solids-> :doc:`Polygon Face (Solid) </nodes/solid/polygon_face>`
* Solids-> :doc:`Revolve Face (Solid) </nodes/solid/revolve_face>`
* Solids-> :doc:`Solid Viewer </nodes/solid/solid_viewer>`
* Spatial-> :doc:`Populate Solid </nodes/spatial/populate_solid>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Outer solid for the same setup:

.. image:: https://user-images.githubusercontent.com/14288520/202755395-edec16e0-042a-4f97-9c1a-f71a39d146dc.png
  :target: https://user-images.githubusercontent.com/14288520/202755395-edec16e0-042a-4f97-9c1a-f71a39d146dc.png

Inner solids with **Volume** mode:

.. image:: https://user-images.githubusercontent.com/14288520/202755962-0c3a7391-330f-4d7c-9301-d7731368e37b.png
  :target: https://user-images.githubusercontent.com/14288520/202755962-0c3a7391-330f-4d7c-9301-d7731368e37b.png

Outer solid with **Volume** mode:

.. image:: https://user-images.githubusercontent.com/14288520/202756392-4490fc0d-2b94-4890-bff7-0397e4186f8a.png
  :target: https://user-images.githubusercontent.com/14288520/202756392-4490fc0d-2b94-4890-bff7-0397e4186f8a.png