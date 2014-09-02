***********************
Introduction to geometry
***********************

Basics
======

If you've ever created a mesh and geometry programatically then you can skip this section.
If you are uncertain what any of the following terms mean then use it as a
reference for further study.

> Vertex, Vector, Index, Edge, Face, Polygon, Normal, Transformation, and Matrix.

3d geometry
-----------

The most fundamental element you need to know about is the *vertex*.
A vertex is a point in 3d space described by 3 or 4 values which represent
its X, Y and Z location. Optionally a 4th value can represent a property of the
vertex, usually *influence* or *weight* and is denoted by **W**.


Relation beteen Vertex and Vector
=================================

*plural: Vertices*

Vertices are the special, limited, case of *Vectors*. Understanding Vectors and Vector math
is an integral part of parametric modeling and generative design, and it's a lot easier than
it might appear at first. 

Think of Vectors as things that have a multitude of properties (also called components). 
For example *House prices* are calculated depending on maybe 20 or more different properties: floor space, neighbourhood, age, any renovations, rooms, bathrooms, garage... The point is, a house can be seen as a Vector datapoint::

    House_one = Vector((floor_space, neighbourhood, age, renovations, rooms, ...))

Geometry really only concentrates on a small number of components. ``X, Y, Z, and maybe W``. In graphics the term Vector is often appropriated and interchangable with Vertex. The various ways in which Vectors can be manipulated will be covered in subsequent parts. If you want to do cool stuff with Sverchok spend time getting to understand Vector based math, it will be time well spent.

You won't have to do the calculations yourself, but you will need to feed Sverchok meaningful input. The good news is that figuring out what Vector math operations produce which results can be observed and understood interactively without understanding the mechanics of the calculations.

Index
=======================

*plural: Indices*

In computer graphics each vertex in an object is uniquely identified by an *index*. 
The index of the first vertex is 0 and the index of the last vertex is equal to 
the number of total vertices minus 1. 

A quick Python example should clarify this. The following would make 3 vertices.
In this case each vertex has 3 components.::

    v0 = (1.0, 1.0, 0.0)
    v1 = (0.5, 0.6, 1.0)
    v2 = (0.0, 1.0, 0.0)

Mesh objects in Blender contain geometric data stored in *lists*. In Python and
Sverchok an empty list looks like `[]`. Vertices are stored in lists too,
a list with 3 vertices might look like::

    vertices = [
        (1.0, 1.0, 0.0),
        (0.5, 0.6, 1.0),
        (0.0, 1.0, 0.0)
    ]


Edges
=====

*Edges* form a bond between 2 vertices. Edges are also stored in a list associated 
with the mesh object. For example the following sets up an empty list to hold the edges::

    edges = []

If we want to declare edges, we reference the vertices by index. Below is an example of
how 3 edges are created::

    edges = [[0, 1], [1, 2], [2, 0]]

Here you see we are using lists inside lists to help separate the edges. This is called *Nesting*

*Lists* are ordered storage.

Polygons
========

*also called Faces or Polys*

Polygons are built using the same convention as Edges. The main difference is that polygons include at least 3 unique vertex indices. For the purposes of this introduction we'll only cover polygons made from 3 or 4 vertices, these are called *Tris and Quads* respectively.

Now imagine we have a total of 6 vertices, the last vertex index is 5. If we want
to create 2 polygons, each built from 3 vertices, we do::

    polygons = [[0, 1, 2], [3, 4, 5]]

In Blender you might mix Tris and Quads in one polygon list during the
modelling process, but for Sverchok geometry you'll find it more convenient
to create separate lists for each and combine them at the end.

An example that sets us up for the first Sverchok example is the cube.
Conceptually in python this looks like::

    # this code can be run from Blender Text Editor and it will generate a Cube.
    
    import bpy
    
    verts = [(1.0, 1.0, -1.0),
             (1.0, -1.0, -1.0),
            (-1.0, -1.0, -1.0),
            (-1.0, 1.0, -1.0),
             (1.0, 1.0, 1.0),
             (1.0, -1.0, 1.0),
            (-1.0, -1.0, 1.0),
            (-1.0, 1.0, 1.0)]
    
    faces = [(0, 1, 2, 3),
             (4, 7, 6, 5),
             (0, 4, 5, 1),
             (1, 5, 6, 2),
             (2, 6, 7, 3),
             (4, 0, 3, 7)]
    
    mesh_data = bpy.data.meshes.new("cube_mesh_data")
    mesh_data.from_pydata(verts, [], faces)
    mesh_data.update() # (calc_edges=True) not needed here
    
    cube_object = bpy.data.objects.new("Cube_Object", mesh_data)
    
    scene = bpy.context.scene  
    scene.objects.link(cube_object)  
    cube_object.select = True  

If we extract from that the geometry only we are left with::

    v0 = Vector((1.0, 1.0, -1.0))
    v1 = Vector((1.0, -1.0, -1.0))
    v2 = Vector((-1.0, -1.0, -1.0))
    v3 = Vector((-1.0, 1.0, -1.0))
    v4 = Vector((1.0, 1.0, 1.0))
    v5 = Vector((1.0, -1.0, 1.0))
    v6 = Vector((-1.0, -1.0, 1.0))
    v7 = Vector((-1.0, 1.0, 1.0))

    vertices = [v0, v1, v2, v3, v4, v5, v6, v7]

    edges = []  # empty list for now.

    polygons = [
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (4, 0, 3, 7)
    ]


Once you define polygons then you are also defining edges implicitely.
If a polygon has 4 vertices, then it also has 4 edges. Two adjacent polygons
may share edges. I think this broadly covers the things you should be
comfortable with before Sverchok will make sense.

Sverchok
========

This section will introduce you to a selection of nodes that can be combined
to create renderable geometry. Starting with the simple Plane generator
