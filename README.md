# ets2openHAB 2.x conversion script

This is a repository of a experimental script to help moving from openHAB 1.x knx1 binding to the new openHAB 2.x knx
binding.  It converts existing knx1 item files and generates a knx.thing file.  Optionally it can also read the
`knxproj` file.

**Note:** This script only works if your are using config files.  It will not work if you use the UI for creating things
and items.  Furthermore it will most likely not work out of the box for everybody but may be a good start for whoever
wants to automate that process.

It has been tested with **ETS 4** project file and runs on a Mac thus it should work on any Unix system.  Not sure about
Windows.

## Prerequisites

- You do need python3.
  I'm using Python 3.7.1.

## Installation

1. Copy the bundle into a new directory.
2. Create a new sub-directory (e.g. *knxporj*) and enter it.
3. Export your `knxproj` file and unzip it into the sub-directory.
   Yes your `knxproj` projext file is a zip file.
4. Search for a file  0.xml.
   In my case it is in the directory `knxproj/P-02A7/0.xml`.
5. Read and adjust the **config.py** file.
6. To run it call: `./convert-knx.py`

Steps 2-4 are optional.  You may also use the script w/o an ETS project file.  Then all your items will be assigned to a
generic device in the thing file and no controls are added.

Due to a general architecture change of the knx binding you only get events in OpenHAB if the item in KNX changes.
Furthermore you will not get any events from wall mounted switches or alike.  To overcome this problem you need so
called control items.  These will be created by this script automatically.  See below and the example folder for
details.

If you have an OH Item (group address) with exactly one *actor* assigned the correct device ID will be used in the thing
file and items file.  If there is more than one actor in ETS assigned (e.g. ALL_LIGHTS_SWITCH) it will be added to the
generic device.

If one or more *control*, like a wall mounted switch) is assigned in the ETS a *control* item is created in the generic
section and will be added to your items file directly below the main item.

All other items read from your ETS file which are not used in your items files will be written to an alternative file.
These can be used for copy & paste if you need to add items at a later stage.  Adjust **config.py** for your preferred
names:

'''python
THINGS_UNUSED_FILE = "unused.things"
ITEMS_UNUSED_FILE = "unused.items"
ITEMS_UNUSED_CONTROLS_FILE ="unused-control.items"
'''

You definitly need to adjust the following settings that the script can determine what are your actors and what are your
controls.  This may be improved in future by extracting more information from the *knxproj* files.  See *TODOS.md*.

'''python
ACTORS = "AKS, AKD, JAL, M-0051_H-hp, QUAD, 2000-1-O000A_P-2174, "
CONTROLS = "TSM, -BE, ZN1IO, ZN1VI, 2000-1-O000A_P-1118, O000A_P-3180, 2000-0_P-2343, LED,"
'''

Depending on your setup the following message may be ok if you have a *read-only* devive or a dummy group address.  Or
it may mean that you need to adjust the above settings.

> INFO: No Actor found for: 4/0/24   	using: generic	BWM_Aussen_Garage

To find out the names of your ETS components you can look into the files containing debug information about all your knx
and openhab items.

'''python
# files containing all information read
DEBUG_KNX = "knx.txt"
DEBUG_OH = "oh.txt"
'''

If you have any issue feel free to contact me or open an issue in the repository.
