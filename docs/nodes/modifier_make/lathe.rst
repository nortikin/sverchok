Lathe
=====

Functionality
-------------

Analogous to the `spin` operator and the Screw modifier. It takes as input vertices and edges and produces vertices, edges and faces based on a rotation axis, center, delta and step count. Internally the node is powered by the `bmesh.spin <http://www.blender.org/documentation/blender_python_api_2_71_release/bmesh.ops.html?highlight=spin#bmesh.ops.spin>` _ operator.

Inputs
------
It's vectorized, meaning it accepts nested and multiple inputs and produces multiple sets of output

