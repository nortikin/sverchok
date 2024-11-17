Straight Skeleton 2d Offset (Alpha)
===================================

.. image:: https://github.com/user-attachments/assets/68a3e88e-8e16-4c0c-8b68-58d81312a265
  :target: https://github.com/user-attachments/assets/68a3e88e-8e16-4c0c-8b68-58d81312a265

Functionality
-------------

This node is a python wrapper of function "Skeleton Offset 2d" of CGAL https://doc.cgal.org/latest/Straight_skeleton_2/index.html.

This package implements straight skeletons offset for two-dimensional polygons with holes.

Simple example:

.. image:: https://github.com/user-attachments/assets/fb5613bc-6ba0-426c-b6ed-be707b333747
  :target: https://github.com/user-attachments/assets/fb5613bc-6ba0-426c-b6ed-be707b333747

More complex example:

.. image:: https://github.com/user-attachments/assets/afa62b30-d5e4-4877-8efc-ccade1730e63
  :target: https://github.com/user-attachments/assets/afa62b30-d5e4-4877-8efc-ccade1730e63

Install dependency
------------------

To use node install additional library pySVCGAL in the Extra Nodes Section:

.. image:: https://github.com/user-attachments/assets/548ad0a2-86af-4f12-9f39-230f6cda7d41
  :target: https://github.com/user-attachments/assets/548ad0a2-86af-4f12-9f39-230f6cda7d41

Inputs
------

- **Vertices**, **Edges**, **Faces** - Input Mesh (2D only) or Meshes. You can use several meshes as input.
    .. image:: https://github.com/user-attachments/assets/460ffdd6-f2d0-4277-9137-fd9e56862f42
      :target: https://github.com/user-attachments/assets/460ffdd6-f2d0-4277-9137-fd9e56862f42

- **Join mode**. Preprocess source meshes. Split, Keep, Merge. **Split** - separate source meshes into independent islands and process them individually. Results boundaries can overlaps. **Keep** - If source meshes has several islands then they has influence. **Merge** - Combine all islands to influence all islands.

    .. image:: https://github.com/user-attachments/assets/3cc4b707-2068-4743-8c81-2b707edfc8ef 
      :target: https://github.com/user-attachments/assets/3cc4b707-2068-4743-8c81-2b707edfc8ef

- **Shapes mode**. Original, Exclude Holes, Invert Holes. Original - Process original meshes. Exclude holes - process only external boundaries. Invert Holes - process holes as islands, exclude external boundaries from process.

    .. image:: https://github.com/user-attachments/assets/f3b577f9-25c1-424b-ac55-0b7ceb754877
      :target: https://github.com/user-attachments/assets/f3b577f9-25c1-424b-ac55-0b7ceb754877

- **Offsets**, **Altitudes**. **Offsets** - distance from contour in plane (one can use negative value). **Altitudes** - results heights in Z axis (one can use negative value).

    .. image:: https://github.com/user-attachments/assets/1f5868a6-141d-4a32-bb9a-1596f2f954a9
      :target: https://github.com/user-attachments/assets/1f5868a6-141d-4a32-bb9a-1596f2f954a9


If you do not connect any lists of floats values then this value will be used for every objects
connected into this node:

    .. image:: https://github.com/user-attachments/assets/21b5edc3-5304-4a40-afb8-f1a2b5781443
      :target: https://github.com/user-attachments/assets/21b5edc3-5304-4a40-afb8-f1a2b5781443

- **Mask of objects** - Mask hide objects. If element of boolean mask is True then object are hidden. If length of mask is more than length of objects then exceeded values will be omitted.

Parameters
----------

.. image:: https://github.com/user-attachments/assets/bc18752b-7ce5-43dd-b0c1-df658a057ded
  :target: https://github.com/user-attachments/assets/bc18752b-7ce5-43dd-b0c1-df658a057ded

- **Result Type**. **Contours** or **Faces**. **Contours** - results are only edges. **Faces** - Results are faces with holes.

    .. image:: https://github.com/user-attachments/assets/7c8edb34-aef2-43a0-907e-83b18e833fe2
      :target: https://github.com/user-attachments/assets/7c8edb34-aef2-43a0-907e-83b18e833fe2

- **Results Join Mode**. **Split**, **Keep**, **Merge**.
    - **Split** - Separate all results into independent meshes. **Keep** - If some of objects has several independent meshes then they will be as one object on output. **Merge** - This node will merge all vertices, edjes, and faces into a single object. Results in merge mode can be overlapped.

      .. image:: https://github.com/user-attachments/assets/e469b38b-a0de-4e7a-a595-a027e77aae48
        :target: https://github.com/user-attachments/assets/e469b38b-a0de-4e7a-a595-a027e77aae48

    - **Only Tests** - If you have a hi poly mesh like imported SVG file one can save time and do not Skeletonize all meshes before fix all. You can connect viewer draw into the "Wrong Contours Verts" with red color or any color you prefer for errors to see any wrong contrours. Red dots are wrong contours.
    - **Force z=0.0** - To force use meshes as planes
    - **Verbose** - Enabled - Show process messages in console while process meshes. Disabled - Hide any process messages.

      .. image:: https://github.com/user-attachments/assets/5b1ffdef-8a1a-4ed0-b580-c53b2d1fdb9d
        :target: https://github.com/user-attachments/assets/5b1ffdef-8a1a-4ed0-b580-c53b2d1fdb9d

Output sockets
--------------

- Vertices, Edges, Faces - Results meshes.
- Wrong Contour Verts - If source meshes can't be processed then this socket will output vertices of that contours (ex. if meshes contours is self intersection)

    .. image:: https://github.com/user-attachments/assets/18cc453d-c1a7-4692-a5b4-ba2e67eb7203
      :target: https://github.com/user-attachments/assets/18cc453d-c1a7-4692-a5b4-ba2e67eb7203

Performance
-----------

If you have a low poly model then no problem - you can work with that model in real time:

.. raw:: html

    <video width="400" controls>
        <source src="https://github.com/user-attachments/assets/eb9dc0cb-cee8-4373-8330-5068c5fd2330" type="video/mp4">
    Your browser does not support the video tag.
    </video>

If you try high poly like Besier 2D with many points and hi resolution (1) then better is to turn off (2) update sverchok nodes while editing objects and run process manually (3):

.. image:: https://github.com/user-attachments/assets/429e6571-fe73-4fc7-b242-4f038f670871
  :target: https://github.com/user-attachments/assets/429e6571-fe73-4fc7-b242-4f038f670871

Examples
--------

Boundary background contour:

.. image:: https://github.com/user-attachments/assets/f6cf099c-1e3a-47ac-be87-e6e9b44b4683
  :target: https://github.com/user-attachments/assets/f6cf099c-1e3a-47ac-be87-e6e9b44b4683

Inner Offset

.. image:: https://github.com/user-attachments/assets/78568725-254e-469c-98bd-50ffb24321b0
  :target: https://github.com/user-attachments/assets/78568725-254e-469c-98bd-50ffb24321b0


DEVELOPMENT
-----------

If you have skills for work with CGAL see: https://github.com/satabol/SVCGAL