#include <M5StickCPlus2.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <ArduinoJson.h> // Проверьте, чтобы стояла свежая версия в менеджере библиотек

// ===== НАСТРОЙКИ =====
const char* ssid = "ASUS_54";
const char* password = "founder_6572";
const char* server_ip = "192.168.50.104";
const int udp_port = 5005;

// ===== ПЕРЕМЕННЫЕ =====
WiFiUDP udp;
bool wifiConnected = false;
int currentLevel = 0;
int menuPosition = 0;
int scrollOffset = 0;  

// ===== МЕНЮ =====
const char* mainMenu[] = {"LIGHT", "SENSOR", "SETTINGS"};
const int mainSize = 3;

const char* lightMenu[] = {"ON", "OFF", "TIMER 30S", "TIMER 60S", "TIMER 120S", "BACK"};
const int lightSize = 6;

const char* sensorMenu[] = {"ON", "OFF", "STATUS", "BACK"};
const int sensorSize = 4;

const char* settingsMenu[] = {"WIFI", "IP", "BACK"};
const int settingsSize = 3;

// ===== ПОЛУЧИТЬ ТЕКУЩЕЕ МЕНЮ =====
void getCurrentMenu(const char*** items, int* size) {
  if (currentLevel == 0) { *items = mainMenu; *size = mainSize; }
  else if (currentLevel == 1) { *items = lightMenu; *size = lightSize; }
  else if (currentLevel == 2) { *items = sensorMenu; *size = sensorSize; }
  else if (currentLevel == 3) { *items = settingsMenu; *size = settingsSize; }
}

const char* getTitle() {
  if (currentLevel == 0) return "MAIN";
  if (currentLevel == 1) return "LIGHT";
  if (currentLevel == 2) return "SENSOR";
  if (currentLevel == 3) return "SETTINGS";
  return "MENU";
}

// ===== ОТРИСОВКА МЕНЮ =====
void drawMenu() {
  const char** items = nullptr;
  int size = 0;
  getCurrentMenu(&items, &size);

  // 1. Очистка экрана (глубокий черный фон)
  StickCP2.Display.fillScreen(TFT_BLACK);
  StickCP2.Display.setRotation(1);
  
  // 2. Верхняя неоново-фиолетовая линия и заголовок
  StickCP2.Display.setTextColor(TFT_MAGENTA);
  StickCP2.Display.setTextSize(2);
  
  // Центрируем заголовок по ширине экрана (240 пикселей)
  String title = getTitle();
  int titleWidth = title.length() * 12; // Каждый символ размера 2 занимает ~12 пикселей
  int titleX = (240 - titleWidth) / 2;
  StickCP2.Display.setCursor(titleX, 6);
  StickCP2.Display.print(title);
  
  // Тонкая стильная линия под заголовком
  StickCP2.Display.drawLine(0, 26, 240, 26, TFT_MAGENTA);
  
  // ===== СКРОЛЛИНГ =====
  int visibleItems = 4;  
  
  if (menuPosition < scrollOffset) {
    scrollOffset = menuPosition;
  }
  if (menuPosition >= scrollOffset + visibleItems) {
    scrollOffset = menuPosition - visibleItems + 1;
  }
  
  int maxScroll = size - visibleItems;
  if (maxScroll < 0) maxScroll = 0;
  
  if (scrollOffset < 0) scrollOffset = 0;
  if (scrollOffset > maxScroll) scrollOffset = maxScroll;
  
  // ===== ОТРИСОВКА ПУНКТОВ МЕНЮ =====
  int startY = 42;
  for (int i = scrollOffset; i < scrollOffset + visibleItems && i < size; i++) {
    int yPos = startY + (i - scrollOffset) * 28;
    bool isBack = (strcmp(items[i], "BACK") == 0);
    
    if (i == menuPosition) {
      // Подсветка выбранного пункта в стиле Bruce (Зеленая рамка или сплошной неоновый блок)
      StickCP2.Display.drawRoundRect(5, yPos - 1, 230, 24, 3, TFT_GREEN);
      
      // Зеленый текст для выбранного пункта
      StickCP2.Display.setTextColor(TFT_GREEN);
      StickCP2.Display.setCursor(22, yPos + 3);
      StickCP2.Display.print(items[i]);
      
      // Хакерские маркеры по бокам "> <"
      StickCP2.Display.setCursor(8, yPos + 3);
      StickCP2.Display.print(">");
      StickCP2.Display.setCursor(222, yPos + 3);
      StickCP2.Display.print("<");
    } else {
      // Невыбранные пункты тускло-белые или серые (для контраста)
      StickCP2.Display.setTextColor(isBack ? TFT_RED : TFT_LIGHTGREY);
      StickCP2.Display.setCursor(22, yPos + 3);
      StickCP2.Display.print(items[i]);
    }
  }
  
  // ===== ИНДИКАТОР ПРОГРЕССА СКРОЛЛА (Правый мини-бар вместо стрелок) =====
  if (size > visibleItems) {
    int barHeight = 100;
    int barWidth = 3;
    int barX = 236;
    int barY = 40;
    
    // Отрисовка подложки бара
    StickCP2.Display.fillRect(barX, barY, barWidth, barHeight, TFT_DARKGREY);
    
    // Расчет высоты и позиции ползунка
    int chunkHeight = barHeight / size;
    int scrollY = barY + (menuPosition * chunkHeight);
    
    // Сам ползунок делаем фиолетовым под общий стиль
    StickCP2.Display.fillRect(barX, scrollY, barWidth, chunkHeight, TFT_MAGENTA);
  }
  
  // ===== ФУТЕР / ПОДСКАЗКА =====
  // Тонкая нижняя рамка
  StickCP2.Display.drawLine(0, 185, 240, 185, TFT_MAGENTA);
  
  // Текст подсказки кнопок (уже с учетом вашей новой раскладки)
  StickCP2.Display.setTextSize(1);
  StickCP2.Display.setTextColor(TFT_DARKGREY);
  StickCP2.Display.setCursor(12, 192);
  StickCP2.Display.print("[B] UP   [PWR] DOWN   [A] OK   [A+B] BACK");
}

