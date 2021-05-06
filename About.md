# About

СВеРЧОК, The Russian word for Cricket, is pronounced "Sverchok" in English.

Sverchok is a parametric CAD tool for [Blender](http://blender.org) built to help generate complex 3d shapes using a node system to control the flow of math and geometry. It is ideally suited to Architects and Designers, but anyone with highschool Math and Trigonometry will be able to produce results that are impossible to achieve unless you know text based programming languages such as Python or C.

Those familiar with Houdini, Rhinoceros3D (Grasshopper), Dynamo or other modular systems should feel at home using our addon. Sverchok is not an attempt to clone existing packages or workflows or copy Geometry Nodes, but a chance to experiment with different approaches to similar constraints.

## The things that Sverchok is good at

- Sverchok _is_ for generating and visualizing geometry (Mesh, NURBS, Solids, Curves, Surfaces, Fields).
- Sverchok is at its core parametric, (almost) everything can be driven by a slider and 3d panel can gathered selected sliders for user;
- Sverchok allows for rapid prototyping of algorithms through nodes or scripted nodes.

## Sverchok is not an all-in-one nodes tool.

Sverchok is directed at Math and Geometry. When we started coding Sverchok the focus was not (and still isn't) on things such as Materials, Textures, Lighting, Particles or Animation. Sverchok can control all these things, but we don't offer many convenience nodes for them. (We do have a frame change node that outputs the current frame, start frame and end frame into the nodeview, this is often enough to get you started with parametric animation.)  

If you want a high level of customization you should be learning Python, we encourage it and you will get the most out of Sverchok. Once you understand Python you can use the scripted node to do anything that `bpy` is capable of, or even write your own nodes (and share if you want advice).  

## Sverchok future 

Some time ago we got Solids/Surfaces/Curves/Fields nodes sets additionally to Blender-relative Mesh. We are waiting now Geometry Nodes and Everything Nodes to be mature, and join there with closer integration. Also closer FreeCAD, Inkscape integration are in list, CNC tools development, even proprietary ArchiCAD interaction that depends on ArchiCAD side ofcourse. More of IFC import-export, more ladybug development. Not sure, but maybe to go beyond existing Genetic Algorythm and Neuro nodes with some AI tools if required application case would appear.  
Knowing Blender is best place to model 3d in opensource (or in the World?), we will place side libreries as pasrt of CAD/BIM process with interaction to OSarch community and other enthusiasts.
