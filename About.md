# About

Sverchok is the Russian word for Cricket (СВеРЧОК). 

> Temperature can be determined by crickets: to do this, count chirps per minute, divide by two, add nine, and again divide by two. The result is the temperature in degrees centigrade.

Sverchok is a parametric tool for [Blender](http://blender.org) built to help generate complex 3d geometry using a node system to control the flow of math and geometry. It is ideally suited to Architects and Designers, but anyone with highschool Math and Trigonometry will be able to produce results that are impossible to achieve unless you know text based programming languages such as Python or C.

Those familiar with the visual programming systems provided by Houdini, Rhinoceros3D (Grasshopper), or Dynamo should feel at home using Sverchok but keep in mind that Sverchok is not intended to be a clone or have any compatibility with any existing file types.

## The things that Sverchok is good at

- Sverchok _is_ for generating and visualizing geometry.
- Sverchok is at its core parametric, (almost) everything can be driven by a slider
- Sverchok allows for rapid prototyping of algorithms through nodes or scripted nodes.

## Sverchok is not an all-in-one nodes tool.

Sverchok is directed at Math and Geometry. When we started coding Sverchok the focus was not (and still isn't) on things such as Materials, Textures, Lighting, Particles or Animation. Sverchok can control all these things, but we don't offer many convenience nodes for animation. We do have a frame change node that outputs the current frame, start frame and end frame into the nodeview. 

If you want a high level of customization you should be learning Python, we encourage it and you will get the most out of Sverchok. Once you understand Python you can use the scripted node to do anything that `bpy` is capable of, or even write your own nodes (and share if you want advice).

## Sverchok future

We wish to get finer python bpy control over curves (SPLINES, NURBS) and Bmesh based Boolean operations. 
