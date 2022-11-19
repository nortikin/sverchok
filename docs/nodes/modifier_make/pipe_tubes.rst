Pipe
====

.. image:: https://user-images.githubusercontent.com/14288520/201471088-81a81e4f-c550-41cc-b8dc-e0b3928ea082.png
  :target: https://user-images.githubusercontent.com/14288520/201471088-81a81e4f-c550-41cc-b8dc-e0b3928ea082.png

Functionality
-------------

Making pipes from edges.   

.. image:: https://user-images.githubusercontent.com/14288520/201471091-8d941abe-eed5-4579-a601-2f912ae443f3.png
  :target: https://user-images.githubusercontent.com/14288520/201471091-8d941abe-eed5-4579-a601-2f912ae443f3.png

Inputs
------

* **Vers** - Vertices of piped object.   
* **Edgs** - Edges of piped object.     
* **diameter** - Diameter of pipe.     
* **nsides** - Number of sides of pipe.     
* **offset** - Offset on length to avoid self intersection.     
* **extrude** - Scale the pipe on local X direction.   


Properties  
----------  

* **close** - Close pipes between each other to make complete topology of united mesh.     


Outputs  
-------  

* **Vers** - Vertices of output.     
* **Pols** - Polygons of output.     

See also
--------

* Modifiers->Modifier Make-> :ref:`Bevel a Curve <BEVEL_A_CURVE_ALGORITHM>`

Examples  
--------  

.. image:: https://user-images.githubusercontent.com/14288520/201471241-581c2b5b-821a-4868-aeae-952f0b704fc6.png
  :target: https://user-images.githubusercontent.com/14288520/201471241-581c2b5b-821a-4868-aeae-952f0b704fc6.png

* Generator->Generatots Extended-> :doc:`Hilbert </nodes/generators_extended/hilbert>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Vector-> :doc:`Vector Interpolation </nodes/vector/interpolation_mk3>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Color-> :doc:`Color Ramp </nodes/color/color_ramp>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

.. image:: https://cloud.githubusercontent.com/assets/5783432/5291188/cf0f6eb8-7b57-11e4-9adf-025bbd1d74eb.png  
  :target: https://cloud.githubusercontent.com/assets/5783432/5291188/cf0f6eb8-7b57-11e4-9adf-025bbd1d74eb.png  
  :alt: noalt  

* Text-> :doc:`Note </nodes/text/note>`
* Float Series: Number-> :doc:`Number Range </nodes/number/number_range>`
* Vector-> :doc:`Vector Interpolation </nodes/vector/interpolation_mk3>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Bmesh Viewer Draw: Viz-> :doc:`Mesh Viewer </nodes/viz/mesh_viewer>`