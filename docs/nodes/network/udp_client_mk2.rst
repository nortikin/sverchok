UDP client mk2
==============

Functionality
-------------
      
Receive or send UDP data to some IP4 adress (if you like it can be extended to ip6).      
To make it sent - link input socket (left), configure ip/port and press run.      
To make receive - link output socket (right), configure ip/port/bufer/timeout and press run.     
To change ip/port - press Stop, change parameters, press Run     
    
Expression syntax 
----------------- 



Inputs
------

- **send**, data, that you wish to send to Internet (or localhost) to some port     

Parameters
----------

This node has the following parameters:

- **Run/Stop**. Buttons to run stuff or stop stuff. It turns on the threading definition o listen ip/port permanently and letting you send data at node tree changes event (when you change data in input socket or press update all).   
- **IP**. ip4 adress to work with. Default 127.0.0.1 - localhost.   
- **Port**. Port to work with.  Default 9250.   
- **Buffer**. Size of buffer to receive data in it. If data larger than bufer size it will be error. In bytes.    
- **Timeout**. Periods to cache one data (frequency) to receive.    


Outputs
-------

- **receive**. data coming in as string, so ast component of python will interprate result literally. If your data is correct sverchok list data, you not need farthere modification of incoming data. 

