import time
import json
import paho.mqtt.client as mqtt
import certifi
from datetime import datetime

def read_database():
    temp_dict = {}
    with open('davis_deploy6_Jul17.json', 'r') as payload:
        print("Davis Weather Stations: Gathering Weather data")
        weather_data = payload.readlines()
        weather_data_reversed = weather_data[::-1]
        
        sensors = [1, 2]
        
        for ID in sensors:
            parameters = {'temperature': 0, 'humidity': 0, 'rain_rate': 0, 'wind_gust': 0}
            param_count = 0
            first_line = 0
            for line in weather_data_reversed:
                data_dict = json.loads(line)
                
                if param_count >= 4:
                    break
                else:
                    pass
                
                if data_dict['ID'] == ID:
                    if first_line == 0:
                        temp_dict[ID] = dict()
                        first_line = 1
                        for parameter in data_dict:
                            temp_dict[ID][parameter] = data_dict[parameter]
                            if parameter in parameters:
                                parameters[parameter] = 1
                                param_count += 1
                    else:
                        for parameter in data_dict:
                            if parameter in parameters:
                                if parameters[parameter] == 0:
                                    temp_dict[ID][parameter] = data_dict[parameter]
                                    parameters[parameter] = 1
                                    param_count += 1
                                
                else:
                    pass

    return temp_dict

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Davis Weather Stations: MQTT Server connection successfully established")
    else:
        print(f"Failed to connect to MQTT Server with return code {rc}")

def make_msg(station_ID, data):
    out_msg = {}
    out_msg['type'] = "data"
    out_msg['source'] = f"Davis_{station_ID}"
    out_msg['local_time'] = datetime.now().isoformat()
    out_msg['DAVIS_RR'] = float(data['rain_rate'])
    out_msg['DAVIS_WG'] = float(data['wind_speed'])
    out_msg['DAVIS_TMP'] = float(data['temperature'])
    out_msg['DAVIS_OH'] = float(data['humidity'])  
    
    return json.dumps(out_msg)

if __name__ == '__main__':
    date_format = '%Y-%m-%d %H:%M:%S.%f'

    try:
        print("Connecting to MQTT Server....")

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
            weather_data = read_database()
            print(f"Successfully fetched: {weather_data}")
            print("Uploading data...")
            
            del_key = []

            # for davis and general
            # separate/filter out those not within 15 minutes
            for key in weather_data:
                latest = weather_data[key]['time'] # for Davis and general
                latest_datetime = datetime.strptime(latest, date_format) # for davis and general
                
                duration = datetime.now() - latest_datetime
                if duration.seconds > 900 or duration.days > 0:
                    del_key.append(key)

            for key in del_key:
                del weather_data[key]                
        
            if len(weather_data) == 0:
                print(f'No publication made. The most recent data was obtained {duration.seconds} seconds ago.')
            else:                
                for ID in weather_data.keys():
                    pmsg = make_msg(ID, weather_data[ID])
                    client.publish("UPCARE/UNDERGRAD/COE199_SDR", pmsg)
                    print(f"Davis stations payload: {pmsg}")
                    time.sleep(2)

                print("Finished sending all data from Davis stations")

        except Exception as e:
            print(f"An error occurred: {e}")

        finally:
            client.disconnect()
            client.loop_stop()

    except Exception as e:
        print("Error:", e)
