'''
in U_nums s d=2 n=2
in V_char s d=2 n=2
in flip s d=0 n=2
out numeration s
'''

numeration = [[]]
charz = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
charth = charz + [i+i for i in charz]
chars = charth[:V_char]
if flip:
    for i in range(U_nums):
        num_ = []
        for ch in chars:
            num_.append([ch+str(i)])
        numeration[0].extend(num_)
else:
    for ch in chars:
        num_ = []
        for i in range(U_nums):
            num_.append([ch+str(i)])
        numeration[0].extend(num_)