**********************************
Introduction to modular components
**********************************

**prerequisites**

Same as lesson 01.


Lesson 03 - A Grid
------------------

Grids are another common geometric primitive, and can be thought of as a Plane subdivided over its *x* and *y* axes. The ``Plane`` generator node makes a grid with edges and polygons, but we'll cover a lot of important concepts by building a grid generator using the elementary nodes. I will show practical tips to help you figure out how to construct topology dynamically.

**What do we know about Grids?**

For simplicity let's take a subdivided `Plane` as our template. We know it's flat and therefore the 3rd dimension (z) can be excluded from our focus. We can either have a uniformly subdivided Plane or allow for x and y to be divided separately. A separate XY division is a little bit more interesting, let's go with that. 

**Where to start?**

It helps to consider and name some properties of the Object we want to create. For non trivial objects we often use a notepad (yes, actual paper -- or blender Greasepencil etc) to draw a simplified version of what we want to accomplish. On a drawing we can easily name things, and even notice problems in advance.

I chose a Grid because it has only a few properties, but they can be exposed in several ways.

- X Side Length 
- Y Side Length
- X num subdivs **or** num Vertices on Side X
- Y num subdivs **or** num Vertices on Side Y
- length per division X
- length per division Y

The upside of building generators from scratch is that you can make decisions based on what is most convenient for you.

**Decide which variables you want to expose**

Sometimes there are so many ways to approach variables that you just have to decide and change it later if you need to. Here I'll pick what I think is the most convenient

- Division distance side X
- Division distance side Y
- Number Vertices on side X
- Number Vertices on side Y

// -- TODO





