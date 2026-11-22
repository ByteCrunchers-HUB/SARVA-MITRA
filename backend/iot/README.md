# 🌱 Sarva Mitra — Universal Farm Companion

> **One device. Any farm. Any language.**
>
> Sarva Mitra (“friend of all”) is a low-cost, profile-driven IoT and AI farming companion designed to monitor farm conditions, predict risks, trigger actions, and communicate practical guidance in **Telugu and Hindi**.

![Sarva Mitra](assets/universal-farm-architecture.png)

## 🚜 What is Sarva Mitra?

Farmers often rely on manual observation and fixed schedules to decide when to irrigate, aerate, or respond to changing environmental conditions. Sarva Mitra brings sensor data, an AI/ML engine, configurable farm profiles, and a voice-first assistant together in one adaptable system.

Instead of making a separate product for every farm type, Sarva Mitra uses a **profile file** to define the sensors, thresholds, alerts, and actions needed for each environment.

## 🎯 Problem

- **Late detection:** Important changes in soil, water, or environmental conditions can go unnoticed until damage occurs.
- **Separate devices:** Different farming activities often need separate monitoring and control systems.
- **Language barriers:** Many tools rely on English and screen-based interactions.
- **Reactive alerts:** Threshold alarms may warn only after a condition becomes unsafe.

## 💡 Our Solution

Sarva Mitra connects sensing, decision-making, control, and farmer assistance in one loop:

1. **Sense:** ESP32 collects readings from available sensors.
2. **Analyze:** The AI/ML engine detects anomalies and forecasts short-term trends.
3. **Decide:** The active farm profile determines whether a condition requires an action or warning.
4. **Act:** Relay outputs can switch equipment such as a pump, valve, fan, or aerator.
5. **Assist:** The farmer receives alerts and can ask questions in Telugu or Hindi through a voice-enabled assistant.

## 🧩 System Architecture

The field node, cloud/API, ML engine, RAG assistant, and dashboard work through a shared backend.

![Sarva Mitra universal system architecture](assets/universal-farm-architecture.png)

### Architecture components

| Component | Responsibility |
|---|---|
| ESP32 sensor node | Reads the connected sensor set and sends measurements |
| Cloud/API | Shared interface for sensor readings, decisions, alerts, and app requests |
| Profile loader | Applies the selected farm type's sensors, limits, messages, and actions |
| AI/ML engine | Anomaly detection and short-term forecasting |
| Relay outputs | Switch compatible equipment based on engine decisions |
| Voice layer | Telugu/Hindi text-to-speech alerts and speech-to-text input |
| Dashboard / bot | Displays readings, status, alerts, and farmer interactions |
| RAG assistant | Answers questions using public advisories and live sensor context |

## 🌾 Supported Farm Profiles

The prototype concept is designed around reusable profiles. Switching profiles changes configuration—not the core device or engine.

| Profile | Sensors / Inputs | Response | Status in project plan |
|---|---|---|---|
| 🐟 Fish / shrimp pond | Temperature, pH, TDS, turbidity | Risk alert, aerator control | Demo profile |
| 🌿 Crop field | Soil moisture, temperature | Irrigation pulse and advisory | Demo profile |
| 🐔 Poultry shed | Temperature, humidity | Fan control | Roadmap |
| 🏡 Greenhouse | Temperature, humidity, soil moisture | Ventilation / fan / mist | Roadmap |

> **Safety note:** The profile thresholds shown in the project plan are demo placeholders. Validate operating limits with qualified agriculture or fisheries experts before real-world deployment.

## 🧠 AI & Machine Learning

Sarva Mitra's ML layer is designed to work with generic sensor streams and profile-specific limits.

### 1. Anomaly Detection

Detects unusual readings—such as sudden temperature changes—relative to recent sensor behaviour.

- Initial approach: rolling Z-score
- Potential upgrade: Isolation Forest

### 2. Short-Term Forecasting

Predicts sensor values over the coming hours and warns when a forecast may cross a profile limit.

- Candidate models: Linear Regression or Gradient Boosting
- Inputs can include lagged sensor readings and time-of-day features

### 3. Profile-Based Decisions

The active JSON profile defines the relevant sensors, warning/critical limits, messages, and actions. The same engine can therefore be reused across different farm scenarios.

> Pond temperature and pH can be used as risk indicators in the demo, but they are **not a direct dissolved-oxygen measurement**. The prototype should communicate risk—not claim to measure oxygen without a DO sensor.

## 🔌 Hardware

The planned prototype uses an ESP32 with interchangeable sensors and relay-controlled equipment.

| Hardware | Purpose | Approx. cost (₹) |
|---|---|---:|
| ESP32 DevKit | Controller and Wi-Fi connectivity | 450 |
| DS18B20 waterproof temperature probe | Water / air temperature | 150 |
| Analog pH sensor kit | Pond pH | 1,200 |
| TDS sensor | Dissolved solids | 450 |
| Turbidity sensor | Water clarity | 350 |
| Capacitive soil-moisture sensor | Field soil moisture | 100 |
| 1-channel relay module | Switches the pump / aerator | 100 |
| Mini water pump | Demonstration load | 200 |
| Power, wiring, enclosure | Prototype assembly | 300 |

**Estimated prototype total:** approximately **₹3,300** (about ₹2,100 without the pH kit). Prices are indicative and may change.

### Hardware wiring concept

