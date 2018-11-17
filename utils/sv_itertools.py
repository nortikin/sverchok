from itertools import chain, repeat, zip_longest


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

class sv_zip_longest:
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

def sv_zip_longest2(*args):
    # by zeffi
    longest = max([len(i) for i in args])
    itrs = [iter(sl) for sl in args]
    for i in range(longest):
        yield tuple((next(iterator, args[idx][-1]) for idx, iterator in enumerate(itrs)))


def recurse_fx(l, f):
    if isinstance(l, (list, tuple)):
        return [recurse_fx(i, f) for i in l]
    else:
        return f(l)

def recurse_fxy(l1, l2, f):
    l1_type = isinstance(l1, (list, tuple))
    l2_type = isinstance(l2, (list, tuple))
    if not (l1_type or l2_type):
        return f(l1, l2)
    elif l1_type and l2_type:
        fl = l2[-1] if len(l1) > len(l2) else l1[-1]
        res = []
        res_append = res.append
        for x, y in zip_longest(l1, l2, fillvalue=fl):
            res_append(recurse_fxy(x, y, f))
        return res
    elif l1_type and not l2_type:
        return [recurse_fxy(x, l2, f) for x in l1]
    else: #not l1_type and l2_type
        return [recurse_fxy(l1, y, f) for y in l2]


def recurse_verts_fxy(l1, l2, f):
    l1_type = isinstance(l1, (list))
    l2_type = isinstance(l2, (list))
    if not (l1_type or l2_type):
        return f(l1, l2)
    elif l1_type and l2_type:
        fl = l2[-1] if len(l1) > len(l2) else l1[-1]
        res = []
        res_append = res.append
        for x, y in zip_longest(l1, l2, fillvalue=fl):
            res_append(recurse_verts_fxy(x, y, f))
        return res
    elif l1_type and not l2_type:
        return [recurse_verts_fxy(x, l2, f) for x in l1]
    else: #not l1_type and l2_type
        return [recurse_verts_fxy(l1, y, f) for y in l2]

# append all the elements to one single list
def append_all(l, flat):
    if isinstance(l,(list)):
        return [append_all(i, flat) for i in l]
    else:
        flat.append(l)
        return l

# flatten sublists
def flatten(l):
    flat = []
    append_all(l, flat)
    return flat

# append all the lists to one single list
def append_lists(l, lists):
    if isinstance(l,(list)):
        flat_list = True
        for i in l:
            if isinstance(i,(list)):
                flat_list = False
                break
        if flat_list:
            lists.append(l)
            return None
        else:
            return [append_lists(i, lists) for i in l]
    else:
        lists.append([l])
        return None

# generate a single list with 1 level lists inside
def list_of_lists(l):
    out_list = []
    append_lists(l, out_list)
    return out_list

# works with irregular sublists
def match_longest_lists(lists):
    add_level = max([isinstance(l, list) for l in lists])
    if add_level:
        for i in range(len(lists)):
            l = lists[i]
            if not isinstance(l, list):
                lists[i] = [l]
    length = [len(l) for l in lists]
    max_length = max(length)
    # extend shorter lists
    for l in lists:
        for i in range(len(l), max_length):
            l.append(l[-1])
    try:
        return zip(*[match_longest_lists([l[i] for l in lists]) for i in range(max_length)])
    except:
        return lists


def extend_if_needed(vl, wl, default=0.5):
    # match wl to correspond with vl
    try:
        last_value = wl[-1][-1]
    except:
        last_value = default

    if (len(vl) > len(wl)):
        num_new_empty_lists = len(vl) - len(wl)
        for emlist in range(num_new_empty_lists):
            wl.append([])

    # extend each sublist in wl to match quantity found in sublists of v1
    for i, vlist in enumerate(vl):
        if (len(vlist) > len(wl[i])):
            num_new_repeats = len(vlist) - len(wl[i])
            for n in range(num_new_repeats):
                wl[i].append(last_value)
    return wl
