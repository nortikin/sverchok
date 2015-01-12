# About

СВеРЧОК, The Russian word for Cricket, is pronounced "Sverchok" in English.

Sverchok is a parametric tool for [Blender](http://blender.org) built to help generate complex 3d shapes using a node system to control the flow of math and geometry. It is ideally suited to Architects and Designers, but anyone with highschool Math and Trigonometry will be able to produce results that are impossible to achieve unless you know text based programming languages such as Python or C.

Those familiar with Houdini, Rhinoceros3D (Grasshopper), Dynamo or other modular systems should feel at home using our addon. Sverchok is not an attempt to clone existing packages or workflows, but a chance to experiment with different approaches to similar constraints.

## The things that Sverchok is good at

- Sverchok _is_ for generating and visualizing geometry.
- Sverchok is at its core parametric, (almost) everything can be driven by a slider
- Sverchok allows for rapid prototyping of algorithms through nodes or scripted nodes.

## Sverchok is not an all-in-one nodes tool.

Sverchok is directed at Math and Geometry. When we started coding Sverchok the focus was not (and still isn't) on things such as Materials, Textures, Lighting, Particles or Animation. Sverchok can control all these things, but we don't offer many convenience nodes for them. We do have a frame change node that outputs the current frame, start frame and end frame into the nodeview, this is often enough to get you started with parametric animation. 

If you want a high level of customization you should be learning Python, we encourage it and you will get the most out of Sverchok. Once you understand Python you can use the scripted node to do anything that `bpy` is capable of, or even write your own nodes (and share if you want advice).

## Sverchok future

We wish to get finer python bpy control over curves (SPLINES, NURBS) and Bmesh based Boolean operations. 
