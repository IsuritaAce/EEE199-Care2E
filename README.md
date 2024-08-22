# Development of Time-division Multiplexing Scanner for Weather Stations of Different Protocols Using Software Defined Radio
A weather-monitoring system has been developed such that it receives data from multiple weather stations. It employs two receivers, one that is dedicated for a specific weather station, while the other switches between two other weather stations that have different frequencies and protocols.

<img src="https://github.com/user-attachments/assets/933e7a29-1867-42ee-9f0f-0489bac95514" height="300">

# Software Functionality
Most of the system runs on python code. The particular functionality are the following:
1. Switching between rtl-433 (General sensors) and SDRangel (LoRa-based stations)
2. Rtldavis activation
3. Storage of data from Davis stations
4. Uploading of data to the CARE database

# Software Dependencies
This system requires numerous software as described below:

## SDR drivers
## rtldavis
## rtl_433
## SDRangel
## Arduino IDE
