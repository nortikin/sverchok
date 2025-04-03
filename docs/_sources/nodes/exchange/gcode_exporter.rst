Export G-code
=============

Functionality
-------------

Export file with G-code describing the generated shape

Inputs
------

* **Layer Height** - List of coefficients for layer height        
* **Flow Mult** - List of coefficients for Print speed        
* **Vertices** - Main thing The Geometry (can be one or several paths)        

Outputs
-------

- **Info** - Information for sthetoscope of properties of Gcode - path length, filament extrusion and Extruded Volume    
- **Vertices** - Vertices that will be exported    
- **Printed Edges** - Edges will be printed    
- **Travel Edges** - Edges not will be printed    

Properties
----------

- **File** - Define file in directory, that will be written    
- **Continuous / Retraction** - Define would be filament retracted back in to nozzle (some kind of effect)    
- **Start** - Starting Gcode before it starts printing    

------

- **End** - Finishing Gcode after all geometry done (turn back nozzle to home position for example)    
- **Export G-code** - Button to export when all ready    

Continuous
----------

- **Filament (Ф)** - Thickness of fliament    
- **Nozzle** - Coeffitient of nozzle diameter    
- **Print** - Printing Speed general    

Retraction
----------

- **Filament (Ф)** - Thickness of fliament    
- **Nozzle** - Coeffitient of nozzle diameter    

------

- **Print** - Printing Speed general    
- **Zlift** - Lift when retract    
- **Travel** - Travel when retract    

------

- **Retraction** - Itself parameter    
- **Z Hop** - Hop after retract    
- **Preload** - Load after retract action done    

------

- **Sort Layers (z)** - Sorting if input geometry have some disorder    
- **Close Shapes** - Close all layers    

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/5783432/113355242-1f2ef980-9349-11eb-8467-b9be96c9cca3.png
  :alt: Gcode.PNG

