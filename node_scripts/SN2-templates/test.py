
class MyScript( SvScript):
    inputs = [("s" , "List")]
    outputs = [("s", "Sum")]
    
    def process(self):
        name, data = self.get_data()
        out = []
        for obj in data:
            out.append(sum(obj))
            
        self.set_data({'Sum':out})
