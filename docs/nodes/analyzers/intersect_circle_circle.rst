Circle Intersection
===================

Functionality
-------------

The node is designed to get the intersection between two co-planar circles in space. To define the containing plane it can accept a third point or the normal of the plane.

To work in 2D just set a normal vector of (0,0,1)

Inputs / Parameters
-------------------


+------------------+-------------+----------------------------------------------------------------------+
| Param            | Type        | Description                                                          |  
+==================+=============+======================================================================+
| **Define Plane** | Enum.       | Determine method: input the plane's normal or a third point in plane | 
+------------------+-------------+----------------------------------------------------------------------+
| **Center A**     | Vertices    | Center of the first circle                                           |
+------------------+-------------+----------------------------------------------------------------------+
| **Radius A**     | Vertices    | Radius of the first circle                                           |
+------------------+-------------+----------------------------------------------------------------------+
| **Center B**     | Vertices    | Center of the second circle                                          |
+------------------+-------------+----------------------------------------------------------------------+
| **Radius B**     | Vertices    | Radius of the second circle                                          |
+------------------+-------------+----------------------------------------------------------------------+
| **Pt in plane**  | Vertices    | Input point in working plane. It can't be aligned with the centers   |
+------------------+-------------+----------------------------------------------------------------------+
| **Normal**       | Vertices    | Input normal of working plane. It can't be (0,0,0)                   |
+------------------+-------------+----------------------------------------------------------------------+

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can use the toggle:
 
**Match List Global**: Define how list with different lengths should be matched. Refers to the matching of level 1 

**Match List Local**: Define how list with different lengths should be matched. Refers to the matching of level 2

Outputs
-------

**Intersect**: Returns True if the circles intersect.

**Intersection A**: Returns first intersection between the circles (Starting at left or top)

**Intersection B**: Returns second intersection between the circles (Starting at left or top)


Example of usage
----------------

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/analyzer/intersect_circle_circle/intersect_circle_circle_example.png
  :alt: circle_intersection_procedural.png

Using the node to calculate an extensible scissors-like structure

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/analyzer/intersect_circle_circle/intersect_circle_circle_example_scissors_structure.png
  :alt: Sverchok_Distance_point_line.PNG


