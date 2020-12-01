'''
in U_nums s d=2 n=2
in V_char s d=2 n=2
enum = Orig Flip
out numeration s
'''

from functools import reduce


def ui(self, context, layout):
    layout.prop(self, 'custom_enum',expand=True)
    cb_str = 'node.scriptlite_custom_callback'
#ND = self.node_dict.get(hash(self))               #
#if ND:                                            #
#    callbacks = ND['sockets']['callbacks']        #    this will be hidden in the node eventually 
#    if not 'my_operator' in callbacks:            #
#        callbacks['my_operator'] = my_operator    #


numeration = [[]]
charz = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
charth = [charz] + [[i+k for k in charz] for i in charz]
charth = reduce(lambda x,y: x+y, charth)

if self.custom_enum == 'Orig':
    chars = charth[:V_char]
    for i in range(U_nums):
        num_ = []
        for ch in chars:
            num_.append([ch+str(i)])
        numeration[0].extend(num_)
elif self.custom_enum == 'Flip':
    U_nums, V_char = V_char, U_nums
    chars = charth[:V_char]
    for ch in chars:
        num_ = []
        for i in range(U_nums):
            num_.append([str(ch)+str(i)])
        numeration[0].extend(num_)