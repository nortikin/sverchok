Elman neuro node layer 1
------------------------

По-русски
---------

  Узел нейронной сети
  ^^^^^^^^^^^^^^^^^^^

- koef_learning - коэффициент скорости обучения, влияет на точность (чем меньше, тем точнее и дольше);
- gisterezis - разброс выходных и эталонных данных;
- maximum - максимальное числа на входе (лучше задать чуть больше);
- cycles - количество проходов на просчет одного объекта;
- A layer - количество ядер входного слоя (равно числу в чисел в объекте);
- B layer - количество ядер внутреннего слоя - чем больше, тем умнее нейрон (большое количество может привести к переобучению сети, иногда лучше его уменьшить);
- C layer - количество ядер выходного слоя - равно количеству чисел в объекте на выходе;
- epsilon - внутренняя переменная - определяет сдвиг аргумента в циклах cycles (на результат слабо влияет);
- lambda - сдерживающий коэффициент, чтобы сеть не забивалась данными;
- treshold - внутренняя переменная - определяет порог разумности обучения в циклах cycles (на результат не особо влияет).

English
-------

  Neuro network node
  ^^^^^^^^^^^^^^^^^^

- koef_learning - learning speed koeffitient, accuracy influence (less - more accuracy);
- gisterezis - spread of input and etalon data;
- maximum - maximum number input (better define little overhang number);
- cycles - passes on one object;
- A layer - input layer cores (and it is number of objects);
- B layer - inner layer cores - more - smarter (overlearning is bad too);
- C layer - output layer cores - numbers quantity in output;
- epsilon - inner veriable - argument offset in passes 'cycles' (not much influence totally);
- lambda - holding coefficient, to preserve data flooding;
- treshold - inner veriable - defines reasonability limit in passes 'cycles' (not much influence totally).

