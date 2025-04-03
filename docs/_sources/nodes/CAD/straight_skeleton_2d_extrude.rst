Straight Skeleton 2d Extrude (Alpha)
====================================

.. image:: https://github.com/user-attachments/assets/9f51d3d0-822f-43ee-adde-ce06acc09ea2
  :target: https://github.com/user-attachments/assets/9f51d3d0-822f-43ee-adde-ce06acc09ea2

!!! **"Exclude height" parameter was renamed into "Restrict Height" !!! Images will be update later...**

**It is Alpha version of node. Any function and names can be changed without notification! (but it will most likely be reported in the documentation).**

Now tested with  **Windows 10**, **Windows 11**, **Ubuntu 22.04** (minimal libstdc++ version 12.3 ). It is not work with iOS (Apple) and we has no plan for a while. If you get issue please write https://github.com/nortikin/sverchok/issues

Functionality
-------------

This node is a python wrapper of function "Skeleton Extrude 2d" of CGAL https://doc.cgal.org/latest/Straight_skeleton_2/index.html.

This package implements weighted straight skeletons for two-dimensional polygons with holes.
An intuitive way to think of the construction of straight skeletons is to imagine that wavefronts
(or grassfires) are spawned at each edge of the polygon, and are moving inward. As the fronts progress,
they either contract or expand depending on the angles formed between polygon edges, and sometimes
disappear. Under this transformation, polygon vertices move along the angular bisector of the lines
subtending the edges, tracing a tree-like structure, the straight skeleton.

.. image:: https://github.com/user-attachments/assets/774128fa-5a89-4d54-ba78-89e7ac10f274
  :target: https://github.com/user-attachments/assets/774128fa-5a89-4d54-ba78-89e7ac10f274

.. image:: https://github.com/user-attachments/assets/8baaadf0-1e09-454a-af6a-85517db3bdb4
  :target: https://github.com/user-attachments/assets/50fd85bb-db65-41d3-a536-142c2cefffac

Install dependency
------------------

To use node install additional library pySVCGAL in the Extra Nodes Section:

.. image:: https://github.com/user-attachments/assets/548ad0a2-86af-4f12-9f39-230f6cda7d41
  :target: https://github.com/user-attachments/assets/548ad0a2-86af-4f12-9f39-230f6cda7d41



Inputs
------

- **Vertices**, **Edges**, **Faces** - Input Mesh (2D only)
    .. image:: https://github.com/user-attachments/assets/3ce5a747-9b8d-4aef-94fc-9e268425e6a6
      :target: https://github.com/user-attachments/assets/3ce5a747-9b8d-4aef-94fc-9e268425e6a6

- **Taper Angle** - Angle between plane and Face that this algorithm will build. Valid range is 0 < Taper Angle <180 Degrees; 0 and 180 are invelid angles. Also 90 degrees is invalid param if "Restrict Height" is off.

    .. image:: https://github.com/user-attachments/assets/666c3a16-f124-4230-906b-8b4ea2cd699c
      :target: https://github.com/user-attachments/assets/666c3a16-f124-4230-906b-8b4ea2cd699c
    
    This parameter has only radians value but you can change its view in Blender Settings:

    .. image:: https://github.com/user-attachments/assets/7828d4c0-eac3-4c7d-992e-c527cdcbfbe0
      :target: https://github.com/user-attachments/assets/7828d4c0-eac3-4c7d-992e-c527cdcbfbe0

If you do not connect any lists of floats values then this value will be used for every objects
connected into this node:

    .. image:: https://github.com/user-attachments/assets/51ccfb1a-30c5-43ed-9b9f-b2e1c6402cb8
      :target: https://github.com/user-attachments/assets/51ccfb1a-30c5-43ed-9b9f-b2e1c6402cb8

If you connect list of floats then it will be used per objects:

    .. image:: https://github.com/user-attachments/assets/f40f4f4f-92dd-4d41-9eae-ddb890214fb6
      :target: https://github.com/user-attachments/assets/f40f4f4f-92dd-4d41-9eae-ddb890214fb6

- **Shapes mode**. Original, Exckude Holes, Invert Holes
- **Restrict Height**.
- **Height** - Height of object or objects. If used single value then this value vill be used for every objects. If socket is connected with float values then values will be used per objects:

.. raw:: html

    <video width="700" controls>
        <source src="https://github.com/user-attachments/assets/97a9e1f8-cd46-451e-902d-3606ed53b255" type="video/mp4">
    Your browser does not support the video tag.
    </video>

- **Mask of objects** - Mask hide objects. If element of boolean mask is True then object are hidden. If length of mask is more than length of objects then exceeded values will be omitted.

.. raw:: html

    <video width="700" controls>
        <source src="https://github.com/user-attachments/assets/2e3f2799-0098-41f5-9def-e5ca971fd028" type="video/mp4">
    Your browser does not support the video tag.
    </video>

    You can use index mask of integer values. If index is out of count of objects then it will be omitted. Equals values are merged.

.. raw:: html

    <video width="700" controls>
        <source src="https://github.com/user-attachments/assets/4f8a9474-c4a6-4ab1-9d7f-e445cdde3f0b" type="video/mp4">
    Your browser does not support the video tag.
    </video>

Parameters
----------

.. image:: https://github.com/user-attachments/assets/0119d5b9-09d2-49a4-b4fd-91e0afdcf76c
  :target: https://github.com/user-attachments/assets/0119d5b9-09d2-49a4-b4fd-91e0afdcf76c