![ESP32 sensor and relay wiring concept](assets/hardware-wiring.png)

**Build precautions:**
- Connect analog sensors to ESP32 ADC1 pins (GPIO 32–35) when using Wi-Fi.
- The ESP32 GPIO inputs are limited to 3.3 V. Use suitable voltage division/level conditioning for sensor outputs that exceed this.
- The DS18B20 requires a 4.7 kΩ pull-up between data and 3.3 V.
- Power pumps separately and switch them through an appropriately rated relay. Follow electrical safety practices.

## 🌦️ Weather-Aware Irrigation (Crop Profile)

The crop-field mode is intended to combine soil moisture with weather forecasts to make an irrigation recommendation.

- Monitor soil moisture and temperature.
- Estimate how quickly the soil is drying.
- Check the forecast (planned integration: Open-Meteo).
- Recommend **irrigate** or **hold**, with a plain-language explanation.
- Hold irrigation when forecast rain makes watering unnecessary, where the decision logic supports it.

![Crop irrigation architecture](assets/crop-irrigation-architecture.png)

## 🗣️ Voice & RAG Assistant

Sarva Mitra is intended to reduce screen and language barriers for farmers.

- Ask questions in Telugu or Hindi by text or voice.
- Speech-to-text can convert voice notes to text (planned options include Bhashini or Whisper).
- The RAG assistant retrieves relevant information from public crop/farm advisories.
- Answers use advisory context together with current sensor readings and include source references.
- Text-to-speech can read alerts and answers aloud.
- WhatsApp or Telegram can serve as the farmer-facing channel, alongside a web dashboard.

## 📱 Dashboard Concept

The app/dashboard is planned to show:

- Current sensor readings (moisture, temperature, humidity or water metrics)
- Active farm profile
- Pump / relay status
- Latest ML decision and its reason
- Dry-soil, rain-hold, or risk alerts
- Ask-the-assistant screen with text/voice input
- Profile switching and optional history charts

## 🔁 Demo Workflow

The demo highlights how the same hardware and engine can adapt by changing a profile.

![Sarva Mitra demo workflow](assets/demo-workflow.png)

1. Show the device and explain the farm-monitoring problem.
2. Run the pond scenario and demonstrate sensor readings, a risk decision, relay action, and Telugu alert.
3. Switch to the crop-field profile.
4. Demonstrate dry-soil detection, irrigation action, and a Hindi advisory.
5. Explain scalability: a new farm type can be introduced through a new profile file.

## 🛠️ Planned Technology Stack

| Layer | Technology / option |
|---|---|
| IoT | ESP32, sensor modules, relay |
| API / backend | FastAPI (planned shared API) |
| Data storage | Cloud database / sensor history store |
| ML | Python, anomaly detection, short-term forecasting |
| Forecast data | Open-Meteo (planned) |
| AI assistant | LLM + Retrieval-Augmented Generation (RAG) |
| Knowledge sources | Public agriculture / fisheries advisories |
| Voice | Telugu/Hindi speech-to-text and text-to-speech services |
| Farmer interface | Web dashboard + WhatsApp/Telegram bot concept |

## 🗂️ Profile-Driven Design

A farm profile is a configuration file that describes how the system should behave. Example (illustrative demo configuration):

```json
{
  "profile": "fish_pond",
  "language_default": "te",
  "sensors": ["temp_c", "ph", "tds", "turbidity"],
  "limits": {
    "temp_c": { "warn": 32, "critical": 34 },
    "ph": { "min": 6.5, "max": 8.5 }
  },
  "forecast_horizon_hours": 4,
  "actions": {
    "on_risk": { "relay": 1, "state": "on", "label": "aerator" }
  }
}
```

*Thresholds above are illustrative only and must be reviewed for the target species, crop, environment, and local conditions.*

## 📈 Expected Impact

- Potentially reduce avoidable water and electricity usage through more informed irrigation decisions.
- Provide earlier warnings to help farmers respond before conditions become severe.
- Make farming information more accessible through Telugu and Hindi voice interactions.
- Reduce the need for separate monitoring hardware by reusing a configurable device.
- Support extension to additional crops and farm types through profile files.

These are project goals and expected benefits—not measured field results yet.

## 🚧 Project Status

**Prototype / hackathon build.** Sarva Mitra is a concept and development prototype. Hardware testing, model validation, sensor calibration, advisory verification, and field trials are needed before it can be relied on for real farm decisions.

## 👥 Team

| Member | Workstream |
|---|---|
| Teja | IoT, firmware, and app integration |
| Venkat | RAG assistant and advisory knowledge flow |
| Priyanshu | Machine Learning and decision engine |
| Tanaka | UI/UX and API integration |

## 🔮 Future Scope

- Support more crops, ponds, poultry, and greenhouse profiles
- Add real sensor datasets and field validation
- Improve forecasting and anomaly detection as more data becomes available
- Add history, multiple fields per account, and notification integrations
- Expand language and voice support
- Improve offline and simulated-data fallback modes

## 🤝 Contributing

Contributions, suggestions, and prototype improvements are welcome. Open an issue to discuss a change or submit a pull request with a clear description of what was improved.


## 📄 License

A license has not been selected yet. Add a license file before publishing this repository for open-source reuse.


---

<p align="center"><b>Sarva Mitra — One device. Any farm. Any language. 🌱</b></p>
