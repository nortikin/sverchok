Rigid Body
==========

.. image:: https://github.com/user-attachments/assets/b8768bc2-8b19-40e9-a9ce-b4f5c87d9c83
  :target: https://github.com/user-attachments/assets/b8768bc2-8b19-40e9-a9ce-b4f5c87d9c83


.. image:: https://github.com/user-attachments/assets/1b59ca91-3eb6-41ec-ad7c-61052a0e0be8
  :target: https://github.com/user-attachments/assets/1b59ca91-3eb6-41ec-ad7c-61052a0e0be8

Description
-----------

This node does only copy parameters from several sources of data. It can copy animations.

Этот нод предназначен для параметрического управления свойствами Rigid Body на объектах в Blender.
Значения могут браться как из дополнительных объектов с уже настроенными параметрами Rigid Body
(шаблонами), из настроек самого нода, из подключенных к ноду сокетов. Нод не требует установки всех
параметров Rigid Body, что позволяет настраивать некоторые параметры индивидуально для некоторых
отдельных объектов с Rigid Body. При установке значений учитываются признаки копирования,
которые устанавливаются в соответствующих диалоговых окнах нода. Нод может копировать анимацию
параметров (пока без учёта модификаторов анимации), может стирать анимацию параметров.

Примечание:

- Этот нод не имеет собственных функций по работе с Rigid Body, а только копирует
  параметры в заданные объекты!

- Если параметры имеют анимацию (ключи анимации), то установка значений в эти параметры не выполняется (независимо от
  того, как параметры анимации были скопированы - с помощью нода или установлены вручную)

Original templates objects do not show here. It will be explained later.

Principal map of work with Rigid Body Node:

    .. image:: https://github.com/user-attachments/assets/a838c1c5-e236-4328-abaf-79de8d8e796d
      :target: https://github.com/user-attachments/assets/a838c1c5-e236-4328-abaf-79de8d8e796d

After assign parameters (ex. mass) you have to disable Sverchok scene update and play Blender animation:

    .. raw:: html

        <video width="700" controls>
        <source src="https://github.com/user-attachments/assets/bd3ac331-3f19-4f0d-82aa-3333d124319c" type="video/mp4">
        Your browser does not support the video tag.
        </video>

Описание интерфейса
-------------------

Несмотря на большое количество параметров 90% интерфейса нода повторяет набор параметров, которые существуют в настройках
Rigid Body:

  .. image:: https://github.com/user-attachments/assets/112506ed-61b0-423e-a6dd-abf6b83302b7
    :target: https://github.com/user-attachments/assets/112506ed-61b0-423e-a6dd-abf6b83302b7

Есть небольшое отличие - нода в Sverchok всегда отображает все параметры одновременно. Интерфейс Blender Rigid Body,
в зависимости от выбранных настроек, может отображать не все параметры одновременно. Кроме того, интерфейс ноды
Sverchok не отображает параметры анимации (в интерфейсе Blender анимированные параметры отображаются жёлтым цветом
и ромбом справа от параметра).

  .. image:: https://github.com/user-attachments/assets/6721febe-bbef-46a4-a917-d53a1fe311ad
    :target: https://github.com/user-attachments/assets/6721febe-bbef-46a4-a917-d53a1fe311ad

Другие части интерфейса выполняют вспомогательные функции настроек, определяющие как ноду следует поступать с
параметрами, которые следует копировать в объекты.

Копирование анимации
--------------------

Копирование анимации является командой. Перед выполнением копирования анимации в исходном объекте следует настроить
ключевые анимационные кадры у соответствующих параметров, например, параметр Animated часто используется в Rigid Body.

  .. image:: https://github.com/user-attachments/assets/22e6c550-6f98-4674-a8a3-88ecbacacf8d
    :target: https://github.com/user-attachments/assets/22e6c550-6f98-4674-a8a3-88ecbacacf8d

Требуется скопировать анимационные параметры во все объекты, обведённые рамкой:

  .. image:: https://github.com/user-attachments/assets/90ba9409-4d72-4edf-82ac-96be8ec132fb
    :target: https://github.com/user-attachments/assets/90ba9409-4d72-4edf-82ac-96be8ec132fb

Делается это по следующей схеме с помощью вызова диалогового окна "Copy Animatioon":

  .. image:: https://github.com/user-attachments/assets/7e74dc7d-0b7c-4be8-b2d9-6e8511f7e8c0
    :target: https://github.com/user-attachments/assets/7e74dc7d-0b7c-4be8-b2d9-6e8511f7e8c0

Примечание: по умолчанию копируются все параметры, но можно выключить параметры, которые не требуется копировать, например,
если требуется скопировать только один параметр, например, только Animation, то можно выключить всё, кроме этого параметра:

  .. image:: https://github.com/user-attachments/assets/a2c0799d-e97c-474e-b8ef-6e7d1cd346de
    :target: https://github.com/user-attachments/assets/a2c0799d-e97c-474e-b8ef-6e7d1cd346de

