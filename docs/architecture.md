# WeatherGPT architecture overview

WeatherGPT has a responsive React/Vite client and a FastAPI backend. The client provides Home, Chat, Travel, Disaster, Settings, and Farmer Mode flows. The backend receives location-aware requests, resolves intent, fetches data through a cache and a degradation ladder, normalizes verified facts, and returns a grounded response with provenance.

```text
User (web / voice)
        |
React + Vite frontend
        |
FastAPI API
  |-- geocoding and intent handling
  |-- live-weather source ladder and cache
  |-- grounding and response assembly
  |-- farmer, travel, and disaster modules
        |
Weather APIs / geocoding / optional LLM phrasing
```

The detailed component diagram, API contract, data-source approach, failure behaviour, and planned enhancements are documented in [SIH26068_WeatherGPT_Architecture_and_Build_Plan.md](SIH26068_WeatherGPT_Architecture_and_Build_Plan.md).
