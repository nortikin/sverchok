Rigid Body
==========

.. image:: https://github.com/user-attachments/assets/b37e081b-4552-476a-a195-cf9a05a880d3
  :target: https://github.com/user-attachments/assets/b37e081b-4552-476a-a195-cf9a05a880d3


.. image:: https://github.com/user-attachments/assets/74b2f61f-1da0-4ce9-b17d-9918d2185fd6
  :target: https://github.com/user-attachments/assets/74b2f61f-1da0-4ce9-b17d-9918d2185fd6

Description
-----------

This node does only copy parameters from several sources of data. It can copy animations.

Этот нод предназначен для работы с системой Rigid Body в Blender на уровне объектов, но
в процедурном формате Sverchok. Он позволяет назначать, настраивать и синхронизировать
параметры физики для набора объектов без необходимости вручную заходить в настройки каждого
из объектов. В качестве источника параметров может использоваться один или несколько "шаблонных"
объектов, с которого считываются все свойства Rigid Body (включая анимируемые), после чего
они применяются к целевым объектам. Это упрощает массовое управление физикой и обеспечивает
единообразие поведения даже при динамическом изменении сцены нодами Сверчка.

Original templates objects do not show here. It willl be explained later.

Principal map of work with Rigid Body Node:

    .. image:: https://github.com/user-attachments/assets/a838c1c5-e236-4328-abaf-79de8d8e796d
      :target: https://github.com/user-attachments/assets/a838c1c5-e236-4328-abaf-79de8d8e796d

After assign parameters (ex. mass) you have to disable Sverchok scene update and play Blender animation:

    .. raw:: html

        <video width="700" controls>
        <source src="https://github.com/user-attachments/assets/bd3ac331-3f19-4f0d-82aa-3333d124319c" type="video/mp4">
        Your browser does not support the video tag.
        </video>