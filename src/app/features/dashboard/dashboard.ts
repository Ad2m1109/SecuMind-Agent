import { Component, signal, effect, computed, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/api.service';

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
export class Dashboard implements OnInit {
  C = DESIGN_TOKENS;
  SOURCES = SOURCES;
  TL = TL;
  ACTIONS = ACTIONS;

  // State
  activePage = signal('Dashboard');
  liveTime = signal(this.getCurrentTime());
  alerts = signal<any[]>([]);
  history = signal<any[]>([]);
  selectedAlert = signal<any>(null);
  agents = signal(AGENTS_DATA);

  // Analysis state
  isProcessing = signal(false);
  isRetraining = signal(false);
  analysisResult = signal<any>(null);

  // Filters
  alertSearch = signal('');
  filterSource = signal('ALL');
  filterLevel = signal('ALL');
  filterStatus = signal('ALL');

  // Dashboard Tabs
  tabs = ['Dashboard', 'Alertes', 'Agents', 'Histoire', 'Actions', 'Rapports'];

  // Trend Data (Computed from history)
  threatTrend = computed(() => {
    const list = this.history();
    const counts: Record<string, number> = {};
    list.forEach(a => {
      counts[a.attack_type] = (counts[a.attack_type] || 0) + 1;
    });
    return Object.entries(counts).map(([label, value]) => ({ label, value }));
  });

  // Dashboard stats
  stats = computed(() => {
    const list = this.alerts();
    const hist = this.history();
    return {
      total: list.length + hist.length,
      critical: list.filter(a => a.level === 'CRITICAL').length + hist.filter(a => a.severity_score > 0.8).length,
      resolved: hist.length,
      blocked: hist.filter(a => a.decision === 'block_ip').length,
      patches: hist.filter(a => a.action === 'PATCH_APPLY').length,
      agents: this.agents().filter(a => a.status === 'online').length
    };
  });

  // Source stats
  sourceStats = computed(() => {
    const list = [...this.alerts(), ...this.history()];
    return Object.keys(SOURCES).map(sk => ({
      src: SOURCES[sk],
      count: list.filter(a => a.source === sk || a.attack_type === sk).length,
      crit: list.filter(a => (a.source === sk || a.attack_type === sk) && (a.level === 'CRITICAL' || a.severity_score > 0.8)).length
    }));
  });

  // Filtered alerts
  filteredAlerts = computed(() => {
    let list = this.activePage() === 'Histoire' ? this.history() : this.alerts();
    const search = this.alertSearch().toLowerCase();
    const source = this.filterSource();
    const level = this.filterLevel();
    const status = this.filterStatus();

    return list.filter(a => {
      const matchSearch = !search || [a.rule, a.ip, a.agent, a.ruleId, a.attack_type].join(' ').toLowerCase().includes(search);
      const matchSource = source === 'ALL' || a.source === source || a.attack_type === source;
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

  constructor(private apiService: ApiService) {
    // Current time updater
    setInterval(() => this.liveTime.set(this.getCurrentTime()), 1000);
    // Data auto-refresh every 5 seconds
    setInterval(() => this.refreshData(), 5000);
  }

  ngOnInit(): void {
    this.refreshData();
  }

  refreshData() {
    this.apiService.getAlerts().subscribe(data => {
      const initialAlerts = data.map((a, i) => ({
        ...a,
        id: 100 + i,
        time: '14:22:00',
        status: 'pending',
        level: a.severity_score > 0.8 ? 'CRITICAL' : a.severity_score > 0.5 ? 'HIGH' : 'MEDIUM',
        rule: a.attack_type.replace(/_/g, ' ').toUpperCase(),
        source: 'WAZUH',
        agent: 'srv-prod-0' + (i % 5 + 1),
        ip: '192.168.1.' + (100 + i),
        ruleId: 'SIG-' + (1000 + i),
        desc: `Detection of ${a.attack_type} activity with ${a.failed_attempts} failed attempts and severity ${a.severity_score}.`
      }));
      this.alerts.set(initialAlerts);
      if (initialAlerts.length > 0 && !this.selectedAlert()) {
        this.selectedAlert.set(initialAlerts[0]);
      }
    });

    this.apiService.getHistory().subscribe(data => {
      this.history.set(data.reverse()); // Show latest first
    });
  }

  analyzeAlert(alert: any) {
    this.isProcessing.set(true);
    this.analysisResult.set(null);

    // Prepare data for backend
    const payload = {
      attack_type: alert.attack_type || 'unknown',
      failed_attempts: alert.failed_attempts || 0,
      severity_score: alert.severity_score || 0,
      ip_reputation: alert.ip_reputation || 0,
      previous_incidents: alert.previous_incidents || 0
    };

    this.apiService.processAlert(payload).subscribe({
      next: (res) => {
        this.analysisResult.set(res);
        this.isProcessing.set(false);
        this.refreshData();
      },
      error: (err) => {
        console.error(err);
        this.isProcessing.set(false);
      }
    });
  }

  triggerRetrain() {
    this.isRetraining.set(true);
    this.apiService.retrain().subscribe({
      next: (res) => {
        console.log('Retrain result:', res);
        setTimeout(() => {
          this.isRetraining.set(false);
          this.refreshData();
        }, 1500); // Visual feedback delay
      },
      error: (err) => {
        console.error(err);
        this.isRetraining.set(false);
      }
    });
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

