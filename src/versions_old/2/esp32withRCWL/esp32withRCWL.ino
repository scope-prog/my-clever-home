// ============================================
// ESP32 ДАТЧИК ДВИЖЕНИЯ (UDP)
// Отправляет сигнал на компьютер при движении
// ============================================

#include <WiFi.h>
#include <WiFiUdp.h>

// ===== НАСТРОЙКИ Wi-Fi =====
const char* ssid = "ASUS_54";           // Ваш Wi-Fi
const char* password = "founder_6572";  // Пароль

// ===== НАСТРОЙКИ UDP =====
const char* server_ip = "192.168.50.104";  // IP вашего КОМПЬЮТЕРА
const int udp_port = 5005;                 // Порт для UDP

// ===== ПИН ДАТЧИКА =====
#define SENSOR_PIN 26

// ===== ПЕРЕМЕННЫЕ =====
WiFiUDP udp;
unsigned long lastMotionTime = 0;
bool lastState = false;

void setup() {
  Serial.begin(115200);
  pinMode(SENSOR_PIN, INPUT);
  
  // Подключаемся к Wi-Fi
  Serial.print("Подключение к Wi-Fi");
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\n✅ Wi-Fi подключен!");
  Serial.print("IP адрес ESP: ");
  Serial.println(WiFi.localIP());
  Serial.println("ESP готова к работе!");
}

void loop() {
  // Читаем датчик
  int motion = digitalRead(SENSOR_PIN);
  
  // Если движение обнаружено (HIGH)
  if (motion == HIGH) {
    // Отправляем не чаще 1 раза в секунду (чтобы не спамить)
    if (millis() - lastMotionTime > 1000) {
      lastMotionTime = millis();
      
      // ОТПРАВЛЯЕМ UDP СООБЩЕНИЕ
      udp.beginPacket(server_ip, udp_port);
      udp.print("MOTION_ON");
      udp.endPacket();
      
      Serial.println("🔴 ДВИЖЕНИЕ ОБНАРУЖЕНО! Отправлено: MOTION_ON");
    }
  }
  
  delay(50);  // Небольшая задержка
}