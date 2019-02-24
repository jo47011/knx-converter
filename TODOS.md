The following issues may be improved one day:
* Read datapoints from ets (dpt)
* Support single quotes in item files,
  as for now only double quotes are supported
* Improve NS_URL = '{http://knx.org/xml/project/11}'
* As of now all items read from ETS which are not in any items file
  are handled as Switches.
  Determine correct type based on *knxproj* files what are actors,
  controls, etc.
