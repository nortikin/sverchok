Straight Skeleton 2d Offset (Alpha)
===================================

.. image:: https://github.com/user-attachments/assets/c4f3f9dd-9866-4a52-b49b-fc3ea4b84ad8
  :target: https://github.com/user-attachments/assets/c4f3f9dd-9866-4a52-b49b-fc3ea4b84ad8

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

Additionally you can perform the offset connection of profiles to get a dimensional shape:

.. image:: https://github.com/user-attachments/assets/72cbb4df-097c-4a2f-9b7b-413d539c642f
  :target: https://github.com/user-attachments/assets/72cbb4df-097c-4a2f-9b7b-413d539c642f


Install dependency
------------------

To use node install additional library pySVCGAL in the Extra Nodes Section:

.. image:: https://github.com/user-attachments/assets/548ad0a2-86af-4f12-9f39-230f6cda7d41
  :target: https://github.com/user-attachments/assets/548ad0a2-86af-4f12-9f39-230f6cda7d41

Inputs
------

- **Vertices**, **Edges**, **Faces** - Input Mesh (2D only) or Meshes. You can use several meshes as input.
    .. image:: https://github.com/user-attachments/assets/8249d2f4-6c22-4899-b63e-1ded807a7f82
      :target: https://github.com/user-attachments/assets/8249d2f4-6c22-4899-b63e-1ded807a7f82

- **Join mode**. Preprocess source meshes. **Split**, **Keep**, **Merge**. 
    - **Split** - separate source meshes into independent islands and process them individually. Results boundaries can overlaps.
    - **Keep** - If source meshes has several islands then they has influence.
    - **Merge** - Combine all islands to influence all islands.

    .. image:: https://github.com/user-attachments/assets/3cc4b707-2068-4743-8c81-2b707edfc8ef 
      :target: https://github.com/user-attachments/assets/3cc4b707-2068-4743-8c81-2b707edfc8ef

- **Shapes mode**. **Original**, **Exclude Holes**, **Invert Holes**.

    - **Original** - Process original meshes.
    - **Exclude holes** - process only external boundaries.
    - **Invert Holes** - process holes as islands, exclude external boundaries from process.

    .. image:: https://github.com/user-attachments/assets/f3b577f9-25c1-424b-ac55-0b7ceb754877
      :target: https://github.com/user-attachments/assets/f3b577f9-25c1-424b-ac55-0b7ceb754877

- **Offsets**, **Altitudes**. 

    **Offsets** - distance from contour in plane (one can use negative value). 
    **Altitudes** - results heights in Z axis (one can use negative value).

    .. image:: https://github.com/user-attachments/assets/ea4938cc-7c67-4543-900a-1b2edeb473f1
      :target: https://github.com/user-attachments/assets/ea4938cc-7c67-4543-900a-1b2edeb473f1


If you do not connect any lists of floats values then this value will be used for every objects
connected into this node:

    .. image:: https://github.com/user-attachments/assets/21b5edc3-5304-4a40-afb8-f1a2b5781443
      :target: https://github.com/user-attachments/assets/21b5edc3-5304-4a40-afb8-f1a2b5781443

- **Profile faces indexes**. Only used in **Bevel mode**. List of indexes to connect offsets. If you use some mesh objects you can use profile faces to connect these offset as in profile shape:

      .. image:: https://github.com/user-attachments/assets/96398637-a68b-4439-a379-e5f718e0865c
        :target: https://github.com/user-attachments/assets/96398637-a68b-4439-a379-e5f718e0865c


- **Profile close mode**. Only used in **Bevel mode**. This option affects the way the profile points are connected.

      - **Close** - Profile forms closed shape. The first and last points are connected. The shape is closed from all sides.

          .. image:: https://github.com/user-attachments/assets/12a69746-7ecf-492d-84ce-964aa1f0af66
            :target: https://github.com/user-attachments/assets/12a69746-7ecf-492d-84ce-964aa1f0af66

      - **Open**  - Profile forms opened shape. The first and last points do not connect

          .. image:: https://github.com/user-attachments/assets/826f2671-8167-4a75-b2bc-a2add3b404a1
            :target: https://github.com/user-attachments/assets/826f2671-8167-4a75-b2bc-a2add3b404a1

      - **Pair**  - List items are joined in pairs. If an index is out of offset index range, the pair is completely ignored. Ex.: [1,2,3,4,5,6,7,8,9,0] will be [1,2],[3,4],[5,6],[7,8],[9,0] and you get the bands

          .. image:: https://github.com/user-attachments/assets/4f461c1e-86f4-47fe-bcf2-8cba5d23c29f
            :target: https://github.com/user-attachments/assets/4f461c1e-86f4-47fe-bcf2-8cba5d23c29f


- **Mask of objects** - Mask hide objects. If element of boolean mask is True then object are hidden. If length of mask is more than length of objects then exceeded values will be omitted.

      .. image:: https://github.com/user-attachments/assets/0afddc03-fb45-483e-aad5-01f387a4a584
        :target: https://github.com/user-attachments/assets/0afddc03-fb45-483e-aad5-01f387a4a584

      You can get this result with boolean mask too

      .. image:: https://github.com/user-attachments/assets/b96936b4-68bf-4037-8d9b-e5ec592f04ae
        :target: https://github.com/user-attachments/assets/b96936b4-68bf-4037-8d9b-e5ec592f04ae


Parameters
----------

.. image:: https://github.com/user-attachments/assets/40187fad-ab8f-4e01-b299-c19d3c383f5a
  :target: https://github.com/user-attachments/assets/40187fad-ab8f-4e01-b299-c19d3c383f5a

