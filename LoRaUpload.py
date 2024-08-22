# -*- coding: utf-8 -*-

import certifi
import json
import paho.mqtt.client as mqtt
import time
from datetime import datetime

def read_database():

    temp_dict = {}
    with open('LoRa_Weather.json', 'r') as payload:
        print ("Radio 3: Gathering Weather Data from LoRa Stations")
        weather_data = payload.readlines()
        weather_data_reversed = weather_data[::-1]
        frequencies = [433, 915]
        for frequency in frequencies:
            for lines in weather_data_reversed:
                lines_to_dict = json.loads(lines)
                if frequency == int(lines_to_dict['Frequency'].split()[0]):
                    temp_dict[frequency] = lines_to_dict
                    print(frequency)
                    break

    return (temp_dict)

def make_msg(ID, data):
    out_msg = {}
    out_msg['type'] = "data"
    out_msg['source'] = f"LoRa_{ID}"
    
    out_msg['local_time'] = data['TimeStamp']
    
    if (out_msg['source']=='LoRa_433'):
        out_msg['DHT22_TMP_433'] = float(data['Temperature'])
        out_msg['DHT22_RH_433'] = float(data['Relative Humidity'])
        out_msg['MQ135_433'] = float(data['Air Quality'])
    elif (out_msg['source']=='LoRa_915'):
        out_msg['DHT22_TMP_915'] = float(data['Temperature'])
        out_msg['DHT22_RH_915'] = float(data['Relative Humidity'])
        out_msg['MQ2_915'] = float(data['Smoke and Flammable Gas'])

    return json.dumps(out_msg) #converts the dictionary into a json structure

def on_connect(client, userdata, flag, rc):
    print("MQTT Server connection successfully established")

def upload_data():
    del_key = []
    date_format_LoRa = '%Y-%m-%dT%H:%M:%S.%f'

    client = mqtt.Client()
    client.on_connect = on_connect

    MQTT_HOST = 'ed7632329e6e4fbcbe77b1fa917585a1.s1.eu.hivemq.cloud'
    MQTT_PORT = 8883
    MQTT_USER = 'jbcaminsi'
    MQTT_PW = 'UPcareteam2e'

    client.tls_set(certifi.where())
    client.username_pw_set(MQTT_USER, MQTT_PW)

    client.connect(MQTT_HOST, MQTT_PORT)

    client.loop_start()
    time.sleep(3)

    data = read_database()
    
    for key in data:
        latest = data[key]['TimeStamp'] # for lora
        latest_datetime = datetime.strptime(latest, date_format_LoRa) # for lora
    
        duration = datetime.now() - latest_datetime
        if duration.seconds > 900 or duration.days > 0:
            del_key.append(key)

    for key in del_key:
        del data[key]

    try:
        if len(data) == 0:
            print(f'No publication made. The most recent data was obtained {duration.seconds} seconds ago.')
    
        else:
            for key in data.keys():
                pmsg = make_msg(key, data[key])    
                client.publish("UPCARE/UNDERGRAD/COE199_SDR", pmsg) #upload data
                print(f"LoRa Weather Stations payload: {pmsg}")
                time.sleep(2)
            print("Finished sending all data from LoRa Weather Stations")
    
    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        client.disconnect()
        client.loop_stop()
    
if __name__ == "__main__":
    try:
        upload_data()
    except Exception as e:
        print("Error:", e)
