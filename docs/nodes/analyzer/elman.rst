Elman neuro node layer 1
========================

По-русски
---------

 Узел нейронной сети
  Обучаемый узел. вы его можете обучить закономерностям в данных, подавая данные для просчёта и идеальные числа.
  Выставляя параметры вы коррекируете работу нейросети. Данный узел просто вырабатывает "условный рефлекс".
  Вынимая идеальный эталонный параметр вы отпускаете его в вольное плаванье, узел теперь сам решает что надо выдавать в ответ на данные.
  Данные запакованные в каждый объект. Если подаёшь серию по одному числу в объекте, то на входе будет много объектов. И на выходе будет столько же объектов с числом.
  Если на вход подать все числа в одном объекте, это будет считаться много параметров и выдавать один объект.
  Всегда вводите постоянное число переменных, если переменные поменялись - сбрасываются все исчисления. Будьте последовательны.

- coef_learning - коэффициент скорости обучения, влияет на точность (чем меньше, тем точнее и дольше);
- gisterezis - разброс выходных и эталонных данных;
- maximum - максимальное числа на входе (лучше задать чуть больше);
- cycles - количество проходов на просчет одного объекта;
- A layer - количество ядер входного слоя (равно числу в чисел в объекте);
- B layer - количество ядер внутреннего слоя - чем больше, тем умнее нейрон (большое количество может привести к переобучению сети, иногда лучше его уменьшить);
- C layer - количество ядер выходного слоя - равно количеству чисел в объекте на выходе;
- epsilon - внутренняя переменная - определяет сдвиг аргумента в циклах cycles (на результат слабо влияет);
- lambda - сдерживающий коэффициент, чтобы сеть не забивалась данными;
- threshold - внутренняя переменная - определяет порог разумности обучения в циклах cycles (на результат не особо влияет).

English
-------

 Neuro network node
  This node teachable. You may teach him rules, that he understand himself. Just put data and correct answer. When displace answer, he will find right answer himself.
  Input data. Inserting many objects - output many objects. Inserting one object with many parameters - output one object.
  Always insert constant numbers count of parameters, otherwise it will reset neuro data and start every time from beginning. Keep constant numbers count.

- coef_learning - learning speed coeffitient, accuracy influence (less - more accuracy);
- gisterezis - spread of input and etalon data;
- maximum - maximum number input (better define little overhang number);
- cycles - passes on one object;
- A layer - input layer cores (and it is number of objects);
- B layer - inner layer cores - more - smarter (overlearning is bad too);
- C layer - output layer cores - numbers quantity in output;
- epsilon - inner variable - argument offset in passes 'cycles' (not much influence totally);
- lambda - holding coefficient, to preserve data flooding;
- threshold - inner variable - defines reasonability limit in passes 'cycles' (not much influence totally).

