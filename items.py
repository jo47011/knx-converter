#!/usr/bin/env python3
'''Provides for KNX- and OpenHab-Items

Disclaimer:

   This file is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
'''

import sys
import re
from dataclasses import dataclass, field
from abc import ABCMeta, abstractmethod

from myargs import config


@dataclass(order=True)
class Item(metaclass=ABCMeta):
    '''Helper super-class for storing common data per Item
    '''
    sort_index: int = field(init=False, repr=False)
    name: str = ''
    address: str = ''

    # all_items = [] must be declared in subclass
    @property
    @abstractmethod
    def all_items(self):
        pass

    @classmethod
    def items(cls):
        return cls.all_items

    @classmethod
    def remove(cls, item):
        cls.items().remove(item)


@dataclass(order=True)
class OpenHABItem(Item):
    '''Helper class for storing relevant data per OH Item
    '''
    all_items = []
    autoupdateTrue = None
    autoupdateFalse = None

    line: str = ''
    type: str = None
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

    def myinit(self):
        '''Read some config variables, if defined.
        '''
        if not OpenHABItem.all_items:
            try:
                OpenHABItem.autoupdateTrue = config.AUTOUPDATE_TRUE.replace(" ", "").split(",")
            except (NameError, AttributeError):
                pass

            try:
                OpenHABItem.autoupdateFalse = config.AUTOUPDATE_FALSE.replace(" ", "").split(",")
            except (NameError, AttributeError):
                pass

    def __post_init__(self):
        self.myinit()
        self.parse_KNX_line()
        OpenHABItem.add(self)
        self.calculate_sort_index()
        self.assign_KNX_devices()

    def parse_KNX_line(self):
        '''Extract knx address and OH" group address config etc.
        '''

        # find knx address etc.
        self.groupaddress_oh1 = re.search(r'{.*(knx[ \t]*=.*)[ \t]*}', self.line).group(1)
        self.type, self.name = self.line.split()[:2]
        ga = re.search(r'[ \t]*knx[ \t]*=[ \t]*["\'](.*)["\']', self.groupaddress_oh1).group(1)
        self.address = re.search(r'([0-9]*/[0-9]*/[0-9]*).*', ga).group(1)

        # print warning on old style alexa, yet not supported
        if re.search('alexa', self.line, re.IGNORECASE):
            print('Warning: Alexa only supported with this format: e.g. ["Lighting"].  As of now removed.')
            print(self.line)

        # datapoint
        if ':' in ga:
            self.dpt = re.search(r'[<>]?(.*):.*', ga).group(1)

        # feedback
        if '<' in ga:
            self.feedback = re.search(r'.*<(.*:)?([0-9]*/[0-9]*/[0-9]*).*', ga).group(2)

        # remove all spaces in group address
        ga = self.groupaddress_oh1.replace(" ", "")

        # knx
        knx = re.search(r'(knx[ \t]*="[0-9/,+-<>]*").*', ga).group(1)

        # extract option expire if applicable
        if 'expire' in ga:
            self.expire = re.search(r'.*[ \t]*expire[ \t]*=[ \t]*(["\'][\w,=]*["\'])[,]?.*', ga).group(1)

        # extract option autoupdate if applicable
        if 'autoupdate' in ga:
            self.autoupdate = re.search(r'.*[ \t]*autoupdate[ \t]*=[ \t]*(["\'][\w]*["\']).*', ga).group(1)
        elif self.is_autoupdate_true():
            self.autoupdate = '"true"'
        elif self.is_autoupdate_false():
            self.autoupdate = '"false"'

        # assign OH2 group address
        if self.type == 'Dimmer':
            values = re.sub(r'knx[ \t]*=|["\']', '', ga).split(',')
            if len(values) >= 3:
                s, i, p = map(str.strip, values[:3])
                self.groupaddress_oh2 = f'switch = "{s}", position = "{p}", increaseDecrease = "{i}"'
            else:
                self.groupaddress_oh2 = f'switch = "{values[0]}"'

        elif self.type == 'Rollershutter':
            try:
                u, s, p = map(str.strip, re.sub(r'knx[ \t]*=|["\']', '', ga).split(',')[:3])
                self.groupaddress_oh2 = f'upDown = "{u}", stopMove = "{s}", position = "{p}"'
            except (ValueError):
                print("ERROR: The following Rollershutter should have 3 KNX entries for: upDown, stopMove, position")
                print(self.line)

        else:
            # default is ga
            self.groupaddress_oh2 = knx.replace("knx", "ga")

    def calculate_sort_index(self):
        '''Assign sortable number
        '''
        self.sort_index = 0
        for idx, f in enumerate(self.address.split('/')):
            self.sort_index += int(f) * 10**(3 - idx)

    def assign_KNX_devices(self):
        '''Assign corresponding KNX devices.
        '''
        if len(KNXItem.items()) > 0:
            devices = [x for x in KNXItem.items() if x.address == self.address]

            # print(devices)

            selection = devices.copy()
            try:
                selection = list(filter(lambda x: not self.in_list(x.device_id, config.IGNORE_DEVICES), devices))
            except (NameError, AttributeError):
                pass

            if len(devices) == 0:
                print(f"INFO: OH Item not found in ETS export: {self.address.ljust(8,' ')} "
                      f"\tusing {config.DEVICE_GENERIC}"
                      f"\t{self.name}")
                entry = KNXItem.create_generic(ohItem=self)
                entry.ohItem = self
            elif len(selection) == 0:
                print(f"OH Item filtered out in ETS export: {self.address.ljust(8,' ')} "
                      f"\tusing: {config.DEVICE_GENERIC}")
                entry = KNXItem.create_generic(ohItem=self)
            else:

                # join knxItem and ohItem
                actors = []
                try:
                    actors = list(filter(lambda x: self.in_list(x.device_id, config.ACTORS),
                                         selection))
                except (NameError, AttributeError):
                    pass

                if len(actors) == 0:
                    print(f"INFO: No Actor found for: {self.address.ljust(8,' ')} "
                          f"\tusing: {config.DEVICE_GENERIC}"
                          f"\t{self.name}")
                    entry = KNXItem.create_generic(ohItem=self)
                else:
                    for entry in actors:
                        entry.ohItem = self

                controls = []
                try:
                    controls = list(filter(lambda x: self.in_list(x.device_id, config.CONTROLS), selection))
                except (NameError, AttributeError):
                    pass

                for entry in controls:
                    entry.ohItem = self
                    entry.isControl = True

                missing = list(filter(lambda x: not self.in_list(x.device_id, config.ACTORS + ',' + config.CONTROLS),
                                      selection))

                if len(missing) > 0:
                    for entry in missing:
                        print(f"OH Items not assigned: {self.address.ljust(8,' ')}: {entry}")

                intersect = list(filter(lambda x: x in controls, actors))

                if len(intersect) > 0:
                    for entry in intersect:
                        print(f"KNX Item matches actor and control: {self.address.ljust(8,' ')}:")
                        self.in_list(entry.device_id, config.ACTORS, True)
                        self.in_list(entry.device_id, config.CONTROLS, True)
                        print(entry)

    def in_list(self, str, searchString, debug=False):
        for i in searchString.replace(" ", "").split(","):
            if i != "" and i in str:
                if debug:
                    print(f"{i} in {str} matches")
                return True
        return False

    def __eq__(self, other):
        return self.address == other.address and self.name == other.name

    def is_autoupdate_true(self):
        if self.autoupdateTrue is None:
            return False
        for r in self.autoupdateTrue:
            if re.match(r, self.name):
                return True

        return False

    def is_autoupdate_false(self):
        if self.autoupdateFalse is None:
            return False
        for r in self.autoupdateFalse:
            if re.match(r, self.name):
                return True

        return False

    @classmethod
    def add(cls, self):
        '''Add item to list of all items.
        '''
        search = list(filter(lambda x: self == x, cls.all_items))
        if len(search) == 0:
            cls.all_items.append(self)
        else:
            print("ERROR: The following address is assigned twice in your item files:")
            print(search)
            print(self)
            print(cls.all_items)
            sys.exit(1)


