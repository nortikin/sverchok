Stright Skeleton 2d Offset (Alpha)
===================================

.. image:: https://github.com/user-attachments/assets/68a3e88e-8e16-4c0c-8b68-58d81312a265
  :target: https://github.com/user-attachments/assets/68a3e88e-8e16-4c0c-8b68-58d81312a265

Functionality
-------------

This node is a python wrapper of function "Skeleton Offset 2d" of CGAL https://doc.cgal.org/latest/Straight_skeleton_2/index.html.

This package implements straight skeletons offset for two-dimensional polygons with holes.

Install dependency
------------------

To use node install additional library pySVCGAL in the Extra Nodes Section:

.. image:: https://github.com/user-attachments/assets/548ad0a2-86af-4f12-9f39-230f6cda7d41
  :target: https://github.com/user-attachments/assets/548ad0a2-86af-4f12-9f39-230f6cda7d41

Inputs
------

- **Vertices**, **Edges**, **Faces** - Input Mesh (2D only)
    .. image:: https://github.com/user-attachments/assets/71a237f7-098b-4344-87a0-ca83c290a411
      :target: https://github.com/user-attachments/assets/71a237f7-098b-4344-87a0-ca83c290a411

- **Join mode**
- **Shapes mode**. Original, Exckude Holes, Invert Holes
- **Offsets**
- **Altitudes**


If you do not connect any lists of floats values then this value will be used for every objects
connected into this node:

    .. image:: https://github.com/user-attachments/assets/21b5edc3-5304-4a40-afb8-f1a2b5781443
      :target: https://github.com/user-attachments/assets/21b5edc3-5304-4a40-afb8-f1a2b5781443

- **Mask of objects** - Mask hide objects. If element of boolean mask is True then object are hidden. If length of mask is more than length of objects then exceeded values will be omitted.

Parameters
----------

.. image:: https://github.com/user-attachments/assets/638a4c5a-d651-45fd-b88f-e18d0c8ef25e
  :target: https://github.com/user-attachments/assets/638a4c5a-d651-45fd-b88f-e18d0c8ef25e

- **Source Join mode** / **Results Join Mode**. **Split**, **Keep**, **Merge**.
    - **Split** - If some of objects has several independent meshes then they will be splitten individually and you can get more object on output than on input. (Mask will hide all meshes in multimesh objects)
    - **Keep** - If some of objects has several independent meshes then they will be as one object on output.
    - **Merge** - This node will merge all vertices, edjes, and faces into a single object.
    - **Only Tests** - If you have a hi poly mesh like imported SVG file one can save time and do not Skeletonize all meshes before fix all. You can connect viewer draw into the "Wrong Contours Verts" with red color or any color you prefer for errors to see any wrong contrours. Red dots are wrong contours.
    - **Force z=0.0**
    - **Verbose** - On will show more info in console while Extrude Straight Sceleton. Off will show less info.

Output sockets
--------------

- Vertices, Edges, Faces
- Wrong Contour Verts

Performance
-----------

If you have a low poly model then no problem - you can work with that model in real time:

If you try high poly like Besier 2D with many points and hi resolution (1) then better is to turn off (2) update sverchok nodes while editing objects and run process manually (3):

.. image:: https://github.com/user-attachments/assets/7103fb0d-3ad2-477a-8364-8997722c261c
  :target: https://github.com/user-attachments/assets/7103fb0d-3ad2-477a-8364-8997722c261c

Examples
========


DEVELOPMENT
===========

If you have skills for work with CGAL see: https://github.com/satabol/SVCGAL