// ===== ОТПРАВКА КОМАНД =====
void sendUDPCommand(String command, int value = 0) {
  JsonDocument doc; // Исправлено под ArduinoJson v7
  doc["type"] = "command";
  doc["device"] = "m5stick";
  doc["command"] = command;
  if (value > 0) doc["value"] = value;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  Serial.println("Sending: " + jsonString);
  
  udp.beginPacket(server_ip, udp_port);
  udp.print(jsonString);
  udp.endPacket();
  
  Serial.println("Sent!");
}

// ===== ПОКАЗ СООБЩЕНИЯ =====
void showMessage(String msg) {
  StickCP2.Display.fillScreen(TFT_BLACK);
  
  // Зеленая хакерская рамка во весь экран
  StickCP2.Display.drawRoundRect(10, 10, 220, 115, 5, TFT_GREEN);
  
  StickCP2.Display.setTextColor(TFT_GREEN);
  StickCP2.Display.setTextSize(2);
  
  // Текст по центру рамки
  int len = msg.length();
  int xPos = (240 - len * 12) / 2;
  if (xPos < 20) xPos = 20;
  
  StickCP2.Display.setCursor(xPos, 55);
  StickCP2.Display.print(msg);
  
  delay(1000);
  drawMenu();
}

// ===== ВОЗВРАТ В ГЛАВНОЕ МЕНЮ =====
void goBack() {
  if (currentLevel != 0) {
    currentLevel = 0;
    menuPosition = 0;
    scrollOffset = 0;
    drawMenu();
    Serial.println("Back to MAIN");
  }
}

// ===== ВЫПОЛНЕНИЕ ДЕЙСТВИЯ =====
void executeAction() {
  const char** items = nullptr;
  int size = 0;
  getCurrentMenu(&items, &size);
  
  if (items == nullptr || menuPosition >= size) return;
  String selected = String(items[menuPosition]);
  
  int yPos = 42 + (menuPosition - scrollOffset) * 28;
  // Заливаем прямоугольник зеленым, текст делаем черным
  StickCP2.Display.fillRoundRect(5, yPos - 1, 230, 24, 3, TFT_GREEN);
  StickCP2.Display.setTextColor(TFT_BLACK);
  StickCP2.Display.setCursor(22, yPos + 3);
  StickCP2.Display.print(items[menuPosition]);
  delay(70); // Короткий блик

  if (selected == "BACK") {
    goBack();
    return;
  }
  
  if (currentLevel == 0) {
    if (selected == "LIGHT") { currentLevel = 1; menuPosition = 0; scrollOffset = 0; drawMenu(); }
    else if (selected == "SENSOR") { currentLevel = 2; menuPosition = 0; scrollOffset = 0; drawMenu(); }
    else if (selected == "SETTINGS") { currentLevel = 3; menuPosition = 0; scrollOffset = 0; drawMenu(); }
  } 
  else if (currentLevel == 1) {
    if (selected == "ON") { sendUDPCommand("light_on"); showMessage("LIGHT ON"); }
    else if (selected == "OFF") { sendUDPCommand("light_off"); showMessage("LIGHT OFF"); }
    else if (selected == "TIMER 30S") { sendUDPCommand("timer", 30); showMessage("TIMER 30S"); }
    else if (selected == "TIMER 60S") { sendUDPCommand("timer", 60); showMessage("TIMER 60S"); }
    else if (selected == "TIMER 120S") { sendUDPCommand("timer", 120); showMessage("TIMER 120S"); }
  } 
  else if (currentLevel == 2) {
    if (selected == "ON") { sendUDPCommand("motion_on"); showMessage("SENSOR ON"); }
    else if (selected == "OFF") { sendUDPCommand("motion_off"); showMessage("SENSOR OFF"); }
    else if (selected == "STATUS") { sendUDPCommand("motion_status"); showMessage("STATUS..."); }
  } 
  else if (currentLevel == 3) {
    if (selected == "WIFI") { showMessage(wifiConnected ? "WiFi: OK" : "WiFi: NO"); }
    else if (selected == "IP") { showMessage(wifiConnected ? "IP: " + WiFi.localIP().toString() : "No IP"); }
  }
}

