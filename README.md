# ets2openHAB 2.x conversion script

This is a repository of a experimental script to help moving from openHAB 1.x knx1 binding to the new openHAB 2.x knx
binding.  It converts existing knx1 item files and generates a knx.thing file.  Optionally it can also read the
`knxproj` file(s).

**Note:** This script only works if your are using config files.  It will not work if you use the UI for creating things
and items.  Furthermore it will most likely not work out of the box for everybody but may be a good start for whoever
wants to automate that process.

It has been tested with an **ETS 4** and **ETS 5** project file and runs on a Mac thus it should work
on any Unix system.  Also tested on Windows 7.


## Prerequisites

- You do need python3.7 or above.

## Installation

1. Make a backup.
2. Copy the bundle into a new directory.
3. Create a new sub-directory (e.g. `knxproj`) and enter it.
4. Export your `knxproj` file and unzip it into the sub-directory.
   Yes your `knxproj` project file is a zip file.
5. Search for a file  0.xml.
   In my case it is in the directory `knxproj/P-02A7/0.xml`.
6. Read and adjust the **config.py** file.
7. To run it call: `./convert-knx.py`

Steps 3-5 are optional.  You may also use the script w/o an ETS project file.  Then all your items will be assigned to a
generic device in the thing file and no controls are added.

Due to a general architecture change of the knx binding you only get events in OpenHAB if the item in KNX changes.
Furthermore you will not get any events from wall mounted switches or alike.  To overcome this problem you need so
called control items.  These will be created by this script automatically.  See below for details.

If you have an OH Item (group address) with exactly one *actor* assigned in your ETS the correct device ID will be used
in the thing file and items file.  If there is more than one actor in ETS assigned (e.g. ALL_LIGHTS_SWITCH) it will be
added to the generic device.

If one or more *control* (e.g. a wall mounted switch) is assigned in the ETS a *control* item is created in the generic
section and will be added to your items file directly below the main item.

All other items read from your ETS file which are not used in your items files will be written to an alternative file.
These can be used for copy & paste if you need to add items at a later stage.  Adjust **config.py** for your preferred
names:

```python
# knx1 openHAB item file(s)
ITEMS_FILES = "../items/knx1/myhome.items , \
    ../items/knx1/heating.items, \
    ../items/knx1/window.items, \
    ../items/knx1/xbmc.items"

# converted item files will be created in this directory
ITEM_RESULT_DIR = "../items/"

# out file names
THINGS_FILE = "../things/knx.things"

THINGS_UNUSED_FILE = "unused.things"
ITEMS_UNUSED_FILE = "unused.items"
ITEMS_UNUSED_CONTROLS_FILE ="unused-control.items"
```

You definitely need to adjust the following settings that the script can determine what are your actors and what are your
controls.  This may be improved in future by extracting more information from the *knxproj* files.  See *TODOS.md*.

```python
# These are the primary addresses which will be used for read/write
ACTORS = "AKS, AKD, JAL, M-0051_H-hp, QUAD,"

# These will be added as -control items
CONTROLS = "TSM, -BE, ZN1IO, ZN1VI, LED,"

# These will ignored, uncomment to use
# IGNORE_DEVICES = "LED,"
```

Depending on your setup the following message may be ok if you have a *read-only* device or a dummy group address.  Or
it may mean that you need to adjust the above settings.

> INFO: No Actor found for: 4/0/24   	using: generic	BWM_Aussen_Garage

To find the names of your ETS components you can look into the files containing debug information about all your knx
and openHAB items after a 1st run of this script.

```python
# files containing all information read
DEBUG_KNX = "knx.txt"
DEBUG_OH = "oh.txt"
```

### NEW: 20190302

Since the script produces a lot of control items which I don't really need I added a new feature.  You can now set the
following variable to prevent the creation of the unused control items.  They will still be created in the
*ITEMS_UNUSED_CONTROLS_FILE* so you can copy & paste them later once you need them.

```python
# If defined, only these controls will be added to the items and things file.
# If undefined all possible controls will be created, this may be a good start
# but may flood your system.  You may use regex to match.
WANTED_CONTROLS = "Switch_Szene, \
   Licht_EG_Gaderobe, \
   Switch_Beschattung, \
   Rolladen_.*_Switch, \
   Licht_ALL"
```

### NEW: 20190314

*WANTED_CONTROLS* (see above) now support regular expressions.

New autoupdate feature: if below variables are defined the *autoupdate="true"* or *false* is
added to the item in the items file:

```python
# If defined, ``autoupdate="true"`` will be added to all matching items.
# You may use regex to match.
AUTOUPDATE_TRUE = "Alarm_, \
   Rolladen_.*_Switch"

# If defined, ``autoupdate="false"`` will be added to all matching items.
# You may use regex to match.
AUTOUPDATE_FALSE = "Licht_ALL"
```


### NEW:  20190325

Now creating configured output directories if non existent.

### NEW:  20190327

Tested and adjusted for Windows 7.  Make sure you add an **r** in front of your config paths, especially if it is a
multi-line string concatenated with a backslash. e.g.:

```python
ITEMS_FILES = r"../items/knx1/myhome.items , \
    ../items/knx1/heating.items, \
    ../items/knx1/window.items, \
    ../items/knx1/xbmc.items"
```

Added encoding option, fixes German *Umlaut* problems and others.  Add this to your config file if it is
not there yet:

```python
# file encodings
IN_ENCODING = r"utf8"
OUT_ENCODING = r"utf8"
```

### NEW:  20191012

Now supporting multiple KNX project files.  Thanks to @rmayr

Also added option `-c` to use alternative config file.

--------

 If you have any issue feel free to contact me or open an issue in the repository.

Have fun...
