import paho.mqtt.client as mqtt
from yeelight import Bulb
import threading
import time

# ===== НАСТРОЙКИ =====
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
TOPIC_MOTION = "room/motion"

BULB_IP = "192.168.50.21"
TIMEOUT_SECONDS = 30  # Свет горит 60 секунд после последнего движения

# ===== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ =====
light_on = False
timer = None

# ===== ФУНКЦИИ УПРАВЛЕНИЯ ЛАМПОЧКОЙ =====
def turn_light_on():
    global light_on
    try:
        bulb = Bulb(BULB_IP)
        bulb.turn_on()
        light_on = True
        print("💡 Лампочка ВКЛЮЧЕНА")
    except Exception as e:
        print(f"❌ Ошибка включения: {e}")

def turn_light_off():
    global light_on
    try:
        bulb = Bulb(BULB_IP)
        bulb.turn_off()
        light_on = False
        print("💡 Лампочка ВЫКЛЮЧЕНА")
    except Exception as e:
        print(f"❌ Ошибка выключения: {e}")

def timer_callback():
    print("⏰ Таймер сработал! Выключаю свет...")
    turn_light_off()

# ===== ОБРАБОТЧИК MQTT =====
def on_message(client, userdata, msg):
    global timer, light_on
    payload = msg.payload.decode().strip().upper()
    print(f"📩 Получено: {payload} из топика {msg.topic}")

    if payload == "ON":
        turn_light_on()
        
        # Отменяем старый таймер
        if timer is not None:
            timer.cancel()
            print("⏹️ Старый таймер отменён")
        
        # Запускаем новый таймер
        timer = threading.Timer(TIMEOUT_SECONDS, timer_callback)
        timer.daemon = True
        timer.start()
        print(f"⏳ Таймер запущен на {TIMEOUT_SECONDS} секунд. Текущее состояние света: {'ВКЛ' if light_on else 'ВЫКЛ'}")

# ===== ЗАПУСК =====
if __name__ == "__main__":
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message

    print("🔌 Подключение к MQTT-брокеру...")
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.subscribe(TOPIC_MOTION)
        print(f"✅ Подключен. Ожидание сообщений в топике {TOPIC_MOTION}...")
        client.loop_forever()
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        print("Проверь, запущен ли Mosquitto!")