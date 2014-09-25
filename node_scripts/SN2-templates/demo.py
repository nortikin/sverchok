class MyRangeNode( SvCustomNodeScript):
    intputs = [
        ("s", "Start", 0),
        ("s", "Stop", 10),
        ("s", "Step", 1)]
    
    outputs = [
        ("s", "Output")
        ]
    
    @atom_level
    @match_long_repeat
    def func(start, stop, step):
        return list(range(start, stop, step))

class MySumNode( SvCustomNodeScript):
    intputs = [
        ("s", "Input", None),
    ]
    
    outputs = [
        ("s", "Output")
        ]
    
    @list_level
    def func(list_to_sum):
        return sum(list_to_sum)
