KDT Closest Verts
=================

.. image:: https://user-images.githubusercontent.com/14288520/196113100-d9d9325b-d9e8-4f5e-902f-01deb94e4ed4.png
  :target: https://user-images.githubusercontent.com/14288520/196113100-d9d9325b-d9e8-4f5e-902f-01deb94e4ed4.png

.. image:: https://user-images.githubusercontent.com/14288520/196104413-3d997890-3199-46af-b3e5-394a46f46bef.png
  :target: https://user-images.githubusercontent.com/14288520/196104413-3d997890-3199-46af-b3e5-394a46f46bef.png

Functionality
-------------

For every vertex in Verts, it checks the list of Vertices in Check Verts. 
What it does exactly depends on the *Search Mode*. Search modes are mere examples of what is possible with Blender's KDTree module. The documentation for kdtree is found at the latest version of ``mathutils.kdtree.html``. 

Inputs
------

+--------+--------------+--------------------------+
| Mode   | Input Name   | type                     |
+========+==============+==========================+
| All    | Verts        | vertices                 |
+--------+--------------+--------------------------+
|        | Check Verts  | vertices                 |
+--------+--------------+--------------------------+
| N      | N            | int, or list of ints     |
+--------+--------------+--------------------------+
| Radius | Radius       | float, or list of floats |
+--------+--------------+--------------------------+

Verts and Check Verts do not need to be the same pool of verts, they don't even need to be the same
length.

Parameters
----------

+-------------+-----------------------------------------------------------------------------------------+
| Search Mode | Description                                                                             |
+=============+=========================================================================================+
| 1           | for each vertex in *Verts* return the vertex in *Check Verts* which is closest.         |
+-------------+-----------------------------------------------------------------------------------------+
| N           | for each vertex in *Verts* return the list of N closest vertices found in Check Verts   |
+-------------+-----------------------------------------------------------------------------------------+
| Radius      | for each vertex in *Verts* return the *vertices* of *Check Verts* that are found        |
|             | within radius-distance of that vertex.                                                  |
+-------------+-----------------------------------------------------------------------------------------+


Outputs
-------

The meaning of each output differs between Modes, but essentially they are:

- Vertices coordinates
- Vertex Indices of related vertex in Check Verts
- Vertex Distance between Vertex in Verts and Check Verts

The output lists will be nested if the ``Mode`` allows multiple outputs, as is the case in N and Radius Mode.


Examples
--------

All kinds of crazy things are possible, see some examples here in 
`the development thread <https://github.com/nortikin/sverchok/issues/99>`_

---------

.. image:: https://user-images.githubusercontent.com/14288520/196110903-4ccd8d4a-dd5e-4f68-a88d-781be497101c.png
  :target: https://user-images.githubusercontent.com/14288520/196110903-4ccd8d4a-dd5e-4f68-a88d-781be497101c.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Circle </nodes/generator/circle>`
* Transform-> :doc:`Rotate </nodes/transforms/rotate_mk3>`
* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

.. image:: https://user-images.githubusercontent.com/14288520/196110859-a2e4795e-0973-403f-aaa3-5262ae2db495.gif
  :target: https://user-images.githubusercontent.com/14288520/196110859-a2e4795e-0973-403f-aaa3-5262ae2db495.gif

---------

.. image:: https://user-images.githubusercontent.com/14288520/196107686-69b611f0-826c-4291-9769-041fb2602468.png
  :target: https://user-images.githubusercontent.com/14288520/196107686-69b611f0-826c-4291-9769-041fb2602468.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Circle </nodes/generator/circle>`
* Transform-> :doc:`Rotate </nodes/transforms/rotate_mk3>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

.. image:: https://user-images.githubusercontent.com/14288520/196108334-be4e2fbe-1e47-4473-bce6-295ff491c126.gif
  :target: https://user-images.githubusercontent.com/14288520/196108334-be4e2fbe-1e47-4473-bce6-295ff491c126.gif

---------

Notes
-----

**Design specs**

::

    '''
    find(co)
        : internal function
        : < Find nearest point to co
        : > returns co, index, dist

        : inputs:
            1) Main Verts for kdtree to hold
            2) [cVert(s)] to check against
        : outputs:
            1) [Verts.co] from Main Verts that were closest
            2) [Verts.idx] from Main Verts that were closest


    find_n(co, n)
        : internal function
        : > Find nearest n points to co
        : < returns iterable of (co, index, dist)

        : inputs:
            1) Main Verts for kdtree to hold
            2) [cVert(s)] to check against (size don't have to match)
            3) n, max n nearest
            optional?
            1) mask, [0, 0, 1, 0, 1]  (return 3rd and 5th closest)
            2) range clamp, [2:] (don't return first 2 closest)
        : outputs:
            for v in cVerts:
            1) ([Verts.co],..) from Main Verts closest to v.co
            2) ([Verts.idx],..) from Main Verts closest to v.co
            optional!
            1) could generate edges directly (Saves node noodle)


    find_range(co, radius)
        : > Find all points within radius of co
        : < returns iterable of (co, index, dist)

        : inputs:
            1) Main Verts for kdtree to hold
            2) [cVert(s)] to check against (size don't have to match)
            3) [distance(s)] ,

        : outputs:
            options:
            1) grouped [.co for points in Main Verts in radius of v in cVert]
            2) grouped [.idx for points in Main Verts in radius of v in cVert]
            3) grouped [.dist for points in Main Verts in radius of v in cVert]

    '''


If you need large kdtree searches and memoization or specific functionality you shall want to write your own Node to utilize the kdtree module. Part of the problem of making a *general use* node is that it becomes sub-optimal for certain tasks. On the up-side, having this node allows you to rip out the specifics and implement your own more specialized kdtree node. Recommend using a different Node name and sharing it with team Sverchok :)



