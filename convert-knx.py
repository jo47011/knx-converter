#!/usr/bin/env python3
'''Updates existing knx1 item files and generates a knx.things file.

see readme.md and config.py

Disclaimer:

   This file is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

'''

import os
import sys
from collections import namedtuple
import xml.etree.ElementTree as ET
import re
import subprocess
from os import path
from shutil import move
from dataclasses import dataclass, field
from collections import OrderedDict as od

import config

knxItems = []
ohItems = []


@dataclass(order=True)
class OpenHABItem:
    '''Helper class for storing relevant data per OH Item
    '''
    sort_index: int = field(init=False, repr=False)
    line: str
    address: str = None
    type: str = None
    name: str = None
    dpt: str = None
    feedback: str = ""
    expire: str = ""
    autoupdate: str = ""
    groupaddress_oh1: str = None
    groupaddress_oh2: str = None

    def __str__(self):
        return (
            f"OpenHABItem:\n\n"
            f"    line            :\t{self.line}"
            f"    address         :\t{self.address}\n"
            f"    type            :\t{self.type}\n"
            f"    name            :\t{self.name}\n"
            f"    dpt             :\t{self.dpt}\n"
            f"    feedback        :\t{self.feedback}\n"
            f"    expire          :\t{self.expire}\n"
            f"    autoupdate      :\t{self.autoupdate}\n"
            f"    groupaddress_oh1:\t{self.groupaddress_oh1}\n"
            f"    groupaddress_oh2:\t{self.groupaddress_oh2}\n"
        )

    # extract knx address and OH" group address config
    def __post_init__(self):
        # find knx address etc.
        self.groupaddress_oh1 = re.search(r'{[ \t]*(knx[ \t]*=.*)[ \t]*}', self.line).group(1)
        self.type, self.name = self.line.split()[:2]
        ga = re.search(r'[ \t]*knx[ \t]*=[ \t]*"(.*)"', self.groupaddress_oh1).group(1)
        self.address = re.search(r'([0-9]*/[0-9]*/[0-9]*).*', ga).group(1)

        # datapoint
        if ':' in ga:
            self.dpt = re.search(r'[<>]?(.*):.*', ga).group(1)

        # feedback
        if '<' in ga:
            self.feedback = re.search(r'.*<(.*:)?([0-9]*/[0-9]*/[0-9]*).*', ga).group(2)

        # align spaces around = and , 1st
        ga = self.groupaddress_oh1.replace(" = ", "=").replace(" ,", ",").replace(", ", ",").strip()

        # extract option expire if applicable
        if 'expire' in ga:
            self.expire = re.search(r'.*[ \t]*expire[ \t]*=[ \t]*("[\w,=]*")[,]?.*', ga).group(1)

        # extract option autoupdate if applicable
        if 'autoupdate' in ga:
            self.autoupdate = re.search(r'.*[ \t]*autoupdate[ \t]*=[ \t]*("[\w]*").*', ga).group(1)

        # assign OH2 group address
        if self.type == 'Dimmer':
            values = re.sub(r'knx[ \t]*=|"', '', ga).split(',')
            if len(values) >= 3:
                s, i, p = map(str.strip, values[:3])
                self.groupaddress_oh2 = f'switch = "{s}", position = "{p}", increaseDecrease = "{i}"'
            else:
                self.groupaddress_oh2 = f'switch = "{values[0]}"'

        elif self.type == 'Rollershutter':
            u, s, p = map(str.strip, re.sub(r'knx[ \t]*=|"', '', ga).split(',')[:3])
            self.groupaddress_oh2 = f'upDown = "{u}", stopMove = "{s}", position = "{p}"'

        else:
            # default is ga
            self.groupaddress_oh2 = ga.replace("knx", "ga")

        # assign sortable number
        self.sort_index = 0
        for idx, f in enumerate(self.address.split('/')):
            self.sort_index += int(f) * 10**(3 - idx)

        # add OpenHAB item
        search = list(filter(lambda x: self == x, ohItems))
        if len(search) == 0:
            ohItems.append(self)
        else:
            print("ERROR: The following address is assigned twice in your item files:")
            print(search[0])
            sys.exit(1)

        # assign corresponding KNX devices
        if len(knxItems) > 0:
            devices = [x for x in knxItems if x.address == self.address]

            # print(devices)

            selection = devices.copy()
            try:
                selection = list(filter(lambda x: not self.inList(x.device_id, config.IGNORE_DEVICES), devices))
            except (NameError, AttributeError) as excep:
                pass

            if len(devices) == 0:
                print(f"OH Item not found in ETS export: {self.address.ljust(8,' ')} "
                      f"\tusing {config.DEVICE_GENERIC}"
                      f"\t{self.name}")
                entry = createGenericKNXItem(ohItem=self)
                entry.ohItem = self
            elif len(selection) == 0:
                print(f"OH Item filtered out in ETS export: {self.address.ljust(8,' ')} "
                      f"\tusing: {config.DEVICE_GENERIC}")
                entry = createGenericKNXItem(ohItem=self)
            else:

                # join knxItem and ohItem
                actors = []
                try:
                    actors = list(filter(lambda x: self.inList(x.device_id, config.ACTORS),
                                          selection))
                except (NameError, AttributeError) as excep:
                    pass

                if len(actors) == 0:
                    print(f"INFO: No Actor found for: {self.address.ljust(8,' ')} "
                          f"\tusing: {config.DEVICE_GENERIC}"
                          f"\t{self.name}")
                    entry = createGenericKNXItem(ohItem=self)
                else:
                    for entry in actors:
                        entry.ohItem = self

                controls = []
                try:
                    controls = list(filter(lambda x: self.inList(x.device_id, config.CONTROLS), selection))
                except (NameError, AttributeError) as excep:
                    pass

                for entry in controls:
                    entry.ohItem = self
                    entry.isControl = True

                missing = list(filter(lambda x: not self.inList(x.device_id, config.ACTORS + ',' + config.CONTROLS),
                                      selection))

                if len(missing) > 0:
                    for entry in missing:
                        print(f"OH Items not assigned: {self.address.ljust(8,' ')}: {entry}")

    def inList(self, str, searchString):
        for i in searchString.replace(" ", "").split(","):
            if i != "" and i in str:
                return True
        return False

    def __eq__(self, other):
        return self.address == other.address and self.name == other.name


