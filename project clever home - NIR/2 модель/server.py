# ============================================
# СЕРВЕР УМНОГО СВЕТА (UDP) - с поддержкой M5Stick
# ============================================

import socket
import json
import threading
import time
from yeelight import Bulb

# ===== НАСТРОЙКИ =====
BULB_IP = "192.168.50.21"
TIMEOUT = 30
UDP_PORT = 5005

# ===== ПОДКЛЮЧЕНИЕ К ЛАМПОЧКЕ =====
bulb = Bulb(BULB_IP)
timer = None
light_on = False
motion_enabled = True  # ГЛОБАЛЬНАЯ ПЕРЕМЕННАЯ

def turn_on():
    global light_on
    try:
        bulb.turn_on()
        light_on = True
        print("💡 Свет ВКЛЮЧЕН")
        return True
    except Exception as e:
        print(f"❌ Ошибка включения: {e}")
        return False

def turn_off():
    global light_on
    try:
        bulb.turn_off()
        light_on = False
        print("💡 Свет ВЫКЛЮЧЕН")
        return True
    except Exception as e:
        print(f"❌ Ошибка выключения: {e}")
        return False

def timer_callback():
    print("⏰ Таймер закончился!")
    turn_off()

def reset_timer(seconds=None):
    global timer
    if timer:
        timer.cancel()
    
    timeout = seconds if seconds else TIMEOUT
    timer = threading.Timer(timeout, timer_callback)
    timer.daemon = True
    timer.start()
    print(f"⏳ Таймер запущен на {timeout} секунд")

def handle_command(data):
    global motion_enabled  # ПРАВИЛЬНО - global ДО использования
    
    try:
        # Парсим JSON
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        
        if data.startswith('{'):
            doc = json.loads(data)
            cmd = doc.get('command', '')
            value = doc.get('value', 0)
            device = doc.get('device', '')
            
            print(f"📝 Команда: {cmd}, значение: {value}, устройство: {device}")
            
            if cmd == 'light_on':
                turn_on()
                reset_timer()
                return True
            elif cmd == 'light_off':
                turn_off()
                return True
            elif cmd == 'timer':
                reset_timer(value if value > 0 else TIMEOUT)
                return True
            elif cmd == 'motion_on':
                motion_enabled = True
                print("📡 Датчик движения ВКЛЮЧЕН")
                return True
            elif cmd == 'motion_off':
                motion_enabled = False
                print("📡 Датчик движения ВЫКЛЮЧЕН")
                return True
            elif cmd == 'motion_status':
                print(f"📊 Статус датчика: {'ВКЛ' if motion_enabled else 'ВЫКЛ'}")
                return True
        else:
            # Старый формат (от датчика движения)
            if data.strip() == "MOTION_ON":
                if motion_enabled:
                    print("🔴 ДВИЖЕНИЕ ОБНАРУЖЕНО!")
                    turn_on()
                    reset_timer()
                    return True
    except Exception as e:
        print(f"❌ Ошибка обработки команды: {e}")
    
    return False

def start_udp_server():
    """Запуск UDP сервера"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", UDP_PORT))
    
    print("=" * 50)
    print("🏠 УМНЫЙ СВЕТ - СЕРВЕР v2 (с поддержкой M5Stick)")
    print("=" * 50)
    print(f"🚀 UDP сервер запущен на порту {UDP_PORT}")
    print(f"💡 Лампочка: {BULB_IP}")
    print(f"⏱️  Таймер: {TIMEOUT} секунд")
    print(f"📡 Датчик движения: {'ВКЛ' if motion_enabled else 'ВЫКЛ'}")
    print("=" * 50)
    print("Ожидание команд...")
    
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            print(f"📩 Получено от {addr[0]}: {data.decode('utf-8')}")
            handle_command(data)
        except Exception as e:
            print(f"❌ Ошибка: {e}")

# ===== ЗАПУСК =====
if __name__ == "__main__":
    # Проверка лампочки
    try:
        bulb.get_properties()
        print("✅ Лампочка доступна")
    except:
        print("⚠️ Не удалось подключиться к лампочке!")
        print("   Проверьте IP и что лампочка включена")
        print("   Включите LAN Control в приложении Yeelight")
    
    start_udp_server()