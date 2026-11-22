/*
 * =====================================================================
 *  SMART AGRICULTURE MONITORING SYSTEM - ESP32 FIRMWARE
 * =====================================================================
 *  Project: SARVA-MITRA / SmartFarm IoT
 *  Microcontroller: ESP32 NodeMCU / DevKit V1
 *
 *  Sensors:
 *   - DHT11 (Air Temperature & Relative Humidity) -> GPIO 27
 *   - Capacitive / Resistive Soil Moisture Sensor -> GPIO 35 (ADC1_CH7)
 *
 *  Communication Protocol:
 *   - JSON formatted telemetry emitted over USB Serial at 115200 baud
 *   - Sensor readings also stored in ThingSpeak over secure HTTPS
 *   - Payload matches FastAPI backend schema (ESP32SensorReading)
 *   - Non-blocking loop using millis()
 *   - Multi-sample ADC averaging for stable soil moisture
 *   - Glitch-retry for DHT11 single-wire communication
 * =====================================================================
 */

#include <DHT.h>
#include <string.h>
#define TS_ENABLE_SSL
#include <WiFi.h>
#include <WiFiClientSecure.h>
#if __has_include("secrets.h")
#include "secrets.h"
#else
// Serial-only builds still work; add secrets.h to enable Wi-Fi cloud uploads.
#define SECRET_SSID ""
#define SECRET_PASS ""
#define SECRET_CH_ID 0UL
#define SECRET_WRITE_APIKEY ""
#endif
#include <ThingSpeak.h>

// ========== PIN DEFINITIONS ==========
#define DHT_PIN         27        // DHT11 Data Pin connected to GPIO 27
#define DHT_TYPE        DHT11     // DHT sensor model (DHT11)
#define SOIL_PIN        35        // Soil Moisture Analog Pin connected to GPIO 35 (ADC1)

// ========== SENSOR CALIBRATION ==========
// ADC values range from 0 to 4095 on 12-bit ESP32 ADC.
// Calibrate these two thresholds for your specific soil probe:
// In completely dry air (high resistance / high voltage output):
#define SOIL_DRY_VAL    3500
// Immersed in water (low resistance / low voltage output):
#define SOIL_WET_VAL    1500

// Number of analog samples to average for noise reduction
#define ADC_SAMPLES     10

// ThingSpeak free channels accept updates no more frequently than every 15 seconds.
#define TELEMETRY_INTERVAL_MS 20000

// Device Identifier (must match DEVICE_ID in backend .env)
const char* DEVICE_ID = "ESP32_01";

// ========== HARDWARE INSTANCES ==========
DHT dht(DHT_PIN, DHT_TYPE);
WiFiClientSecure secureClient;

// ========== STATE TRACKING ==========
unsigned long lastTelemetryTime = 0;
float lastValidTemp = 25.0;
float lastValidHumidity = 50.0;

// ========== FILTERED SOIL MOISTURE HELPER ==========
int readFilteredSoilMoisture() {
  long sum = 0;
  for (int i = 0; i < ADC_SAMPLES; i++) {
    sum += analogRead(SOIL_PIN);
    delay(5);
  }
  int rawValue = sum / ADC_SAMPLES;

  // Map inverted analog reading to 0 - 100% moisture:
  // Dry reading (e.g. 3500) -> 0%
  // Wet reading (e.g. 1500) -> 100%
  int percentage = map(rawValue, SOIL_DRY_VAL, SOIL_WET_VAL, 0, 100);
  percentage = constrain(percentage, 0, 100);

  return percentage;
}

// ========== SETUP ==========
void setup() {
  // Serial interface matching backend SERIAL_BAUDRATE (115200)
  Serial.begin(115200);

  // Initialize DHT11 sensor
  dht.begin();

  // Initialize Wi-Fi and the secure ThingSpeak client.
  WiFi.mode(WIFI_STA);
  ThingSpeak.begin(secureClient);
  if (strlen(SECRET_SSID) > 0) {
    WiFi.begin(SECRET_SSID, SECRET_PASS);
  } else {
    Serial.println("No secrets.h Wi-Fi credentials; running in USB Serial-only mode.");
  }

  // Configure ESP32 12-bit ADC (values: 0 to 4095)
  analogReadResolution(12);

  // Settle time for sensors on power up
  delay(1500);

}

// ========== MAIN LOOP (NON-BLOCKING) ==========
void loop() {
  unsigned long currentMillis = millis();

  if (currentMillis - lastTelemetryTime >= TELEMETRY_INTERVAL_MS) {
    lastTelemetryTime = currentMillis;

    // 1. Read DHT11 Temperature and Humidity
    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();

    // Auto-retry on single read glitch (common with 1-wire timing)
    if (isnan(temperature) || isnan(humidity)) {
      delay(100);
      temperature = dht.readTemperature();
      humidity = dht.readHumidity();
    }

    // Fallback to last known good reading to avoid dropping serial frames
    if (isnan(temperature) || isnan(humidity)) {
      temperature = lastValidTemp;
      humidity = lastValidHumidity;
    } else {
      lastValidTemp = temperature;
      lastValidHumidity = humidity;
    }

    // 2. Read Averaged Soil Moisture
    int soilMoisture = readFilteredSoilMoisture();

    // Emit only the three requested measurements in the backend's JSON format.
    Serial.print("{\"device_id\":\"");
    Serial.print(DEVICE_ID);
    Serial.print("\",\"temperature\":");
    Serial.print(temperature, 1);
    Serial.print(",\"humidity\":");
    Serial.print(humidity, 1);
    Serial.print(",\"soil_moisture\":");
    Serial.print(soilMoisture);
    Serial.println("}");

    // ThingSpeak fields: 1=temperature (°C), 2=humidity (%), 3=soil moisture (%).
    if (strlen(SECRET_SSID) > 0 && WiFi.status() != WL_CONNECTED) {
      WiFi.begin(SECRET_SSID, SECRET_PASS);
      Serial.println("Wi-Fi reconnect requested.");
    } else if (WiFi.status() == WL_CONNECTED && SECRET_CH_ID != 0 && strlen(SECRET_WRITE_APIKEY) > 0) {
      ThingSpeak.setField(1, temperature);
      ThingSpeak.setField(2, humidity);
      ThingSpeak.setField(3, soilMoisture);
      int result = ThingSpeak.writeFields(SECRET_CH_ID, SECRET_WRITE_APIKEY);
      if (result == 200) {
        Serial.println("ThingSpeak telemetry stored successfully.");
      } else {
        Serial.print("ThingSpeak write failed, HTTP status: ");
        Serial.println(result);
      }
    } else if (WiFi.status() != WL_CONNECTED) {
      Serial.println("Wi-Fi is not connected; telemetry remains available on USB Serial.");
    }

  }
}