@dataclass(order=True)
class KNXItem:
    '''Helper class for storing relevant data per GA
    '''
    sort_index: int = field(init=False, repr=False)
    name: str
    address: str
    device_address: str = config.DEVICE_GENERIC
    refid: str = ""
    device_id: str = ""
    building: str = ""
    dpt: str = None
    ohItem: OpenHABItem = None
    isControl: bool = False
    exported: bool = False
    ignore: bool = False

    def __str__(self):
        return (
            f"KNXItem:\n\n"
            f"    name          :\t{self.name}\n"
            f"    address       :\t{self.address}\n"
            f"    device_address:\t{self.device_address}\n"
            f"    refid         :\t{self.refid}\n"
            f"    device_id     :\t{self.device_id}\n"
            f"    building      :\t{self.building}\n"
            f"    dpt           :\t{self.dpt}\n"
            f"    ohItem        :\t{self.ohItem.name if self.ohItem else 'None'}\n"
            f"    isControl     :\t{self.isControl}\n"
        )

    def __post_init__(self):
        if len(list(filter(lambda x: x == self, knxItems))) == 0:
            knxItems.append(self)

        # assign sortable number by device_address and knx address
        self.sort_index = 0
        for idx, f in enumerate(self.address.split('/')):
            self.sort_index += int(f) * 10**(3 - idx)

        if '.' in self.device_address:
            for idx, f in enumerate(self.device_address.split('.')):
                self.sort_index += int(f) * 10**(3 - idx) * 10**4

    def __eq__(self, other):
        return self.getID() == other.getID() and self.isControl == other.isControl

    def __hash__(self):
        return hash(self.getID() + "1" if self.isControl else "0")

    def getID(self):
        return self.device_address + '-' + self.address.replace("/", "_")

    def getDeviceName(self, prefix=""):
        result = prefix + self.device_address.replace(".", "_")
        return result

    def getExpire(self):
        if self.ohItem is not None and self.ohItem.expire:
            return ", expire=" + self.ohItem.expire
        return ""

    def getAutoUpdate(self):
        if self.ohItem is not None and len(self.ohItem.autoupdate) > 0:
            return ", autoupdate=" + self.ohItem.autoupdate
        return ""

    def isGeneric(self):
        return self.device_address == config.DEVICE_GENERIC

    def getItemRepresentation(self, line=None):
        if self.ohItem is None:
            name = self.getID()
        else:
            name = self.ohItem.name

        channel = (config.CHANNEL.replace('<generic>', self.getDeviceName())
                   + self.getExpire() + self.getAutoUpdate())

        if line is None:
            unique = ""
            if self.isControl:
                if self.isGeneric:
                    unique = config.CONTROL_SUFFIX
                else:
                    unique = self.getDeviceName('_')

            if self.ohItem is None:
                type = config.UNUSED_TYPE
            else:
                type = self.ohItem.type

            result = (f'{type} {name}{unique} "{self.name}" '
                      + '{' + channel.replace('<name>', name + unique) + '}')
        else:
            result = re.sub(r'{.*}', '{' + channel.replace('<name>', name) + '}', line)
        return result


