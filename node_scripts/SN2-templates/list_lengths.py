
class MultiInputDemo(SvMultiInput):
    
    # Start amount of sockets 
    inputs  = [
        ['s', 'Data 0'],
    ]
    # multi socket type, for inputs
    multi_socket_type = "s"
    
    # string to use for socket names will be called like base_name.format(socket_nr)
    base_name = "Data {}"
    
    # output function, only one allowed
    outputs = [("s", "Data")]
   
    # static method, args is a list of the data from the linked sockets 
    @staticmethod
    def function(args):
        return [[len(arg) for arg in args]]
