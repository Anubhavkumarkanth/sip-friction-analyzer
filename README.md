# 📊 SIP Friction Analyzer

> **Visualize the Real Cost of Investment Indiscipline** — An advanced financial simulator that models how investor behavior friction affects systematic investment plan (SIP) wealth accumulation.

![React](https://img.shields.io/badge/React-19.2.4-61DAFB?style=flat-square&logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688?style=flat-square&logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

## 🎯 Problem Statement

Most investor education tools talk about SIP returns in a vacuum. But real-world wealth accumulation depends heavily on **investor discipline**.

**SIP Friction Analyzer** quantifies the hidden cost of:
- ❌ Pausing investments during market downturns
- ❌ Reducing contribution amounts
- ❌ Increasing/decreasing investments emotionally
- ❌ Skipping months entirely

This is a **full-stack financial simulator** that educates investors about discipline's compound impact.

---

## ✨ Key Features

### 📈 **SIP Simulation Engine**
- Month-by-month wealth accumulation with real compound interest
- Customizable friction events (Pause, Skip, Reduce, Increase, Step-up)
- Dual visualization: Ideal (disciplined) vs. Actual (with friction)
- Automatically calculates financial metrics:
  - **Ideal Wealth**: Perfect discipline scenario
  - **Actual Wealth**: Realistic path with events
  - **Compounding Loss**: Quantified cost of friction
  - **CCR** (Contribution Compliance Rate): % of intended contributions made
  - **Discipline Score**: 0-100 metric combining CCR and compounding loss

### 🔍 **Fund Explorer**
- Search 5,000+ mutual funds across platforms (Groww, Zerodha, Angel One)
- Filter by risk level, category, returns
- One-click detailed analysis
- Compare funds side-by-side with key metrics

### 📊 **Interactive Charts**
- Real-time responsive area charts with Recharts
- Tooltip showing exact values at any year
- Professional glass-morphism design
- Mobile-optimized visualization

### 💾 **Investor Archetypes** (Coming Soon)
- Conservative, Moderate, Aggressive profiles
- Auto-populated friction events based on profile
- Benchmark results against historical Nifty 50/Sensex

---

## 📖 How It Works

### 1. Configure Your SIP
```
Monthly Amount: ₹10,000
Annual Return: 12%
Investment Period: 20 years
```

### 2. Add Friction Events
- **Pause SIP**: Stop contributing for months (e.g., during market crash)
- **Step Up**: Increase contributions annually by %
- **Reduce SIP**: Temporarily reduce amount
- **Skip Month**: Skip a specific month
- **Increase**: Boost contribution amount

### 3. Run Simulation
The engine calculates:
- All 240 monthly values with compound growth
- Event impact on actual wealth accumulation
- Comparative metrics vs. ideal disciplined investor

### 4. Analyze Results
- See the "friction loss" visualized as grey area
- Check your discipline score (0-100)
- Compare against other investor profiles

---

## 📈 Metrics Explained

### **CCR (Contribution Compliance Rate)**
```
CCR = Total Actual Contributions / Total Expected Contributions
```
- **90-100%**: Excellent discipline ✅
- **60-90%**: Good discipline ⚠️
- **<60%**: Poor discipline ❌

### **Compounding Loss (CLD)**
```
CLD = Ideal Wealth - Actual Wealth
```
The absolute rupee amount lost due to friction events.

### **Discipline Score**
```
Score = 100 - (40 × (1 - CCR) + 60 × (CLD / Ideal Wealth))
```
Weighted penalty combining:
- 40% weight: Contribution consistency
- 60% weight: Compounding impact

---