def trace(func):
    '''Helper decorator function.
    Add @trace before your function for debug output'''
    def wrapper(*args, **kwargs):
        print(f'TRACE: calling {func.__name__}() '
              f'with {args}, {kwargs}')

        original_result = func(*args, **kwargs)

        print(f'TRACE: {func.__name__}() '
              f'returned {original_result!r}')

        return original_result
    return wrapper


def createGenericKNXItem(ohItem=None, isControl=False):
    '''Adds a gereric (empty) KNXItem

    :param OpenHABItem item: OpenHABItem to be referred to
    '''
    return KNXItem(name=ohItem.name,
                   address=ohItem.address,
                   ohItem=ohItem,
                   isControl=isControl)


def createGenericControls():
    '''Creates a generic control entry for any control that is used in an item file
    '''
    for item in list(od.fromkeys(filter(lambda x: x.ohItem is not None and x.isControl, knxItems)).keys()):
        entry = createGenericKNXItem(ohItem=item.ohItem, isControl=True)


def readParts(type, root, part, name=''):
    # print(f"reading {part.attrib['Name']}")
    name = (name + " " + part.attrib['Name']).lstrip()

    # find all devices in building
    for devref in part.findall(config.FIND_DEVICEREF):
        readDevice(root, devref.attrib['RefId'], name)

    # apply for all building sub-parts
    for subpart in part.findall(type):
        readParts(type, root, subpart, name)


def readDevice(root, ref, building):
    device = root.findall('.//' + config.FIND_DEVICE + "[@Id='" + ref + "']")[0]

    for comobj in device.findall('.//' + config.FIND_COMREF):
        if 'DatapointType' not in comobj.attrib.keys():
            continue

        dpt = comobj.attrib['DatapointType']  # FIXME: need some mapping here to dtps

        for connector in comobj.findall('.//' + config.FIND_CONNECTOR):

            for send in connector.findall('.//' + config.FIND_SEND) + connector.findall('.//' + config.FIND_RECEIVE):

                if 'GroupAddressRefId' in send.keys():
                    ga_ref = send.attrib['GroupAddressRefId']
                    ga = root.findall('.//' + config.FIND_GA + "[@Id='" + ga_ref + "']")[0]
                    ga_str = ga2str(int(ga.attrib['Address']))

                    if len(ga_str) > 0:
                        ga = KNXItem(name=ga.attrib['Name'],
                                     address=ga_str,
                                     refid=ga_ref,
                                     device_address=f"{config.ETS_LINE_PREFIX}{device.attrib['Address']}",
                                     device_id=device.attrib['ProductRefId'],
                                     # dpt=dpt,
                                     building=building)


def ga2str(ga):
    return "%d/%d/%d" % ((ga >> 11) & 0xf, (ga >> 8) & 0x7, ga & 0xff)


def cleanupFeedback():
    '''Removes KNXItems which are known feedback group addresses
    '''

    def isAssignedFeedback(item1, item2):
        '''Returns true if group address of a device is already used as a feedback address at the same device
        '''
        result = (item1 != item2 and                              # not the same item
                  item1.device_address == item2.device_address and    # same device
                  item1.ohItem is None and                            # item1 not assigned in OH item file
                  item2.ohItem is not None and                        # item2 is assigned in OH item file
                  item1.address == item2.ohItem.feedback)              # item1 used as feedback of item2

        return result

    before = len(knxItems)

    # remove already assigned feedback GAs at the same device
    for item in filter(lambda x: x.ohItem is not None and x.ohItem.feedback, knxItems):
        for foundItem in [x for x in knxItems if isAssignedFeedback(x, item)]:
            knxItems.remove(foundItem)

    # print(f"Debug: remove feedback {before} => {len(knxItems)}")