- **Results Join mode**. **Split**, **Keep**, **Merge**.
    - **Split** - If some of objects has several independent meshes then they will be splitten individually and you can get more object on output than on input. (Mask will hide all meshes in multimesh objects)

        .. image:: https://github.com/user-attachments/assets/5d76cd4f-bb2a-4a05-b218-85ae0d96adee
          :target: https://github.com/user-attachments/assets/5d76cd4f-bb2a-4a05-b218-85ae0d96adee

    - **Keep** - If some of objects has several independent meshes then they will be as one object on output.
    
        .. image:: https://github.com/user-attachments/assets/41364d77-ae72-46f6-b4b7-eceaf6bda435
          :target: https://github.com/user-attachments/assets/41364d77-ae72-46f6-b4b7-eceaf6bda435

    - **Merge** - This node will merge all vertices, edjes, and faces into a single object.

        .. image:: https://github.com/user-attachments/assets/bd119bb8-ad08-4983-be67-d97c20ad8bb3
          :target: https://github.com/user-attachments/assets/bd119bb8-ad08-4983-be67-d97c20ad8bb3

    - **Restrict Height** -  If you want to see objects without height limits just turn it off. All objects will be recalulated without heights limits (in the input field or socket).

        .. raw:: html

            <video width="700" controls>
                <source src="https://github.com/user-attachments/assets/e7220c7f-4f8c-4dca-b5b8-5fe648dade7e" type="video/mp4">
            Your browser does not support the video tag.
            </video>

    - **Only Tests** - If you have a hi poly mesh like imported SVG file one can save time and do not Skeletonize all meshes before fix all. You can connect viewer draw into the "Wrong Contours Verts" with red color or any color you prefer for errors to see any wrong contrours. Red dots are wrong contours.

        .. image:: https://github.com/user-attachments/assets/e349df88-3e4b-4096-b2f5-2682b13ed48a
          :target: https://github.com/user-attachments/assets/e349df88-3e4b-4096-b2f5-2682b13ed48a

    - **Verbose** - On will show more info in console while Extrude Straight Sceleton. Off will show less info.

        .. image:: https://github.com/user-attachments/assets/f71aba10-3d00-48d0-b352-907f20b45ef8
          :target: https://github.com/user-attachments/assets/f71aba10-3d00-48d0-b352-907f20b45ef8

Output sockets
--------------




Performance
-----------

If you have a low poly model then no problem - you can work with that model in real time:

.. image:: https://github.com/user-attachments/assets/6bb3f564-5773-4458-be44-8e437c1d33d6
  :target: https://github.com/user-attachments/assets/6bb3f564-5773-4458-be44-8e437c1d33d6

.. raw:: html

    <video width="700" controls>
        <source src="https://github.com/user-attachments/assets/b239559d-f414-4992-8ab0-b9b52e5c2df4" type="video/mp4">
    Your browser does not support the video tag.
    </video>

If you try high poly like Besier 2D with many points and hi resolution (1) then better is to turn off (2) update sverchok nodes while editing objects and run process manually (3):

.. image:: https://github.com/user-attachments/assets/7103fb0d-3ad2-477a-8364-8997722c261c
  :target: https://github.com/user-attachments/assets/7103fb0d-3ad2-477a-8364-8997722c261c

Examples
--------

Hexagon with Straight Skeleton
------------------------------

.. image:: https://github.com/user-attachments/assets/61342e4d-7a10-4903-90e9-5e654db42dae
  :target: https://github.com/user-attachments/assets/61342e4d-7a10-4903-90e9-5e654db42dae

.. image:: https://github.com/user-attachments/assets/57e801d4-e46f-49e8-9831-728be1628c82
  :target: https://github.com/user-attachments/assets/57e801d4-e46f-49e8-9831-728be1628c82


Palm Tree
---------

Src: https://www.143vinyl.com/free-svg-download-palm-trees.html

.. image:: https://github.com/user-attachments/assets/3911de50-2708-411b-aedf-6427e1a0131b
  :target: https://github.com/user-attachments/assets/3911de50-2708-411b-aedf-6427e1a0131b

Src: https://www.templatesarea.com/celtic-tree-of-life-silhouettes-free-vector-graphics/

.. image:: https://github.com/user-attachments/assets/6527588d-a89e-4b04-8965-9450014cc0ba
  :target: https://github.com/user-attachments/assets/6527588d-a89e-4b04-8965-9450014cc0ba


Creating Abstract Shape from 2D Bezier Circle
---------------------------------------------

.. image:: https://github.com/user-attachments/assets/1feac759-2b7f-4266-86f4-f9e0a8e0244d
  :target: https://github.com/user-attachments/assets/1feac759-2b7f-4266-86f4-f9e0a8e0244d

.. raw:: html

    <video width="700" controls>
        <source src="https://github.com/user-attachments/assets/781b8de0-183e-46b8-a9c3-b5abc9656470" type="video/mp4">
    Your browser does not support the video tag.
    </video>

This shape with autosmooth:

.. image:: https://github.com/user-attachments/assets/10c38207-9d24-4b00-bcd6-84d502bc964e
  :target: https://github.com/user-attachments/assets/10c38207-9d24-4b00-bcd6-84d502bc964e

DEVELOPMENT
-----------

If you have skills for work with CGAL see: https://github.com/satabol/SVCGAL