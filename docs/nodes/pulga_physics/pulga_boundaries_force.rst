Pulga Boundaries Force
======================

Functionality
-------------

This node creates a force to be applied with the Pulga Physics Solver node.

The node will apply a constrain each vertex into a defined boundaries.

Options & Inputs
----------------

**Mode**: Defines how boundaries are defined.

- Box: Given a list of vertices it will calculate their bounding box and use it as limit of the simulation

  Inputs: Vertices (Bounding Box)

- Sphere: Run the simulation into a spherical space.

  Inputs: Center and radius

- Sphere (Surface): Run the simulation into a spherical surface

  Inputs: Center and radius

- Plane: Run the simulation into a defined plane

  Inputs: Center and Normal

- Mesh (Surface): Run simulation in the surface of a mesh

  Inputs: Vertices and Polygons

- Mesh (Volume): Run the simulation inside a mesh

  Inputs: Vertices and Polygons

- Solid (Surface): Run simulation in the surface of a solid (requires _FreeCAD)

  Inputs: Solid

- Solid (Volume): Run the simulation inside a solid (requires _FreeCAD)

  Inputs: Solid

- Solid Face: Run the simulation the surface of a solid face (requires _FreeCAD)

  Inputs: Solid Face

.. _FreeCAD: ../../solids.rst


Examples
--------

Preforming simulation in the surface of a torus:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_boundaries_force/blender_sverchok_pulga_boundaries_force_example_01.png


Preforming simulation in the surface of a plane and inside a bounding box:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_boundaries_force/blender_sverchok_pulga_boundaries_force_example_02.png
