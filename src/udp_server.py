import socket
import json
import threading
import time
from yeelight import Bulb

BULB_IP = "192.168.50.21"
UDP_PORT = 5005
TIMEOUT = 30

# Глобальные переменные
bulb = None
timer = None
motion_enabled = True

def get_bulb():
    global bulb
    if bulb is not None:
        return bulb
    else:
        try:
            bulb = Bulb(BULB_IP)
            print("✅ Лампа подключена")
            return bulb
        except:
            print("❌ Лампа недоступна")
            return None


def turn_on():
    b = get_bulb()
    # Включить лампу
    if b is not None:
        b.turn_on()
        print("Свет включен!")
    # Запустить таймер
    reset_timer()

def turn_off():
    global timer 
    b = get_bulb()
    # Включить лампу
    if b is not None:
        b.turn_off()
        print("Свет выключен!")
    # Выключить таймер
    if timer is not None:
        timer.cancel()
        timer = None

def timer_callback():
    print("⏰ Таймер сработал!")
    turn_off()

def reset_timer(seconds=None):
    global timer
    if timer is not None:
        timer.cancel()
    if seconds is not None:
        timeout = seconds
    else:
        timeout = TIMEOUT
    timer = threading.Timer(timeout, timer_callback)
    timer.daemon = True
    timer.start()
    print("Таймер запустился!")

def udp_listener():
    global motion_enabled
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)    # 1. Создать сокет
    sock.bind(("0.0.0.0", UDP_PORT))    # 2. Привязать к порту
    
    print("📡 UDP слушает...") # 3. Напечатать "📡 UDP слушает..."
    
    # 4. Бесконечный цикл
    while True:
        data, addr = sock.recvfrom(1024) # 5. Принять данные
        message = data.decode('utf-8')   # 6. Декодировать в строку
        if message == "MOTION_ON":
            if motion_enabled:  # проверяем, включён ли датчик
                turn_on()
            else:
                print("🔍 Движение зафиксировано, датчик отключён")
        elif message.startswith("{"):   # 8. Если начинается с "{" — распарсить JSON и выполнить команду
            try: 
                data = json.loads(message)
                command = data.get("command")
                if command == "light_on":
                    turn_on()
                    motion_enabled = False
                elif command == "light_off":
                    turn_off()
                    motion_enabled = False
                elif command == "timer":
                    reset_timer(data.get("value"))
                elif command == "motion_off":
                    motion_enabled = False
                    print("📡 Датчик движения: ВЫКЛ")
                elif command == "motion_on":
                    motion_enabled = True
                    print("📡 Датчик движения: ВКЛ")
                elif command == "motion_status":
                    # Отправляем статус обратно на M5Stick
                    status = "ON" if motion_enabled else "OFF"
                    response = json.dumps({"status": "ok", "motion_enabled": motion_enabled, "message": f"Sensor: {status}"})
                    sock.sendto(response.encode('utf-8'), addr)
                    print(f"📊 Статус отправлен: {status}")
            except json.JSONDecodeError:
                print("❌ Ошибка: невалидный JSON")
        else:
            print("Неизвестно:", message)  # 9. Иначе — напечатать "Неизвестно"


                
if __name__ == "__main__":
    udp_listener()    
