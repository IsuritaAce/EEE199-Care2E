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
This system requires certain software/dependencies as detailed below. These software (aside from Arduino IDE) are mainly for Linux-based operating systems.

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
This software is used to decode data from WH31E and WH40, or the general sensors. The installation guide can be found in the [rtl-433 github page](https://github.com/merbanan/rtl_433/blob/master/docs/BUILDING.md) by user merbanan. SoapySDR and/or RTL-SDR must first be installed in order for the SDRs to use it.
## SDRangel
This software is used for decoding LoRa signals. The installation process can be found in the [wiki page](https://github.com/f4exb/sdrangel/wiki/Compile-from-source-in-Linux) of the SDRangel github page made by user f4exb.

### NOTES
- Not all hardware dependencies are required, select only the ones that are needed (for this study, only ADALM-Pluto is needed for SDRangel) and reflect the changes in the final build command, accordingly.
- SDRangel requires the `powerdown` attribute of Pluto to be `0` in order for it to be used as a receiver. This can be done by using the `iio_attr -u ip:192.168.2.1 -c ad9361-phy altvoltage0 powerdown 0` command.
## Arduino IDE
This is used for coding the LoRa transmitters.

# Recommendations
- Centralize all stations into one radio via implementing a version of rtldavis that is compatible with ADALM-Pluto, i.e., create a custom program.
