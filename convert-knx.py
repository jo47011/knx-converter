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
from collections import OrderedDict as od
import re
from os import path

import config
from items import KNXItem, OpenHABItem


def readParts(type, root, part, name=''):
    '''Recursively reads all parts from ETS root.
    '''
    # print(f"reading {part.attrib['Name']}")
    name = (name + " " + part.attrib['Name']).lstrip()

    # find all devices in building
    for devref in part.findall(getNsURL(root) + config.FIND_DEVICEREF):
        readDevice(root, devref.attrib['RefId'], name)

    # apply for all building sub-parts
    for subpart in part.findall(type):
        readParts(type, root, subpart, name)


def readDevice(root, ref, building):
    ''' Reads top level ref device and all containing group addresses from ETS root.
    '''
    device = root.findall(getNsURL(root) + config.FIND_DEVICE + "[@Id='" + ref + "']")[0]

    for comobj in device.findall(getNsURL(root) + config.FIND_COMREF):
        if 'DatapointType' not in comobj.attrib.keys():
            continue

        dpt = comobj.attrib['DatapointType']  # FIXME: need some mapping here to dtps

        for connector in comobj.findall(getNsURL(root) + config.FIND_CONNECTOR):

            for send in (connector.findall(getNsURL(root) + config.FIND_SEND) +
                         connector.findall(getNsURL(root) + config.FIND_RECEIVE)):

                if 'GroupAddressRefId' in send.keys():
                    ga_ref = send.attrib['GroupAddressRefId']
                    ga = root.findall(getNsURL(root) + config.FIND_GA + "[@Id='" + ga_ref + "']")[0]
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
    # Converts ETS stlye group address to openhab format: 0/0/0.
    return "%d/%d/%d" % ((ga >> 11) & 0xf, (ga >> 8) & 0x7, ga & 0xff)


def cleanupFeedback():
    '''Removes KNXItems which are known feedback group addresses
    '''

    def isAssignedFeedback(item1, item2):
        '''Returns true if group address of a device is already used as a feedback address at the same device
        '''
        result = (item1 != item2 and                                  # not the same item
                  item1.device_address == item2.device_address and    # same device
                  item1.ohItem is None and                            # item1 not assigned in OH item file
                  item2.ohItem is not None and                        # item2 is assigned in OH item file
                  item1.address == item2.ohItem.feedback)             # item1 used as feedback of item2

        return result

    before = len(KNXItem.items())

    # remove already assigned feedback GAs at the same device
    for item in filter(lambda x: x.ohItem is not None and x.ohItem.feedback, KNXItem.items()):
        for foundItem in [x for x in KNXItem.items() if isAssignedFeedback(x, item)]:
            KNXItem.remove(foundItem)

    # print(f"Debug: remove feedback {before} => {len(KNXItem.items())}")


def createGenericControls():
    '''Creates a generic control entry for any control that is used in an item file
    '''
    allControls = list(od.fromkeys(filter(lambda x: x.ohItem is not None
                                          and x.isControl
                                          and x.isWantedControl(), KNXItem.items())).keys())
    for item in allControls:
        entry = KNXItem.createGeneric(ohItem=item.ohItem, isControl=True)
        item.ignore = True


def getNsURL(root):
    '''Checks for KNX tag in root node.  Script is terminated if not found.
    '''
    if not root.tag.endswith('KNX'):
        print(f'ERROR: no KNX root found in: {root}')
        sys.exit(1)

    return './/' + root.tag[:-3]    # .//{http://knx.org/xml/project/11}


def readETSFile():
    '''Reads the ETS Project file if defined.
    '''
    try:
        config.PROJECTFILE
    except (NameError, AttributeError) as excep:
        config.PROJECTFILE = None
        print('PROJECTFILE is not defined (see config.py), so we proceed w/o ETS input.')

    if config.PROJECTFILE is not None:
        project = ET.parse(config.PROJECTFILE)
        root = project.getroot()
        buildings = root.find(getNsURL(root) + config.FIND_BUILDINGS)
        print(f"reading {config.PROJECTFILE}")

        if buildings is None:
            print("Buildings not found")
        else:
            for part in buildings:
                readParts(config.FIND_BUILDINGPART, root, part)

        trades = root.find(getNsURL(root) + config.FIND_TRADES)

        if trades is not None:
            for part in trades:
                # print(part)
                readParts(config.FIND_TRADEPART, root, part)


def readOHFiles():
    '''Reads the OpenHAB item file(s) if defined
    '''
    try:
        config.ITEMS_FILES
    except (NameError, AttributeError) as excep:
        config.ITEMS_FILES = None
        print('ITEMS_FILES are not defined (see config.py), so we proceed w/o OpenHAB item files.')

    if config.ITEMS_FILES is not None:
        for myfile in map(str.strip, config.ITEMS_FILES.split(',')):
            myfile = myfile.strip('\\\r\n').strip()
            print(f"reading {myfile}")
            with open(myfile, 'r', encoding=config.IN_ENCODING) as infile:
                for line in infile.readlines():
                    # knx items only, remove trailing comments //
                    if line.startswith(config.CHANNELS) and re.match(r'.*knx[ ]*=.*', re.sub(r'//.*', '', line)):
                        # remember values for things file
                        item = OpenHABItem(line=line)


