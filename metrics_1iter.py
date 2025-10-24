# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import repeat as rp


def format_number(x):
    return f"{x:.1f}".replace('.', ',')

user = rp.User(token = '')
app = rp.Application(user)
project =

"""
- SW время смены (в сек)
- P_RES_1 мощность ВИЭ 0-SW
- P_RES_2 мощность ВИЭ SW-...
- P_BESS_1 мощность СНЭ 0-SW
- P_BESS_2 мощность СНЭ SW-...
- R1 сопротивление 0-SW
- R2 сопротивление SW-...
"""

sw = 5
#p_res_1 = 5000
#p_res_2 = -20000
#p_bess_1 = 20000
#p_bess_2 = 10000
#r1 = 3.2
#r2 = 2.4
p_bess_list = [12, 7.5, 3, 4.5, -18, -7.5, -1.5, 9, 19.5, 20, 20, 20,
              11.5, 0, 0, 0, 0, 0, 0, -20, -20, -20, -20, -20]
p_res_list = [18, 16.5, 15, 13.5, 12, 12, 13.5, 15, 16.5, 18, 19.5, 21,
              22.5, 24, 25.5, 27, 28.5, 30, 28.5, 27, 25.5, 24, 22.5, 21]
p_list = [60, 54, 48, 48, 54, 60, 72, 84, 96, 102, 108, 114,
              120, 114, 108, 102, 108, 120, 114, 96, 84, 72, 66, 60]
scale = 1000

all_metrics = []

h_iter = 19
#for h_iter in range(24):

p_res_1 = p_res_list[h_iter] * scale
p_res_2 = p_res_list[(h_iter + 1) % 24] * scale
p_bess_1 = p_bess_list[h_iter] * scale
p_bess_2 = p_bess_list[(h_iter + 1) % 24] * scale
r1 = (380 ** 2) / (p_list[h_iter] * scale)
r2 = (380 ** 2) / (p_list[(h_iter + 1) % 24] * scale)
var_data = {'SW': sw, 'P_RES_1': p_res_1, 'P_RES_2': p_res_2,
            'P_BESS_1': p_bess_1, 'P_BESS_2': p_bess_2, 'R1': r1, 'R2': r2}
t_interval = rp.TimeInterval(start = sw * 1000 + 1, end = 10000)
csv_t_interval = rp.TimeInterval(start= 0, end=10000)
model = app.get_exploration_model(project)
variables = pd.Series(var_data, dtype = float)

print("Запуск модели")
with model as md:
    md.run(variables)
    p_out_load = md.get_results('P_OUT_LOAD', t_interval)
    u_out_sg = md.get_results('U_OUT_SG', t_interval)
    csv_p_out_load = md.get_results('P_OUT_LOAD', csv_t_interval)
    csv_u_out_sg = md.get_results('U_OUT_SG', csv_t_interval)

next_hour = (h_iter + 1) % 24

csv_filename_p = f"NSU_P_OUT_LOAD_h{h_iter}-h{next_hour}.csv"
df_p = pd.DataFrame({
    'Время, с': (csv_p_out_load.index.values / scale).round(3),
    'P_OUT_LOAD': csv_p_out_load.values.round(5)
})
df_p['Время, с'] = df_p['Время, с'].map(lambda x: f"{x:.3f}".replace('.', ','))
df_p['P_OUT_LOAD'] = df_p['P_OUT_LOAD'].map(lambda x: f"{x:.3f}".replace('.', ','))
df_p.to_csv(csv_filename_p, sep=';', index=False, encoding='utf-8')

csv_filename_u = f"NSU_U_OUT_SG_h{h_iter}-h{next_hour}.csv"
df_u = pd.DataFrame({
    'Время, с': (csv_u_out_sg.index.values / scale).round(3),
    'U_OUT_SG': csv_u_out_sg.values.round(5)
})
df_u['Время, с'] = df_u['Время, с'].map(lambda x: f"{x:.3f}".replace('.', ','))
df_u['U_OUT_SG'] = df_u['U_OUT_SG'].map(lambda x: f"{x:.5f}".replace('.', ','))
df_u.to_csv(csv_filename_u, sep=';', index=False, encoding='utf-8')

print(f"Сохранено: {csv_filename_p}, {csv_filename_u}")

steady_stay_power = None
u_nominal = None
current_tolerance = 1e-9
max_tolerance_increases = 15
n = len(p_out_load)

print(p_out_load)
print(u_out_sg)

for tolerance_increase in range(max_tolerance_increases + 1):
    for i in range(1, n):
        if abs(u_out_sg.iloc[i] - u_out_sg.iloc[i - 1]) <= current_tolerance:
            u_nominal = u_out_sg.iloc[i]
            break
        if u_nominal is not None:
            break
        current_tolerance *= 10
current_tolerance = 1e-9

for tolerance_increase in range(max_tolerance_increases + 1):
    for i in range(1, n):
        if abs(p_out_load.iloc[i] - p_out_load.iloc[i - 1]) <= current_tolerance:
            steady_stay_power = p_out_load.iloc[i]
            break
        if steady_stay_power is not None:
            break
        current_tolerance *= 10

max_difference = 0
sum_pi_ps = 0
sum_ui_un = 0


for i in range(n):
    difference = abs(p_out_load.iloc[i] - steady_stay_power)
    if max_difference <= difference:
        max_difference = difference
    sum_pi_ps += difference ** 2
    sum_ui_un += abs(u_out_sg.iloc[i] - u_nominal) ** 2

first_metric = max_difference / steady_stay_power * 100
second_metric = np.sqrt(sum_pi_ps / n)
third_metric = np.sqrt(sum_ui_un / n)

print(f"Итерация {h_iter}: Первая метрика: {first_metric:.2f}%")
print(f"Итерация {h_iter}: Вторая метрика: {second_metric:.2f} Вт")
print(f"Итерация {h_iter}: Третья метрика: {third_metric:.2f} В")

"""
metrics = {
    'hour_range': f"h{h_iter}-h{next_hour}",
    'first_metric': first_metric,
    'second_metric': second_metric,
    'third_metric': third_metric,
    'steady_stay_power': steady_stay_power,
    'u_nominal': u_nominal
}
all_metrics.append(metrics)

print("\n" + "="*60)
print("ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ ПО ВСЕМ ИТЕРАЦИЯМ:")
print("="*60)

for metrics in all_metrics:
    print(f"{metrics['hour_range']}: "
          f"М1={metrics['first_metric']:.2f}%, "
          f"М2={metrics['second_metric']:.2f}Вт, "
          f"М3={metrics['third_metric']:.2f}В")

print("\n" + "="*80)
print("ТАБЛИЦА РЕЗУЛЬТАТОВ:")
print("="*80)
print("Диапазон часов  |  Метрика 1 (%)  |  Метрика 2 (Вт)  |  Метрика 3 (В)")
print("-" * 80)

for metrics in all_metrics:
    print(f"{metrics['hour_range']:^15} | {metrics['first_metric']:^15.2f} | "
          f"{metrics['second_metric']:^15.2f} | {metrics['third_metric']:^13.2f}")
"""