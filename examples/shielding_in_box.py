import os
import numpy as np
import matplotlib.pyplot as plt

import ema


# User settings
basepath = 'shielding_in_box/1'
probe1_name = 'long_box_probe.dat'
probe2_name = 'short_box_probe.dat'
ref_name = 'Plane_Wave.dat'
se_name = 'se_stats.dat'


# Construct paths
probe1_path = os.path.join(basepath, probe1_name)
probe2_path = os.path.join(basepath, probe2_name)
ref_path = os.path.join(basepath, ref_name)
se_path = os.path.join(basepath, se_name)


# Calculate shielding if se_stats.dat does not yet exist
if not os.path.exists(se_path):
	# Load electric field data from two box probes
	t, e = ema.load_box_probes(probe1_path, probe2_path)

	# Load reference waveform (plane wave source file)
	tr, er = ema.load_data(ref_path)

	# Pad and resample reference waveform to match box probes
	tr, er = ema.pad_to_time(tr, er, t[-1])
	tr, er = ema.resample(tr, er, t)

	# Calculate shielding effectiveness and statistics
	f, se = ema.shielding_from_timeseries(t, e, er)
	se_min, se_mean, se_max = ema.stats(se, axis=0)

	# Save stats to file for future use
	data = np.array([f, se_min, se_mean, se_max]).T
	np.savetxt(se_path, data)

	print('Calculated shielding and saved to', se_path)

# Import se_stats.dat if it already exists
else:
	f, se_min, se_mean, se_max = ema.load_data(se_path)
	print('Found shielding statistics at', se_path)


# Create plot of shielding statistics
fig, ax = plt.subplots()

ax.fill_between(f, se_min, se_max, color=(.5, .5, .5, .5), label='Range')
ax.plot(f, se_mean, label='Mean')

ax.set_xscale('log')
ax.set_xlabel('Frequency (Hz)')
ax.set_ylabel('Shielding effectiveness (dB)')
ax.legend()

fig.suptitle('Shielding statistics calculated from two box probes')
fig.show()