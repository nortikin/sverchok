Randomize
=========

.. image:: https://user-images.githubusercontent.com/14288520/194019958-bfb7326f-578e-4a59-8cbf-86a2be485312.png
  :target: https://user-images.githubusercontent.com/14288520/194019958-bfb7326f-578e-4a59-8cbf-86a2be485312.png

Functionality
-------------

This mode processes set of vertices by moving each of them by random distance
along X, Y, and Z axis. You can specify maximum distance of moving for each
axis.

Inputs
------

This node has the following inputs:

- **Vertices**
- **X amplitude**
- **Y amplitude**
- **Z amplitude**
- **Seed**

Parameters
----------

All parameters can be given by the node or an external input.
This node has the following parameters:

+-----------------+---------------+-------------+----------------------------------------------------+
| Parameter       | Type          | Default     | Description                                        |
+=================+===============+=============+====================================================+
| **X amplitude** | Float         | 0.0         | Maximum distance to move vertices along X axis.    |
+-----------------+---------------+-------------+----------------------------------------------------+
| **Y amplitude** | Float         | 0.0         | Maximum distance to move vertices along Y axis.    |
+-----------------+---------------+-------------+----------------------------------------------------+
| **Z amplitude** | Float         | 0.0         | Maximum distance to move vertices along Z axis.    |
+-----------------+---------------+-------------+----------------------------------------------------+
| **Seed**        | Int           | 0           | Random seed.                                       |
+-----------------+---------------+-------------+----------------------------------------------------+

**Note**. Each amplitude input specifies maximum distance to move vertices
along corresponding axis. Vertices can be moved both in negative and positive
directions. For example, for vertex X coordinate = 10.0, and ``X amplitude`` = 1.0,
you can get output vertex coordinate from 9.0 to 11.0.

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Output NumPy**: Output NumPy arrays in stead of regular lists (makes the node faster)

Outputs
-------

This node has one output: **Vertices**.

Example of usage
----------------

Given simplest nodes setup you will have something like:

.. image:: https://user-images.githubusercontent.com/14288520/194020683-bff9d2e3-2a6d-4980-af95-775ad60023ce.png
  :target: https://user-images.githubusercontent.com/14288520/194020683-bff9d2e3-2a6d-4980-af95-775ad60023ce.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`