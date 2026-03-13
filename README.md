# 🖥 Sentinel AI - SOC Dashboard

A premium security visualization dashboard built with Angular v20 and PrimeNG. This interface provides real-time visibility into the Sentinel AI intelligence engine.

## 🚀 Key Features
- **Live SOC Feed**: Real-time monitoring of alerts flowing through the backend.
- **Interactive AI Analysis**: Visual justification forทุก decision, including confidence metrics and technical reasoning.
- **Threat Intelligence**: Advanced charts showing attack trends and learned threat distributions.
- **Intelligence Control**: Integrated UI to trigger backend model retraining.
- **Audit History**: Searchable history of all past AI actions and reasoning.

## 🛠 Setup & Development

1. **Install Dependencies**:
   ```bash
   npm install
   ```

2. **Start Development Server**:
   ```bash
   npm start
   ```
   Navigate to `http://localhost:4200/`.

3. **Build for Production**:
   ```bash
   npm run build
   ```

## 🏗 Architecture
- **Core Services**: `ApiService` handles all REST communication with the FastAPI backend.
- **Feature Modules**: 
  - `Dashboard`: The main SOC hub with live widgets.
  - `Alertes`: Deep dive into current pending threats.
  - `Histoire`: The database of AI decisions.
- **Design System**: Built with modern CSS variables, glassmorphism, and interactive micro-animations for a premium feel.

## 🔗 Connection
The frontend is configured to connect to the backend at `http://127.0.0.1:8000`. This can be adjusted in:
`src/app/core/api.service.ts`

## 🧪 How to Test the Features

Follow these steps to verify the full SOC intelligence pipeline:

### 1. Simulate a Real-time Alert
Open a terminal and run a `curl` command (available in the Backend README). Example:
```bash
curl -X POST http://127.0.0.1:8000/process_alert -H "Content-Type: application/json" -d '{"attack_type": "brute_force", "failed_attempts": 25, "severity_score": 0.85, "ip_reputation": 0.7, "previous_incidents": 1}'
```
**Observation**: Go to the **"Histoire"** tab in the dashboard. You will see the alert appear automatically within 5 seconds thanks to the auto-polling mechanism.

### 2. Manual AI Analysis
1. Go to the **"Dashboard"** or **"Alertes"** tab.
2. Select any alert from the list.
3. In the right-side **AI Panel**, click the button **"◈ LANCER ANALYSE IA"**.
4. **Observation**: The status will change to "IA EN TRAIN D'ANALYSER...", then display the technical justification and decided action (Automated or Escalated).

### 3. Model Retraining
1. Look at the **Top Navigation Bar**.
2. Click the button **"⚙ RE-ENTRAINER MODÈLE"**.
3. **Observation**: The button will change to "RE-ENTRAINEMENT..." and the backend will rebuild the Random Forest model using all logged historical data, improving its future accuracy.

### 4. Interactive History
1. Navigate to the **"Histoire"** tab.
2. Click on any past decision.
3. **Observation**: The AI Panel will update to show exactly what reasoning and metrics were used for that specific historical event.
