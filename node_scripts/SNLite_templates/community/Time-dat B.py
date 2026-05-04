"""
in dummy s
in mode s d=1 n=1
in target_tz s d=3 n=1
out time_out s
out date_out s
out rot_h s
out rot_m s
out rot_s s
# @il_de_signer
"""

import time
import math
from datetime import datetime, timedelta

# 1. Распаковка
def unwrap(data, default=0):
    if isinstance(data, (list, tuple)):
        return unwrap(data[0], default) if len(data) > 0 else default
    return data

mode_val = unwrap(mode, 1)
tz_val = unwrap(target_tz, 3)

# 2. Получаем время UTC
timestamp = time.time()
utc_now = datetime.utcfromtimestamp(timestamp)

# 3. Добавляем часовой пояс
t_now = utc_now + timedelta(hours=tz_val)

# 4. Расчет дробного времени (часы)
t_val = (t_now.hour + 
         (t_now.minute / 60.0) + 
         (t_now.second / 3600.0) + 
         (t_now.microsecond / 3600000000.0))

# 5. Углы (Радианы)
tau = -2 * math.pi
offset = math.pi / 2 # Чтобы 00:00 смотрело ВВЕРХ

rot_h = [[ ((t_val % 12) * (tau / 12)) + offset ]]
rot_m = [[ ((t_val % 1) * tau) + offset ]]
rot_s = [[ (((t_val * 60) % 1) * tau) + offset ]]

# 6. Выходы
if mode_val >= 0.5:
    time_out = [[round(t_val, 7)]]
    date_out = [[float(t_now.timetuple().tm_yday)]]
else:
    time_out = [[t_now.strftime("%H:%M:%S")]]
    date_out = [[t_now.strftime("%d-%m-%Y")]] 