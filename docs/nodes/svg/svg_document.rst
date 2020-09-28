SVG Document
============

Functionality
-------------

This node outputs the SVG objects to a SVG document.

Inputs
------

- Folder Path: Folder where de SVG file will be placed.
- Template Path: File to use as template.
- SVG Objects: Objects to add to the document.

Options
-------

- Live Update: When enabled the output file will be rewritten with any change in the data flow that leads to the node.
- Units: Document units. This will affect all the input SVG Objects and numerical properties (Element Size, Stroke Width, Font Size...)
- Name: Name of the output file.
- Width: Document width
- Height: Document height
- Scale: Objects scale and properties scale.

Operators
---------

- Open Server: The file will be opened with a web-browser inside a page that will update to see the changes in almost real-time.
- Write: Write output file.

Outputs
-------

- Canvas Vertices and Edges: Geometry to visualize the canvas limits in 3d view


Examples
--------

.. image:: https://user-images.githubusercontent.com/10011941/90965270-f5fede80-e4c6-11ea-85c9-31701ebe211f.png
