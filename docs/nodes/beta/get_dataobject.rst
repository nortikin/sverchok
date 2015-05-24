Set_dataobject
==============

*destination after Beta:*

Functionality
-------------

*Работает с одним списком объектов и одним списком Values*

*можно обьединять несколько списков в один с помощью ListJoin node*

Когда подключен только один Objects сокет, выполняет **(Объект.текст)**

Если подключен Value сокет, выполняет **(Объект.текст=Value)**

Если подключен OutValue сокет, выполняет **(OutValue=Объект.текст)**

*нельзя подключать оба Values сокета одновременно*

Inputs
------

This node has the following inputs:

- **Objects** 
- **values**


Outputs
-------

This node has the following outputs:

- **outvalues**

Examples of usage
-----------------
