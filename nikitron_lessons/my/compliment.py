#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2013 Городецкий
# Генератор комплиментов
# Licensed GPL 3.0
# http://nikitronn.narod.ru/
# Python 3,3




import sys
import codecs
import random

def w(a):
  return random.choice(a)

def main():
  a1 = ['Ты']
  a2 = ['так', "очень", "офигенски", "просто", 'невероятно', 'супер', 'безумно']
  a3 = ['круто','потрясно','вкусно','улётно','клёво','прелестно','замечательно']
  a4 = ['выглядишь','пахнешь','целуешься','печёшь пирожки','двигаешься','танцуешь','готовишь','поёшь','смеёшься']
  a5 = ['пупсик','дорогая','милая','солнце','зайка','как всегда']
  compliment = (str(w(a1))+' '+ str(w(a2))+ ' '+ str(w(a3))+ ' '+ str(w(a4)) + ','+ ' '+ str(w(a5)) + '!')
  print (compliment)

  
if __name__ == '__main__':
  main()