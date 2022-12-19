#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Городецкий
# Licensed GPL 3.0
# http://nikitronn.narod.ru/
# Python 2.7



#Это программа-дешифратор типа пунто-свитчера, только не потоковая,
#а как бы переводчик. И работает через терминал.

import sys
import codecs

def decode(filename, doprint):
  dictionary={'q':'й','w':'ц','e':'у','r':'к','t':'е','y':'н','u':'г','i':'ш','o':'щ','p':'з',
              '[':'х',']':'ъ','a':'ф','s':'ы','d':'в','f':'а','g':'п','h':'р','j':'о','k':'л',
              'l':'д',';':'ж',"""'""":'э','z':'я','x':'ч','c':'с','v':'м','b':'и','n':'т',
              'm':'ь',',':'б','.':'ю','/':'.','`':'ё','^':':','$':';','#':'№','@':'''"''',
              '&':'?','<':'б','>':'ю','~':'ё'}
  newword=[]
  if not doprint:
    file_open=open(filename, 'rU')
    text=file_open.read()
    file_open.close()
  else:
    text = raw_input('Ваш текст:')
  for char in text:
    ch = str.lower(char)
    if ch in dictionary:
      newword.append(dictionary[ch])
    else:
      newword.append(ch)
  lit=''
  for i in newword:
    lit += i
  print '\n', lit.decode('utf-8'), '\n'
  return lit

def main():
  if len(sys.argv) != 2:
    print '''использование: python ./trans.py [входной_файл]/[-p]
-p означает ввод текста вручную или копипаст'''
    sys.exit(1)
  filename = sys.argv[1]
  if filename == '-p':
    doprint=True
  decode(filename, doprint)

  
if __name__ == '__main__':
  main()
