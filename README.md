# OpenAQ
This Domoticz plugin gets the air quality at your location from https://openaq.org. 
OpenAQ is collecting data in 64 different countries and always seeking to add more. They aggregate PM<sub>2.5</sub>, PM<sub>10</sub>, ozone (O<sub>3</sub>), sulfur dioxide (SO<sub>2</sub>), nitrogen dioxide (NO<sub>2</sub>), carbon monoxide (CO), and black carbon (BC) from real-time government and research grade sources.
The plugin scans the stations nearby your location and takes the data about all the pollutants which are closest to your location.

## Parameters
| Name       | Description                                                              |
| :---       | :---                                                                     |
| **Radius** | Radius in kilometers from your location defined in Settings. Default: 10 |

Check https://openaq.org/#/map to see if a source can be found at your location.

This plugin uses the latitude and longitude as specified in Domoticz Settings - System - Location.

## Devices
| Name                 | Description                                              |
| :---                 | :---                                                     |
| **BC**               | Black Carbon                                             |
| **CO**               | Carbon Monoxide                                          |
| **NO<sub>2</sub>**   | Nitrogen Dioxide                                         |
| **O<sub>3</sub>**    | Ozone                                                    |
| **PM<sub>10</sub>**  | Particulate matter less than 10 micrometers in diameter  |
| **PM<sub>2.5</sub>** | Particulate matter less than 2.5 micrometers in diameter |
| **SO<sub>2</sub>**   | Sulfur Dioxide                                           |
| **Info**             | Information, like nearest location, number of locations  |
| **Index**            | Air Quality Index                                        |

![OpenAQ](./images/Knipsel.PNG)

## Air Quality Index
This alert sensor indicates the quality of the air. The upper limits below are based on information from http://www.airqualitynow.eu/about_indices_definition.php

| Pollutant            | Very low |     Low  |    Medium |     High | Very high |
| :---                 |     ---: |     ---: |      ---: |     ---: |      ---: |
| **CO**               |     5000 |     7500 |     10000 |    20000 |   > 20000 |
| **NO<sub>2</sub>**   |       50 |      100 |       200 |      400 |     > 400 |
| **O<sub>3</sub>**    |       60 |      120 |       180 |      240 |     > 240 |
| **PM<sub>10</sub>**  |       25 |       50 |        90 |      180 |     > 180 |
| **PM<sub>2.5</sub>** |       15 |       30 |        55 |      110 |     > 110 |
| **SO<sub>2</sub>**   |       50 |      100 |       350 |      500 |     > 500 |
|                      |     gray |    green |    yellow |   orange |       red |