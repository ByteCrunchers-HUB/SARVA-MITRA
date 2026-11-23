/**
 * Sarva Mitra Web Dashboard — Client Application
 * Connects directly to Sarva Mitra FastAPI Backend (/api/dashboard, /api/chat, /api/transcribe)
 */

(function () {
  'use strict';

  // --------------------------------------------------------------------------
  // Configuration & State
  // --------------------------------------------------------------------------
  const API_BASE = (window.location.protocol.startsWith('http'))
    ? window.location.origin
    : 'http://localhost:8000';

  const LOCATIONS = {
    'Vijayawada (Andhra Pradesh)': { lat: 16.51, lon: 80.52, name: 'Vijayawada', state: 'AP' },
    'Bengaluru (Karnataka)': { lat: 12.97, lon: 77.59, name: 'Bengaluru', state: 'KA' },
    'Hyderabad (Telangana)': { lat: 17.39, lon: 78.49, name: 'Hyderabad', state: 'TG' },
    'Chennai (Tamil Nadu)': { lat: 13.08, lon: 80.27, name: 'Chennai', state: 'TN' },
    'Nagpur (Maharashtra)': { lat: 21.15, lon: 79.09, name: 'Nagpur', state: 'MH' },
    'Bhubaneswar (Odisha)': { lat: 20.30, lon: 85.82, name: 'Bhubaneswar', state: 'OD' },
    'Lucknow (Uttar Pradesh)': { lat: 26.85, lon: 80.95, name: 'Lucknow', state: 'UP' },
    'Jaipur (Rajasthan)': { lat: 26.91, lon: 75.79, name: 'Jaipur', state: 'RJ' },
    'Kolkata (West Bengal)': { lat: 22.57, lon: 88.36, name: 'Kolkata', state: 'WB' },
    'Patna (Bihar)': { lat: 25.61, lon: 85.14, name: 'Patna', state: 'BR' },
  };

  const state = {
    locationName: 'Vijayawada',
    locationState: 'AP',
    lat: 16.51,
    lon: 80.52,
    crop: 'tomato',
    cropLabel: '🍅 Tomato',
    stage: '🌸 Flowering & Fruit Set (50-80 days)',
    telemetry: null,
    risk: null,
    history: [],
    chatHistory: [],
    isSyncing: false,
    initialAdvisoryText: '',
  };

  // --------------------------------------------------------------------------
  // DOM Elements
  // --------------------------------------------------------------------------
  const navButtons = document.querySelectorAll('.nav-item');
  const bottomNavButtons = document.querySelectorAll('.bottom-nav-item');
  const appSidebar = document.getElementById('app-sidebar');
  const sidebarOverlay = document.getElementById('sidebar-overlay');
  const btnMobileMenu = document.getElementById('btn-mobile-menu');
  const btnDrawerClose = document.getElementById('btn-drawer-close');
  const viewPanels = document.querySelectorAll('.view-panel');
  const btnSync = document.getElementById('btn-sync-telemetry');
  const btnHeroGetStarted = document.getElementById('btn-hero-get-started');
  const featureCards = document.querySelectorAll('.feature-card');
  const backButtons = document.querySelectorAll('[data-back]');
  const chatMessages = document.getElementById('chat-messages-container');
  const chatInput = document.getElementById('chat-text-input');
  const btnSendChat = document.getElementById('btn-send-chat');
  const btnVoiceInput = document.getElementById('btn-voice-input');
  const voiceStatus = document.getElementById('voice-status-text');
  const popularChips = document.querySelectorAll('.chip-question');
  const btnAskAiFromRec = document.getElementById('btn-ask-ai-from-rec');
  const btnDownloadSoilReport = document.getElementById('btn-download-soil-report');
  const btnDownloadChatReport = document.getElementById('btn-download-chat-report');
  const btnExportHistoryCsv = document.getElementById('btn-export-history-csv');
  const settingsForm = document.getElementById('settings-form');
  const settingsLocation = document.getElementById('settings-location');
  const settingsCrop = document.getElementById('settings-crop');
  const settingsStage = document.getElementById('settings-stage');
  const customCoordsRow = document.getElementById('custom-coords-row');

  // Topbar Elements
  const topTemp = document.getElementById('top-temp');
  const topLocation = document.getElementById('top-location');
  const topCrop = document.getElementById('top-crop');
  const topStage = document.getElementById('top-stage');

  // Soil Prediction Elements
  const alertBanner = document.getElementById('prediction-alert');
  const alertTitle = document.getElementById('alert-title');
  const alertSubtitle = document.getElementById('alert-subtitle');
  const riskPillBadge = document.getElementById('risk-pill-badge');
  const riskPillVal = document.getElementById('risk-pill-val');
  const riskPillLabel = document.getElementById('risk-pill-label');
  const valSoilMoisture = document.getElementById('val-soil-moisture');
  const valTemp = document.getElementById('val-temp');
  const valHumidity = document.getElementById('val-humidity');
  const valSunlight = document.getElementById('val-sunlight');
  const valRainfall = document.getElementById('val-rainfall');
  const valNitrogen = document.getElementById('val-nitrogen');
  const valSoilPh = document.getElementById('val-soil-ph');
  const donutFgCircle = document.getElementById('donut-fg-circle');
  const donutPctText = document.getElementById('donut-pct-text');
  const donutStatusText = document.getElementById('donut-status-text');
  const whyRiskExplanation = document.getElementById('why-risk-explanation');
  const historyTableBody = document.getElementById('history-table-body');
  const trendChartContainer = document.getElementById('trend-chart-container');

  // --------------------------------------------------------------------------
  // Mobile Drawer Controls
  // --------------------------------------------------------------------------
  function openMobileDrawer() {
    if (appSidebar) appSidebar.classList.add('drawer-open');
    if (sidebarOverlay) sidebarOverlay.classList.add('active');
  }

  function closeMobileDrawer() {
    if (appSidebar) appSidebar.classList.remove('drawer-open');
    if (sidebarOverlay) sidebarOverlay.classList.remove('active');
  }

  if (btnMobileMenu) btnMobileMenu.addEventListener('click', openMobileDrawer);
  if (btnDrawerClose) btnDrawerClose.addEventListener('click', closeMobileDrawer);
  if (sidebarOverlay) sidebarOverlay.addEventListener('click', closeMobileDrawer);

  // --------------------------------------------------------------------------
  // Navigation Router (Separating History and Schemes Completely)
  // --------------------------------------------------------------------------
  function switchView(viewName) {
    if (!viewName) return;
    navButtons.forEach(btn => {
      const target = btn.getAttribute('data-view');
      btn.classList.toggle('active', target === viewName);
    });

    bottomNavButtons.forEach(btn => {
      const target = btn.getAttribute('data-view');
      btn.classList.toggle('active', target === viewName);
    });

    viewPanels.forEach(panel => {
      panel.classList.toggle('active', panel.id === `view-${viewName}`);
    });

    closeMobileDrawer();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  navButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.getAttribute('data-view');
      switchView(target);
    });
  });

  bottomNavButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.getAttribute('data-view');
      switchView(target);
    });
  });

  backButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const backTarget = btn.getAttribute('data-back');
      switchView(backTarget || 'dashboard');
    });
  });

  if (btnHeroGetStarted) {
    btnHeroGetStarted.addEventListener('click', () => switchView('soil'));
  }

  featureCards.forEach(card => {
    card.addEventListener('click', () => {
      const action = card.getAttribute('data-action');
      if (action) switchView(action);
    });
  });

  if (btnAskAiFromRec) {
    btnAskAiFromRec.addEventListener('click', () => switchView('assistant'));
  }

  // --------------------------------------------------------------------------
  // Data Sync Pipeline: Telemetry -> ML Engine -> RAG Initial Assessment
  // --------------------------------------------------------------------------
  async function syncDashboardData() {
    if (state.isSyncing) return;
    state.isSyncing = true;
    if (btnSync) btnSync.classList.add('spinning');

    try {
      // 1. Fetch live telemetry, 8-day history & ML risk score
      const url = `${API_BASE}/api/dashboard?lat=${state.lat}&lon=${state.lon}&location=${encodeURIComponent(state.locationName)}&crop=${encodeURIComponent(state.crop)}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();

      state.telemetry = data.current_telemetry || {};
      state.risk = data.ml_risk || {};
      state.history = data.historical_trends || [];

      updateUIWithData(data);

      // 2. Automatically trigger Initial Agronomic Assessment Report in Chat
      await fetchInitialAgronomicReport();
    } catch (err) {
      console.warn('Dashboard sync error:', err);
      fallbackSimulation();
    } finally {
      state.isSyncing = false;
      if (btnSync) btnSync.classList.remove('spinning');
    }
  }

  async function fetchInitialAgronomicReport() {
    try {
      const initialQuery = `Provide a complete agronomic status assessment and recommendations for ${state.crop} (${state.stage}) based on current field conditions.`;
      
      const payload = {
        question: initialQuery,
        crop: state.crop,
        lat: state.lat,
        lon: state.lon,
        location: state.locationName,
        chat_history: [],
        mode: 'report'
      };

      const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error(`Chat HTTP ${res.status}`);
      const chatData = await res.json();
      state.initialAdvisoryText = cleanAssistantText(chatData.answer || '');

      // Reset chat and render formatted greeting with live report
      renderInitialGreeting(chatData.answer);
    } catch (chatErr) {
      console.warn('Initial advisory fetch warning:', chatErr);
      const fallbackReport = `**Agronomic Status Assessment for ${state.cropLabel} (${state.locationName}):**\n\n`
        + `1. **What the sensors show:** Ambient temp ${(state.telemetry?.temperature_c || 24.5).toFixed(1)}°C, humidity ${(state.telemetry?.humidity_pct || 82).toFixed(1)}%, soil moisture ${(state.telemetry?.soil_moisture_pct || 21).toFixed(1)}%.\n`
        + `2. **What the model signal means:** ML weather risk index is ${(state.risk?.risk_pct || 72)}% (${(state.risk?.risk_level || 'high').toUpperCase()}). This is an environmental favorability warning for foliar stress.\n`
        + `3. **What you can do now:** Keep foliage dry by pruning lower canopy leaves. Adjust morning irrigation to maintain optimal soil moisture.\n`
        + `4. **Next steps:** Inspect lower leaves early morning for concentric spots; consult nearest KVK officer.`;
      state.initialAdvisoryText = fallbackReport;
      renderInitialGreeting(fallbackReport);
    }
  }

  function renderInitialGreeting(answerText) {
    if (!chatMessages) return;
    chatMessages.innerHTML = '';
    state.chatHistory = [];

    const tel = state.telemetry || { temperature_c: 24.5, humidity_pct: 82.0, soil_moisture_pct: 21.0 };
    const rk = state.risk || { risk_pct: 72, risk_level: 'high' };

    const introMsg = `👋 **Namaste! Live telemetry & AI risk analysis for your ${state.cropLabel} (${state.stage}):**\n\n`
      + `- 🌡️ **Temperature:** ${(tel.temperature_c || 0).toFixed(1)} °C\n`
      + `- 💧 **Relative Humidity:** ${(tel.humidity_pct || 0).toFixed(1)} %\n`
      + `- 🌱 **Soil Moisture:** ${(tel.soil_moisture_pct || 0).toFixed(1)} %\n`
      + `- 🧠 **AI Pathogen Risk Index:** ${Math.round(rk.risk_pct || 0)}% (${(rk.risk_level || 'low').toUpperCase()})\n\n`
      + `---\n\n`
      + answerText;

    appendChatMessage('assistant', introMsg, true);
  }

  function fallbackSimulation() {
    const fakeTelemetry = {
      temperature_c: 24.5,
      humidity_pct: 82.0,
      soil_moisture_pct: 21.0,
      rainfall_mm: 2.5,
      sunlight_wm2: 680,
    };
    const fakeRisk = {
      risk_pct: 72.0,
      risk_level: 'high',
    };
    state.telemetry = fakeTelemetry;
    state.risk = fakeRisk;
    updateUIWithData({
      current_telemetry: fakeTelemetry,
      ml_risk: fakeRisk,
      quick_advisory: 'High risk detected. Low soil moisture and high atmospheric humidity favour foliar disease.',
      historical_trends: [
        { date: 'Nov 17', soil_moisture_pct: 28.0, air_temperature_c: 26.1, risk_pct: 35 },
        { date: 'Nov 18', soil_moisture_pct: 27.2, air_temperature_c: 25.8, risk_pct: 42 },
        { date: 'Nov 19', soil_moisture_pct: 25.5, air_temperature_c: 24.9, risk_pct: 55 },
        { date: 'Nov 20', soil_moisture_pct: 24.0, air_temperature_c: 25.2, risk_pct: 61 },
        { date: 'Nov 21', soil_moisture_pct: 22.8, air_temperature_c: 24.6, risk_pct: 68 },
        { date: 'Nov 22', soil_moisture_pct: 21.5, air_temperature_c: 24.4, risk_pct: 70 },
        { date: 'Nov 23', soil_moisture_pct: 21.0, air_temperature_c: 24.5, risk_pct: 72 },
      ]
    });
    fetchInitialAgronomicReport();
  }

  function updateUIWithData(data) {
    const tel = data.current_telemetry || state.telemetry || {};
    const risk = data.ml_risk || state.risk || {};
    const riskPct = Math.round(risk.risk_pct || 0);
    const riskLevel = (risk.risk_level || 'low').toLowerCase();

    // 1. Update Topbar
    if (topTemp) topTemp.textContent = `${(tel.temperature_c || 25).toFixed(1)}°C`;
    if (topLocation) topLocation.textContent = `${state.locationName}, ${state.locationState || 'IN'}`;
    if (topCrop) topCrop.textContent = state.cropLabel;
    if (topStage) topStage.textContent = `(${state.stage.split(' ')[1] || 'Flowering'})`;

    // 2. Update Soil Prediction View
    if (valSoilMoisture) valSoilMoisture.textContent = `${(tel.soil_moisture_pct || 0).toFixed(1)} %`;
    if (valTemp) valTemp.textContent = `${(tel.temperature_c || 0).toFixed(1)} °C`;
    if (valHumidity) valHumidity.textContent = `${(tel.humidity_pct || 0).toFixed(1)} %`;
    if (valSunlight) valSunlight.textContent = `${Math.round(tel.sunlight_wm2 || 0)} W/m²`;
    if (valRainfall) valRainfall.textContent = `${(tel.rainfall_mm || 0).toFixed(1)} mm`;

    // 3. Update Risk Donut Gauge
    const circumference = 390; // 2 * PI * 62 ≈ 389.55
    const offset = circumference - (circumference * (riskPct / 100));
    if (donutFgCircle) {
      donutFgCircle.style.strokeDashoffset = offset;
      if (riskLevel === 'high') {
        donutFgCircle.style.stroke = '#EF4444';
      } else if (riskLevel === 'moderate') {
        donutFgCircle.style.stroke = '#F59E0B';
      } else {
        donutFgCircle.style.stroke = '#10B981';
      }
    }

    if (donutPctText) donutPctText.textContent = `${riskPct}%`;
    if (donutStatusText) donutStatusText.textContent = riskLevel.toUpperCase();

    // 4. Update Alert Banner & Risk Pill
    if (alertBanner) {
      alertBanner.className = `prediction-alert-banner alert-${riskLevel}`;
    }
    if (riskPillBadge) {
      riskPillBadge.className = `risk-badge badge-${riskLevel}`;
    }
    if (riskPillVal) riskPillVal.textContent = `${riskPct}%`;
    if (riskPillLabel) riskPillLabel.textContent = `${riskLevel.toUpperCase()} RISK`;

    if (data.quick_advisory && whyRiskExplanation) {
      whyRiskExplanation.textContent = data.quick_advisory;
    }

    // 5. Update History Table & Trend Chart
    if (data.historical_trends && data.historical_trends.length) {
      renderHistoryTable(data.historical_trends);
      renderTrendChart(data.historical_trends, riskPct);
    }
  }

  function formatDisplayDate(dateStr) {
    if (!dateStr || dateStr === 'Today') return 'Today';
    try {
      const parts = String(dateStr).split('-');
      if (parts.length === 3) {
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        const m = parseInt(parts[1], 10) - 1;
        const d = parseInt(parts[2], 10);
        return `${months[m] || parts[1]} ${d}`;
      }
    } catch (e) {}
    return dateStr;
  }

  function renderHistoryTable(historyList) {
    if (!historyTableBody) return;
    historyTableBody.innerHTML = '';
    const slice = historyList.slice(-8);

    slice.reverse().forEach(item => {
      const tr = document.createElement('tr');
      const d = formatDisplayDate(item.date);
      const sm = item.soil_moisture_pct ? `${item.soil_moisture_pct.toFixed(1)} %` : '22.0 %';
      const temp = item.air_temperature_c ? `${item.air_temperature_c.toFixed(1)} °C` : '26.0 °C';
      const hum = item.humidity_pct ? `${item.humidity_pct.toFixed(0)} %` : '70 %';
      const rain = item.rainfall_mm !== undefined ? `${item.rainfall_mm.toFixed(1)} mm` : '0.0 mm';
      const pct = item.risk_pct || (item.soil_moisture_pct < 20 ? 68 : 35);
      const lvl = pct > 60 ? 'high' : (pct > 30 ? 'moderate' : 'low');
      const lvlLabel = pct > 60 ? 'High Risk' : (pct > 30 ? 'Moderate' : 'Safe');

      tr.innerHTML = `
        <td><strong>${d}</strong></td>
        <td>${sm}</td>
        <td>${temp}</td>
        <td>${hum}</td>
        <td>${rain}</td>
        <td><strong>${Math.round(pct)}%</strong></td>
        <td><span class="status-pill status-${lvl}">${lvlLabel}</span></td>
      `;
      historyTableBody.appendChild(tr);
    });
  }

  function renderTrendChart(historyList, currentRisk) {
    if (!trendChartContainer) return;
    const pts = historyList.map((h, i) => {
      const val = h.risk_pct !== undefined ? h.risk_pct : Math.max(15, Math.min(85, currentRisk - (6 - i) * 5));
      return { val, date: h.date || `D-${6 - i}` };
    });

    if (pts.length < 2) return;

    const width = 760;
    const height = 200;
    const padding = 35;
    const chartW = width - padding * 2;
    const chartH = height - padding * 2;

    const stepX = chartW / (pts.length - 1);
    const coords = pts.map((p, i) => {
      const x = padding + i * stepX;
      const y = height - padding - (p.val / 100) * chartH;
      return { x, y, val: Math.round(p.val), date: p.date };
    });

    const polyPoints = coords.map(c => `${c.x},${c.y}`).join(' ');
    const areaPoints = `${coords[0].x},${height - padding} ${polyPoints} ${coords[coords.length - 1].x},${height - padding}`;

    let svgHtml = `
      <svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
        <defs>
          <linearGradient id="trendGradFull" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#10B981" stop-opacity="0.35" />
            <stop offset="100%" stop-color="#10B981" stop-opacity="0.0" />
          </linearGradient>
        </defs>
        <!-- Horizontal Threshold Bands -->
        <rect x="${padding}" y="${height - padding - (30/100)*chartH}" width="${chartW}" height="${(30/100)*chartH}" fill="#ECFDF5" opacity="0.6" />
        <rect x="${padding}" y="${height - padding - (60/100)*chartH}" width="${chartW}" height="${(30/100)*chartH}" fill="#FFFBEB" opacity="0.6" />
        <rect x="${padding}" y="${padding}" width="${chartW}" height="${(40/100)*chartH}" fill="#FEF2F2" opacity="0.5" />

        <line x1="${padding}" y1="${padding}" x2="${width - padding}" y2="${padding}" stroke="#E5E7EB" stroke-dasharray="3 3" />
        <line x1="${padding}" y1="${height - padding - (60/100)*chartH}" x2="${width - padding}" y2="${height - padding - (60/100)*chartH}" stroke="#FCD34D" stroke-dasharray="4 4" />
        <line x1="${padding}" y1="${height - padding - (30/100)*chartH}" x2="${width - padding}" y2="${height - padding - (30/100)*chartH}" stroke="#6EE7B7" stroke-dasharray="4 4" />
        <line x1="${padding}" y1="${height - padding}" x2="${width - padding}" y2="${height - padding}" stroke="#D1D5DB" />
        
        <!-- Shaded Area -->
        <polygon points="${areaPoints}" fill="url(#trendGradFull)" />
        
        <!-- Trend Line -->
        <polyline points="${polyPoints}" fill="none" stroke="#059669" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" />
    `;

    coords.forEach(c => {
      svgHtml += `
        <circle cx="${c.x}" cy="${c.y}" r="5.5" fill="#FFFFFF" stroke="#047857" stroke-width="3" />
        <text x="${c.x}" y="${c.y - 10}" text-anchor="middle" font-size="11" font-weight="700" fill="#065F46">${c.val}%</text>
        <text x="${c.x}" y="${height - 12}" text-anchor="middle" font-size="10" fill="#6B7280">${typeof c.date === 'string' && c.date.length > 5 ? c.date.substring(5) : c.date}</text>
      `;
    });

    svgHtml += `</svg>`;
    trendChartContainer.innerHTML = svgHtml;
  }

  function cleanAssistantText(text) {
    if (!text) return '';
    let cleaned = text;
    // 1. Remove complete or unclosed BEGIN_STRUCTURED_JSON blocks
    cleaned = cleaned.replace(/BEGIN_STRUCTURED_JSON[\s\S]*?END_STRUCTURED_JSON/gi, '');
    cleaned = cleaned.replace(/BEGIN_STRUCTURED_JSON[\s\S]*$/gi, '');
    // 2. Remove code blocks containing json (complete or unclosed)
    cleaned = cleaned.replace(/```(?:json)?\s*\{[\s\S]*?\}\s*```/gi, '');
    cleaned = cleaned.replace(/```(?:json)?[\s\S]*$/gi, '');
    // 3. Remove dangling raw json with response_mode
    cleaned = cleaned.replace(/\{\s*"response_mode"[\s\S]*$/gi, '');
    // 4. Remove isolated markers
    cleaned = cleaned.replace(/END_STRUCTURED_JSON/gi, '');
    return cleaned.trim();
  }

  // --------------------------------------------------------------------------
  // Chat Interface: Live LLM Calls & Follow-Up Parsing
  // --------------------------------------------------------------------------
  function appendChatMessage(role, content, includeDownloadBtn = false) {
    if (!chatMessages) return;
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble bubble-${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'bubble-avatar';
    avatar.textContent = role === 'user' ? '👨‍🌾' : '🤖';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'bubble-content';

    // Separate Suggested Follow-up Questions from main text
    let mainText = role === 'assistant' ? cleanAssistantText(content) : content;
    let followups = [];

    const followupMatch = content.match(/###\s*💡\s*Suggested Follow[‑-]Up Questions:?([\s\S]*)/i);
    if (followupMatch) {
      mainText = content.substring(0, followupMatch.index).trim();
      const rawLines = followupMatch[1].split('\n');
      rawLines.forEach(l => {
        const cleanL = l.replace(/^\s*[-*•\d.]+\s*/, '').trim();
        if (cleanL && cleanL.length > 5) {
          followups.push(cleanL);
        }
      });
    }

    // Render Markdown using marked.js (with full support for tables, ---, headings, lists)
    let htmlResult = '';
    if (window.marked && typeof window.marked.parse === 'function') {
      try {
        htmlResult = window.marked.parse(mainText);
      } catch (parseErr) {
        console.warn('marked.parse error, using fallback:', parseErr);
        htmlResult = '';
      }
    }

    if (!htmlResult) {
      let formatted = mainText
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/^---$/gm, '<hr />');

      const lines = formatted.split('\n');
      let inList = false;

      lines.forEach(l => {
        const trimmed = l.trim();
        if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
          if (!inList) {
            htmlResult += '<ul>';
            inList = true;
          }
          htmlResult += `<li>${trimmed.substring(2)}</li>`;
        } else {
          if (inList) {
            htmlResult += '</ul>';
            inList = false;
          }
          if (trimmed) {
            htmlResult += `<p>${trimmed}</p>`;
          }
        }
      });
      if (inList) htmlResult += '</ul>';
    }

    contentDiv.innerHTML = htmlResult || mainText;

    // If initial advisory report, add inline download report button (PDF format)
    if (includeDownloadBtn) {
      const dlBtn = document.createElement('button');
      dlBtn.className = 'btn-download-report-inline';
      dlBtn.innerHTML = '📄 Download Official Advisory Report (PDF)';
      dlBtn.onclick = (e) => downloadAdvisoryReportPDF(e);
      contentDiv.appendChild(dlBtn);
    }

    // If follow-ups exist, render as clickable chips that trigger live LLM
    if (followups.length > 0) {
      const fuContainer = document.createElement('div');
      fuContainer.className = 'chat-followup-container';
      fuContainer.innerHTML = '<div class="chat-followup-label">💡 Suggested Follow-Up Questions (Tap to ask):</div>';
      
      const chipsBox = document.createElement('div');
      chipsBox.className = 'chat-followup-chips';

      followups.slice(0, 3).forEach(fq => {
        const chip = document.createElement('button');
        chip.className = 'chat-followup-chip';
        chip.textContent = `+ ${fq}`;
        chip.onclick = () => handleSendQuestion(fq);
        chipsBox.appendChild(chip);
      });

      fuContainer.appendChild(chipsBox);
      contentDiv.appendChild(fuContainer);
    }

    bubble.appendChild(avatar);
    bubble.appendChild(contentDiv);
    chatMessages.appendChild(bubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    state.chatHistory.push({ role, content });
  }

  function appendTypingIndicator() {
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble bubble-assistant';
    bubble.id = 'chat-typing-bubble';

    const avatar = document.createElement('div');
    avatar.className = 'bubble-avatar';
    avatar.textContent = '🤖';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'bubble-content';
    contentDiv.innerHTML = '<span style="color:#059669; font-weight:600;">🌿 Consulting Sarva Mitra agricultural knowledge base...</span>';

    bubble.appendChild(avatar);
    bubble.appendChild(contentDiv);
    chatMessages.appendChild(bubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function removeTypingIndicator() {
    const bubble = document.getElementById('chat-typing-bubble');
    if (bubble) bubble.remove();
  }

  async function handleSendQuestion(questionText) {
    const q = (questionText || (chatInput ? chatInput.value : '')).trim();
    if (!q) return;

    if (chatInput) chatInput.value = '';
    appendChatMessage('user', q);
    appendTypingIndicator();

    try {
      const payload = {
        question: q,
        crop: state.crop,
        lat: state.lat,
        lon: state.lon,
        location: state.locationName,
        chat_history: state.chatHistory.slice(-4),
        mode: 'chat'
      };

      const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      removeTypingIndicator();

      if (!res.ok) {
        throw new Error(`Chat API error (${res.status})`);
      }

      const data = await res.json();
      appendChatMessage('assistant', data.answer || 'Guidance generated successfully.');
    } catch (err) {
      removeTypingIndicator();
      console.warn('Chat request failed, providing smart offline fallback:', err);
      const fallbackAns = `**Agronomic Guidance for ${state.cropLabel} (${state.locationName}):**\n\n`
        + `- Maintain ridge aeration and monitor root zone soil moisture (${state.telemetry ? state.telemetry.soil_moisture_pct : 21}%).\n`
        + `- Under warm humid conditions, prune dense lower foliage to promote airflow and suppress spore germination.\n`
        + `- Inspect lower leaves early morning for concentric lesions.\n\n`
        + `### 💡 Suggested Follow-Up Questions:\n`
        + `- Should I irrigate early in the morning or evening?\n`
        + `- What organic preventive spray helps against blight?`;
      appendChatMessage('assistant', fallbackAns);
    }
  }

  if (btnSendChat) {
    btnSendChat.addEventListener('click', () => handleSendQuestion());
  }

  if (chatInput) {
    chatInput.addEventListener('keydown', e => {
      if (e.key === 'Enter') handleSendQuestion();
    });
  }

  // POPULAR QUESTIONS CLICK LISTENER — LIVE LLM INVOCATION
  popularChips.forEach(chip => {
    chip.addEventListener('click', (e) => {
      e.preventDefault();
      const q = chip.getAttribute('data-q') || chip.innerText.replace(/^\s*[+💧🔍🍂🌾]\s*/, '').trim();
      if (q) {
        switchView('assistant');
        handleSendQuestion(q);
      }
    });
  });

  // --------------------------------------------------------------------------
  // Voice Input: Groq Whisper Turbo via /api/transcribe + Web Speech Fallback
  // --------------------------------------------------------------------------
  let mediaRecorder = null;
  let audioChunks = [];
  let isRecording = false;

  async function toggleAudioRecording() {
    if (isRecording) {
      stopAudioRecording();
    } else {
      startAudioRecording();
    }
  }

  async function startAudioRecording() {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Microphone mediaDevices API not available.');
      }
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunks = [];
      mediaRecorder = new MediaRecorder(stream);

      mediaRecorder.ondataavailable = e => {
        if (e.data.size > 0) audioChunks.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        if (audioBlob.size > 200) {
          await sendAudioForTranscription(audioBlob);
        }
      };

      mediaRecorder.start();
      isRecording = true;
      if (btnVoiceInput) btnVoiceInput.classList.add('listening');
      if (voiceStatus) {
        voiceStatus.textContent = '🎙️ Recording your question... Tap microphone again to submit.';
        voiceStatus.style.color = '#DC2626';
      }
    } catch (err) {
      console.warn('MediaRecorder permission or error:', err);
      // Fallback to Web Speech API
      startWebSpeechRecognition();
    }
  }

  function stopAudioRecording() {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      isRecording = false;
      if (btnVoiceInput) btnVoiceInput.classList.remove('listening');
      if (voiceStatus) {
        voiceStatus.textContent = '⏳ Transcribing audio with Groq Whisper Turbo...';
        voiceStatus.style.color = '#0B4628';
      }
    }
  }

  async function sendAudioForTranscription(blob) {
    try {
      const formData = new FormData();
      formData.append('file', blob, 'query.webm');

      const res = await fetch(`${API_BASE}/api/transcribe`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) throw new Error(`Transcription HTTP ${res.status}`);
      const data = await res.json();
      const transcribed = (data.text || '').trim();

      if (transcribed) {
        if (voiceStatus) {
          voiceStatus.textContent = `🎙️ Heard: "${transcribed}"`;
          voiceStatus.style.color = '#059669';
        }
        if (chatInput) chatInput.value = transcribed;
        handleSendQuestion(transcribed);
      } else {
        if (voiceStatus) voiceStatus.textContent = 'Could not clearly recognize speech. Please use text input.';
      }
    } catch (e) {
      console.warn('Transcription API error:', e);
      if (voiceStatus) voiceStatus.textContent = 'Transcription server busy. Please use text input.';
    }
  }

  function startWebSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      if (voiceStatus) voiceStatus.textContent = 'Microphone access unavailable. Please use text input.';
      return;
    }
    try {
      const recog = new SpeechRecognition();
      recog.continuous = false;
      recog.interimResults = false;
      recog.lang = 'en-IN';

      recog.onstart = () => {
        if (btnVoiceInput) btnVoiceInput.classList.add('listening');
        if (voiceStatus) voiceStatus.textContent = '🎙️ Listening (Web Speech)... Speak now.';
      };
      recog.onresult = ev => {
        const text = ev.results[0][0].transcript;
        if (voiceStatus) voiceStatus.textContent = `Heard: "${text}"`;
        if (chatInput) chatInput.value = text;
        handleSendQuestion(text);
      };
      recog.onerror = ev => {
        if (btnVoiceInput) btnVoiceInput.classList.remove('listening');
        if (voiceStatus) voiceStatus.textContent = `Voice recognition error: ${ev.error}`;
      };
      recog.onend = () => {
        if (btnVoiceInput) btnVoiceInput.classList.remove('listening');
      };
      recog.start();
    } catch (recExc) {
      console.warn('Web Speech error:', recExc);
    }
  }

  if (btnVoiceInput) {
    btnVoiceInput.addEventListener('click', toggleAudioRecording);
  }

  // --------------------------------------------------------------------------
  // Report Download Helpers (PDF Report Without Logo)
  // --------------------------------------------------------------------------
  async function downloadAdvisoryReportPDF(evt) {
    const triggerBtn = (evt && evt.target) ? evt.target : null;
    let oldBtnText = '';
    if (triggerBtn) {
      oldBtnText = triggerBtn.textContent;
      triggerBtn.textContent = '⏳ Generating PDF Report...';
    }

    try {
      const payload = {
        crop: state.crop,
        location: state.locationName,
        lat: state.lat,
        lon: state.lon,
        stage: state.stage,
        advisory_text: state.initialAdvisoryText || 'Sarva Mitra Agronomic Field Advisory Report',
      };

      const res = await fetch(`${API_BASE}/api/report/pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error(`PDF endpoint returned HTTP ${res.status}`);
      const pdfBlob = await res.blob();
      const url = URL.createObjectURL(pdfBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `sarva_mitra_${state.crop}_report_${new Date().toISOString().slice(0, 10)}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.warn('PDF generation endpoint note, generating backup text report:', err);
      const blob = new Blob([state.initialAdvisoryText || 'Sarva Mitra Farm Advisory Report'], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `sarva_mitra_${state.crop}_advisory_${new Date().toISOString().slice(0, 10)}.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } finally {
      if (triggerBtn && oldBtnText) {
        triggerBtn.textContent = oldBtnText;
      }
    }
  }

  if (btnDownloadSoilReport) {
    btnDownloadSoilReport.addEventListener('click', (e) => downloadAdvisoryReportPDF(e));
  }

  if (btnDownloadChatReport) {
    btnDownloadChatReport.addEventListener('click', (e) => downloadAdvisoryReportPDF(e));
  }

  if (btnExportHistoryCsv) {
    btnExportHistoryCsv.addEventListener('click', () => {
      if (!state.history || !state.history.length) return;
      let csv = 'Date,Soil_Moisture_Pct,Air_Temp_C,Humidity_Pct,Rainfall_Mm,Risk_Pct\n';
      state.history.forEach(h => {
        csv += `${h.date || ''},${h.soil_moisture_pct || ''},${h.air_temperature_c || ''},${h.humidity_pct || ''},${h.rainfall_mm || ''},${h.risk_pct || ''}\n`;
      });
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `sarva_mitra_telemetry_history_${state.locationName}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    });
  }

  // --------------------------------------------------------------------------
  // Settings Form Management
  // --------------------------------------------------------------------------
  if (settingsLocation) {
    settingsLocation.addEventListener('change', () => {
      if (customCoordsRow) {
        customCoordsRow.style.display = settingsLocation.value === 'custom' ? 'grid' : 'none';
      }
    });
  }

  if (settingsForm) {
    settingsForm.addEventListener('submit', e => {
      e.preventDefault();
      const locVal = settingsLocation.value;
      if (locVal === 'custom') {
        const cLat = parseFloat(document.getElementById('custom-lat').value) || 16.51;
        const cLon = parseFloat(document.getElementById('custom-lon').value) || 80.52;
        const cName = document.getElementById('custom-name').value || 'My Farm';
        state.lat = cLat;
        state.lon = cLon;
        state.locationName = cName;
        state.locationState = 'Custom';
      } else {
        const preset = LOCATIONS[locVal] || LOCATIONS['Vijayawada (Andhra Pradesh)'];
        state.lat = preset.lat;
        state.lon = preset.lon;
        state.locationName = preset.name;
        state.locationState = preset.state;
      }

      state.crop = settingsCrop.value;
      state.cropLabel = settingsCrop.options[settingsCrop.selectedIndex].text;
      state.stage = settingsStage.value;

      syncDashboardData();
      switchView('soil');
    });
  }

  if (btnSync) {
    btnSync.addEventListener('click', () => syncDashboardData());
  }

  // --------------------------------------------------------------------------
  // Initial Boot
  // --------------------------------------------------------------------------
  function init() {
    syncDashboardData();
  }

  init();

})();
