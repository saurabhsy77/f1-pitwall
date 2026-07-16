import os
import fastf1
from fastf1 import utils
import matplotlib.pyplot as plt

os.makedirs('cache', exist_ok=True)
fastf1.Cache.enable_cache('cache')

session = fastf1.get_session(2024, 'Monaco', 'R')
session.load()

driver1 = 'LEC'
driver2 = 'PIA'

lap1 = session.laps.pick_drivers(driver1).pick_fastest()
lap2 = session.laps.pick_drivers(driver2).pick_fastest()

tel1 = lap1.get_car_data().add_distance()
tel2 = lap2.get_car_data().add_distance()

delta_time, ref_tel, compare_tel = utils.delta_time(lap1, lap2)

fig, axes = plt.subplots(4, 1, figsize=(12, 14), sharex=True)

axes[0].plot(tel1['Distance'], tel1['Speed'], color='red', label=driver1)
axes[0].plot(tel2['Distance'], tel2['Speed'], color='orange', label=driver2)
axes[0].set_ylabel('Speed (km/h)')
axes[0].legend()
axes[0].grid(True)

axes[1].plot(tel1['Distance'], tel1['Throttle'], color='red')
axes[1].plot(tel2['Distance'], tel2['Throttle'], color='orange')
axes[1].set_ylabel('Throttle (%)')
axes[1].grid(True)

axes[2].plot(tel1['Distance'], tel1['Brake'], color='red')
axes[2].plot(tel2['Distance'], tel2['Brake'], color='orange')
axes[2].set_ylabel('Brake')
axes[2].grid(True)

axes[3].plot(ref_tel['Distance'], delta_time, color='purple')
axes[3].axhline(0, color='gray', linestyle='--', linewidth=1)
axes[3].set_ylabel(f'Delta (s)\n<-{driver2} | {driver1}->')
axes[3].set_xlabel('Distance around lap (m)')
axes[3].grid(True)

fig.suptitle(f'{driver1} vs {driver2} — Monaco 2024 — Pit Wall View')
plt.tight_layout()
plt.savefig('stacked_dashboard.png')
print("Saved chart as stacked_dashboard.png")