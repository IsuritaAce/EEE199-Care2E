#!/usr/bin/env python3

import subprocess
import time
from multiprocessing import Process
import math
import json
from datetime import date

# START of rtldavis software automation

# Interpolate(), calc_wind_speed_ec(), calculate_thermistor_temp(),
# and parse_packet() copied from weewx-rtldavis
# https://github.com/lheijst/weewx-rtldavis/blob/master/bin/user/rtldavis.py

def interpolate(rx0, rx1,
                ry0, ry1,
                x0, x1,
                y0, y1,
                x, y):

    print("rx0=%s, rx1=%s, ry0=%s, ry1=%s, x0=%s, x1=%s, y0=%s, y1=%s, x=%s, y=%s" %
              (rx0, rx1, ry0, ry1, x0, x1, y0, y1, x, y))

    if rx0 == rx1:
        return y + x0 + (y - ry0) / float(ry1 - ry0) * (y1 - y0)

    if ry0 == ry1:
        return y + y0 + (x - rx0) / float(rx1 - rx0) * (x1 - x0)

    dy0 = x0 + (y - ry0) / float(ry1 - ry0) * (y0 - x0)
    dy1 = x1 + (y - ry0) / float(ry1 - ry0) * (y1 - x1)

    return y + dy0 + (x - rx0) / float(rx1 - rx0) * (dy1 - dy0)

def calc_wind_speed_ec(raw_mph, raw_angle):

    # some sanitization: no corrections needed under 3 and no values exist
    # above 150 mph
    if raw_mph < 3 or raw_mph > 150:
        return raw_mph

    # Error correction values for
    #  [ 1..29 by 1, 30..150 by 5 raw mph ]
    #   x
    #  [ 1, 4, 8..124 by 4, 127, 128 raw degrees ]
    #
    # Extracted from a Davis Weather Envoy using a DIY transmitter to
    # transmit raw values and logging LOOP packets.
    # first row: raw angles;
    # first column: raw speed;
    # cells: values provided in response to raw data by the Envoy;
    # [0][0] is filler
    windtab = [
        [0, 1, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60, 64, 68, 72, 76, 80, 84, 88, 92, 96, 100, 104, 108, 112, 116, 120, 124, 127, 128],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0],
        [4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0],
        [5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0],
        [6, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 0, 0],
        [7, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 1, 0, 0],
        [8, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 1, 0, 0],
        [9, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 1, 0, 0],
        [10, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 1, 0, 0],
        [11, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 1, 0, 0],
        [12, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 1, 0, 0],
        [13, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 3, 3, 1, 0, 0],
        [14, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 3, 3, 1, 0, 0],
        [15, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 3, 3, 1, 0, 0],
        [16, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 3, 3, 1, 0, 0],
        [17, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 3, 3, 1, 0, 0],
        [18, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 3, 3, 1, 0, 0],
        [19, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 4, 4, 1, 0, 0],
        [20, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 3, 4, 4, 2, 0, 0],
        [21, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 3, 4, 4, 2, 0, 0],
        [22, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 3, 4, 4, 2, 0, 0],
        [23, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 3, 4, 4, 2, 0, 0],
        [24, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 2, 3, 4, 4, 2, 0, 0],
        [25, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 2, 3, 4, 4, 2, 0, 0],
        [26, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 2, 3, 5, 4, 2, 0, 0],
        [27, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 2, 3, 5, 5, 2, 0, 0],
        [28, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 2, 3, 5, 5, 2, 0, 0],
        [29, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 2, 3, 5, 5, 2, 0, 0],
        [30, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 2, 3, 5, 5, 2, 0, 0],
        [35, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 2, 4, 6, 5, 2, 0, -1],
        [40, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 2, 4, 6, 6, 2, 0, -1],
        [45, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 2, 4, 7, 6, 2, -1, -1],
        [50, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 2, 5, 7, 7, 2, -1, -2],
        [55, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 2, 5, 8, 7, 2, -1, -2],
        [60, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 2, 5, 8, 8, 2, -1, -2],
        [65, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 2, 5, 9, 8, 2, -2, -3],
        [70, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 0, 2, 5, 9, 9, 2, -2, -3],
        [75, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 0, 2, 6, 10, 9, 2, -2, -3],
        [80, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 0, 2, 6, 10, 10, 2, -2, -3],
        [85, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 0, 2, 7, 11, 11, 2, -3, -4],
        [90, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 2, 7, 12, 11, 2, -3, -4],
        [95, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 2, 3, 2, 2, 2, 1, 1, 1, 1, 2, 7, 12, 12, 3, -3, -4],
        [100, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 3, 3, 2, 2, 2, 1, 1, 1, 1, 2, 8, 13, 12, 3, -3, -4],
        [105, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 3, 3, 3, 3, 3, 2, 2, 2, 1, 1, 1, 2, 8, 13, 13, 3, -3, -4],
        [110, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 3, 3, 3, 3, 3, 2, 2, 2, 1, 1, 1, 2, 8, 14, 14, 3, -3, -5],
        [115, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 2, 3, 3, 3, 3, 3, 2, 2, 2, 1, 1, 1, 2, 9, 15, 14, 3, -3, -5],
        [120, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 2, 3, 3, 3, 3, 3, 2, 2, 2, 1, 1, 1, 3, 9, 15, 15, 3, -4, -5],
        [125, 1, 1, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 3, 3, 3, 3, 3, 2, 2, 1, 1, 1, 3, 10, 16, 16, 3, -4, -5],
        [130, 1, 1, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 3, 3, 3, 3, 3, 2, 2, 2, 1, 1, 3, 10, 17, 16, 3, -4, -6],
        [135, 1, 2, 2, 1, 1, 0, 0, 0, -1, 0, 0, 1, 1, 2, 2, 3, 3, 3, 3, 4, 3, 3, 2, 2, 2, 1, 1, 3, 10, 17, 17, 4, -4, -6],
        [140, 1, 2, 2, 1, 1, 0, 0, 0, -1, 0, 0, 1, 1, 2, 2, 3, 3, 3, 4, 4, 3, 3, 2, 2, 2, 1, 1, 3, 11, 18, 17, 4, -4, -6],
        [145, 2, 2, 2, 1, 1, 0, 0, 0, -1, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 4, 3, 3, 3, 2, 2, 1, 1, 3, 11, 19, 18, 4, -4, -6],
        [150, 2, 2, 2, 1, 1, 0, 0, -1, -1, 0, 0, 1, 1, 2, 3, 3, 4, 4, 4, 4, 4, 3, 3, 2, 2, 1, 1, 3, 12, 19, 19, 4, -4, -6]
    ]

    # EC is symmetric between W/E (90/270°) - probably a wrong assumption,
    # table needs to be redone for 0-360°
    if raw_angle > 128:
        raw_angle = 256 - raw_angle

    s0 = a0 = 1

    while windtab[s0][0] < raw_mph:
        s0 += 1
    while windtab[0][a0] < raw_angle:
        a0 += 1

    if windtab[s0][0] == raw_mph:
        s1 = s0
    else:
        if s0 > 1:
            s0 -= 1
        s1 = len(windtab) - 1 if s0 == len(windtab) - 1 else s0 + 1

    if windtab[0][a0] == raw_angle:
        a1 = a0
    else:
        if a0 > 1:
            a0 -= 1
        a1 = len(windtab[0]) - 2 if a0 == len(windtab) - 1 else a0 + 1

    if s0 == s1 and a0 == a1:
        return raw_mph + windtab[s0][a0]
    else:
        return interpolate(windtab[0][a0], windtab[0][a1],
                                      windtab[s0][0], windtab[s1][0],
                                      windtab[s0][a0], windtab[s0][a1],
                                      windtab[s1][a0], windtab[s1][a1],
                                      raw_angle, raw_mph)

