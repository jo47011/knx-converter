# Adjust this file to your the settings

# knx1 openhab items file(s)
ITEMS_FILES = r"../items/knx1/myhome.items , \
    ../items/knx1/heating.items, \
    ../items/knx1/window.items, \
    ../items/knx1/xbmc.items"

# converted items files will be created in this directory
ITEM_RESULT_DIR = r"../items/"

# out file names
THINGS_FILE = r"../things/knx.things"

THINGS_UNUSED_FILE = r"unused.things"
ITEMS_UNUSED_FILE = r"unused.items"
ITEMS_UNUSED_CONTROLS_FILE =r"unused-control.items"

# files containing all information read
DEBUG_KNX = "knx.txt"
DEBUG_OH = "oh.txt"

# knxproj file (optional), unzip your knxproj file
# comment out this lines if you do not have/want to read ETS config
PROJECTFILE = r"./knxproj/P-02A7/0.xml"

### specify device types by vendor name (must be part of the *ProductRefId*)
# If unsure: run the script and look into the DEBUG_KNX file

# These are the primary addresses which will be used for read/write
ACTORS = "AKS, AKD, JAL, M-0051_H-hp, QUAD,"

# These will be added as -control items
CONTROLS = "TSM, -BE, ZN1IO, ZN1VI, LED,"

# These will ignored, uncomment to use
# IGNORE_DEVICES = "LED,"

# As of now all unknown GAs are switches
# FIXME: this could be improved!
UNUSED_TYPE = 'Switch'

# Suffix for generic control items
CONTROL_SUFFIX = '_Control'

# If defined, only these controls will be added to the item and things file.
# If undefined all possible controls will be created, this may be a good start
# but may flood your system.

# If defined, only these controls will be added to the items and things file.
# If undefined all possible controls will be created, this may be a good start
# but may flood your system.  You may use regex to match.
# WANTED_CONTROLS = "Switch_Szene, \
#     Licht_EG_Gaderobe, \
#     Switch_Beschattung, \
#     Rolladen_.*_Switch, \
#     Licht_ALL"

# If defined, ``autoupdate="true"`` will be added to all matching items.
# You may use regex to match.
# AUTOUPDATE_TRUE = "Alarm_"

# If defined, ``autoupdate="false"`` will be added to all matching items.
# You may use regex to match.
# AUTOUPDATE_FALSE = "Licht_ALL"


# values in <...> will be replaced. So do not change <...> values.
CHANNEL = ' channel="knx:device:bridge:<generic>:<name>" '

# IMPORTANT: adjust your IP (KNX and local) below
THING_HEADER = '''Bridge knx:ip:bridge [
    ipAddress="192.168.x.xxx",
    portNumber=3671,
    localIp="192.168.x.xxx",
    type="TUNNEL",
    readingPause=50,
    responseTimeout=10,
    readRetriesLimit=3,
    autoReconnectPeriod=1,
    localSourceAddr="0.0.0"
] {'''

# Generic device name
DEVICE_GENERIC = "generic"

DEVICE = '''
    Thing device <generic> [
        // device ID: <device_id>
        // <building>
        address="<address>",
        fetch=false,
        pingInterval=600,
        readInterval=0
    ] {'''

DEVICE_EMPTY = '''
    Thing device <generic> [
    ] {'''

CHANNELS = (
    "Switch",

    "Rollershutter",
    "Contact",
    "Number",
    "Dimmer",
    "String",
    "DateTime",
    "Color",  # supported since Dec 2018, so check your OH version if needed
)

# only one line supported, if you have more than one you need to implement it.
ETS_LINE_PREFIX = "1.1."

# ETS 4.x xml tags, may depend on ETS version
FIND_BUILDINGS = 'Buildings'   # Gebaeude
FIND_BUILDINGPART = 'BuildingPart'

# maybe use those for ETS 5.x
# FIND_BUILDINGS = 'Locations'   # Gebaeude
# FIND_BUILDINGPART = 'Space'

# ETS xml tags, usually no need to change those
FIND_TRADES = 'Trades'         # Gewerke
FIND_TRADEPART = 'Trade'
FIND_DEVICEREF = 'DeviceInstanceRef'
FIND_DEVICE = 'DeviceInstance'
FIND_COMREF = 'ComObjectInstanceRef'
FIND_CONNECTOR = 'Connectors'
FIND_SEND = 'Send'
FIND_RECEIVE = 'Receive'
FIND_GA = 'GroupAddress'
