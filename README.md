# ☀ Solar PV Yield Calculator

A **mobile-first, full-stack web app** built with Flask that calculates solar panel energy yield using **real NASA satellite data** — no API key required!

---

## 🚀 How to Run on Replit

1. **Import this project** into Replit (upload all files or paste into a new Python Repl)
2. Click the green **▶ Run** button
3. Replit will install all dependencies automatically
4. Your public URL appears at the top — share it with anyone!

---

## 📁 File Structure

```
solar-pv-calculator/
├── main.py          # Flask app + all API endpoints
├── calculator.py    # Solar yield calculation engine
├── nasa_api.py      # NASA POWER API integration (free, no key)
├── requirements.txt # Python dependencies
├── .replit          # Replit configuration (one-click run)
├── README.md        # This file
└── templates/
    └── index.html   # Mobile-first frontend UI
```

---

## ⚡ Features

### Backend (Flask API)
| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Main web app |
| `/api/calculate` | POST | Full solar yield calculation |
| `/api/compare` | POST | Compare 2 system sizes |
| `/api/presets` | GET | Indian city presets |
| `/api/report` | POST | Download PDF report |

### Calculations Performed
- ✅ Daily / Monthly / Yearly energy output (kWh)
- ✅ Tilt angle correction (cosine model)
- ✅ System losses: wiring + inverter + dust (14% total)
- ✅ Monsoon seasonal loss factors for India
- ✅ Panel degradation: 0.5%/year over 25 years
- ✅ Electricity savings in ₹
- ✅ CO₂ reduction (0.82 kg/kWh, India grid factor)
- ✅ Trees equivalent calculation
- ✅ ROI + payback period
- ✅ Battery backup sizing (1-day & 2-day)
- ✅ Zero-electricity-bill system size suggestion
- ✅ 10-year AI forecast (linear regression with degradation)
- ✅ Side-by-side system comparison

### Frontend Features
- ✅ Mobile-first responsive design
- ✅ 🌙 Dark mode toggle
- ✅ Auto-detect location (browser geolocation)
- ✅ 10 Indian city presets (Mumbai, Delhi, Bengaluru, etc.)
- ✅ Interactive bar chart (monthly energy + savings)
- ✅ 10-year forecast line chart
- ✅ System comparison bar chart
- ✅ Monthly breakdown table
- ✅ PDF report download

---

## 📊 Data Source

**NASA POWER API** — Prediction Of Worldwide Energy Resources
- URL: https://power.larc.nasa.gov/
- Parameter: `ALLSKY_SFC_SW_DWN` (All-Sky Surface Shortwave Downward Irradiance)
- Resolution: Monthly averages (2015–2022), any location on Earth
- **100% FREE, no registration, no API key**

---

## 📦 Dependencies

All free, open-source Python libraries:
- `flask` — Web framework
- `requests` — HTTP client for NASA API
- `scikit-learn` — Linear regression for AI forecast
- `numpy` — Numerical computations
- `reportlab` — PDF generation

---

## 🇮🇳 Indian City Presets

| City | Lat | Lon | Optimal Tilt |
|---|---|---|---|
| Mumbai | 19.076 | 72.877 | 19° |
| Delhi | 28.704 | 77.102 | 29° |
| Bengaluru | 12.972 | 77.594 | 13° |
| Chennai | 13.083 | 80.270 | 13° |
| Kolkata | 22.573 | 88.364 | 23° |
| Hyderabad | 17.385 | 78.487 | 17° |
| Jaipur | 26.912 | 75.787 | 27° |
| Ahmedabad | 23.023 | 72.572 | 23° |
| Pune | 18.520 | 73.856 | 19° |
| Bhopal | 23.259 | 77.413 | 23° |

---

## 💡 Key Assumptions

- Installation cost: ₹50,000/kW (typical Indian market, 2024)
- CO₂ factor: 0.82 kg/kWh (India Central Electricity Authority)
- System losses: ~14% (wiring 3% + inverter 4% + dust/misc 7%)
- Panel degradation: 0.5%/year (industry standard)
- Battery DoD: 80% (typical for Li-ion)
- Monsoon loss: up to 35% reduction in July-August (India)

---

*Built with ❤ using Flask + NASA POWER API*
