
class SocketInfo(object):
    def __init__(self, type, id, display_shape=None, idx=None):
        self.type = type
        self.id = id
        self.idx = idx
        self.display_shape = display_shape

class SvExDynamicSocketsHandler(object):
    def __init__(self):
        self.inputs_registry = dict()
        self.outputs_registry = dict()

    def register_inputs(self, *sockets):
        for idx, socket in enumerate(sockets):
            socket.idx = idx
            self.inputs_registry[socket.id] = socket
        return sockets

    def register_outputs(self, *sockets):
        for idx, socket in enumerate(sockets):
            socket.idx = idx
            self.outputs_registry[socket.id] = socket
        return sockets

    def get_input_by_idx(self, idx):
        for socket in self.inputs_registry.values():
            if socket.idx == idx:
                return socket
        raise Exception("unsupported input idx")
        
    def get_output_by_idx(self, idx):
        for socket in self.outputs_registry.values():
            if socket.idx == idx:
                return socket
        raise Exception("unsupported output idx")

    def init_sockets(self, node):
        for socket in self.inputs_registry.values():
            s = node.inputs.new(socket.type, socket.id)
#             if socket.display_shape is not None:
#                 s.display_shape = socket.display_shape
        for socket in self.outputs_registry.values():
            s = node.outputs.new(socket.type, socket.id)
#             if socket.display_shape is not None:
#                 s.display_shape = socket.display_shape

