# Development of Time-division Multiplexing Scanner for Weather Stations of Different Protocols Using Software Defined Radio
A weather-monitoring system has been developed such that it receives data from multiple weather stations. It employs two software-defined radios (SDRs) acting as receivers, one that is dedicated for a specific weather station, while the other switches between two other weather stations that have different frequencies and protocols.

<img src="https://github.com/user-attachments/assets/933e7a29-1867-42ee-9f0f-0489bac95514" height="300">

# Software Functionality
Most of the system runs on python code. The particular functionality are the following:
1. Switching between rtl-433 (General sensors) and SDRangel (LoRa-based stations)
2. Rtldavis activation
3. Storage of data from Davis stations
4. Uploading of data to the CARE database

# Software Dependencies
This system requires certain software/dependencies as described below:

## SDR drivers
In order for the Raspberry Pi to communicate with the SDRs, their respective drivers must be installed first. For **RTL-SDR**, installation procedure for Linux systems can be found [here](https://www.rtl-sdr.com/v4/), while for the **ADALM-Pluto**, its procedure can be found [here](https://wiki.analog.com/university/tools/pluto/drivers/linux) or simply access the `info.html` file when the Pluto is plugged in (the latter is more reliable).

### NOTES

**RTL-SDR**
- Successful driver installation can be tested using the `rtl_test` command.
- If using Raspberry Pi 4, invoking multiple (at least 2) `rtl_test` may cause an error. Solution to this is either:
  -   use a Raspberry Pi 3, since the error does not occur for that model
  -   unplug and replug the RTL-SDR device

**ADALM-Pluto**
- the `libiio` package must also be installed
- successful installation can be verified via `iio_info -s`
## Rtldavis
This is the software used for decoding Davis Vantage Vue stations. Installation process is detailed by user guidocini in [their guide](https://www.instructables.com/Davis-Van-ISS-Weather-Station-With-Raspbe/). However, for the purposes of this study, only steps 2-4 in the guide are important.
## Rtl_433

## SDRangel
## Arduino IDE