# Simple bilinear interpolation
#
#  a0         a1 <-- fixed raw angles
#  x0---------x1 s0
#  |          |
#  |          |
#  |      * <-|-- raw input angle, raw speed value (x, y)
#  |          |
#  y0---------y1 s1
#                ^
#                \__ speed: measured raw / correction values

def calculate_thermistor_temp(temp_raw):
    """ Decode the raw thermistor temperature, then calculate the actual
    thermistor temperature and the leaf_soil potential, using Davis' formulas.
    see: https://github.com/cmatteri/CC1101-Weather-Receiver/wiki/Soil-Moisture-Station-Protocol
    :param temp_raw: raw value from sensor for leaf wetness and soil moisture
    """

    # Convert temp_raw to a resistance (R) in kiloOhms
    a = 18.81099
    b = 0.0009988027
    r = a / (1.0 / temp_raw - b) / 1000 # k ohms

    # Steinhart-Hart parameters
    s1 = 0.002783573
    s2 = 0.0002509406
    try:
        thermistor_temp = 1 / (s1 + s2 * math.log(r)) - 273
        print('r (k ohm) %s temp_raw %s thermistor_temp %s' %
                  (r, temp_raw, thermistor_temp))
        return thermistor_temp
    except ValueError as e:
        print('thermistor_temp failed for temp_raw %s r (k ohm) %s'
               'error: %s' % (temp_raw, r, e))
    return 24
    