@dataclass(order=True)
class KNXItem(Item):
    '''Helper class for storing relevant data per GA
    '''
    all_items = []
    wantedControls = None

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

    def myinit(self):
        '''Read some config variables, if defined.
        '''
        if not KNXItem.all_items:
            try:
                KNXItem.wantedControls = config.WANTED_CONTROLS.replace(" ", "").split(",")
            except (NameError, AttributeError):
                pass

    def __post_init__(self):
        self.myinit()
        KNXItem.add(self)
        self.calculate_sort_index()

    def calculate_sort_index(self):
        '''Assign sortable number by device_address and knx address
        '''
        self.sort_index = 0
        for idx, f in enumerate(self.address.split('/')):
            self.sort_index += int(f) * 10**(3 - idx)

        if '.' in self.device_address:
            for idx, f in enumerate(self.device_address.split('.')):
                self.sort_index += int(f) * 10**(3 - idx) * 10**4

    def __eq__(self, other):
        return self.get_id() == other.get_id() and self.isControl == other.isControl

    def error_not_unique(self, duplicate):
        print("ERROR: The following address exits twice in your ETS file:")
        print(duplicate)
        print(self)
        sys.exit(1)

    def __hash__(self):
        return hash(self.get_id() + "1" if self.isControl else "0")

    def get_id(self):
        return self.device_address + '-' + self.address.replace("/", "_")

    def get_device_name(self, prefix=""):
        result = prefix + self.device_address.replace(".", "_")
        return result

    def get_expire(self):
        if self.ohItem is not None and self.ohItem.expire:
            return ", expire=" + self.ohItem.expire
        return ""

    def get_auto_update(self):
        if self.ohItem is not None and len(self.ohItem.autoupdate) > 0:
            return ", autoupdate=" + self.ohItem.autoupdate
        return ""

    def is_generic(self):
        return self.device_address == config.DEVICE_GENERIC

    def is_wanted_control(self):
        if KNXItem.wantedControls is None or self.ohItem is None:
            return False
        for r in KNXItem.wantedControls:
            if re.match(r, self.ohItem.name):
                return True

        return False

    def get_item_representation(self, line=None):
        if self.ohItem is None:
            name = self.get_id()
        else:
            name = self.ohItem.name

        channel = (config.CHANNEL.replace('<generic>', self.get_device_name())
                   + self.get_expire() + self.get_auto_update())

        if line is None:
            unique = ""
            if self.isControl:
                if self.is_generic:
                    unique = config.CONTROL_SUFFIX
                else:
                    unique = self.get_device_name('_')

            if self.ohItem is None:
                type = config.UNUSED_TYPE
            else:
                type = self.ohItem.type

            result = (f'{type} {name}{unique} "{self.name}" '
                      + '{' + channel.replace('<name>', name + unique) + '}')
        else:
            result = re.sub(r'{.*}', '{' + channel.replace('<name>', name) + '}', line)
        return result

    @classmethod
    def create_generic(cls, ohItem=None, isControl=False):
        '''Adds a gereric (empty) KNXItem

        :param OpenHABItem item: OpenHABItem to be referred to
        '''
        return KNXItem(name=ohItem.name,
                       address=ohItem.address,
                       ohItem=ohItem,
                       isControl=isControl)

    @classmethod
    def add(cls, self):
        '''Add item to list of all items.
        '''
        search = list(filter(lambda x: self == x, cls.all_items))
        if len(search) == 0:
            cls.all_items.append(self)
        else:
            # nop, we accept duplicates in ETS file
            pass
