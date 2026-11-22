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
 *   - Payload matches FastAPI backend schema (ESP32SensorReading)
 *   - Non-blocking loop using millis()
 *   - Multi-sample ADC averaging for stable soil moisture
 *   - Glitch-retry for DHT11 single-wire communication
 * =====================================================================
 */

#include <DHT.h>

// ========== PIN DEFINITIONS ==========
#define DHT_PIN         27        // DHT11 Data Pin connected to GPIO 27
#define DHT_TYPE        DHT11     // DHT sensor model (DHT11)
#define SOIL_PIN        35        // Soil Moisture Analog Pin connected to GPIO 35 (ADC1)
#define STATUS_LED_PIN  2         // Onboard Blue LED for transmission heartbeat

// ========== SENSOR CALIBRATION ==========
// ADC values range from 0 to 4095 on 12-bit ESP32 ADC.
// Calibrate these two thresholds for your specific soil probe:
// In completely dry air (high resistance / high voltage output):
#define SOIL_DRY_VAL    3500
// Immersed in water (low resistance / low voltage output):
#define SOIL_WET_VAL    1500

// Number of analog samples to average for noise reduction
#define ADC_SAMPLES     10

// Telemetry interval in milliseconds (e.g., 5000ms = every 5 seconds)
#define TELEMETRY_INTERVAL_MS 5000

// Device Identifier (must match DEVICE_ID in backend .env)
const char* DEVICE_ID = "ESP32_01";

// ========== HARDWARE INSTANCES ==========
DHT dht(DHT_PIN, DHT_TYPE);

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

  // Status LED
  pinMode(STATUS_LED_PIN, OUTPUT);
  digitalWrite(STATUS_LED_PIN, LOW);

  // Initialize DHT11 sensor
  dht.begin();

  // Configure ESP32 12-bit ADC (values: 0 to 4095)
  analogReadResolution(12);

  // Settle time for sensors on power up
  delay(1500);

  // Startup ready blink
  digitalWrite(STATUS_LED_PIN, HIGH);
  delay(200);
  digitalWrite(STATUS_LED_PIN, LOW);
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

    // 3. Emit Pure, Strict JSON Line for Python SerialReceiver
    // IMPORTANT: Do NOT print extra non-JSON lines to prevent buffer desync
    Serial.print("{\"device_id\":\"");
    Serial.print(DEVICE_ID);
    Serial.print("\",\"temperature\":");
    Serial.print(temperature, 1);
    Serial.print(",\"humidity\":");
    Serial.print(humidity, 1);
    Serial.print(",\"soil_moisture\":");
    Serial.print(soilMoisture);
    Serial.println("}");

    // Visual transmission heartbeat blink
    digitalWrite(STATUS_LED_PIN, HIGH);
    delay(30);
    digitalWrite(STATUS_LED_PIN, LOW);
  }
}