def parse_packet(msg_type, pkt):
    data = {}
    
    # Each data packet of iss or anemometer contains wind info,
    # but it is only valid when received from the channel with
    # the anemometer connected
    # message examples:
    # 51 06 B2 FF 73 00 76 61
    # E0 00 00 4E 05 00 72 61 (no sensor)
    
    # received pkt is in hexadecimal, type str
    # hence the int(pkt[n], 16) syntax, which converts hexadecimal into integer
    wind_speed_raw = int(pkt[1], 16)
    wind_dir_raw = int(pkt[2], 16)
    if not(wind_speed_raw == 0 and wind_dir_raw == 0):
        """ The elder Vantage Pro and Pro2 stations measured
        the wind direction with a potentiometer. This type has
        a fairly big dead band around the North. The Vantage
        Vue station uses a hall effect device to measure the
        wind direction. This type has a much smaller dead band,
        so there are two different formulas for calculating
        the wind direction. To be able to select the right
        formula the Vantage type must be known.
        For now we use the traditional 'pro' formula for all
        wind directions.
        """
        print("wind_speed_raw=%03x wind_dir_raw=0x%03x" %
                  (wind_speed_raw, wind_dir_raw))

        # Vantage Pro and Pro2
        if wind_dir_raw == 0:
            wind_dir_pro = 5.0
        elif wind_dir_raw == 255:
            wind_dir_pro = 355.0
        else:
            wind_dir_pro = 9.0 + (wind_dir_raw - 1) * 342.0 / 253.0

            # Vantage Vue
            wind_dir_vue = wind_dir_raw * 1.40625 + 0.3

            # wind error correction is by raw byte values
            wind_speed_ec = round(calc_wind_speed_ec(wind_speed_raw, wind_dir_raw))

            data['wind_dir'] = wind_dir_pro
            data['wind_speed'] = wind_speed_ec
            print("WS=%s WD=%s WS_raw=%s WS_ec=%s WD_raw=%s WD_pro=%s WD_vue=%s" %
                      (data['wind_speed'], data['wind_dir'],
                       wind_speed_raw, wind_speed_ec,
                       wind_dir_raw if wind_dir_raw <= 180 else 360 - wind_dir_raw,
                       wind_dir_pro, wind_dir_vue))

    # data from both iss sensors and extra sensors on
    # Anemometer Transport Kit
    
    if msg_type == 3:
        pass
        
    elif msg_type == 5:
        time_between_tips_raw = ((int(pkt[4], 16) & 0x30) << 4) + int(pkt[3], 16)
        print("time_between_tips_raw=%03x (%s)" %
              (time_between_tips_raw, time_between_tips_raw))
        rain_rate = None
        
        if time_between_tips_raw == 0x3ff:
            # no rain
            rain_rate = 0
            print("No rain=%s mm/h" % rain_rate)
            
        elif int(pkt[4], 16) & 0x40 == 0:
            # heavy rain
            
            time_between_tips = time_between_tips_raw / 16.0
            rain_rate = 3600.0 / time_between_tips_raw * 0.2 # default is 0.2, can be 0.254
            print("Heavy rain=%s mm/h, time_between_tips= %s s" % (rain_rate, time_between_tips))
            
        else:
            # light rain
            
            time_between_tips = time_between_tips_raw
            rain_rate = 3600.0 / time_between_tips_raw * 0.2 # default is 0.2, can be 0.254
            print("Light rain=%s mm/h, Time between tips=%s s" % (rain_rate, time_between_tips))
            
        data['rain_rate'] = rain_rate
            
    elif msg_type == 8:
        # outside temperature
        # message examples:
        # 80 00 00 33 8D 00 25 11 (digital temp)
    
        # 81 00 00 59 45 00 A3 E6 (analog temp)
        # 81 00 DB FF C3 00 AB F8 (no sensor)
        
        temp_raw = (int(pkt[3], 16) << 4) + (int(pkt[4], 16) >> 4)  # 12-bits temp value
        if temp_raw != 0xFFC:
            if int(pkt[4], 16) & 0x8:
                # digital temp sensor
                temp_f = temp_raw / 10.0
                temp_c = (temp_f - 32) * 5 / 9 # C
                print("Digital temp_raw=0x%03x temp_f=%s temp_c=%s"
                          % (temp_raw, temp_f, temp_c))
            else:
                # analog sensor (thermistor)
                temp_raw /= 4  # 10-bits temp value
                temp_c = calculate_thermistor_temp(temp_raw)
                print("thermistor temp_raw=%s temp_c=%s"
                          % (temp_raw, temp_c))
        data['temperature'] = temp_c
                
    elif msg_type == 9:
        # 10-min average wind gust
        # message examples:
        # 91 00 DB 00 03 0E 89 85
        # 90 00 00 00 05 00 31 51 (no sensor)
        gust_raw = int(pkt[3], 16)  # mph
        gust_index_raw = int(pkt[5], 16) >> 4
        print("W10=%s gust_index_raw=%s" %
                  (gust_raw, gust_index_raw))
        
        data['wind_gust'] = gust_raw
            
    elif msg_type == 0xA:
        # outside humidity
        # message examples:
        # A0 00 00 C9 3D 00 2A 87 (digital sensor, variant a)
        # A0 01 3A 80 3B 00 ED 0E (digital sensor, variant b)
        # A0 01 41 7F 39 00 18 65 (digital sensor, variant c)
        # A0 00 00 22 85 00 ED E3 (analog sensor)
        # A1 00 DB 00 03 00 47 C7 (no sensor)
        humidity_raw = ((int(pkt[4], 16) >> 4) << 8) + int(pkt[3], 16)
        if humidity_raw != 0:
            if int(pkt[4], 16) & 0x08 == 0x8:
                # digital sensor
                humidity = humidity_raw / 10.0
            else:
                # analog sensor (pkt[4] & 0x0f == 0x5)
                humidity = humidity_raw * -0.301 + 710.23       
            print("humidity_raw=0x%03x value=%s" %
                              (humidity_raw, humidity))
            
        data['humidity'] = humidity
    else:
        pass
    return data

