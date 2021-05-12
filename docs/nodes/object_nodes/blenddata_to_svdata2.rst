Object In
=========

Functionality
-------------
Takes object from scene to sverchok. Support meshed, empties, curves, NURBS, but all converting to mesh. Empties has only matrix data.

Inputs
------

Object: Blender Object


Parameters
----------

Post Modifiers: Postprocessing, if activated, modifiers applied to mesh before importing

Outputs
-------

+------------------+--------------------------------------------------------------------------+
| Output           | Description                                                              |
+==================+==========================================================================+
| Vertices         | Vertices of objects                                                      |
+------------------+--------------------------------------------------------------------------+
| Vertex Normals   | Vertex Normals                                                           |
+------------------+--------------------------------------------------------------------------+
| Edges            | Edges of objects                                                         |
+------------------+--------------------------------------------------------------------------+
| Polygons         | Polygons of objects                                                      |
+------------------+--------------------------------------------------------------------------+
| Polygons Areas   | Polygons of objects.                                                     |
+------------------+--------------------------------------------------------------------------+
| Polygons Centers | Polygons Center of objects.                                              |
+------------------+--------------------------------------------------------------------------+
| Polygons Normal  | Polygons Normal of objects.                                              |
+------------------+--------------------------------------------------------------------------+
| Matrix           | Matrices of objects                                                      |
+------------------+--------------------------------------------------------------------------+


It can output Numpy arrays of all outputs (except polygons) if enabled on N-panel properties (makes node faster)

Examples
--------
Importing collection from scene:

.. image:: https://user-images.githubusercontent.com/10011941/117944618-beaeb700-b30d-11eb-9efa-2171381bcbfb.png
