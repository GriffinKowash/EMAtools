# Examples

This document provides context and discussion for the example scripts located in the "examples" directory of EMAtools. For greatest clarity, reference the appropriate scripts while reading, as the discussions skip some details for the sake of brevity. To access any additional files needed to execute the example scripts, see K:/Griffin/EMAtools/examples.


## Table of Contents
- **[Shielding effectiveness of an irregular box](#shielding-effectiveness-of-an-irregular-box)**
- **[Bulk modification of plane wave sources](#bulk-modification-of-plane-wave-sources)**

## Shielding effectiveness of an irregular box

The following example is based on a real customer use case that motivated much of the functionality in this package.

  The problem involves measuring the shielding effectiveness of an irregularly-shaped conductive enclosure with an EMI gasket. A similar, simplified model is shown in Figure 1 below.

<p align="center"><img src="images/shielding_in_box_1.png" /></p>
<p align="center">Figure 1: Shielding enclosure problem setup</p>
<br>

To characterize the shielding throughout the enclosure, two box field probes were added, as shown in Figure 2. The first is oriented horizontally along the longest wall of the enclosure, while the second fills the region protruding from the side.

<p align="center"><img src="images/shielding_in_box_2.png" /></p>
<p align="center">Figure 2: Electric field box probes filling enclosure volume</p>
<br>

EMAtools provides a straightforward workflow for analyzing the simulation results. First, the data from the two box probes is loaded, as well as the plane wave source to be used as the reference waveform:

```
t, e = ema.load_box_probes(probe1_path, probe2_path)
tr, er = ema.load_data(ref_path)
```

In this example, the source waveform has a different time step and end time than the probe results. The `pad_to_time` and `resample` functions from the `signal` module are used to extend and match it to the time steps of the box probes:

```
tr, er = ema.pad_to_time(tr, er, t[-1])
tr, er = ema.resample(tr, er, t)
```

Now, the `shielding_from_timeseries` function from the `emc` module is called to calculate the shielding effectiveness:

```
f, se = ema.shielding_from_timeseries(t, e, er)
```

Finally, to obtain the minimum, mean, and maximum shielding through the entire enclosure, the `stats` function from the `signal` module is called. Note that `axis=0` is specified in order to calculate the statistics across all sample points.

```
se_min, se_mean, se_max = ema.stats(se, axis=0)
```

Plotting these results against frequency in Figure 3, we can see how shielding effectiveness varies throughout the enclosure:

<p align="center"><img src="images/shielding_in_box_3.png" /></p>
<p align="center">Figure 3: Shielding statistics over all sample points</p>
<br>


## Bulk modification of plane wave sources

Another use case encountered during a customer project involved modifying large numbers of Emin files. For this task, an electronics enclosure was to be simulated with 12 different plane wave orientations and polarizations in order to assess the shielding effectiveness under different conditions. Instead of manually modifying the 12 source definitions each time a new set of simulations was run, EMAtools was used to automate the process, making large batch simulations easy to prepare.
  
  The original plane wave definition is shown below:
  
```
74      | !PLANE WAVE SOURCE
75      | Plane_Wave.dat
76      | locked
77      | 4    4    4
78      | 34   28   16
79      | 0.0000000000E+000    0.0000000000E+000    1.5707963268E+000    0.0000000000E+000
```
  
  The four values on line 79 specify the orientation and polarization of the plane wave. We can create a list of strings in the same format for each of the desired plane wave configurations, along with comments labeling the orientation and polarization for future reference. These strings are defined manually here, but could be generated programmatically instead.

```
sources = ['0.0000000000E+000    0.0000000000E+000    1.5707963268E+000    0.0000000000E+000',
	   '0.0000000000E+000    0.0000000000E+000    1.5707963268E+000    1.5707963268E+000',
	   '1.5707963268E+000    3.1415926536E+000    0.0000000000E+000    1.5707963268E+000',
	   '1.5707963268E+000    3.1415926536E+000    1.5707963268E+000    1.5707963268E+000',
	   '3.1415926536E+000    0.0000000000E+000    1.5707963268E+000    1.5707963268E+000',
	   '3.1415926536E+000    0.0000000000E+000    1.5707963268E+000    0.0000000000E+000',
	   '1.5707963268E+000    0.0000000000E+000    0.0000000000E+000    3.1415926536E+000',
	   '1.5707963268E+000    0.0000000000E+000    1.5707963268E+000    1.5707963268E+000',
	   '1.5707963268E+000    4.7123889804E+000    0.0000000000E+000    3.1415926536E+000',
	   '1.5707963268E+000    4.7123889804E+000    1.5707963268E+000    0.0000000000E+000',
	   '1.5707963268E+000    1.5707963268E+000    1.5707963268E+000    0.0000000000E+000',
	   '1.5707963268E+000    1.5707963268E+000    0.0000000000E+000    0.0000000000E+000']

comments = ['* k: +Z | E: +X',
	    '* k: +Z | E: +Y',
	    '* k: -X | E: +Z',
	    '* k: -X | E: +Y',
	    '* k: -Z | E: +Y',
	    '* k: -Z | E: +X',
	    '* k: +X | E: +Z',
	    '* k: +X | E: +Y',
	    '* k: -Y | E: +Z',
	    '* k: -Y | E: +X',
	    '* k: +Y | E: +X',
	    '* k: +Y | E: +Z']
```

Iterating over all of the target Emin files using `for i, path in enumerate(paths)`, load each Emin file:

```
from ema import Emin
emin = Emin(path)
```

Next, create a list of the lines to be inserted:

```
new_lines = [sources[i], comments[i]]
```

Find the index of the plane wave definition header and move ahead by five lines, where the orientation and polarization angles are specified:

```
index = emin.find('!PLANE WAVE SOURCE') + 5
```

Replace the existing definition with the new lines:

```
emin.replace(index, new_lines)
```

Finally, overwrite the Emin file with the modified contents:

```
emin.save()
```

Opening one of the modified Emin files shows that the definition has been updated as desired:

```
74      | !PLANE WAVE SOURCE
75      | Plane_Wave.dat
76      | locked
77      | 4    4    4
78      | 34   28   16
79      | 1.5707963268E+000    3.1415926536E+000    1.5707963268E+000    1.5707963268E+000
80      | * k: -X | E: +Y
```