import subprocess
import time
import json
import paho.mqtt.client as mqtt
import certifi
from datetime import datetime, timezone
	 
def read_database():

    temp_dict = {}
    with open('genws_data.json', 'r') as payload:
        print ("General Weather Sensors: Gathering Weather data")
        weather_data = payload.readlines()
        weather_data_reversed = weather_data[::-1]
        sensors = [21881, 102]
        for id in sensors:
            for lines in weather_data_reversed:
                lines_to_dict = json.loads(lines)
                if id == lines_to_dict['id']:
                    temp_dict[id] = lines_to_dict
                    print(id)
                    break

    return (temp_dict)

def on_connect(client, userdata, flag, rc):
    print("General Weather Stations: MQTT Server connection successfully established") 

def make_message(station_ID, data):
    out_msg = {}
    out_msg['type'] = "data"
    out_msg['source'] = data['model'] +"_" + str(station_ID)
    out_msg['local_time'] = datetime.now().isoformat()
        
    if (data['model'] == "EcoWitt-WH40"):
        out_msg['WH40_RA'] = float(data['rain_mm'])
    else: 
        out_msg['WH31E_TMP'] = float(data['temperature_C'])
        out_msg['WH31E_RH'] = float(data['humidity'])
  
    
    return json.dumps(out_msg)
    
def upload_data():
    date_format = '%Y-%m-%d %H:%M:%S'
    
    try:
        print ("General Weather Stations: Connecting to MQTT Server....")
	    
        client = mqtt.Client()
        client.on_connect = on_connect

        MQTT_HOST = "ed7632329e6e4fbcbe77b1fa917585a1.s1.eu.hivemq.cloud"
        MQTT_PORT = 8883
        MQTT_USER = "jbcaminsi"
        MQTT_PW = "UPcareteam2e"
        
        client.tls_set(certifi.where())
        client.username_pw_set(MQTT_USER, MQTT_PW)

        client.connect(MQTT_HOST, MQTT_PORT)

        client.loop_start()
        time.sleep(3)
        
        try:
            # retrieve data from local database
            weather_data = read_database()
            print(f"Successfully fetched: {weather_data}")
            print("Uploading data...")
            
            del_key = []

            # for general
            
            # separate/filter out those not within 15 minutes
            for key in weather_data:
                latest = weather_data[key]['time']
                latest_datetime = datetime.strptime(latest, date_format)
                
                duration = datetime.now() - latest_datetime
                if duration.seconds > 900 or duration.days > 0:
                    del_key.append(key)

            for key in del_key:
                del weather_data[key]            
            
            
            # publish data into online database
            if len(weather_data) == 0:
                print(f'No publication made. The most recent data was obtained {duration.seconds} seconds ago.')
            else:                
                for keys in list(weather_data.keys()):
                    pmsg = make_message(keys, weather_data[keys])
                    client.publish("UPCARE/UNDERGRAD/COE199_SDR", pmsg)
                    print(f"General Weather Sensors payload: {pmsg}")
                    time.sleep(2)
                print(len(weather_data))
                print("Finished sending all data from General Weather Sensors")
             
        except Exception as e:
            print(f"Error occurred: {e}")
            
        finally:
            client.disconnect()
            client.loop_stop()
            
    except Exception as e:
        print("Error:", e)

if __name__=='__main__':
    upload_data()
