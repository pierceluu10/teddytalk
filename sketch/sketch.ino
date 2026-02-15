/*
 * Teddy Talk - Arduino Side
 * 2x SSD1306 OLED (128x32) as robot eyes when Adafruit libs available.
 * Falls back to LED blink when OLED libs not found (e.g. App Lab).
 * Uses Arduino_RouterBridge for App Lab.
 */

#include <Arduino_RouterBridge.h>
#include <Wire.h>

#ifdef __has_include
#if __has_include(<Adafruit_SSD1306.h>)
#include <Adafruit_SSD1306.h>
#include <Adafruit_GFX.h>
#define HAS_OLED 1
#endif
#endif

String current_emotion = "NEUTRAL";
float current_confidence = 80.0f;
unsigned long last_pupil_move = 0;
int pupil_offset_x = 0;
int pupil_offset_y = 0;

#ifdef HAS_OLED
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 32
#define OLED_RESET -1
#define SCREEN_ADDRESS 0x3C
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
void draw_eyes(String emotion, float confidence, bool blink);
void draw_blink();
#endif

#define BUTTON_PIN 2
volatile bool button_pressed = false;
bool last_button_state = HIGH;

void set_emotion(String emotion, float confidence);
bool get_button_pressed();

void setup() {
  Serial.begin(115200);

  pinMode(BUTTON_PIN, INPUT_PULLUP);

#ifdef HAS_OLED
  Wire.begin();
  if (!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println("SSD1306 init failed");
  } else {
    display.clearDisplay();
    display.display();
  }
#else
  Serial.println("OLED libs not found - using LED only");
#endif

  Bridge.begin();
  Bridge.provide("setEmotion", set_emotion);
  Bridge.provide("getButtonPressed", get_button_pressed);

  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  Serial.println("Teddy Talk - Ready");
}

bool get_button_pressed() {
  bool p = button_pressed;
  button_pressed = false;
  return p;
}

void loop() {
  bool now = digitalRead(BUTTON_PIN);
  if (last_button_state == HIGH && now == LOW) {
    button_pressed = true;
  }
  last_button_state = now;
#ifdef HAS_OLED
  unsigned long now = millis();
  if (now - last_pupil_move > 2000) {
    last_pupil_move = now;
    pupil_offset_x = (pupil_offset_x + 2) % 5 - 2;
    pupil_offset_y = (pupil_offset_y + 1) % 3 - 1;
    draw_eyes(current_emotion, current_confidence, false);
  }
#endif
  delay(10);
}

void set_emotion(String emotion, float confidence) {
  Serial.print("Emotion: ");
  Serial.print(emotion.c_str());
  Serial.print(" (");
  Serial.print(confidence);
  Serial.println("%)");

#ifdef HAS_OLED
  if (emotion != current_emotion) {
    draw_blink();
    delay(80);
  }
#endif

  current_emotion = emotion;
  current_confidence = confidence;

  digitalWrite(LED_BUILTIN, LOW);
  delay(100);
  digitalWrite(LED_BUILTIN, HIGH);

#ifdef HAS_OLED
  draw_eyes(emotion, confidence, false);
#endif
}

#ifdef HAS_OLED
void draw_blink() {
  display.clearDisplay();
  display.drawLine(20, 16, 44, 16, SSD1306_WHITE);
  display.drawLine(84, 16, 108, 16, SSD1306_WHITE);
  display.display();
  delay(80);
}

void draw_eyes(String emotion, float confidence, bool blink) {
  if (blink) {
    draw_blink();
    return;
  }

  display.clearDisplay();

  int eye_w = 24;
  int eye_h = 20;
  int left_cx = 32;
  int right_cx = 96;
  int cy = 16;
  int pupil_r = 4;
  int px = pupil_offset_x;
  int py = pupil_offset_y;

  draw_eye_expression(left_cx, cy, eye_w, eye_h, pupil_r, px, py, emotion);
  draw_eye_expression(right_cx, cy, eye_w, eye_h, pupil_r, -px, py, emotion);

  display.display();
}

void draw_eye_expression(int cx, int cy, int w, int h, int pupil_r,
                         int pupil_dx, int pupil_dy, String emotion) {
  emotion.toUpperCase();

  if (emotion == "HAPPY" || emotion == "HAPPINESS") {
    display.drawCircle(cx, cy, w / 2, SSD1306_WHITE);
    for (int x = -w / 2; x <= w / 2; x++) {
      int y = 3 + (x * x) / 20;
      if (y < h / 2) display.drawPixel(cx + x, cy + y, SSD1306_WHITE);
    }
    display.fillCircle(cx + pupil_dx, cy - 2 + pupil_dy, pupil_r, SSD1306_WHITE);
  } else if (emotion == "ANGRY" || emotion == "ANGER") {
    display.drawCircle(cx, cy, w / 2, SSD1306_WHITE);
    display.drawLine(cx - w / 2, cy - h / 3, cx + w / 2, cy + h / 4, SSD1306_WHITE);
    display.fillCircle(cx + pupil_dx, cy + pupil_dy, pupil_r, SSD1306_WHITE);
  } else if (emotion == "SAD" || emotion == "SADNESS") {
    display.drawCircle(cx, cy, w / 2, SSD1306_WHITE);
    display.drawLine(cx - w / 2, cy - h / 4, cx + w / 2, cy - h / 4, SSD1306_WHITE);
    display.fillCircle(cx + pupil_dx, cy - 2 + pupil_dy, pupil_r, SSD1306_WHITE);
  } else if (emotion == "SURPRISE") {
    display.drawCircle(cx, cy, w / 2 + 2, SSD1306_WHITE);
    display.drawCircle(cx, cy, w / 2 + 1, SSD1306_WHITE);
    display.fillCircle(cx + pupil_dx, cy + pupil_dy, pupil_r + 1, SSD1306_WHITE);
  } else {
    display.drawCircle(cx, cy, w / 2, SSD1306_WHITE);
    display.fillCircle(cx + pupil_dx, cy + pupil_dy, pupil_r, SSD1306_WHITE);
  }
}
#endif