def decode_store_davis():
    """
    Local storage for Davis stations data.
    
    Uses subprocess module to extract the data from the command terminal.

    Returns
    -------
    None.

    """
    # Define the command to execute
    command = "/home/sdr/work/bin/rtldavis -tr 6 -tf US"

    # Open a file to store the output continuously
    output_filename = "davis_deploy7_Aug08.json"
    #filterout_filename = 'filter.log'

    # Define keywords to filter lines by
    keywords = ['msg.ID=1', 'msg.ID=2']
    
    missed = 0
    
    while True:
        print("Receiving from Davis Vantage Vue Weather Stations...")
        time.sleep(3)
        
        try:
            # Save the contents of the file
            listObj = []
            with open(output_filename, "r") as f:
                for line in f:
                    if line == {} or line == None or line =='\n':
                        pass
                    else:
                        local_data = json.loads(line)
                        listObj.append(json.dumps(local_data))
                      
            with open(output_filename, "w") as f:
                # Execute the command using subprocess and capture stdout
                process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True)
                
                for line in listObj:
                    if line == listObj[0]:
                        f.write(line)        # Append data 
                        f.flush()            # Ensure data is written to file immediately
                    else:
                        f.seek(0, 2)
                        f.write('\n')        # Write newline
                        f.write(line)        # Append data 
                        f.flush()            # Ensure data is written to file immediately

                # Continuously read from terminal and write into output file
                while True:
                    # Temporary Storage for New Data to Local Database
                    stored_data = {}
                    line = process.stdout.readline()
                    if not line:
                        break
                    if 'packet missed' in line:
                        print(line, end="")  # print if missed packets
                        missed += 1
                        print(f'{missed} Davis packets were missed.')
                    
                    if any(keyword in line for keyword in keywords):
                        
                        # Split the line into parts (separated by spaces)
                        data = line.split()
                        
                        # Specify Date and Time
                        timestamp = data[0]
                        stored_data['time'] = date.today().strftime("%Y-%m-%d") + " " + timestamp
                        
                        # Specify ID
                        ID = data[-1]
                        stored_data['ID'] = int(ID[-1])
                        
                        # Specify Data Packet
                        data_packet = data[1]
                        #print(data_packet)
                        if len(data_packet) == 16:
                            i = 0
                            pkt = [0]*8
                            while i < len(pkt):
                                # ihiwalay yung packet into bytes
                                pkt[i] = data_packet[2*i]+data_packet[2*i+1]
                                i += 1
                                
                        print("Extracted Data")
                                
                        msg_type = (int(pkt[0], 16) >> 4) & 0xF
                        actual_data = parse_packet(msg_type, pkt)
                        
                        
                        for parameter in actual_data:
                            stored_data[parameter] = actual_data[parameter]
                        
                        print(stored_data)
                        
                        print("Appending data into file")
                        json_data = json.dumps(stored_data)
                        
                        print(json_data)
                        
                        f.seek(0, 2)
                        f.write('\n')        # Write newline
                        f.write(json_data)   # Append data 
                        f.flush()            # Ensure data is written to file immediately

        except FileNotFoundError:
            with open(output_filename, "w") as f:
                pass

# END of rtldavis software automation

def rtl433_automate():
    """
    Run for 65 seconds, then terminate
    WH40 Update Interval: 49sec
    WH31E Update Interval: 1min 1sec or 61sec

    Returns
    -------
    None.

    """   
    
    print("RTL_433 Start-up")

    rtl_433 = subprocess.Popen(["rtl_433", "-d", "", "-f", "915000000", "-s", "1000k", "-g", "60", "-F", "json:genws_data.json", "-F", "kv", "-R", "113"])
    
    # -d "": selects ADALM-Pluto
    # -f 915000000: tunes to 915 MHz frequency
    # -s 1000k: set sample rate to 1000k (avoid errors for ADALM-Pluto (v0.30 firmware))
    # -g 60: set Rx gain to 60, arbitrary selection from 0-70
    # -F json:genws_data.json: save data to json file under genws_data.json
    # -R 113: decode only WH31E and WH40 protocols
    
    print("Decoding...")
    time.sleep(65)
    rtl_433.terminate()
    print("RTL_433 has been terminated.")

