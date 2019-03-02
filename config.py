# Adjust this file to your the settings

# knx1 openhab items file(s)
ITEMS_FILES = "../items/knx1/myhome.items , \
    ../items/knx1/heating.items, \
    ../items/knx1/window.items, \
    ../items/knx1/xbmc.items"

# converted items files will be created in this directory
ITEM_RESULT_DIR = "../items/"

# out file names
THINGS_FILE = "../things/knx.things"

THINGS_UNUSED_FILE = "unused.things"
ITEMS_UNUSED_FILE = "unused.items"
ITEMS_UNUSED_CONTROLS_FILE ="unused-control.items"

# files containing all information read
DEBUG_KNX = "knx.txt"
DEBUG_OH = "oh.txt"

# knxproj file (optional), unzip your knxproj file
# comment out this lines if you do not have/want to read ETS config
PROJECTFILE = "./knxproj/P-02A7/0.xml"

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
WANTED_CONTROLS = "Switch_Szene_Garage_links, \
    Switch_Szene_Garage_rechts , \
    Licht_EG_Gaderobe, \
    Switch_Beschattung_OG, \
    Licht_ALL"

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

# depending on your ETS version you may need to adjust the /11
# just look at the 1st tag in your 0.xml
NS_URL = '{http://knx.org/xml/project/11}'
FIND_BUILDINGS = NS_URL + 'Buildings'   # Gebaeude
FIND_BUILDINGPART = NS_URL + 'BuildingPart'
FIND_TRADES = NS_URL + 'Trades'         # Gewerke
FIND_TRADEPART = NS_URL + 'Trade'
FIND_DEVICEREF = NS_URL + 'DeviceInstanceRef'
FIND_DEVICE = NS_URL + 'DeviceInstance'
FIND_COMREF = NS_URL + 'ComObjectInstanceRef'
FIND_CONNECTOR = NS_URL + 'Connectors'
FIND_SEND = NS_URL + 'Send'
FIND_RECEIVE = NS_URL + 'Receive'
FIND_GA = NS_URL + 'GroupAddress'
