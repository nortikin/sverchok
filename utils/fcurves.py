import bpy

def get_action(ad):
    if hasattr(ad, "action_slot") and ad.action_slot:
        return ad.action_slot
    elif hasattr(ad, "action"):
        return ad.action
    else:
        raise Exception("0021. Unknown property action for animation operations. ")

def get_fcurves(obj):
    """
    Blender 5.x:
    Возвращает список FCurve для obj из active Action/Slot.
    """

    ad = obj.animation_data
    if not ad or not ad.action:
        return []

    action = ad.action
    slot = get_action(ad)
    if action is None or slot is None:
        return []

    result = []

    if hasattr(action, "fcurves"):
        # Blender 3.0
        result.extend( [fcurve for fcurve in action.fcurves] )
    else:
        for layer in action.layers:
            for strip in layer.strips:
                # Нас интересует keyframe strip, который умеет вернуть channelbag для slot.
                bag = None

                # На разных сборках/переходных API имя может отличаться,
                # поэтому пробуем несколько вариантов.
                if hasattr(strip, "channelbag"):
                    try:
                        bag = strip.channelbag(slot, ensure=False)
                    except TypeError:
                        bag = strip.channelbag(slot)
                elif hasattr(strip, "channelbag_for_slot"):
                    bag = strip.channelbag_for_slot(slot)
                elif hasattr(strip, "channelbag_slot"):
                    bag = strip.channelbag_slot(slot)

                if bag and hasattr(bag, "fcurves"):
                    result.extend(list(bag.fcurves))
        pass

    return result

def remove_fcurves(obj, data_path):
    """
    Blender 5.x:
    Возвращает список FCurve для obj из active Action/Slot.
    """

    ad = obj.animation_data
    if not ad or not ad.action:
        return []

    action = ad.action
    slot = get_action(ad)
    if action is None or slot is None:
        return []

    result = []
    if hasattr(action, "fcurves"):
        # Blender 3.0
        for fcurve in list(action.fcurves):
            action.fcurves.remove(fcurve)
            #result.append(fcurve) # В Blender 3.0 нельзя обращаться к кривой после удаления. Возникает исключение An exception was raised: ReferenceError('StructRNA of type FCurve has been removed'). Если требуется прочитать свойства, то это нужно делать заранее.
    else:
        for layer in action.layers:
            for strip in layer.strips:
                # Нас интересует keyframe strip, который умеет вернуть channelbag для slot.
                bag = None

                # На разных сборках/переходных API имя может отличаться,
                # поэтому пробуем несколько вариантов.
                if hasattr(strip, "channelbag"):
                    try:
                        bag = strip.channelbag(slot, ensure=False)
                    except TypeError:
                        bag = strip.channelbag(slot)
                elif hasattr(strip, "channelbag_for_slot"):
                    bag = strip.channelbag_for_slot(slot)
                elif hasattr(strip, "channelbag_slot"):
                    bag = strip.channelbag_slot(slot)

                if bag and hasattr(bag, "fcurves"):
                    for fc_to_remove in bag.fcurves:
                        if fc_to_remove.data_path in data_path:
                            bag.fcurves.remove(fc_to_remove)
                            #result.append(fcurve)
                        pass
                    pass
            pass
        pass

    return result


def copy_fcurves(src_obj, target_obj, data_paths, only_clear=False):
    """
    Копирует FCurves с src_obj на target_obj только для указанных data_paths.
    """

    # --- Проверка источника
    if not src_obj.animation_data or not src_obj.animation_data.action:
        #print("[ERROR] Source has no animation")
        return

    src_fcurves = get_fcurves(src_obj,)

    # --- Проверка доступных путей
    available_paths = {fc.data_path for fc in src_fcurves}
    #print(f'available_paths={available_paths}')

    valid_paths = []
    invalid_paths = []
    no_animation_paths = []

    for path in data_paths:
        # --- 1. Проверяем, что параметр вообще существует у target
        try:
            target_obj.path_resolve(path)
        except Exception:
            #print(f"[WARN] Path not valid for target object: {path}")
            invalid_paths.append(path)
            continue

        # --- 2. Проверяем, есть ли анимация у source
        if path not in available_paths:
            #print(f"[INFO] No animation for path (skipped): {path}")
            no_animation_paths.append(path)
            continue

        # --- 3. Всё ок
        valid_paths.append(path)

    #print(f'invalid_paths={invalid_paths}')
    #print(f'no_animation_paths={no_animation_paths}')

    # --- если есть реально невалидные параметры — останавливаемся
    if invalid_paths:
        #print(f"[ERROR] Invalid paths: {invalid_paths}")
        return

    # --- Подготовка target
    if not target_obj.animation_data:
        target_obj.animation_data_create()

    if not target_obj.animation_data.action:
        target_obj.animation_data.action = bpy.data.actions.new(
            name=f"{target_obj.name}_Action"
        )

    dst_action = target_obj.animation_data.action
    dst_fcurves = remove_fcurves(target_obj, valid_paths,)

    ## --- Удаление старых FCurves (ВАЖНО: через list)
    # 
    # fcurves_to_remove = [
    #     fc for fc in list(dst_fcurves)
    #     if fc.data_path in valid_paths
    # ]

    # #print(f'Количество fcurves_to_remove: {len(fcurves_to_remove)}, {fcurves_to_remove}')

    # for fc in fcurves_to_remove:
    #     dst_fcurves.remove(fc)

    if only_clear==True:
        return

    # --- Копирование
    if hasattr(dst_action, "fcurve_ensure_for_datablock")==False:
        # Blender 3.0
        for fc in src_fcurves:
            if fc.data_path not in valid_paths:
                continue

            # В 3.0 нет fcurve_ensure_for_datablock
            new_fc = dst_action.fcurves.find(fc.data_path, index=fc.array_index)

            if new_fc is None:
                new_fc = dst_action.fcurves.new(
                    data_path=fc.data_path,
                    index=fc.array_index
                )

            # очищаем существующие ключи (если были)
            kps = new_fc.keyframe_points
            if hasattr(kps, "clear"):
                kps.clear()
            else:
                for kp in list(kps):
                    kps.remove(kp)

            new_fc.keyframe_points.add(len(fc.keyframe_points))

            for i, kp in enumerate(fc.keyframe_points):
                new_kp = new_fc.keyframe_points[i]

                new_kp.co = kp.co.copy()
                new_kp.handle_left = kp.handle_left.copy()
                new_kp.handle_right = kp.handle_right.copy()

                new_kp.interpolation = kp.interpolation
                new_kp.handle_left_type = kp.handle_left_type
                new_kp.handle_right_type = kp.handle_right_type

            # В 3.0 лучше обновлять так:
            new_fc.keyframe_points.update()
        pass
    else:
        for fc in src_fcurves:
            if fc.data_path not in valid_paths:
                continue

            new_fc = dst_action.fcurve_ensure_for_datablock(
                target_obj,
                data_path=fc.data_path,
                index=fc.array_index
            )

            # очищаем существующие ключи (если были)
            new_fc.keyframe_points.clear()

            new_fc.keyframe_points.add(len(fc.keyframe_points))

            for i, kp in enumerate(fc.keyframe_points):
                new_kp = new_fc.keyframe_points[i]

                new_kp.co = kp.co.copy()
                new_kp.handle_left = kp.handle_left.copy()
                new_kp.handle_right = kp.handle_right.copy()

                new_kp.interpolation = kp.interpolation
                new_kp.handle_left_type = kp.handle_left_type
                new_kp.handle_right_type = kp.handle_right_type

            new_fc.update()
            pass
        pass

    return