IcoSphere Node
==============

.. image:: https://user-images.githubusercontent.com/14288520/188708444-303645fa-7260-4326-94f7-0eb251740aa1.png
  :target: https://user-images.githubusercontent.com/14288520/188708444-303645fa-7260-4326-94f7-0eb251740aa1.png

Functionality
-------------

This node creates an IcoSphere primitive. In case of zero subdivisions, it simply produces right icosahedron.

.. image:: https://user-images.githubusercontent.com/14288520/191254102-557f8ade-e6a9-4473-b86d-05cda5f22096.png
  :target: https://user-images.githubusercontent.com/14288520/191254102-557f8ade-e6a9-4473-b86d-05cda5f22096.png

Inputs
------

This node has the following inputs:

- **Subdivisions** - How many times to recursively subdivide the sphere. min=0.
- **Radius** - Sphere radius. min=0.

Parameters
----------

This node has the following parameters:
  
- **Max. Subdivisions**. Maximum value available for **Subdivisions** parameter. This affects not only parameter, but also restricts values provided via input. Default maximum is 5.
- **Subdivisions**. How many times to recursively subdivide the sphere. In case this parameter is 0, the node will simply produce right icosahedron. Maximum value is restricted by **Max. Subdivisions** parameter. This parameter can be provided via node input.
- **Radius**. Sphere radius. This parameter can be provided via node input.

Outputs
-------

This node has the following outputs:

- **Vertices**
- **Edges**
- **Faces**

Example of usage
----------------

Simple example:

.. image:: https://user-images.githubusercontent.com/14288520/188708570-5c9fda27-d754-4876-ad46-db798efdf798.png
  :target: https://user-images.githubusercontent.com/14288520/188708570-5c9fda27-d754-4876-ad46-db798efdf798.png

