#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  OpenAQ Python Plugin
#
# Author: Xorfor
# Maintainer: Waltervl
#
# Air Quality Index based on:
#   http://www.airqualitynow.eu/about_indices_definition.php

"""
<plugin key="xfr_openaq" name="OpenAQ" author="Xorfor, Waltervl" version="3.1" wikilink="https://github.com/waltervl/Domoticz-OpenAQ-Plugin" externallink="https://openaq.org/">
    <params>
        <param field="Mode1" label="Radius (km)" width="75px" default="10" required="true"/>
        <param field="Mode2" label="OpenAQ API-KEY" width="175px" default="" required="true"/>
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
import time


class BasePlugin:

    __HEARTBEATS2MIN = 6
    __MINUTES = 60  # 1 hour or use a parameter

    __API_CONN = "openaq"
    __API_ENDPOINT = "api.openaq.org"
    __API_URL = "/v2/latest?coordinates={},{}&radius={}&order_by=location"

    __LEVELS = {0: "Very low", 1: "Low", 2: "Medium", 3: "High", 4: "Very high"}
    __VALUES = {
        # id: [date, value, unit, name, units, low, medium, high, very high]
        "bc": [None, None, 1, "BC", None, None, None, None, None],
        "co": [None, None, 2, "CO", None, 5000, 7500, 10000, 20000],
        "no2": [None, None, 3, "NO<sub>2</sub>", None, 50, 100, 200, 400],
        "o3": [None, None, 4, "O<sub>3</sub>", None, 60, 120, 180, 240],
        "pm10": [None, None, 5, "PM<sub>10</sub>", None, 25, 50, 90, 180],
        "pm25": [None, None, 6, "PM<sub>2.5</sub>", None, 15, 30, 55, 110],
        "so2": [None, None, 7, "SO<sub>2</sub>", None, 50, 100, 350, 500],
    }

    def __init__(self):
        self.__runAgain = 0
        self.__radius = 0
        self.__url = ""
        self.__conn = None

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
        Domoticz.Debug("Image created. ID: {}".format(image))
        # Validation of parameters
        self.__radius = int(Parameters["Mode1"])
        if self.__radius < 0:
            self.__radius = 0
        self.__radius *= 1000  # Convert km to m
        loc = Settings["Location"].split(";")
        lat = loc[0]
        lon = loc[1]
        if lat is None or lon is None:
            Domoticz.Error("Unable to parse coordinates")
            return False
        self.__url = self.__API_URL.format(lat, lon, str(self.__radius))
        Domoticz.Debug("url: {}".format(self.__url))
        # get API KEY
        self.__API_KEY = Parameters["Mode2"]
        if self.__API_KEY is "":
            Domoticz.Error("Unable to read openaq API-KEY from settings")
            return False
        
        # Create devices
        # if len(Devices) == 0:
        for id in self.__VALUES:
            if self.__VALUES[id][2] not in Devices:
                self.__VALUES[id][0] = None
                self.__VALUES[id][1] = None
                Domoticz.Device(
                    Unit=self.__VALUES[id][2],
                    Name=self.__VALUES[id][3],
                    TypeName="Custom",
                    Options={"Custom": "0;µg/m³"},
                    Image=image,
                    Used=1,
                ).Create()
        #
        unit = len(self.__VALUES)
        #
        unit += 1
        if unit not in Devices:
            Domoticz.Device(Unit=unit, Name="Info", TypeName="Text", Used=1).Create()
        #
        unit += 1
        if unit not in Devices:
            Domoticz.Device(
                Unit=unit,
                Name="Pollutants",
                Type=243,
                Subtype=22,
                Options={},
                Used=1,
            ).Create()
        #
        unit += 1
        if unit not in Devices:
            Domoticz.Device(
                Unit=unit,
                Name="Air Quality Index",
                TypeName="Custom",
                Options={"Custom": "0;"},
                Image=image,
                Used=1,
            ).Create()
        #
        config_2_log()
        # Setup connection
        self.__conn = Domoticz.Connection(
            Name=self.__API_CONN,
            Transport="TCP/IP",
            Protocol="HTTPS",
            Address=self.__API_ENDPOINT,
            Port="443",
        )
        self.__conn.Connect()

    def onStop(self):
        Domoticz.Debug("onStop")
        for id in self.__VALUES:
            self.__VALUES[id][0] = None
            self.__VALUES[id][1] = None

    def onConnect(self, Connection, Status, Description):
        Domoticz.Debug(
            "onConnect: {}, {}, {}".format(Connection.Name, Status, Description)
        )
        if Connection.Name == self.__API_CONN:
            if Status == 0:
                sendData = {
                    "Verb": "GET",
                    "URL": self.__url,
                    "Headers": {
                        "Host": self.__API_ENDPOINT,
                        "User-Agent": "Domoticz/1.0",
                        "X-API-Key": self.__API_KEY,
                    },
                }
                Connection.Send(sendData)

    def onMessage(self, Connection, Data):
        Domoticz.Debug("onMessage: {}, {}".format(Connection.Name, Data))
        status = int(Data["Status"])
        if Connection.Name == self.__API_CONN:
            if status == 200:
                values = json.loads(Data["Data"].decode("utf-8", "ignore"))
                # Get most recent value from each parameter. Data already ordered by distance, so check dates.
                locations = values["results"]
                totLocations = len(locations)
                totMeasurements = 0
                Domoticz.Debug("Locations found: {}".format(totLocations))
                for location in locations:
                    measurements = location["measurements"]
                    numberOfMeasurements = len(measurements)
                    totMeasurements += numberOfMeasurements
                    Domoticz.Debug(
                        "Location {} - measurements: {}".format(
                            location["location"], numberOfMeasurements
                        )
                    )
                    for measurement in measurements:
                        Domoticz.Debug(
                            "{} ... {}: {} {}".format(
                                measurement["lastUpdated"],
                                measurement["parameter"],
                                measurement["value"],
                                measurement["unit"],
                            )
                        )
                        lastUpdated = measurement["lastUpdated"][0:19]
                        parameter = measurement["parameter"]
                        value = float(measurement["value"])
                        unit = measurement["unit"]
                        Domoticz.Debug("lastUpdated: {}".format(lastUpdated))
                        Domoticz.Debug("parameter: {}".format(parameter))
                        Domoticz.Debug("value: {}".format(value))
                        Domoticz.Debug("unit: {}".format(unit))
                        # Fix for Python bug
                        try:
                            t = datetime.strptime(lastUpdated, "%Y-%m-%dT%H:%M:%S")
                        except TypeError:
                            t = datetime.fromtimestamp(
                                time.mktime(
                                    time.strptime(
                                        lastUpdated,
                                        "%Y-%m-%dT%H:%M:%S",
                                    )
                                )
                            )
                        # Skip values like '-999'
                        if value > 0.0 and parameter in self.__VALUES:
                            if self.__VALUES[parameter][1] is None:
                                # First time value found. Always get this one.
                                self.__VALUES[parameter][0] = t
                                self.__VALUES[parameter][1] = value
                                self.__VALUES[parameter][4] = unit
                            else:
                                # Is this value more actual?
                                if t > self.__VALUES[parameter][0]:
                                    # Domoticz.Debug("More recent date!!!")
                                    self.__VALUES[parameter][0] = t
                                    self.__VALUES[parameter][1] = value
                                    self.__VALUES[parameter][4] = unit
                # Domoticz.Debug("Results: {}".format(self.__VALUES))
                # Update the devices
                level = 0
                txt = ""
                for id in self.__VALUES:
                    if self.__VALUES[id][1] is not None:
                        update_device_options(
                            self.__VALUES[id][2],
                            {"Custom": "0;{}".format(self.__VALUES[id][4])},
                        )
                        update_device(
                            self.__VALUES[id][2],
                            int(self.__VALUES[id][1]),
                            str(round(self.__VALUES[id][1], 1)),
                        )
                        # Check warning levels of this sensor
                        offset = 4
                        for i in range(4, 0, -1):
                            if (  # Warning level available for this sensor
                                self.__VALUES[id][offset + i] is not None
                                # Value higher then upper level
                                and self.__VALUES[id][1] > self.__VALUES[id][offset + i]
                            ):
                                Domoticz.Debug(
                                    "{}: {} > {}?".format(
                                        self.__VALUES[id][2],
                                        self.__VALUES[id][1],
                                        self.__VALUES[id][offset + i],
                                    )
                                )
                                # level higher then previous value?
                                if i > level:
                                    level = i
                                    # Add pollutant to the warning text
                                    txt += self.__VALUES[id][3] + " "
                            else:
                                exit
                # Info
                unit = len(self.__VALUES)
                unit += 1
                stat = "Number of stations: {}<br/>Measurements: {}".format(
                    totLocations, totMeasurements
                )
                update_device(unit, 0, stat)
                # Alert
                Domoticz.Debug("Level: {}".format(level))
                unit += 1
                if level == 0:
                    update_device(unit, level, "No alert")
                else:
                    update_device(unit, level, "{}".format(txt))
                # Index
                unit += 1
                update_device(unit, level, "{}".format(level))
            else:
                Domoticz.Error(
                    "{} returned a status: {}".format(Connection.Name, status)
                )

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("onCommand: {}, {}, {}, {}".format(Unit, Command, Level, Hue))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug(
            "onNotification: {}, {}, {}, {}, {}, {}, {}".format(
                Name, Subject, Text, Status, Priority, Sound, ImageFile
            )
        )

    def onDisconnect(self, Connection):
        Domoticz.Debug("onDisconnect: {}".format(Connection.Name))

    def onHeartbeat(self):
        Domoticz.Debug("onHeartbeat")
        Domoticz.Debug("url: {}".format(self.__url))
        # Live
        self.__runAgain -= 1
        if self.__runAgain <= 0:
            if self.__conn.Connecting() or self.__conn.Connected():
                Domoticz.Debug("onHeartbeat ({}): is alive".format(self.__conn.Name))
                sendData = {
                    "Verb": "GET",
                    "URL": self.__url,
                    "Headers": {
                        "Host": self.__API_ENDPOINT,
                        "User-Agent": "Domoticz/1.0",
                        "X-API-Key": self.__API_KEY,
                    },
                }
                self.__conn.Send(sendData)
            else:
                self.__conn.Connect()
            self.__runAgain = self.__HEARTBEATS2MIN * self.__MINUTES
        Domoticz.Debug(
            "onHeartbeat ({}): {} heartbeats".format(self.__conn.Name, self.__runAgain)
        )


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
def config_2_log():
    # Show parameters
    Domoticz.Debug("Parameters count.....: {}".format(len(Parameters)))
    for x in Parameters:
        Domoticz.Debug("Parameter '{}'...: '{}'".format(x, Parameters[x]))
    # Show settings
    Domoticz.Debug("Settings count...: {}".format(len(Settings)))
    for x in Settings:
        Domoticz.Debug("Setting '{}'...: '{}'".format(x, Settings[x]))
    # Show images
    Domoticz.Debug("Image count..........: {}".format(len(Images)))
    for x in Images:
        Domoticz.Debug("Image '{}'...': '{}'".format(x, Images[x]))
    # Show devices
    Domoticz.Debug("Device count.........: {}".format(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device...............: {} - {}".format(x, Devices[x]))
        Domoticz.Debug("Device Idx...........: {}".format(Devices[x].ID))
        Domoticz.Debug(
            "Device Type..........: {} / {}".format(Devices[x].Type, Devices[x].SubType)
        )
        Domoticz.Debug("Device Name..........: '{}'".format(Devices[x].Name))
        Domoticz.Debug("Device nValue........: {}".format(Devices[x].nValue))
        Domoticz.Debug("Device sValue........: '{}'".format(Devices[x].sValue))
        Domoticz.Debug("Device Options.......: '{}'".format(Devices[x].Options))
        Domoticz.Debug("Device Used..........: {}".format(Devices[x].Used))
        Domoticz.Debug("Device ID............: '{}'".format(Devices[x].DeviceID))
        Domoticz.Debug("Device LastLevel.....: {}".format(Devices[x].LastLevel))
        Domoticz.Debug("Device Image.........: {}".format(Devices[x].Image))


def update_device(Unit, nValue, sValue, TimedOut=0, AlwaysUpdate=False):
    if Unit in Devices:
        if (
            Devices[Unit].nValue != nValue
            or Devices[Unit].sValue != sValue
            or Devices[Unit].TimedOut != TimedOut
            or AlwaysUpdate
        ):
            Devices[Unit].Update(nValue=nValue, sValue=str(sValue), TimedOut=TimedOut)
            Domoticz.Debug(
                "Update {}: {} - '{}'".format(Devices[Unit].Name, nValue, sValue)
            )


def response_2_log(response):
    if isinstance(response, dict):
        Domoticz.Debug("Response: ({})".format(len(response)))
        for x in response:
            if isinstance(response[x], dict):
                Domoticz.Debug(".... {} ({})".format(x, len(response[x])))
                for y in response[x]:
                    Domoticz.Debug("........ '{}': '{}'".format(y, response[x][y]))
            else:
                Domoticz.Debug(".... '{}': '{}'".format(x, response[x]))


def update_device_options(Unit, Options={}):
    if Unit in Devices:
        Devices[Unit].Update(
            nValue=Devices[Unit].nValue, sValue=Devices[Unit].sValue, Options=Options
        )
        Domoticz.Debug("Update options {}: {}".format(Devices[Unit].Name, Options))