def readETSFile():
    '''Reads the ETS Project file if defined.
    '''
    try:
        project = ET.parse(config.PROJECTFILE)
        root = project.getroot()
        buildings = root.find('.//' + config.FIND_BUILDINGS)
        print(f"reading {config.PROJECTFILE}")

        if buildings is None:
            print("Buildings not found")
        else:
            for part in buildings:
                readParts(config.FIND_BUILDINGPART, root, part)

        trades = root.find('.//' + config.FIND_TRADES)

        if trades is not None:
            for part in trades:
                # print(part)
                readParts(config.FIND_TRADEPART, root, part)

    except (NameError, AttributeError) as excep:
        print('PROJECTFILE is not defined (see config.py), so we proceed w/o ETS input.')


def readOHFiles():
    '''Reads the OpenHAB item file(s) if defined
    '''
    try:
        for myfile in map(str.strip, config.ITEMS_FILES.split(',')):
            print(f"reading {myfile}")
            with open(myfile, 'r') as infile:
                for line in infile.readlines():
                    # knx items only
                    if line.startswith(config.CHANNELS) and re.match(r'.*knx[ ]*=.*', line):
                        # remember values for things file
                        item = OpenHABItem(line=line)

    except (NameError, AttributeError) as excep:
        print('ITEMS_FILES are not defined (see config.py), so we proceed w/o OpenHAB item files.')


def writeThingFile(filter, filename, comment=''):
    with open(filename, 'w', encoding="utf8") as thingfile:
        print(comment, file=thingfile)
        print(config.THING_HEADER, file=thingfile)

        current = -1
        for item in sorted(list(filter)):

            # print device if new
            if current != item.device_address:
                if current != -1:
                    print("    }", file=thingfile)
                current = item.device_address
                if current is None:
                    dev = config.DEVICE_EMPTY.replace('<generic>', DEVICE_GENERIC)
                else:
                    dev = config.DEVICE.replace('<address>', current) \
                                       .replace('<generic>', item.getDeviceName()) \
                                       .replace('<building>', item.building) \
                                .replace('<device_id>', item.device_id)

                print(dev, file=thingfile)

            # print OH Item
            control = unique = direction = ''
            if item.isControl:
                control = "-control"
                if item.isGeneric:
                    unique = config.CONTROL_SUFFIX
                else:
                    unique = item.getDeviceName('_')

            if item.ohItem:
                print(f'\tType {item.ohItem.type.lower()}{control} : ',
                      f'{item.ohItem.name}{unique} "{item.name}" [ {item.ohItem.groupaddress_oh2} ]', file=thingfile)
            else:
                print(f'\tType {config.UNUSED_TYPE}{control} : ',
                      f'{item.getID()}{unique} "{item.name}" [ ga="{item.address}" ]',
                      file=thingfile)

        # print footer
        print('    }\n'
              '}', file=thingfile)
        print(f"written: {filename}")


