#include <M5StickCPlus2.h>
#include <WiFi.h>
#include <PubSubClient.h>

// ===== ТВОИ ДАННЫЕ =====
const char* ssid = "ASUS_54";
const char* password = "founder_6572";
const char* mqtt_server = "192.168.50.104";
const char* mqtt_topic = "room/motion";

// ===== ПИН ДАТЧИКА =====
#define SENSOR_PIN 26

// ===== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ =====
WiFiClient espClient;
PubSubClient client(espClient);

unsigned long lastMotionTime = 0;   // Время последнего движения

void reconnect() {
  while (!client.connected()) {
    Serial.print("Подключение к MQTT...");
    if (client.connect("M5StickClient")) {
      Serial.println("OK");
    } else {
      Serial.print("Ошибка, rc=");
      Serial.print(client.state());
      Serial.println(" повтор через 5 секунд");
      delay(5000);
    }
  }
}

void sendCommand(bool on) {
  if (on) {
    client.publish(mqtt_topic, "ON");
    Serial.println("📤 Отправлено: ON");
  } else {
    client.publish(mqtt_topic, "OFF");
    Serial.println("📤 Отправлено: OFF");
  }
}

void setup() {
  M5.begin();
  Serial.begin(115200);
  Serial.println("=== СТАРТ ===");
  pinMode(SENSOR_PIN, INPUT);
  
  WiFi.begin(ssid, password);
  Serial.print("Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ Wi-Fi подключен! IP: " + WiFi.localIP().toString());
  
  client.setServer(mqtt_server, 1883);
  reconnect();
  Serial.println("✅ Готов! Жду движения...");
}

void loop() {
  M5.update();
  
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  
  int motion = digitalRead(SENSOR_PIN);
  
  if (motion == HIGH) {
    // При ЛЮБОМ движении отправляем ON и обновляем время
    sendCommand(true);
    lastMotionTime = millis();
    Serial.println("✅ Движение! ON отправлен, таймер на ПК сброшен");
    
    // Небольшая задержка, чтобы не спамить
    delay(500);
  }
  
  delay(50);
}