Mesh Join
=========

.. image:: https://user-images.githubusercontent.com/14288520/200012677-336dc1a6-0b6b-4bc6-b9a7-9440529776c4.png
  :target: https://user-images.githubusercontent.com/14288520/200012677-336dc1a6-0b6b-4bc6-b9a7-9440529776c4.png

Functionality
-------------

Analogue to ``Ctrl+J`` in the 3dview of Blender. Separate nested lists of *vertices* and *polygons/edges* are merged. The keys in the Edge and Polygon lists are incremented to coincide with the newly created vertex list.

.. image:: https://user-images.githubusercontent.com/14288520/200015469-69825d1f-a219-4bd7-bc0f-66e08eb9e1bc.png
  :target: https://user-images.githubusercontent.com/14288520/200015469-69825d1f-a219-4bd7-bc0f-66e08eb9e1bc.png

The inner workings go something like::

    vertices_obj_1 = [
        (0.2, 1.5, 0.1), (1.2, 0.5, 0.1), (1.2, 1.5, 0.1),
        (0.2, 2.5, 5.1), (0.2, 0.5, 2.1), (0.2, 2.5, 0.1)]

    vertices_obj_2 = [
        (0.2, 1.4, 0.1), (1.2, 0.2, 0.3), (1.2, 4.5, 4.1),
        (0.2, 1.5, 3.4), (5.2, 6.5, 2.1), (0.2, 5.5, 2.1)]

    key_list_1 = [[0,1,2],[3,4,5]]
    key_list_2 = [[0,1,2],[3,4,5]]

    verts_nested = [vertices_obj_1, vertices_obj_2]
    keys_nested = [key_list_1, key_list_2]

    def mesh_join(verts_nested, keys_nested):

        mega_vertex_list = []
        mega_key_list = []

        def adjust_indices(klist, offset):
            return [[i+offset for i in keys] for keys in klist]
            # for every key in klist, add offset
            # return result

        for vert_list, key_list in zip(verts_nested, keys_nested):
            adjusted_key_list = adjust_indices(key_list, len(mega_vertex_list))
            mega_vertex_list.extend(vert_list)
            mega_key_list.extend(adjusted_key_list)

        return mega_vertex_list, mega_key_list

    print(mesh_join(verts_nested, keys_nested))

    # result
    [(0.2, 1.5, 0.1), (1.2, 0.5, 0.1), (1.2, 1.5, 0.1),
    (0.2, 2.5, 5.1), (0.2, 0.5, 2.1), (0.2, 2.5, 0.1),
    (0.2, 1.4, 0.1), (1.2, 0.2, 0.3), (1.2, 4.5, 4.1),
    (0.2, 1.5, 3.4), (5.2, 6.5, 2.1), (0.2, 5.5, 2.1)]

    [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, 10, 11]]




Inputs & Outputs
----------------

The inputs and outputs are *vertices*, edges and *polygons*.

Expects a nested collection of vertex lists. Each nested list represents an object which can itself have many vertices and key lists.

See also
--------

* Matrix-> :doc:`Matrix Apply to Mesh </nodes/matrix/apply_and_join>` (param Join On/Off)

Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/200021156-1a575bae-42c8-43a8-b95e-5d0c112fb283.png
  :target: https://user-images.githubusercontent.com/14288520/200021156-1a575bae-42c8-43a8-b95e-5d0c112fb283.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Color-> :doc:`Color Ramp </nodes/color/color_ramp>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/200025633-d89e4b61-e303-4afa-ab2f-0df2c6e21ff9.png
  :target: https://user-images.githubusercontent.com/14288520/200025633-d89e4b61-e303-4afa-ab2f-0df2c6e21ff9.png

* Generator-> :doc:`Sphere </nodes/generator/sphere>`
* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Transform-> :doc:`Matrix Apply (verts) </nodes/transforms/apply>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* List->List Struct-> :doc:`List Repeater </nodes/list_struct/repeater>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

Notes
-----
