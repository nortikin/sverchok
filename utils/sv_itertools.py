from itertools import chain, repeat


# the class based should be slower but kept until tested
class SvZipExhausted(Exception):
    pass

class SvSentinel:
    def __init__(self, fl, top):
        self.fl = fl
        self.top = top
        self.done = False

    def __next__(self):
        if self.done:
            raise StopIteration
        self.top.counter -= 1
        if not self.top.counter:
            raise SvZipExhausted
        self.done = True
        return self.fl

    def __iter__(self):
        return self

class sv_zip_longest2:
    def __init__(self, *args):
        self.counter = len(args) 
        self.iterators = []
        for lst in args:
            fl = lst[-1]
            filler = repeat(fl)
            self.iterators.append(chain(lst, SvSentinel(fl,self), filler))

    def __next__(self):
        try:    
            if self.counter:
                return tuple(map(next, self.iterators))
            else:
                raise StopIteration
        except SvZipExhausted:
            raise StopIteration

    def __iter__(self):
        return self    


def sv_zip_longest(*args):
    # by zeffi
    longest = max([len(i) for i in args])
    itrs = [iter(sl) for sl in args]
    for i in range(longest):
        yield tuple((next(iterator, args[idx][-1]) for idx, iterator in enumerate(itrs)))
