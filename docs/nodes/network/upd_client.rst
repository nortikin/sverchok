upd_client
==========

the docs for this node are found here: https://takuro.ws/2015/09/14/sverchok-udpclientnode/

Anyone familiar with max/msp / puredata will have a fair idea if how this node works.

interface
---------

here are the interface descriptions

============= ====================================================
UI Element    description
============= ====================================================
IP            IP address of remote server you want to access
Port          Port number of remote server you want to access
Buffer(Byte)  Size of buffer you want to read
Timeout(sec)  Timeout length of network connection
============= ====================================================

Examples
--------

The code examples are written for an older version of ScriptNode1::

    def sv_main(in_value=[[0]]):
        out_value = str(in_value[0][0][0])
        in_sockets = [['s', 'in', in_value]]
        out_sockets = [['s','out', out_value]]
        return in_sockets, out_sockets

in snlite that becomes::

    """
    in in_value s d=0 n=2
    out out_value s
    """

    out_value.append(str(in_value))

