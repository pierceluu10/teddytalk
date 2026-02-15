/*
 * Teddy Talk - Arduino Side
 * Minimal version for import. Add LiquidCrystal I2C library for LCD eyes.
 * Uses Arduino_RouterBridge for App Lab.
 */

#include <Arduino_RouterBridge.h>

void set_emotion(String emotion, float confidence);

void setup() {
  Serial.begin(115200);

  Bridge.begin();
  Bridge.provide("setEmotion", set_emotion);

  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  Serial.println("Teddy Talk - Ready");
}

void loop() {
  delay(10);
}

void set_emotion(String emotion, float confidence) {
  Serial.print("Emotion: ");
  Serial.print(emotion.c_str());
  Serial.print(" (");
  Serial.print(confidence);
  Serial.println("%)");
  // Blink LED on emotion (add LCD code when LiquidCrystal I2C is installed)
  digitalWrite(LED_BUILTIN, LOW);
  delay(100);
  digitalWrite(LED_BUILTIN, HIGH);
}
