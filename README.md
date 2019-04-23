# OpenAQ
This Domoticz plugin gets the air quality at your location from https://openaq.org. 
OpenAQ is collecting data in 64 different countries and always seeking to add more. They aggregate PM2.5, PM10, ozone (O3), sulfur dioxide (SO2), nitrogen dioxide (NO2), carbon monoxide (CO), and black carbon (BC) from real-time government and research grade sources.

## Parameters
| Name       | Description                                                              |
| :---       | :---                                                                     |
| **Radius** | Radius in kilometers from your location defined in Settings. Default: 10 |

Check https://openaq.org/#/map to see whether a source can be found at your location.

This plugin uses the latitude and longitude as specified in Domoticz Settings - System - Location.

## Devices
| Name       | Description                                              |
| :---       | :---                                                     |
| **BC**     | Black Carbon                                             |
| **CO**     | Carbon Monoxide                                          |
| **NO2**    | Nitrogen Dioxide                                         |
| **O3**     | Ozone                                                    |
| **PM10**   | Particulate matter less than 10 micrometers in diameter  |
| **PM2.5**  | Particulate matter less than 2.5 micrometers in diameter |
| **SO2**    | Sulfur Dioxide                                           |
| **Info**   | Information, like nearest location, number of locations  |

![OpenAQ](https://github.com/Xorfor/Domoticz-OpenAQ-Plugin/blob/master/images/Knipsel.PNG)