def SDRangel_automate():
    """
    Runs SDRangel and switches between 433 MHz and 915 MHz channels.

    Returns
    -------
    None.

    """

    open_rcv = ["curl", "-X", "POST", "http://127.0.0.1:8091/sdrangel/deviceset?direction=0", "-H",  "accept: application/json", "-d", ""]

    set_dvc = ['curl', '-X', 'PUT', 'http://127.0.0.1:8091/sdrangel/deviceset/0/device', '-H', 'accept: application/json', '-H', 'Content-Type: application/json', '-d', '{\"deviceNbStreams\": 1, \"deviceSetIndex\": -1, \"direction\": 0, \"displayedName\": \"PlutoSDR[0] 1044735411960002f7ff080009f61e0b5b\", \"hwType\": \"PlutoSDR\", \"index\": 6, \"sequence\": 0, \"serial\": \"1044735411960002f7ff080009f61e0b5b\"}']

    set_center_freq_433 = ["curl", "-X", "PATCH", "http://127.0.0.1:8091/sdrangel/deviceset/0/device/settings", "-H",  "accept: application/json", "-H",  "Content-Type: application/json", "-d", "{  \"deviceHwType\": \"PlutoSDR\",  \"direction\": 0,  \"plutoSdrInputSettings\": {    \"LOppmTenths\": 0,    \"antennaPath\": 0,    \"centerFrequency\": 433000000,    \"dcBlock\": 0,    \"devSampleRate\": 2500000,    \"fcPos\": 2,    \"gain\": 50,    \"gainMode\": 0,    \"hwBBDCBlock\": 1,    \"hwIQCorrection\": 1,    \"hwRFDCBlock\": 1,    \"iqCorrection\": 0,    \"iqOrder\": 1,    \"log2Decim\": 0,    \"lpfBW\": 1500000,    \"lpfFIRBW\": 500000,    \"lpfFIREnable\": 0,    \"lpfFIRGain\": 0,    \"lpfFIRlog2Decim\": 0,    \"reverseAPIAddress\": \"127.0.0.1\",    \"reverseAPIDeviceIndex\": 0,    \"reverseAPIPort\": 8888,    \"transverterDeltaFrequency\": 0,    \"transverterMode\": 0,    \"useReverseAPI\": 0  }}"]

    set_center_freq_915 = ["curl", "-X", "PATCH", "http://127.0.0.1:8091/sdrangel/deviceset/0/device/settings", "-H",  "accept: application/json", "-H",  "Content-Type: application/json", "-d", "{  \"deviceHwType\": \"PlutoSDR\",  \"direction\": 0,  \"plutoSdrInputSettings\": {    \"LOppmTenths\": 0,    \"antennaPath\": 0,    \"centerFrequency\": 915000000,    \"dcBlock\": 0,    \"devSampleRate\": 2500000,    \"fcPos\": 2,    \"gain\": 50,    \"gainMode\": 0,    \"hwBBDCBlock\": 1,    \"hwIQCorrection\": 1,    \"hwRFDCBlock\": 1,    \"iqCorrection\": 0,    \"iqOrder\": 1,    \"log2Decim\": 0,    \"lpfBW\": 1500000,    \"lpfFIRBW\": 500000,    \"lpfFIREnable\": 0,    \"lpfFIRGain\": 0,    \"lpfFIRlog2Decim\": 0,    \"reverseAPIAddress\": \"127.0.0.1\",    \"reverseAPIDeviceIndex\": 0,    \"reverseAPIPort\": 8888,    \"transverterDeltaFrequency\": 0,    \"transverterMode\": 0,    \"useReverseAPI\": 0  }}"]

    open_chnl = ["curl", "-X", "POST", "http://127.0.0.1:8091/sdrangel/deviceset/0/channel", "-H",  "accept: application/json", "-H",  "Content-Type: application/json", "-d", "{  \"ChirpChatDemodSettings\": {    \"autoNbSymbolsMax\": 0,    \"bandwidthIndex\": 14,    \"channelMarker\": {      \"centerFrequency\": 0,      \"color\": -65281,      \"frequencyScaleDisplayType\": 0,      \"title\": \"ChirpChat Demodulator\"    },    \"codingScheme\": 0,    \"deBits\": 2,    \"decodeActive\": 1,    \"eomSquelchTenths\": 60,    \"fftWindow\": 5,    \"hasCRC\": 1,    \"hasHeader\": 1,    \"inputFrequencyOffset\": 0,    \"nbParityBits\": 1,    \"nbSymbolsMax\": 255,    \"preambleChirps\": 10,    \"reverseAPIAddress\": \"127.0.0.1\",    \"reverseAPIChannelIndex\": 0,    \"reverseAPIDeviceIndex\": 0,    \"reverseAPIPort\": 8888,    \"rgbColor\": -65281,    \"rollupState\": {      \"childrenStates\": [        {          \"isHidden\": 0,          \"objectName\": \"verticalLayoutWidget\"        },        {          \"isHidden\": 0,          \"objectName\": \"verticalLayoutWidget_2\"        },        {          \"isHidden\": 0,          \"objectName\": \"spectrumContainer\"        }      ],      \"version\": 0    },    \"sendViaUDP\": 1,    \"spectrumConfig\": {      \"averagingMode\": 0,      \"averagingValue\": 1,      \"calibrationInterpMode\": 0,      \"decay\": 1,      \"decayDivisor\": 1,      \"displayCurrent\": 1,      \"displayGrid\": 0,      \"displayGridIntensity\": 5,      \"displayHistogram\": 0,      \"displayMaxHold\": 0,      \"displayTraceIntensity\": 50,      \"displayWaterfall\": 1,      \"fftOverlap\": 0,      \"fftSize\": 4096,      \"fftWindow\": 4,      \"fpsPeriodMs\": 50,      \"histogramStroke\": 30,      \"invertedWaterfall\": 1,      \"linear\": 0,      \"markersDisplay\": 0,      \"powerRange\": 100,      \"refLevel\": 0,      \"ssb\": 0,      \"usb\": 1,      \"useCalibration\": 0,      \"waterfallShare\": 0.5,      \"wsSpectrum\": 0,      \"wsSpectrumAddress\": \"127.0.0.1\",      \"wsSpectrumPort\": 8887    },    \"spreadFactor\": 12,    \"title\": \"ChirpChat Demodulator\",    \"udpAddress\": \"127.0.0.1\",    \"udpPort\": 9999,    \"useReverseAPI\": 0  },  \"channelType\": \"ChirpChatDemod\",  \"direction\": 0}"]

    edit_chnl_settings_433 = ["curl", "-X", "PATCH", "http://127.0.0.1:8091/sdrangel/deviceset/0/channel/0/settings", "-H",  "accept: application/json", "-H",  "Content-Type: application/json", "-d", "{  \"ChirpChatDemodSettings\": {    \"autoNbSymbolsMax\": 0,    \"bandwidthIndex\": 15,    \"channelMarker\": {      \"centerFrequency\": 8640,      \"color\": -65281,      \"frequencyScaleDisplayType\": 0,      \"title\": \"ChirpChat Demodulator\"    },    \"codingScheme\": 0,    \"deBits\": 2,    \"decodeActive\": 1,    \"eomSquelchTenths\": 60,    \"fftWindow\": 5,    \"hasCRC\": 1,    \"hasHeader\": 1,    \"inputFrequencyOffset\": 8640,    \"nbParityBits\": 1,    \"nbSymbolsMax\": 255,    \"preambleChirps\": 10,    \"reverseAPIAddress\": \"127.0.0.1\",    \"reverseAPIChannelIndex\": 0,    \"reverseAPIDeviceIndex\": 0,    \"reverseAPIPort\": 8888,    \"rgbColor\": -65281,    \"rollupState\": {      \"childrenStates\": [        {          \"isHidden\": 0,          \"objectName\": \"verticalLayoutWidget\"        },        {          \"isHidden\": 0,          \"objectName\": \"verticalLayoutWidget_2\"        },        {          \"isHidden\": 0,          \"objectName\": \"spectrumContainer\"        }      ],      \"version\": 0    },    \"sendViaUDP\": 1,    \"spectrumConfig\": {      \"averagingMode\": 0,      \"averagingValue\": 1,      \"calibrationInterpMode\": 0,      \"decay\": 1,      \"decayDivisor\": 1,      \"displayCurrent\": 1,      \"displayGrid\": 0,      \"displayGridIntensity\": 5,      \"displayHistogram\": 0,      \"displayMaxHold\": 0,      \"displayTraceIntensity\": 50,      \"displayWaterfall\": 1,      \"fftOverlap\": 0,      \"fftSize\": 4096,      \"fftWindow\": 4,      \"fpsPeriodMs\": 50,      \"histogramStroke\": 30,      \"invertedWaterfall\": 1,      \"linear\": 0,      \"markersDisplay\": 0,      \"powerRange\": 100,      \"refLevel\": 0,      \"ssb\": 0,      \"usb\": 1,      \"useCalibration\": 0,      \"waterfallShare\": 0.5,      \"wsSpectrum\": 0,      \"wsSpectrumAddress\": \"127.0.0.1\",      \"wsSpectrumPort\": 8887    },    \"spreadFactor\": 10,    \"title\": \"ChirpChat Demodulator\",    \"udpAddress\": \"127.0.0.1\",    \"udpPort\": 9999,    \"useReverseAPI\": 0  },  \"channelType\": \"ChirpChatDemod\",  \"direction\": 0}"]

    edit_chnl_settings_915 = ["curl", "-X", "PATCH", "http://127.0.0.1:8091/sdrangel/deviceset/0/channel/0/settings", "-H",  "accept: application/json", "-H",  "Content-Type: application/json", "-d", "{  \"ChirpChatDemodSettings\": {    \"autoNbSymbolsMax\": 0,    \"bandwidthIndex\": 15,    \"channelMarker\": {      \"centerFrequency\": 23222,      \"color\": -65281,      \"frequencyScaleDisplayType\": 0,      \"title\": \"ChirpChat Demodulator\"    },    \"codingScheme\": 0,    \"deBits\": 2,    \"decodeActive\": 1,    \"eomSquelchTenths\": 60,    \"fftWindow\": 5,    \"hasCRC\": 1,    \"hasHeader\": 1,    \"inputFrequencyOffset\": 23222,    \"nbParityBits\": 1,    \"nbSymbolsMax\": 255,    \"preambleChirps\": 10,    \"reverseAPIAddress\": \"127.0.0.1\",    \"reverseAPIChannelIndex\": 0,    \"reverseAPIDeviceIndex\": 0,    \"reverseAPIPort\": 8888,    \"rgbColor\": -65281,    \"rollupState\": {      \"childrenStates\": [        {          \"isHidden\": 0,          \"objectName\": \"verticalLayoutWidget\"        },        {          \"isHidden\": 0,          \"objectName\": \"verticalLayoutWidget_2\"        },        {          \"isHidden\": 0,          \"objectName\": \"spectrumContainer\"        }      ],      \"version\": 0    },    \"sendViaUDP\": 1,    \"spectrumConfig\": {      \"averagingMode\": 0,      \"averagingValue\": 1,      \"calibrationInterpMode\": 0,      \"decay\": 1,      \"decayDivisor\": 1,      \"displayCurrent\": 1,      \"displayGrid\": 0,      \"displayGridIntensity\": 5,      \"displayHistogram\": 0,      \"displayMaxHold\": 0,      \"displayTraceIntensity\": 50,      \"displayWaterfall\": 1,      \"fftOverlap\": 0,      \"fftSize\": 4096,      \"fftWindow\": 4,      \"fpsPeriodMs\": 50,      \"histogramStroke\": 30,      \"invertedWaterfall\": 1,      \"linear\": 0,      \"markersDisplay\": 0,      \"powerRange\": 100,      \"refLevel\": 0,      \"ssb\": 0,      \"usb\": 1,      \"useCalibration\": 0,      \"waterfallShare\": 0.5,      \"wsSpectrum\": 0,      \"wsSpectrumAddress\": \"127.0.0.1\",      \"wsSpectrumPort\": 8887    },    \"spreadFactor\": 10,    \"title\": \"ChirpChat Demodulator\",    \"udpAddress\": \"127.0.0.1\",    \"udpPort\": 9999,    \"useReverseAPI\": 0  },  \"channelType\": \"ChirpChatDemod\",  \"direction\": 0}"]

    run_decoder = ["curl", "-X", "POST", "http://127.0.0.1:8091/sdrangel/deviceset/0/device/run", "-H",  "accept: application/json", "-H",  "Content-Type: application/json", "-d", "{  \"deviceHwType\": \"PlutoSDR\",  \"direction\": 0,  \"plutoSdrInputSettings\": {    \"LOppmTenths\": 0,    \"antennaPath\": 0,    \"centerFrequency\": 433000000,    \"dcBlock\": 0,    \"devSampleRate\": 2500000,    \"fcPos\": 2,    \"gain\": 50,    \"gainMode\": 0,    \"hwBBDCBlock\": 1,    \"hwIQCorrection\": 1,    \"hwRFDCBlock\": 1,    \"iqCorrection\": 0,    \"iqOrder\": 1,    \"log2Decim\": 0,    \"lpfBW\": 1500000,    \"lpfFIRBW\": 500000,    \"lpfFIREnable\": 0,    \"lpfFIRGain\": 0,    \"lpfFIRlog2Decim\": 0,    \"reverseAPIAddress\": \"127.0.0.1\",    \"reverseAPIDeviceIndex\": 0,    \"reverseAPIPort\": 8888,    \"transverterDeltaFrequency\": 0,    \"transverterMode\": 0,    \"useReverseAPI\": 0  }}"]

    stop_decoder = ["curl", "-X", "DELETE", "http://127.0.0.1:8091/sdrangel/deviceset/0/device/run", "-H",  "accept: application/json", "-H",  "Content-Type: application/json", "-d", "{  \"deviceHwType\": \"PlutoSDR\",  \"direction\": 0,  \"plutoSdrInputSettings\": {    \"LOppmTenths\": 0,    \"antennaPath\": 0,    \"centerFrequency\": 433000000,    \"dcBlock\": 0,    \"devSampleRate\": 2500000,    \"fcPos\": 2,    \"gain\": 50,    \"gainMode\": 0,    \"hwBBDCBlock\": 1,    \"hwIQCorrection\": 1,    \"hwRFDCBlock\": 1,    \"iqCorrection\": 0,    \"iqOrder\": 1,    \"log2Decim\": 0,    \"lpfBW\": 1500000,    \"lpfFIRBW\": 500000,    \"lpfFIREnable\": 0,    \"lpfFIRGain\": 0,    \"lpfFIRlog2Decim\": 0,    \"reverseAPIAddress\": \"127.0.0.1\",    \"reverseAPIDeviceIndex\": 0,    \"reverseAPIPort\": 8888,    \"transverterDeltaFrequency\": 0,    \"transverterMode\": 0,    \"useReverseAPI\": 0  }}"]

    close_rcv = ["curl", "-X", "DELETE", "http://127.0.0.1:8091/sdrangel/deviceset", "-H",  "accept: application/json"]

    #Open sdrangel

    print("SDRangel startup")
    
    sdrangel = subprocess.Popen(["/opt/install/sdrangel/bin/sdrangel", "--soapy", "--fftwf-wisdom", "/home/sdr/.config/f4exb/fftw-wisdom"])
    time.sleep(15) # loading time for sdrangel
    subprocess.Popen(close_rcv) # close any residual settings from previous calls
    time.sleep(2)

    # set the device to ADALM-Pluto
    subprocess.Popen(open_rcv)
    time.sleep(2)
    subprocess.Popen(set_dvc)

    # set the decoder to LoRa @ 433 MHz and run
    time.sleep(1)
    subprocess.Popen(set_center_freq_433)
    time.sleep(1)
    subprocess.Popen(open_chnl)
    time.sleep(2)
    subprocess.Popen(run_decoder)
    time.sleep(2)

    # decode time: 65 seconds
    print("Decoding at 433 MHz...")
    subprocess.Popen(edit_chnl_settings_433)
    time.sleep(65)

    # stop decoder
    subprocess.Popen(stop_decoder)
    time.sleep(5)

    # set the decoder to 915 MHz. then run
    subprocess.Popen(set_center_freq_915)
    time.sleep(2)
    subprocess.Popen(run_decoder)
    time.sleep(1)
    subprocess.Popen(edit_chnl_settings_915)

    print("Decoding at 915 MHz...")
    time.sleep(65)

    subprocess.Popen(stop_decoder)
    time.sleep(2)

    subprocess.Popen(close_rcv)

    time.sleep(2)

    #Close sdrangel

    sdrangel.terminate()
    print("SDRangel has been terminated.")
    time.sleep(5)
    
