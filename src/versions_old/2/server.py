import socket
import json
import threading
import time
from yeelight import Bulb, BulbException

BULB_IP = "192.168.50.21"
UDP_PORT = 5005
TIMEOUT = 30

class SmartLightServer:
    def __init__(self, bulb_ip=BULB_IP, port=UDP_PORT, timeout=TIMEOUT):
        self.port = port
        self.timeout = timeout
        self.bulb_ip = bulb_ip
        
        self.bulb = None
        self.timer = None
        self.motion_enabled = True
        
        self.lock = threading.RLock()
        self.is_operating = False

    def _get_bulb(self):
        """Безопасное получение объекта лампы"""
        with self.lock:
            if self.bulb is not None:
                return self.bulb
            try:
                self.bulb = Bulb(self.bulb_ip, effect="smooth", duration=500)
                print(f"🔌 Подключено к лампе {self.bulb_ip}")
            except Exception as e:
                print(f"⚠️ Ошибка подключения к лампе: {e}")
                self.bulb = None
            return self.bulb

    def _reset_bulb_connection(self):
        with self.lock:
            self.bulb = None

    def _run_async(self, target_func, command_name, force=False):
        with self.lock:
            if self.is_operating and not force:
                print(f"⏳ [Пропуск {command_name}]: Лампа занята.")
                return False
            self.is_operating = True

        def _wrapper():
            try:
                target_func()
            except BulbException as be:
                print(f"❌ Ошибка Yeelight [{command_name}]: {be}")
                self._reset_bulb_connection()
            except Exception as e:
                print(f"❌ Системная ошибка [{command_name}]: {e}")
            finally:
                with self.lock:
                    self.is_operating = False

        threading.Thread(target=_wrapper, daemon=True).start()
        return True

    def turn_on(self):
        def _task():
            bulb = self._get_bulb()
            if not bulb:
                print("❌ Лампа недоступна")
                return
            bulb.turn_on()
            print("💡 Свет ВКЛЮЧЕН")
        self._run_async(_task, "ВКЛЮЧЕНИЕ")

    def turn_off(self, force=False):
        def _task():
            bulb = self._get_bulb()
            if not bulb:
                print("❌ Лампа недоступна")
                return
            bulb.turn_off()
            print("💡 Свет ВЫКЛЮЧЕН")
        self._run_async(_task, "ВЫКЛЮЧЕНИЕ", force=force)

    def _timer_callback(self):
        print("⏰ Таймер закончился!")
        self.turn_off(force=True)

    def reset_timer(self, seconds=None):
        with self.lock:
            if self.timer:
                self.timer.cancel()
            
            timeout = seconds if isinstance(seconds, (int, float)) and seconds > 0 else self.timeout
            self.timer = threading.Timer(timeout, self._timer_callback)
            self.timer.daemon = True
            self.timer.start()
            print(f"⏳ Таймер перезапущен на {timeout} секунд")

    def handle_command(self, raw_data, addr, sock):
        try:
            data = raw_data.decode('utf-8').strip() if isinstance(raw_data, bytes) else raw_data.strip()
            print(f"📩 Пакет от {addr}: '{data}'")
            
            cmd = ""
            value = None
            
            # JSON формат
            try:
                doc = json.loads(data)
                cmd = doc.get('command', '')
                value = doc.get('value', None)
                
                if cmd == 'light_on':
                    self.turn_on()
                    self.reset_timer()
                elif cmd == 'light_off':
                    self.turn_off()
                elif cmd == 'timer':
                    self.reset_timer(value)
                elif cmd == 'motion_on':
                    self.motion_enabled = True
                    print("📡 Датчик движения: ВКЛ")
                elif cmd == 'motion_off':
                    self.motion_enabled = False
                    print("📡 Датчик движения: ВЫКЛ")
                elif cmd == 'motion_status':
                    print(f"📊 Статус: {'ВКЛ' if self.motion_enabled else 'ВЫКЛ'}")
                
                # Отправка подтверждения
                response = json.dumps({"status": "ok", "command": cmd})
                sock.sendto(response.encode('utf-8'), addr)
                return
                
            except json.JSONDecodeError:
                pass
                
            # Текстовый формат (ESP32 датчик)
            if data == "MOTION_ON":
                if self.motion_enabled:
                    print("🔴 ДВИЖЕНИЕ ОБНАРУЖЕНО!")
                    self.turn_on()
                    self.reset_timer()
                else:
                    print("🔍 Движение зафиксировано, датчик отключён")
                return

        except Exception as e:
            print(f"❌ Ошибка обработки: {e}")

    def start(self):
        print("=" * 50)
        print("🏠 СЕРВЕР УМНОГО СВЕТА v4.0")
        print("=" * 50)
        print(f"🚀 UDP порт: {self.port}")
        print(f"💡 Лампочка: {self.bulb_ip}")
        print("=" * 50)
        print("Ожидание команд...")
        
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(("0.0.0.0", self.port))
            sock.settimeout(1.0)
            
            try:
                while True:
                    try:
                        data, addr = sock.recvfrom(1024)
                        self.handle_command(data, addr, sock)
                    except socket.timeout:
                        continue
                    except Exception as e:
                        print(f"❌ Ошибка: {e}")
            except (KeyboardInterrupt, SystemExit):
                print("\n🛑 Сервер остановлен.")

if __name__ == "__main__":
    server = SmartLightServer()
    server.start()