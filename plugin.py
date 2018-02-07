#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  OpenAQ Python Plugin
#
# Author: Xorfor
#
"""
<plugin key="xfr_openaq" name="OpenAQ" author="Xorfor" version="1.0.0" wikilink="https://github.com/Xorfor/Domoticz-OpenAQ-Plugin" externallink="https://openaq.org/">
    <params>
        <param field="Mode1" label="Radius (km)" width="75px" default="10" required="true"/>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal" default="true"/>
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import json
from datetime import datetime


class BasePlugin:

    __HEARTBEATS2MIN = 6
    __MINUTES        = 60       # 1 hour or use a parameter

    __API_ADDRESS = "api.openaq.org"
    __API_URL = "/v1/latest?coordinates={},{}&radius={}&order_by=distance"

    __VALUES = {
        # id      date, value, unit, name,   units
        "bc":   [ None,  None,    1, "BC",    None],
        "co":   [ None,  None,    2, "CO",    None],
        "no2":  [ None,  None,    3, "NO2",   None],
        "o3":   [ None,  None,    4, "O3",    None],
        "pm10": [ None,  None,    5, "PM10",  None],
        "pm25": [ None,  None,    6, "PM2.5", None],
        "so2":  [ None,  None,    7, "SO2",   None],
    }

    def __init__(self):
        self.__runAgain = 0
        self.__radius = 0
        self.__url = ""
        # self.__conn = None

    def onStart(self):
        Domoticz.Debug("onStart called")
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)
        else:
            Domoticz.Debugging(0)
        # Images
        # Check if images are in database
        if "xfr_openaq2" not in Images:
            Domoticz.Image("xfr_openaq2.zip").Create()
        image = Images["xfr_openaq2"].ID
        Domoticz.Debug("Image created. ID: "+str(image))
        # Validation of parameters
        self.__radius = int( Parameters["Mode1"] )
        if self.__radius < 0:
            self.__radius = 0
        self.__radius *= 1000  # Convert km to m
        loc = Settings["Location"].split(";")
        lat = loc[0]
        lon = loc[1]
        if lat is None or lon is None:
            Domoticz.Error( "Unable to parse coordinates" )
            return False
        self.__url = "https://" + self.__API_ADDRESS + self.__API_URL.format( lat, lon, str( self.__radius ) )
        Domoticz.Debug( "url: " + self.__url )
        # Create devices
        for id in self.__VALUES:
            self.__VALUES[id][0] = None
            self.__VALUES[id][1] = None
        if len(Devices) == 0:
            for id in self.__VALUES:
                Domoticz.Device( Unit=self.__VALUES[id][2], Name=self.__VALUES[id][3], TypeName="Custom", Options={"Custom": "0;ppm"}, Image=image, Used=1).Create()
            Domoticz.Device( Unit=len( self.__VALUES ) + 1, Name="Info", TypeName="Text", Image=image, Used=1 ).Create()

        DumpConfigToLog()
        # self.__conn = Domoticz.Connection(Name="OpenAQ", Transport="TCP/IP", Protocol="HTTPS", Address=self.__API_ADDRESS, Port="443")
        # self.__conn.Connect()

    def onStop(self):
        Domoticz.Debug("onStop called")
        for id in self.__VALUES:
            self.__VALUES[id][0] = None
            self.__VALUES[id][1] = None

    def onConnect(self, Connection, Status, Description):
        Domoticz.Debug("onConnect called ("+str(Status)+"): "+Description)

    def onMessage(self, Connection, Data):
        Domoticz.Debug("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug( "onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str( Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Debug("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Debug("onHeartbeat called")
        self.__runAgain -= 1
        if self.__runAgain <= 0:
            self.__runAgain = self.__HEARTBEATS2MIN * self.__MINUTES
            # Init values
            values = getData( self.__url )
            # Get most recent value from each parameter. Data already ordered by distance, so check dates.
            locations = values["results"]
            totLocations = len( locations )
            totMeasurements = 0
            Domoticz.Debug( "Locations found: " + str( totLocations ) )
            for location in locations:
                measurements = location["measurements"]
                numberOfMeasurements = len( measurements )
                totMeasurements += numberOfMeasurements
                Domoticz.Debug( "Location " + location["location"] + " - measurements: " + str( numberOfMeasurements ) )
                for measurement in measurements:
                    Domoticz.Debug( measurement["lastUpdated"] + " ... " + measurement["parameter"] + ": " + str( measurement["value"] ) + " " + measurement["unit"] )
                    t = datetime.strptime( measurement["lastUpdated"], "%Y-%m-%dT%H:%M:%S.%fZ" )
                    # Skip values like '-999'
                    if measurement["value"] > 0.0:
                        if self.__VALUES[measurement["parameter"]][1] is None:
                            # First time value found. Always get this one.
                            self.__VALUES[measurement["parameter"]][0] = t
                            self.__VALUES[measurement["parameter"]][1] = measurement["value"]
                            self.__VALUES[measurement["parameter"]][4] = measurement["unit"]
                        else:
                            # Domoticz.Debug( "parameter: " + measurement["parameter"] )
                            # Domoticz.Debug( "t: " + str(t))
                            # Domoticz.Debug( "self.__VALUES[measurement['parameter']][0]: " + str(self.__VALUES[measurement["parameter"]][0]))
                            # Is this value more actual?
                            if t > self.__VALUES[measurement["parameter"]][0]:
                                # Domoticz.Debug("More recent date!!!")
                                self.__VALUES[measurement["parameter"]][0] = t
                                self.__VALUES[measurement["parameter"]][1] = measurement["value"]
                                self.__VALUES[measurement["parameter"]][4] = measurement["unit"]
            # Domoticz.Debug("Results: " + str(self.__VALUES))
            # Update the devices
            for id in self.__VALUES:
                if self.__VALUES[id][1] is not None:
                    UpdateDeviceOptions(self.__VALUES[id][2], {"Custom": "0;" + self.__VALUES[id][4]})
                    UpdateDevice(self.__VALUES[id][2], int( self.__VALUES[id][1] ), str( round( self.__VALUES[id][1], 1 ) ) )
            txt = "Number of stations: " + str( totLocations ) + "<br/> " + "Measurements: " + str( totMeasurements )
            # UpdateDeviceName(self.__UNIT_TEXT, plaats)
            UpdateDevice( len( self.__VALUES ) + 1, 0, txt, TimedOut=1 )
        else:
            Domoticz.Debug( "onHeartbeat called, run again in " + str( self.__runAgain ) + " heartbeats." )

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

################################################################################
# Generic helper functions
################################################################################
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug("'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    for x in Settings:
        Domoticz.Debug("Setting:           " + str(x) + " - " + str(Settings[x]))

def UpdateDevice(Unit, nValue, sValue, TimedOut=0, AlwaysUpdate=False):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it
    if Unit in Devices:
        if Devices[Unit].nValue != nValue or Devices[Unit].sValue != sValue or Devices[Unit].TimedOut != TimedOut or AlwaysUpdate:
            Devices[Unit].Update(nValue=nValue, sValue=str(sValue), TimedOut=TimedOut)
            Domoticz.Debug("Update " + Devices[Unit].Name + ": " + str(nValue) + " - '" + str(sValue) + "' - " + str(TimedOut))

def DumpHTTPResponseToLog(httpDict):
    if isinstance(httpDict, dict):
        Domoticz.Debug("HTTP Details ("+str(len(httpDict))+"):")
        for x in httpDict:
            if isinstance(httpDict[x], dict):
                Domoticz.Debug("--->'"+x+" ("+str(len(httpDict[x]))+"):")
                for y in httpDict[x]:
                    Domoticz.Debug("------->'" + y + "':'" + str(httpDict[x][y]) + "'")
            else:
                Domoticz.Debug("--->'" + x + "':'" + str(httpDict[x]) + "'")

def UpdateDeviceOptions(Unit, Options={}):
    if Unit in Devices:
        Devices[Unit].Update(nValue=Devices[Unit].nValue, sValue=Devices[Unit].sValue, Options=Options)
        Domoticz.Debug("Update options " + Devices[Unit].Name + ": " + str(Options))


import json
import subprocess

def getData( url ):
    command = "curl"
    options =  "'" + url + "'"
    p = subprocess.Popen( command + " " + options, shell=True, stdout=subprocess.PIPE)
    p.wait()
    data, errors = p.communicate()
    if p.returncode != 0:
        Domoticz.Debug( "Request failed" )
    values = json.loads( data.decode( "utf-8", "ignore" ) )
    return values
