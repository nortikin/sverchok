#English
##Sverchok parametric tools

**addon for**: [Blender](http://blender.org)  (version *2.71* and above).  
**current sverchok version**: find this in the version file in `utils` folder, or properties panel in NodeView   
**License**: [GPL3](http://www.gnu.org/licenses/quick-guide-gplv3.html)   
**prerequisites**: Python 3.4. and numpy, both included in recent versions of Blender  

  
###Description
Sverchok is a powerful parametric tool for architects, allowing geometry to be programmed visually with nodes. 
Mesh and geometry programming consists of combining basic elements such as:  

  - lists of indexed Vectors representing coordinates (Sverchok vectors are zero based)
  - lists of grouped indices to represent edges and polygons.
  - matrices (user-friendly rotation-scale-location transformations)

###Possibilities
Comes with more than 100 nodes to help create and manipulate geometry. Combining these nodes will allow you to:

  - do parametric constructions
  - easily change parameters with sliders and formulas
  - do cross sections, extrusions, other modifications with hight level flexible parametrised and vectorised node tools  
  - calculate areas, volume and other, analize geometry and make CSV tables or import directly to Sverhok
  - use Vector fields, create them, visualize data
  - even code your own custom nodes in python with Scripted node
  - make your own 'addons' on node layouts and utilise them with Sverchok 3dview panel in your everyday pipeline
  - access to pythn API with special node EvalKnieval
  - upgrade Sverchok with pressing one button
  - make your own neuro network
  - and much, much more!

###Installation
Install Sverchok as you would any blender addon.  
  
-  _Installation from Preferences_  
   Download Sverchok from github  
   User Preferences > Addons > install from file >   
   choose zip-archive > activate flag beside Sverchok  
   If appears error - close and run blender again and activate again.  
   Enable permanently in the startup.blend using `Ctrl + U` and `Save User Settings` from the Addons menu.  
  
-  _Manual installation_  
   Download Sverchok from github  
   Drop the `sverchok-master` folder into `/scripts/addons`.  
   User Preferences > Addons > Community > (search Sverchok) > activate flag beside Sverchok  
   Enable permanently in the startup.blend using `Ctrl + U` and `Save User Settings` from the Addons menu.   

-  _Upgrade Sverchok on fly_   
   Use button `Check for new version` in sverchok panel in node editor (press `N` for panel)  
   And at the end press `F8` button to reload addons. In next blender run in panel will appear new version number  

###Troubleshooting Installation Errors

In case Sverchok fails to install, we've compiled a list of reasons and known resolutions [here](/docs/installation.rst). Please let us know if you encounter other installation issues.

###Contact and Credit
Homepage: http://nikitron.cc.ua/sverchok_en.html  
Authors: 
-  Alexander Nedovizin,  
-  Nikita Gorodetskiy,  
-  Linus Yng,  
-  Agustin Gimenez, 
-  Dealga McArdle  

Email: sverchok-b3d@yandex.ru  


#По-русски

версию смотри папку utils файл version   
дополнение для: http://blender.org   
лицензия: GPL3   
совместим с Blender версией: `>=` 2.71  
требует Python 3.4. и numpy (включены в Blender)  

  
###Описание
Сверчок - мощный инструмент для архитектора, позволяющий программировать визуально узлами. 
Программирование сетки и геометрии состоит из "кирпичей":  

  - списков Векторов являющих собой координаты (В Сверчке векторы основаны на нуле)
  - списки групп индексов представляющие рёбра и грани.
  - матрицы (удобный и понятный способ изменения положения-масштаба-поворота)

###Возможности
Более 100 узлов вам помогут создать и изменять геометрию. А сочетания узлов помогут вам:

  - делать параметрические конструкции
  - легко менять параметры слайдерами и формулами
  - делать сечения, выдавливания, другие изменения с гибкым параметризованым и векторизованым набором узловых инструментов  
  - считать площади, объём и прочее, анализировать геометрию и выводить в таблицы CSV или импортировать прямо в Сверчка
  - векторные поля, создать их, визуализировать данные
  - даже написать свой узел на питоне, используя Scripted node
  - делать свои дополнения к блендеру ('addons') раскладкой узлов и затем пользоваться ими в окне 3М вида при помощи панели инструментов Сверчка для 3М окна
  - доступ к API питона с узлом EvalKnieval
  - обновлять сверчка одной кнопкой
  - делать свою собственную нейронную сеть
  - и даже больше   


###Установка
Установите как обычный адон к блендеру.  
  
-  _Установка из пользовательских настроек_  
   Скачать Сверчка с github  
   User Preferences > Addons > install from file >   
   выбрать zip-архив > активировать Сверчка  
   При получении ошибки - закрыть блендер и снова активировать Сверчка.  
   Подтвердите выбор в файле startup.blend используя `Ctrl + U` и `Save User Settings`в меню Addons.  
  
-  _Ручная установка_  
   Скачать Сверчка с github  
   Киньте папку `sverchok-master` в `/scripts/addons`.  
   User Preferences > Addons > Community > (Ищите Сверчка) > Активируйте его  
   Подтвердите выбор в файле startup.blend используя `Ctrl + U` и `Save User Settings`в меню Addons.  

-  _Обновление Сверчка_   
   Используйте кнопку `Check for new version` в панели Сверчка в раскладке узлов (`N` чтобы вызвать)  
   Нажмите потом `F8` чтобы перезагрузить дополнения блендера. Должна поменяться версия  

###Известные ошибки установки
Не установилось? Список причин [тыц](/docs/installation.rst). Если вашей ошибки там нет - пишите письма.

###Контакты и разработчики
Домашняя страница: http://nikitron.cc.ua/sverchok_ru.html  
Разработчики: 
-  Недовизин Александр,  
-  Городецкий Никита,  
-  Инг Линус,  
-  Жименез Агустин, 
-  МакАрдле Деальга  

Email: sverchok-b3d@yandex.ru  
