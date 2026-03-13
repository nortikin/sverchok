Set Loop Normals
================

.. image:: https://user-images.githubusercontent.com/28003269/111056673-62a8ed00-849a-11eb-86b8-faa4bb111f16.png

Functionality
-------------
The nodes allowed to set custom normals to corners of an input mesh.
Most of the time it should be used together with `Origins` nodes which can calculate vertices normals.

Category
--------

BPY Data -> Set Loop Normals

Inputs
------

- **Objects** - Blender mesh objects
- **Vert normals** - normals for each input vertices
- **Faces** - indexes pointing to vertex normals
- **Matrix** - optional, for UV transformation

Outputs
-------

- **Objects** - Blender mesh objects

Parameters
----------

- **Normalized** - It will normalize input normals. It's convenient because if normals are not normalized the result can looks weird.

Usage
-----

Smooth normals

.. image:: https://user-images.githubusercontent.com/28003269/111041776-65342400-8453-11eb-98a7-95b1fcb7eb8e.png

Flat normals

.. image:: https://user-images.githubusercontent.com/28003269/111041779-66fde780-8453-11eb-8de0-92ac014266b9.png

Custom normals based on edges angle

.. image:: https://user-images.githubusercontent.com/28003269/111056842-c1229b00-849b-11eb-9257-1080cd43f3b7.png