// ===== SETUP =====
void setup() {
  auto cfg = M5.config();
  StickCP2.begin(cfg);
  Serial.begin(115200);
  
  // 1. РЕНДЕРИНГ СТАРТОВОГО ЭКРАНА (Стиль Bruce)
  StickCP2.Display.setRotation(1);
  StickCP2.Display.fillScreen(TFT_BLACK);
  
  // Верхняя фиолетовая шапка программы
  StickCP2.Display.setTextColor(TFT_MAGENTA);
  StickCP2.Display.setTextSize(2);
  
  // Центрируем заголовок "scope_prog"
  String title = "scope_prog";
  int titleWidth = title.length() * 12;
  int titleX = (240 - titleWidth) / 2;
  StickCP2.Display.setCursor(titleX, 15);
  StickCP2.Display.print(title);
  
  // Тонкая разделительная линия под заголовком
  StickCP2.Display.drawLine(15, 40, 225, 40, TFT_MAGENTA);
  
  // Статус по умолчанию (снизу)
  StickCP2.Display.setTextColor(TFT_LIGHTGREY);
  StickCP2.Display.setTextSize(2);
  StickCP2.Display.setCursor(65, 75);
  StickCP2.Display.print("LOADING...");
  
  // Декоративная хакерская рамка вокруг экрана загрузки
  StickCP2.Display.drawRoundRect(8, 8, 224, 119, 4, TFT_MAGENTA);
  
  Serial.println("Starting connection...");
  
  // 2. ПОДКЛЮЧЕНИЕ К WI-FI
  WiFi.begin(ssid, password);
  int attempts = 0;
  // Пока подключаемся, можно выводить точки в Serial для дебага
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    attempts++;
    Serial.print(".");
  }
  Serial.println();
  
  // 3. ПРОВЕРКА СТАТУСА И ОБНОВЛЕНИЕ НИЖНЕЙ СТРОКИ
  // Стираем старую надпись "LOADING..." черным прямоугольником перед выводом новой
  StickCP2.Display.fillRect(15, 65, 210, 45, TFT_BLACK);
  
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    Serial.println("WiFi Connected! IP: " + WiFi.localIP().toString());
    
    // Выводим зеленый статус CONNECTED
    StickCP2.Display.setTextColor(TFT_GREEN);
    StickCP2.Display.setTextSize(2);
    StickCP2.Display.setCursor(55, 75);
    StickCP2.Display.print("CONNECTED");
    
  } else {
    Serial.println("WiFi FAILED!");
    
    // Выводим красный статус NOT CONNECTED
    StickCP2.Display.setTextColor(TFT_RED);
    StickCP2.Display.setTextSize(2);
    StickCP2.Display.setCursor(40, 75);
    StickCP2.Display.print("NOT CONNECTED");
  }
  
  // Даем пользователю рассмотреть финальный статус
  delay(2000);
  
  // 4. ЗАПУСК UDP И ПЕРЕХОД К МЕНЮ
  udp.begin(5006);
  drawMenu();
}

// ===== LOOP ===== 
void loop() {
  // Обязательно обновляем состояние кнопок библиотеки M5
  StickCP2.update();

  const char** items = nullptr;
  int size = 0;
  getCurrentMenu(&items, &size);

  // 1. НАЖАТИЕ ДВУХ КНОПОК ОДНОВРЕМЕННО (A + B) -> НАЗАД (BACK)
  if ((StickCP2.BtnA.isPressed() && StickCP2.BtnB.wasPressed()) || 
      (StickCP2.BtnB.isPressed() && StickCP2.BtnA.wasPressed())) {
    goBack();
    delay(300); 
    return;
  }

  // 2. КНОПКА B -> ВВЕРХ (Циклический скролл)
  if (StickCP2.BtnB.wasPressed()) {
    if (menuPosition > 0) {
      menuPosition--;
    } else {
      menuPosition = size - 1; 
    }
    drawMenu();
  }

  // 3. КНОПКА ПИТАНИЯ (M5.BtnPWR) -> ВНИЗ (Циклический скролл)
  if (M5.BtnPWR.wasClicked()) {
    if (menuPosition < size - 1) {
      menuPosition++;
    } else {
      menuPosition = 0; 
    }
    drawMenu();
  }

  // 4. КНОПКА A -> ОК / ВЫБОР (ВЫПОЛНЕНИЕ ДЕЙСТВИЯ)
  if (StickCP2.BtnA.wasPressed()) {
    executeAction();
  }

  delay(10); 
}
