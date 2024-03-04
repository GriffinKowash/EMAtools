import os

from ema import Emin

# User settings
emin_name = 'planewave_example.emin'
basedir = 'planewave_orientation'
folders = [str(i) for i in range(1, 13)]

# Create paths
paths = [os.path.join(basedir, folder, emin_name) for folder in folders]

# Define sources
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

# Loop over Emin files and change source definitions
for i, path in enumerate(paths):
	# Create list of lines to add
	new_lines = [sources[i], comments[i]]

	# Create Emin object
	emin = Emin(path)

	# Find plane wave header and step forward five lines
	index = emin.find('!PLANE WAVE SOURCE') + 5

	# Replace line with new text and save
	emin.replace(index, new_lines)
	emin.save()

	print('Updated Emin file at', path)