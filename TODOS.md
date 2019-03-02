The following issues may be improved one day:
* Read datapoints from ets (dpt)
* Support single quotes in item files,
  as for now only double quotes are supported
* Improve NS_URL = '{http://knx.org/xml/project/11}'
* Determine correct item type based on *knxproj* files what are actors,
  controls, etc.  So we can improve:
  - As of now all items read from ETS which are not in any items file
  are handled as Switches.
  - Distinguish by type if a GA is assigned to e.g. a Dimmer and a Switch.
* Remove spaces from group addresses, based on the forum spaces may
  cause problems in knx2.
* Maybe based on read/write flags in ETS create less control
  items, e.g. movement detecor is one way (read only)

  Same for: knx = "<4/0/31"
* Name matching WANTED_CONTROLS, ACTORS, etc. should be a regular expression.

Q: do we need to copy the expire options to the control options?