def reset_sdrRx():
    """
    Resets powerdown attribute of ADALM-Pluto. Can be found in
    "ad9361-phy" device at the "altvoltage0" channel.
    
    Necessary for successful switching from rtl_433 to SDRangel.

    Returns
    -------
    None.

    """
    subprocess.run(["iio_attr", "-u", "ip:192.168.2.1", "-c", "ad9361-phy", "altvoltage0", "powerdown", "0"])
    
def switching():
    """
    Switching process between rtl_433 and SDRangel.
    
    Uses the automate() functions above.

    Returns
    -------
    None.

    """
    while True:
        rtl433_automate()
        
        lora_receive = subprocess.Popen(["python3", "LoRaReceive_v2.0.py"])
        time.sleep(2)
        reset_sdrRx()
        SDRangel_automate()
        lora_receive.terminate()
        
def uploading():
    """
    Upload data every 5 minutes, but source differs.
    
    Effective upload time for each station: 15 minutes

    Returns
    -------
    None.

    """
    while True:
        subprocess.run(["python3", "davisUpload.py"])
        time.sleep(300)
        subprocess.run(["python3", "generalUpload.py"])
        time.sleep(300)
        subprocess.run(["python3", "LoRaUpload.py"])
        time.sleep(300)

if __name__ == '__main__':
    # Run the algorithms in parallel with each other
    # Can be terminated via command line using ctrl+C (cannot be
    # done with subprocess module)
    
    switching_protocol = Process(target=switching)
    print("Running switching mechanic")
    switching_protocol.start()

    davis_protocol = Process(target=decode_store_davis)
    print("Starting up Davis decoder and storage") 
    davis_protocol.start()
    
    uploading_protocol = Process(target=uploading)
    print("Upload protocol starting")
    uploading_protocol.start()