def writeItemFiles():
    try:
        for myfile in map(str.strip, config.ITEMS_FILES.split(',')):

            outfilename = os.path.join(config.ITEM_RESULT_DIR, path.basename(myfile))
            with open(myfile, 'r') as infile, \
                 open(outfilename, 'w', encoding="utf8") as outfile:

                # read original item file and replace knx2 values
                for line in infile.readlines():

                    if not (line.startswith(config.CHANNELS) and re.match(r'.*knx[ ]*=.*', line)):
                        # non knx items and comments
                        print(line, file=outfile, end='')
                    else:
                        # knx item
                        temp = re.search(r'{[ \t]*(knx[ \t]*=.*)[ \t]*}', line).group(1)
                        knx = re.search(r'([0-9]*/[0-9]*/[0-9]*).*', temp).group(1)

                        if knx is None:
                            print("ERROR: GA address not found in:")
                            print(line)
                            sys.exit(1)

                        # find according ETS Actor by GroupAddress
                        items = [x for x in knxItems if x.address == knx and not x.isControl]
                        if len(items) == 0:
                            # seems like we're running w/o ETS project file so create a generic entry
                            name = line.split()[1:2][0]
                            search = [x for x in ohItems if x.address == knx and x.name == name]
                            if len(search) == 1:
                                item = createGenericKNXItem(ohItem=search[0])
                            else:
                                # we're lost now so we give up
                                print(f"ERROR: OH entry {name} w/ Group Address {knx} not found.")
                                sys.exit(1)

                        elif len(items) > 1:   # multiple entries found
                            print(f"INFO: Multiple item file entries w/ Group Address {knx} found."
                                  f"\tusing: {config.DEVICE_GENERIC}")
                            for item in items:
                                item.ignore = True  # "remove others"
                                item.exported = True

                            item = createGenericKNXItem(ohItem=items[0].ohItem)

                        else:
                            # exactly one item entry found
                            item = items[0]

                        print(item.getItemRepresentation(line), file=outfile, end='')
                        item.exported = True

                        # add generic control item if aplicable
                        items = [x for x in knxItems if x.getID() == item.getID() and x.isGeneric and x.isControl]
                        if len(items) > 1:
                            # should not happen there should be only one generic item
                            print(f"ERROR: Multiple generic controls w/ Group Address {knx} found.")
                            sys.exit(1)

                        if len(items) == 1:
                            print(items[0].getItemRepresentation(), file=outfile)
                            items[0].exported = True

            print(f"written: {outfilename}")
    except (NameError, AttributeError) as excep:
        print('ITEMS_FILES are not defined (see config.py), so we proceed w/o OpenHAB item files.')


def writeFiles():
    '''Link OpenHABitems and KNXItems and writes
    ITEMS_FILES, THINGS_FILE, ITEMS_UNUSED_FILE, THINGS_UNUSED_FILE files in knx2 format.
    '''

    # create result dir if non existant
    if not path.exists(config.ITEM_RESULT_DIR):
        subprocess.call(["mkdir", '-p', config.ITEM_RESULT_DIR])

    writeItemFiles()

    # print left over KNXItems to ITEMS_UNUSED_FILE
    devc = None
    devu = None
    with open(config.ITEMS_UNUSED_FILE, 'w', encoding="utf8") as unusedfile, \
         open(config.ITEMS_UNUSED_CONTROLS_FILE, 'w', encoding="utf8") as controlfile:

        print('// These control switches should be added to get event from wall switches', file=controlfile)

        print('// These group addresses are available in your ETS '
              'but are not configured/used in any of your item files', file=unusedfile)

        for item in sorted(list(filter(lambda x: not x.exported and not x.ignore, knxItems))):

            if item.ohItem is None:
                file = unusedfile
                if devu != item.getDeviceName():
                    devu = item.getDeviceName()
                    print('', file=file)
            else:
                file = controlfile
                if devc != item.getDeviceName():
                    devc = item.getDeviceName()
                    print('', file=file)

            print(item.getItemRepresentation(), file=file)

        print(f"written: {config.ITEMS_UNUSED_CONTROLS_FILE}")
        print(f"written: {config.ITEMS_UNUSED_FILE}")

    # write thing files
    writeThingFile(filter(lambda x: x.ohItem is not None and not x.ignore
                          and (x.isGeneric or not x.isControl), knxItems),
                   config.THINGS_FILE)

    writeThingFile(filter(lambda x: not x.exported and not x.ignore, knxItems), config.THINGS_UNUSED_FILE,
                   '// These things are available in your ETS but are not configured/used in any of your item files\n')


# here we go...
if __name__ == '__main__':
    readETSFile()
    readOHFiles()

    # remove already assigned feedback addresses
    cleanupFeedback()

    # create generic controls for used items
    createGenericControls()

    # debug output
    try:
        with open(config.DEBUG_KNX, 'w') as file:
            for item in sorted(knxItems):
                print(item, file=file)
    except (NameError, AttributeError) as excep:
        pass

    try:
        with open(config.DEBUG_OH, 'w') as file:
            for item in sorted(ohItems):
                print(item, file=file)
    except (NameError, AttributeError) as excep:
        pass

    writeFiles()
