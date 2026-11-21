DOC_ID: 00_README_manifest
TITLE: Corpus manifest and rules for use (SARVA-MITRA agricultural knowledge corpus)
CROPS: tomato; chilli; ragi (finger millet)
SENSOR_SIGNALS: soil_moisture_pct; temperature_c; humidity_pct; leaf_wet; rainfall_mm; sunlight_wm2; soil_ec_dsm
EMBED: no (meta file for the team; do not embed)

PURPOSE
This corpus supports a RAG system that advises small farmers in Karnataka, including Bengaluru, from IoT sensor readings and an ML abnormality output. It is written in English for internal retrieval. Answers are produced by the Groq LLM from retrieved chunks. Embeddings use Hugging Face sentence-transformers; vectors are stored in MongoDB Atlas Vector Search.

CORPUS RULES
1. One logical topic per file; one .txt file per topic. Each file starts with DOC_ID, TITLE, CROPS and SENSOR_SIGNALS.
2. Every agricultural statement carries a source tag [S#] that points to the REFERENCES list at the end of the same file. Source tags are local to a file, so a citation in an answer must give DOC_ID and tag together.
3. No pesticide product names, doses, mixing instructions or spray schedules are included. Where a source names a chemical option, the file says so without the name and refers the farmer to the KVK or agriculture officer. Registration status of chemicals in Karnataka could not be verified, so none are named.
4. No disease classifier, no diagnosis and no invented sensor threshold. Where reliable information is not available, the file says UNAVAILABLE.
5. Sensor readings indicate risk, not diagnosis. The ML output is only an abnormality signal. No file may say that a reading or ML output confirms a disease.
6. Crop names are written consistently. CROPS lines use: tomato; chilli; ragi (finger millet). Running text uses the short forms tomato, chilli and ragi. Spellings such as "chili", "tomatoes", "capsicum" and "brinjal" are not used outside reference titles.
7. Units are always written: °C, %, dS/m, mm, W/m2, hours.

EVIDENCE LABELS USED INSIDE FILES
Type: OBS = directly observed or stated fact; FAV = sensor condition that only favours a problem; INSP = physical symptom that needs field inspection; PHYS = physiological disorder (not an infection); WEAK = uncertain or weak evidence.
Origin: KA = Karnataka / UAS Bengaluru; IN = India (ICAR, NIPHM, TNAU and other Indian bodies; TNAU is a Tamil Nadu university, not Karnataka); INTL = international research or extension; SEC = course or secondary material.
Other prefixes: UNAVAILABLE = information not available; CORPUS RULE and CORPUS NOTE = guidance from the corpus team, not an agricultural source.

SUPPORTED CROPS
tomato; chilli; ragi (finger millet). Other crops named in sources (potato, brinjal, capsicum) are not supported. Where a source studied potato, the line is marked POTATO-DERIVED.

WEATHER SOURCE GEOGRAPHY
Karnataka-origin weather data is present only for ragi (UAS Bengaluru tables, 16_ragi_weather_uas_bengaluru_tables), and its week-level alignment is uncertain. Indian values come from Tamil Nadu (TNAU), national (NIPHM, ICAR) and Haryana (CCSHAU) sources. All other thresholds are international, mainly from the USA, Canada, Australia, France, Egypt, China and Japan, and were not measured in Karnataka. Each file has a SOURCE GEOGRAPHY section.

VERIFICATION STATUS
- This rebuild restructured and cleaned the previous corpus. Sources and URLs are carried forward from the previous version, whose manifest stated the pages were retrieved on 21 Nov 2026. The pages were not re-opened during this rebuild. Re-check key thresholds against the links before production use.
- Structural checks (unique DOC_ID values, source tags defined, no doses, unit presence, crop spelling) were run by script on the final files.
- Some source locations are marked "not verified" where the carried-forward record did not state them.

KNOWN LIMITS
- The dataset has no crop column. Ask the farmer.
- Most weather thresholds are biological limits from non-Karnataka studies. They may transfer, but this is not confirmed.
- Two Indian pages (NIPHM/Vikaspedia) had scrambled text when retrieved; only clearly attributed lines were kept.

TOPIC MAP (requested topic to DOC_ID)
- Crop-specific disease conditions, identification and management: 03 to 17 (each file has its own identification, symptoms, field inspection and management sections).
- Weather thresholds: 02, 16
- Soil moisture effects: 21
- Soil salinity: 20
- Heat stress: 19
- Physiological disorder: 18
- Healthy-state improvements: 22
- Field hygiene: 24 (new document; ID assigned in this rebuild, please confirm)
- Master prompt: 23

DOC_ID LIST
00_README_manifest (not embedded)
01_dataset_columns_reference (not embedded)
02_weather_thresholds_by_disease
03_late_blight_tomato_potato
04_early_blight_tomato_potato
05_septoria_leaf_spot_tomato
06_powdery_mildew_tomato_chilli
07_gray_mold_botrytis_tomato
08_tomato_bacterial_leaf_spot
09_bacterial_wilt_ralstonia
10_fusarium_wilt_tomato
11_damping_off_seedlings
12_tomato_leaf_curl_virus_whitefly
13_chilli_anthracnose_dieback_fruit_rot
14_chilli_other_diseases_conditions
15_ragi_blast
16_ragi_weather_uas_bengaluru_tables
17_ragi_other_diseases_and_varieties
18_blossom_end_rot_tomato
19_heat_stress_fruit_set_tomato
20_soil_salinity_ec_tomato
21_soil_moisture_effects_by_disease
22_healthy_state_betterments
23_master_prompt (not embedded)
24_field_hygiene

ID NOTES
- Existing IDs 02 to 22 were kept because each existing document was updated. IDs containing "potato" (03, 04) were kept for continuity; their content is tomato only.
- 24_field_hygiene is the only new ID. No other IDs were invented.
