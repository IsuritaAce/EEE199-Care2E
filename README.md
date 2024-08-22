# Development of Time-division Multiplexing Scanner for Weather Stations of Different Protocols Using Software Defined Radio
A weather-monitoring system has been developed such that it receives data from multiple weather stations. It employs two receivers, one that is dedicated for a specific weather station, while the other switches between two other weather stations that have different frequencies and protocols.

Most of the functionality of the system, in particular the **switching**, **rtldavis activation**, **storage of data from Davis stations**, and **uploading of data to the CARE database**, runs on python code.

# Radio Receivers
- ADALM Pluto
- RTL-SDR
# Gateway
- Raspberry Pi 4 (RPi 4)
# Weather Stations
- Davis Vantage Vue
- General Sensors
  - WH31E
  - WH40
- LoRa-based Stations
# Software Dependencies
- SDR drivers
- rtldavis
- rtl_433
- SDRangel
- Arduino IDE
