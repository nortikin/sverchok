# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


class SvNoDataError(LookupError):
    def __init__(self, socket=None, node=None, msg=None):

        self.extra_message = msg if msg else ""

        if node is None and socket is not None:
            node = socket.node
        self.node = node
        self.socket = socket

        super(LookupError, self).__init__(self.get_message())

    def get_message(self):
        if self.extra_message:
            return f"node {self.socket.node.name} (socket {self.socket.name}) {self.extra_message}"
        if not self.node and not self.socket:
            return "SvNoDataError"
        else:
            return f"No data passed into socket '{self.socket.name}'"

    def __repr__(self):
        return self.get_message()

    def __str__(self):
        return repr(self)

    def __unicode__(self):
        return repr(self)

    def __format__(self, spec):
        return repr(self)


class CancelError(Exception):
    """Aborting tree evaluation by user"""


class SvProcessingError(Exception):
    pass


class SvNotFullyConnected(SvProcessingError):

    def __init__(self, node, sockets):
        self.node = node
        self.sockets = sockets
        socket_names = ", ".join(sockets)
        self.message = "The following inputs are required for node to perform correctly: " + socket_names

    def __str__(self):
        return self.message


class ImplicitConversionProhibited(Exception):
    def __init__(self, socket, msg=None):
        super().__init__()
        self.socket = socket
        self.node = socket.node
        self.from_socket_type = socket.other.bl_idname
        self.to_socket_type = socket.bl_idname
        if msg is None:
            msg = f"Implicit conversion from socket type {self.from_socket_type}" \
                  f" to socket type {self.to_socket_type} is not supported for" \
                  f" socket {socket.name} of node {socket.node.name}. Please" \
                  f" use explicit conversion nodes."
        self.message = msg

    def __str__(self):
        return self.message


class DependencyError(Exception):
    """Raise when some library is not installed"""
