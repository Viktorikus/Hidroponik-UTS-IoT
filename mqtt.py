import paho.mqtt.client as mqtt
import json
import requests
import time
from datetime import datetime

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "hidroponik/sensor/data"
MQTT_TOPIC_CONTROL = "hidroponik/control/relay"

BACKEND_URL = "http://localhost:3000/api/data_sensor"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected to MQTT Broker at {MQTT_BROKER}")
        client.subscribe(MQTT_TOPIC)
        client.subscribe(MQTT_TOPIC_CONTROL)
        print(f"Subscribed to topics: {MQTT_TOPIC}, {MQTT_TOPIC_CONTROL}")
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Received on {msg.topic}")
        print(f"Payload: {payload}")
        
        if msg.topic == MQTT_TOPIC:
            data = json.loads(payload)

            normalized_data = {}
            
            if 'temperature' in data:
                normalized_data['suhu'] = data['temperature']
            elif 'suhu' in data:
                normalized_data['suhu'] = data['suhu']
            
            if 'humidity' in data:
                normalized_data['humidity'] = data['humidity']
            
            if 'lux' in data:
                normalized_data['lux'] = data['lux']
            elif 'light' in data:
                normalized_data['lux'] = data['light']
            
            if 'suhu' in normalized_data and 'humidity' in normalized_data and 'lux' in normalized_data:
                response = requests.post(BACKEND_URL, json=normalized_data)
                
                if response.status_code == 200:
                    print(f"✓ Data saved to database: ID={response.json().get('id')}")
                    print(f"  Temperature: {normalized_data['suhu']}°C")
                    print(f"  Humidity: {normalized_data['humidity']}%")
                    print(f"  Light: {normalized_data['lux']} lux")
                else:
                    print(f"✗ Failed to save data: {response.status_code}")
            else:
                print(f"✗ Invalid data format. Expected: suhu/temperature, humidity, lux/light")
                print(f"✗ Received keys: {list(data.keys())}")
        
        elif msg.topic == MQTT_TOPIC_CONTROL:
            control_data = json.loads(payload)
            print(f"Control command received: {control_data}")
            
    except json.JSONDecodeError:
        print(f"✗ Invalid JSON: {payload}")
    except requests.RequestException as e:
        print(f"✗ Backend request error: {e}")
    except Exception as e:
        print(f"✗ Error processing message: {e}")

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"Unexpected disconnection. Attempting to reconnect...")
        time.sleep(5)

client = mqtt.Client(client_id="mqtt_bridge_python")
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

def publish_control(relay_state):
    control_msg = {
        "relay": relay_state,
        "timestamp": datetime.now().isoformat()
    }
    client.publish(MQTT_TOPIC_CONTROL, json.dumps(control_msg))
    print(f"Published control: Relay={'ON' if relay_state else 'OFF'}")

def main():
    try:
        print("="*50)
        print("MQTT Bridge Service Starting...")
        print("="*50)
        print(f"MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
        print(f"Backend API: {BACKEND_URL}")
        print(f"Listening on topic: {MQTT_TOPIC}")
        print("="*50)
        
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        client.loop_start()

        while True:
            command = input("Ketik 'on' untuk nyalakan relay, 'off' untuk matikan: ").strip().lower()
            
            if command == 'on':
                publish_control(True)
            elif command == 'off':
                publish_control(False)
            elif command == 'exit':
                break

        
        print("\nMQTT Bridge is running. Press Ctrl+C to exit.\n")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nShutting down MQTT Bridge...")
        client.loop_stop()
        client.disconnect()
        print("Disconnected from MQTT Broker")
        
    except Exception as e:
        print(f"Error: {e}")
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()