- **Result Type**. **Contours**, **Faces**, **Bevel**, **Skeleton**. 

    .. image:: https://github.com/user-attachments/assets/c9fb9213-649b-4e31-a608-22af8d84b461
      :target: https://github.com/user-attachments/assets/c9fb9213-649b-4e31-a608-22af8d84b461

    - **Contours** - results are only edges.
    - **Faces** - Results are faces with holes.
    - **Bevel** - Offsets are connected in shapes or figures.
    - **Skeleton** - Show Straight Skeleton scheme.

    .. image:: https://github.com/user-attachments/assets/3f04fc16-212e-457d-9dc2-3b56a0284d5f
      :target: https://github.com/user-attachments/assets/3f04fc16-212e-457d-9dc2-3b56a0284d5f

- **Results Join Mode**. **Split**, **Keep**, **Merge**.

      .. image:: https://github.com/user-attachments/assets/64594acc-667e-4547-bee5-49004dc9f9b6
        :target: https://github.com/user-attachments/assets/64594acc-667e-4547-bee5-49004dc9f9b6

    - **Split** - Separate all results into independent meshes.
    - **Keep** - If some of objects has several independent meshes then they will be as one object on output.
    - **Merge** - This node will merge all vertices, edjes, and faces into a single object. Results in merge mode can be overlapped.

      .. image:: https://github.com/user-attachments/assets/e469b38b-a0de-4e7a-a595-a027e77aae48
        :target: https://github.com/user-attachments/assets/e469b38b-a0de-4e7a-a595-a027e77aae48

- **Force z=0.0** - To force use meshes as planes. Useful for ex. bezier 2D curve some time take Z not zero.

      .. image:: https://github.com/user-attachments/assets/171ee664-1f24-4f00-aed7-4d69ab0f8e75
        :target: https://github.com/user-attachments/assets/171ee664-1f24-4f00-aed7-4d69ab0f8e75

- **Only Tests** - If you have a hi poly mesh like imported SVG file one can save time and do not Skeletonize all meshes before fix all. You can connect viewer draw into the "Wrong Contours Verts" with red color or any color you prefer for errors to see any wrong contrours. Red dots are wrong contours.
- **Verbose** - Enabled - Show process messages in console while process meshes. Disabled - Hide any process messages.

      .. image:: https://github.com/user-attachments/assets/5b1ffdef-8a1a-4ed0-b580-c53b2d1fdb9d
        :target: https://github.com/user-attachments/assets/5b1ffdef-8a1a-4ed0-b580-c53b2d1fdb9d

- **Use cache** - Store Straight Skeleton 2D calculations in cache. If you pass the geometry for calculation a Straight Skeleton a second time, the result will be taken from the cache. This is a new feature so this is disabled by default. If the setting is disabled, the cache is not used.

- **Detailed split** - Work only in Bevel mode. Additional separation of the object by profile faces in **split** mode.

      .. image:: https://github.com/user-attachments/assets/69670c31-d4e8-42ff-936f-699500f41359
        :target: https://github.com/user-attachments/assets/69670c31-d4e8-42ff-936f-699500f41359

Output sockets
--------------

- Vertices, Edges, Faces - Results meshes.
- Wrong Contour Verts - If source meshes can't be processed then this socket will output vertices of that contours (ex. if meshes contours is self intersection)

    .. image:: https://github.com/user-attachments/assets/18cc453d-c1a7-4692-a5b4-ba2e67eb7203
      :target: https://github.com/user-attachments/assets/18cc453d-c1a7-4692-a5b4-ba2e67eb7203

Performance
-----------

If you have a low poly model then no problem - you can work with it in real time:

.. raw:: html

    <video width="400" controls>
        <source src="https://github.com/user-attachments/assets/eb9dc0cb-cee8-4373-8330-5068c5fd2330" type="video/mp4">
    Your browser does not support the video tag.
    </video>

If you try high poly like Besier 2D with many points and hi resolution (1) then better is to turn off (2) update sverchok nodes while editing objects and run process manually (3):

.. image:: https://github.com/user-attachments/assets/429e6571-fe73-4fc7-b242-4f038f670871
  :target: https://github.com/user-attachments/assets/429e6571-fe73-4fc7-b242-4f038f670871

Also you can use cache mode (it is experimental property for a while!!!):

.. image:: https://github.com/user-attachments/assets/2e8eaadc-ac14-4789-826a-3bf992ebeb7d
  :target: https://github.com/user-attachments/assets/2e8eaadc-ac14-4789-826a-3bf992ebeb7d


Examples
--------

Boundary background contour:

.. image:: https://github.com/user-attachments/assets/f6cf099c-1e3a-47ac-be87-e6e9b44b4683
  :target: https://github.com/user-attachments/assets/f6cf099c-1e3a-47ac-be87-e6e9b44b4683

Inner Offset

.. image:: https://github.com/user-attachments/assets/78568725-254e-469c-98bd-50ffb24321b0
  :target: https://github.com/user-attachments/assets/78568725-254e-469c-98bd-50ffb24321b0

Extrude with profile faces:

.. image:: https://github.com/user-attachments/assets/e7278c18-18aa-4e3c-8897-71369f8566b9
  :target: https://github.com/user-attachments/assets/e7278c18-18aa-4e3c-8897-71369f8566b9


DEVELOPMENT
-----------

If you have skills for work with CGAL see: https://github.com/satabol/SVCGAL