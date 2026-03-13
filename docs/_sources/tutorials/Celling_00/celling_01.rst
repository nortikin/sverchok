***************************************************************
Celling 01. Presenting the layout of Generation-to-DWG pipeline
***************************************************************

Aim
~~~

On my job there was order to make complicated celling design, that avoids beams and columns, also turns around corner and going to zero width at the end. So, the shape of celling was predefined as the second-order curve. But from beginning it was pattern that needed to fit design. Pattern of rhomb with fixed dimensions. Also as target was defined gap between plates. And for sure, all peaces needed to be planes without curvature. As fish scales or snake scales more.

Requirements
------------

You will need to install:
    **Blender4.0+**    

    **Sverchok** with dependencies (not *opensubdiv*, no *Freecad* and no *mcubes* needed)     

    **Sverchok-extra** with mostly *xmlx* deps (no *pygalmesh* and no *SDF* needed)     

    ```pip install latex``` for SVG export     

    
    
Inputs
------

|image5|

1. **Pattern**:

   Rhombs where oriented originally in one direction.
   But in workflow was decided to rotate around corner. That
   issue forced me to bake and process pattern manually. In fact
   it was right desigion. Manual workflow here is optimal.

   |image2|


2. **Shape**:

   Initially, there was two guidelines as splines. in lower belt and 
   upper belt, that jointed at one side ni zero distance.

   |image3|


3. **Gap**:

   Gap of 14 mm is more o less regular, but in sharp "corners" 
   may happened conflicts. Checked in process and it was ok.
   Next thing - borders. I needed to step from border at half 
   a distance before offset the plates, but it was not so easy.

   |image4|

4. **Layout**:

   |image1|

   Node tree consists of some parts:

   *  **Cutting** - Borders creates limits of pattern, that are rhombs.

     |image6|

   *  **Surface** - Curves creating shape

     |image7|

   *  **Wireframe** - Projecting pattern to shape:

     - Dissolve node with SNL node gererate and get list of indices for edges. There is manual job nevertheless for indices ordering

     |image8|

     - Working here is: 1. Bake 2. correct indices 3. reload
     - Analyzing panels is analitic block to bugfixing shape

     |image9|

   *  **Halfes** - Plates division for corner to bend them along line:

     |image10|

   *  **Offset** - Offset with edge exclusion, most intriguing part for me:

     |image11|

   *  **Types** - Separate plates to types:

     - + Inspection

     |image12|

   *  **Layout on paper** - spread on paper size:

     |image13|

   *  **SVG plans** - SVG for elevations and marking plans:

     |image14|

   *  **SVG marks** - SVG with marks texts and dimensions:

     |image15|


   *  **XLSX** - XLSX table to gather specification:

     |image16|

   *  **DXF** - DXF outputs block for production:

     |image17|


.. |image1| image:: https://github-production-user-asset-6210df.s3.amazonaws.com/5783432/293879492-fc641b47-3a52-4556-9297-9cc9329280c4.png
.. |image2| image:: https://github-production-user-asset-6210df.s3.amazonaws.com/5783432/293880929-b41d06a9-ff54-4d29-99ce-fd685f49c6d8.png
.. |image3| image:: https://github-production-user-asset-6210df.s3.amazonaws.com/5783432/293881371-9caeecfd-4e6e-4414-bca6-597c8b25eb21.png
.. |image4| image:: https://github-production-user-asset-6210df.s3.amazonaws.com/5783432/293881640-89346b16-ccdb-4334-946e-fc99814cb5de.png
.. |image5| image:: https://github-production-user-asset-6210df.s3.amazonaws.com/5783432/293879925-91339fdf-db1a-401d-b3b9-24fbd0a1a5b1.png
.. |image6| image:: https://github-production-user-asset-6210df.s3.amazonaws.com/5783432/293882058-05418a68-ba0a-4a18-8730-31a4f19949db.png
.. |image7| image:: https://github-production-user-asset-6210df.s3.amazonaws.com/5783432/293881371-9caeecfd-4e6e-4414-bca6-597c8b25eb21.png
.. |image8| image:: https://github-production-user-asset-6210df.s3.amazonaws.com/5783432/293882323-30db62f9-5e17-467d-be6e-bc3ba7def2df.png
.. |image9| image:: https://github-production-user-asset-6210df.s3.amazonaws.com/5783432/293882547-9992aade-32ee-48eb-8849-ed1cafd53706.png
.. |image10| image:: https://github-production-user-asset-6210df.s3.amazonaws.com/5783432/293883019-f6752225-f5a9-4991-8a5e-d8a6577c5813.png
.. |image11| image:: https://github-production-user-asset-6210df.s3.amazonaws.com/5783432/293881640-89346b16-ccdb-4334-946e-fc99814cb5de.png
.. |image12| image:: https://github-production-user-asset-6210df.s3.amazonaws.com/5783432/293883377-6cf5745d-e8a3-4502-b7aa-f31174c8b321.png
.. |image13| image:: https://github-production-user-asset-6210df.s3.amazonaws.com/5783432/293884060-4c90d0a1-7de8-4629-bacc-fcffeb6f152c.png
.. |image14| image:: https://github-production-user-asset-6210df.s3.amazonaws.com/5783432/293884536-12802bd9-8c1a-4014-900f-b4f2b5d94288.png
.. |image15| image:: https://github-production-user-asset-6210df.s3.amazonaws.com/5783432/293884536-12802bd9-8c1a-4014-900f-b4f2b5d94288.png
.. |image16| image:: https://github-production-user-asset-6210df.s3.amazonaws.com/5783432/293884845-96599d3d-9d78-42ef-8e85-7ef4a67f3650.png
.. |image17| image:: https://github-production-user-asset-6210df.s3.amazonaws.com/5783432/293885389-6e5a01c0-07d7-4b53-b17f-95beb7b964cb.png
