import { Component, signal, effect, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

// --- DESIGN TOKENS ---
interface DesignTokens {
  bg: string; surface: string; border: string;
  critical: string; high: string; medium: string; low: string;
  ai: string; text: string; muted: string; mono: string;
}

const DESIGN_TOKENS: DesignTokens = {
  bg: '#06090f', surface: 'rgba(255,255,255,0.028)', border: 'rgba(255,255,255,0.07)',
  critical: '#ff2d55', high: '#ff7e2d', medium: '#f5c518', low: '#4ecdc4',
  ai: '#a78bfa', text: '#dde4f0', muted: 'rgba(255,255,255,0.36)', mono: "'Courier New',monospace",
};

interface Source {
  id: string;
  label: string;
  icon: string;
  color: string;
  desc: string;
}

const SOURCES: Record<string, Source> = {
  WAZUH: { id: 'WAZUH', label: 'Wazuh', icon: '🛡', color: '#4ecdc4', desc: 'SIEM / IDS / Règles' },
  ANTIVIRUS: { id: 'ANTIVIRUS', label: 'Antivirus', icon: '🦠', color: '#ff7e2d', desc: 'Détection Malware' },
  NODEJS: { id: 'NODEJS', label: 'Node.js', icon: '🟢', color: '#68d391', desc: 'Logs Applicatifs' },
  UPDATES: { id: 'UPDATES', label: 'Mises à jour', icon: '🔄', color: '#f5c518', desc: 'Patches / CVE' },
};

const TL: any = {
  CRITICAL: { c: '#ff2d55', bg: 'rgba(255,45,85,0.1)' },
  HIGH: { c: '#ff7e2d', bg: 'rgba(255,126,45,0.1)' },
  MEDIUM: { c: '#f5c518', bg: 'rgba(245,197,24,0.1)' },
  LOW: { c: '#4ecdc4', bg: 'rgba(78,205,196,0.1)' },
};

const ACTIONS: any = {
  BLOCK_IP: { icon: '🚫', label: 'IP Bloquée', color: '#ff2d55' },
  ISOLATE: { icon: '🔌', label: 'Machine Isolée', color: '#ff7e2d' },
  QUARANTINE: { icon: '🧪', label: 'Fichier Quarantaine', color: '#ff7e2d' },
  KILL_PROCESS: { icon: '💀', label: 'Processus Arrêté', color: '#a78bfa' },
  DISABLE_USER: { icon: '🔒', label: 'Compte Désactivé', color: '#f5c518' },
  PATCH_APPLY: { icon: '🩹', label: 'Patch Appliqué', color: '#4ecdc4' },
  RESTART_SVC: { icon: '🔁', label: 'Service Redémarré', color: '#68d391' },
  ALERT_TEAM: { icon: '📡', label: 'SOC Notifié', color: '#a78bfa' },
  SCAN: { icon: '🔬', label: 'Scan Lancé', color: '#667eea' },
};

const ALERT_POOL = [
  { source: 'WAZUH', rule: 'Brute Force SSH', agent: 'srv-prod-01', ip: '185.220.101.45', level: 'CRITICAL', ruleId: 'W-5763', action: 'BLOCK_IP', confidence: 97, tactic: 'Initial Access', technique: 'T1110.001', desc: '10 tentatives SSH échouées en 30s depuis IP externe.' },
  { source: 'WAZUH', rule: 'Escalade de Privilèges', agent: 'ws-finance-03', ip: '10.0.0.54', level: 'HIGH', ruleId: 'W-5501', action: 'DISABLE_USER', confidence: 91, tactic: 'Privilege Escalation', technique: 'T1548', desc: 'Tentative sudo par utilisateur non autorisé.' },
  { source: 'WAZUH', rule: 'Connexion Root Suspecte', agent: 'srv-db-01', ip: '45.33.32.156', level: 'CRITICAL', ruleId: 'W-5402', action: 'ISOLATE', confidence: 99, tactic: 'Lateral Movement', technique: 'T1021', desc: 'Connexion root directe hors horaires autorisés.' },
  { source: 'ANTIVIRUS', rule: 'Emotet Trojan Détecté', agent: 'ws-rh-07', ip: '10.0.0.87', level: 'CRITICAL', ruleId: 'AV-9981', action: 'QUARANTINE', confidence: 99, tactic: 'Execution', technique: 'T1059', desc: 'Signature Emotet trojan dans C:\\Temp\\update.exe.' },
  { source: 'NODEJS', rule: 'API Rate Limit Dépassée', agent: 'api-gateway', ip: '91.108.56.23', level: 'HIGH', ruleId: 'N-3301', action: 'BLOCK_IP', confidence: 89, tactic: 'Initial Access', technique: 'T1190', desc: '5000 req/min sur /api/auth depuis une IP unique.' },
  { source: 'UPDATES', rule: 'CVE-2024-3094 Critique', agent: 'srv-prod-01', ip: '10.0.0.10', level: 'CRITICAL', ruleId: 'U-CVE01', action: 'PATCH_APPLY', confidence: 100, tactic: 'Exploitation', technique: 'T1190', desc: 'XZ Utils backdoor CVE-2024-3094. Patch immédiat requis.' },
];

const AGENTS_DATA = [
  { id: 'WZ-001', name: 'srv-prod-01', ip: '10.0.0.10', os: 'Ubuntu 22.04', status: 'warning', threats: 3, cpu: 71, mem: 67, uptime: '47j 3h', sources: ['WAZUH', 'ANTIVIRUS', 'UPDATES'] },
  { id: 'WZ-002', name: 'srv-web-02', ip: '10.0.0.11', os: 'CentOS 8', status: 'online', threats: 1, cpu: 22, mem: 41, uptime: '12j 8h', sources: ['WAZUH', 'UPDATES'] },
  { id: 'WZ-003', name: 'srv-db-01', ip: '10.0.0.12', os: 'Debian 11', status: 'warning', threats: 5, cpu: 89, mem: 92, uptime: '93j 5h', sources: ['WAZUH', 'UPDATES'] },
  { id: 'WZ-004', name: 'ws-finance-03', ip: '10.0.0.54', os: 'Windows 11', status: 'online', threats: 2, cpu: 12, mem: 58, uptime: '5j 2h', sources: ['WAZUH', 'ANTIVIRUS'] },
  { id: 'WZ-005', name: 'ws-rh-07', ip: '10.0.0.87', os: 'Windows 10', status: 'offline', threats: 1, cpu: 0, mem: 0, uptime: '0', sources: ['ANTIVIRUS'] },
  { id: 'WZ-006', name: 'srv-api-01', ip: '10.0.0.31', os: 'Alpine 3.17', status: 'online', threats: 3, cpu: 45, mem: 38, uptime: '21j 6h', sources: ['WAZUH', 'NODEJS', 'UPDATES'] },
];

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class Dashboard {
  C = DESIGN_TOKENS;
  SOURCES = SOURCES;
  TL = TL;
  ACTIONS = ACTIONS;

  // State
  activePage = signal('Dashboard');
  liveTime = signal(this.getCurrentTime());
  alerts = signal<any[]>([]);
  selectedAlert = signal<any>(null);
  agents = signal(AGENTS_DATA);

  // Filters
  alertSearch = signal('');
  filterSource = signal('ALL');
  filterLevel = signal('ALL');
  filterStatus = signal('ALL');

  // Dashboard Tabs
  tabs = ['Dashboard', 'Alertes', 'Agents', 'Actions', 'Rapports'];

  // Dashboard stats
  stats = computed(() => {
    const list = this.alerts();
    return {
      total: list.length,
      critical: list.filter(a => a.level === 'CRITICAL').length,
      resolved: list.filter(a => a.status === 'resolved').length,
      blocked: list.filter(a => a.action === 'BLOCK_IP').length,
      patches: list.filter(a => a.action === 'PATCH_APPLY').length,
      agents: this.agents().filter(a => a.status === 'online').length
    };
  });

  // Source stats
  sourceStats = computed(() => {
    const list = this.alerts();
    return Object.keys(SOURCES).map(sk => ({
      src: SOURCES[sk],
      count: list.filter(a => a.source === sk).length,
      crit: list.filter(a => a.source === sk && a.level === 'CRITICAL').length
    }));
  });

  // Filtered alerts
  filteredAlerts = computed(() => {
    let list = this.alerts();
    const search = this.alertSearch().toLowerCase();
    const source = this.filterSource();
    const level = this.filterLevel();
    const status = this.filterStatus();

    return list.filter(a => {
      const matchSearch = !search || [a.rule, a.ip, a.agent, a.ruleId].join(' ').toLowerCase().includes(search);
      const matchSource = source === 'ALL' || a.source === source;
      const matchLevel = level === 'ALL' || a.level === level;
      const matchStatus = status === 'ALL' || a.status === status;
      return matchSearch && matchSource && matchLevel && matchStatus;
    });
  });

  // Hour distribution
  hourData = [
    { l: '08h', v: 3 }, { l: '09h', v: 8 }, { l: '10h', v: 6 }, { l: '11h', v: 14 }, { l: '12h', v: 5 }, { l: '13h', v: 11 }, { l: '14h', v: 9 }, { l: '15h', v: 4 }
  ];
  maxHourValue = Math.max(...this.hourData.map(d => d.v));

  constructor() {
    // Current time updater
    setInterval(() => this.liveTime.set(this.getCurrentTime()), 1000);

    // Initial data
    const initialAlerts = ALERT_POOL.map((a, i) => ({
      ...a,
      id: 100 + i,
      time: '14:20:00',
      status: 'resolved'
    }));
    this.alerts.set(initialAlerts);
    this.selectedAlert.set(initialAlerts[0]);

    // Live alert simulator
    let uid = 200;
    setInterval(() => {
      const randomBaseAlert = ALERT_POOL[Math.floor(Math.random() * ALERT_POOL.length)];
      const newAlert = {
        ...randomBaseAlert,
        id: uid++,
        time: this.getCurrentTime(),
        status: 'analyzing',
        isNew: true
      };
      this.alerts.update(prev => [newAlert, ...prev.slice(0, 24)]);

      // Auto-resolve after 3s
      setTimeout(() => {
        this.alerts.update(prev => prev.map(a => a.id === newAlert.id ? { ...a, status: 'resolved', isNew: false } : a));
      }, 3000);
    }, 8000);
  }

  private getCurrentTime(): string {
    const d = new Date();
    return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}:${d.getSeconds().toString().padStart(2, '0')}`;
  }

  setPage(page: string) {
    this.activePage.set(page);
  }

  selectAlert(alert: any) {
    this.selectedAlert.set(alert);
  }

  getSourcesArray(): Source[] {
    return Object.values(SOURCES);
  }
}