def writeThingFile(filter, filename, comment=''):
    '''Write openhab thing file.  See config.THING*
    '''
    # create path to outfile if it doesn't existant
    filepath = os.path.split(filename)[0]
    print(filename, filepath)
    if not path.exists(filepath) and filepath:
        print("mkdir:" + filepath)
        os.makedirs(filepath)

    with open(filename, 'w', encoding=config.OUT_ENCODING) as thingfile:
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
                if not item.isWantedControl():
                    continue

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
    '''Write openhab item files.  See config.ITEMS_FILES.
    '''
    try:
        config.ITEMS_FILES
    except (NameError, AttributeError) as excep:
        config.ITEMS_FILES = None
        print('ITEMS_FILES are not defined (see config.py), so we proceed w/o OpenHAB item files.')

    # create path to outfiles if it doesn't existant
    if not path.exists(config.ITEM_RESULT_DIR) and config.ITEM_RESULT_DIR:
        os.makedirs(config.ITEM_RESULT_DIR)

    if config.ITEMS_FILES is not None:
        for myfile in map(str.strip, config.ITEMS_FILES.split(',')):

            outfilename = os.path.join(config.ITEM_RESULT_DIR, path.basename(myfile))
            myfile = myfile.strip('\\\r\n').strip()
            with open(myfile, 'r', encoding=config.IN_ENCODING) as infile, \
                 open(outfilename, 'w', encoding=config.OUT_ENCODING) as outfile:

                # read original item file and replace knx2 values
                for line in infile.readlines():

                    if not (line.startswith(config.CHANNELS) and re.match(r'.*knx[ ]*=.*', re.sub(r'//.*', '', line))):
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
                        items = [x for x in KNXItem.items() if x.address == knx and
                                 not x.isControl and not x.exported]
                        if len(items) == 0:
                            # seems like we're running w/o ETS project file so create a generic entry
                            name = line.split()[1:2][0]
                            search = [x for x in OpenHABItem.allItems if x.address == knx and x.name == name]
                            if len(search) == 1:
                                item = KNXItem.createGeneric(ohItem=search[0])
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

                            # Use 1st one
                            hit = next(obj for obj in items if obj.ohItem is not None)
                            item = KNXItem.createGeneric(ohItem=hit.ohItem)

                        else:
                            # exactly one item entry found
                            item = items[0]

                        print(item.getItemRepresentation(line), file=outfile, end='')
                        item.exported = True

                        # add generic control item if aplicable
                        items = [x for x in KNXItem.items() if x.getID() == item.getID()
                                 and x.isGeneric and x.isControl and item.isWantedControl()]
                        if len(items) > 1:
                            # should not happen there should be only one generic item
                            print(f"ERROR: Multiple generic controls w/ Group Address {knx} found.")
                            sys.exit(1)

                        if len(items) == 1:
                            print(items[0].getItemRepresentation(), file=outfile)
                            items[0].exported = True

            print(f"written: {outfilename}")


def writeFiles():
    '''Link OpenHABitems and KNXItems and writes
    ITEMS_FILES, THINGS_FILE, ITEMS_UNUSED_FILE, THINGS_UNUSED_FILE files in knx2 format.
    '''

    writeItemFiles()

    # print left over KNXItems to ITEMS_UNUSED_FILE
    devc = None
    devu = None
    with open(config.ITEMS_UNUSED_FILE, 'w', encoding=config.OUT_ENCODING) as unusedfile, \
         open(config.ITEMS_UNUSED_CONTROLS_FILE, 'w', encoding=config.OUT_ENCODING) as controlfile:

        print('// These control switches should be added to get event from wall switches', file=controlfile)

        print('// These group addresses are available in your ETS '
              'but are not configured/used in any of your item files', file=unusedfile)

        for item in sorted(list(filter(lambda x: not x.exported and not x.ignore, KNXItem.items()))):

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
                          and (x.isGeneric or not x.isControl), KNXItem.items()),
                   config.THINGS_FILE)

    writeThingFile(filter(lambda x: not x.exported and not x.ignore, KNXItem.items()), config.THINGS_UNUSED_FILE,
                   '// These things are available in your ETS but are not configured/used in any of your item files\n')


def checkPythonVersion():
    # checks for minimum python version 3.7
    if sys.version_info[0] < 3 or sys.version_info[1] < 7:
        raise Exception("Must be using Python 3.7")


# here we go...
if __name__ == '__main__':

    # check minimum ptyhon version 1st
    checkPythonVersion()

    # read ets & openhab files
    readETSFile()
    readOHFiles()

    # remove already assigned feedback addresses
    cleanupFeedback()

    # create generic controls for used items
    createGenericControls()

    # debug output
    try:
        with open(config.DEBUG_KNX, 'w') as file:
            for item in sorted(KNXItem.items()):
                print(item, file=file)
    except (NameError, AttributeError) as excep:
        pass

    try:
        with open(config.DEBUG_OH, 'w') as file:
            for item in sorted(OpenHABItem.items()):
                print(item, file=file)
    except (NameError, AttributeError) as excep:
        pass

    writeFiles()
