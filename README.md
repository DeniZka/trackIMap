trackIMap
=========

trackIMap compare your gpx track file points with images by timestamps
When it find two nearest timestamps in gpx, it fill images with calculated coordinates
to bee shure that's all OK look results with pinIMap
https://github.com/DeniZka/pinIMap

Usage
=========
simply add alias to uour .bashrc
alias trackim="~/trackIMap/trackimap.py"

Now try:
~trackim ../activity.gpx +4
this will take gpx from upper folder, shift it timestamps to 4 hour and fill all images in current folder and above with calculated coordinates, of cource only if them will be compared
