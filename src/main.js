/**
 * MarineDebrisAI - Main Application Controller
 * Unifies Dashboard, Analysis, Results, Map, and Reports around the real Python YOLO pipeline.
 */

import './styles/variables.css';
import './styles/layout.css';
import './styles/components.css';
import './styles/sonar-viewer.css';
import './styles/map.css';

import { renderSidebar } from './components/Sidebar.js';
import { renderHeader } from './components/Header.js';
import { renderDashboardView } from './components/DashboardView.js';
import { renderSonarAnalysisView } from './components/SonarAnalysisView.js';
import { renderDetectionResultsView } from './components/DetectionResultsView.js';
import { renderGeospatialMapView } from './components/GeospatialMapView.js';
import { renderReportsView } from './components/ReportsView.js';
import { runRealSonarAnalysis, checkBackendHealth } from './services/api.js';

// Application State
const state = {
  activeTab: 'dashboard',
  currentAnalysis: null, // Holds the real YOLO detection output from Python backend
  isBackendOnline: false
};

const TAB_TITLES = {
  dashboard: {
    title: 'Dashboard',
    subtitle: 'Upload sonar imagery to run detection with best.pt'
  },
  analysis: {
    title: 'Sonar Analysis',
    subtitle: 'Image preprocessing & YOLO inference controls'
  },
  results: {
    title: 'Detection Results',
    subtitle: 'Identified target bounding boxes & confidence scores'
  },
  map: {
    title: 'Geospatial Map',
    subtitle: 'Target coordinates & survey localization'
  },
  reports: {
    title: 'Reports',
    subtitle: 'Detection summary & CSV / JSON data export'
  }
};

async function initApp() {
  const health = await checkBackendHealth();
  state.isBackendOnline = health.connected;
  renderAppShell();
}

function renderAppShell() {
  const appRoot = document.getElementById('app');
  if (!appRoot) return;
  appRoot.innerHTML = '';

  const sidebar = renderSidebar(state.activeTab, handleTabSelect, state.currentAnalysis);

  const main = document.createElement('main');
  main.className = 'app-main';

  const tabMeta = TAB_TITLES[state.activeTab] || TAB_TITLES.dashboard;
  const header = renderHeader(tabMeta.title, tabMeta.subtitle, state.currentAnalysis);

  const contentViewport = document.createElement('div');
  contentViewport.className = 'content-viewport';
  contentViewport.id = 'contentViewport';

  main.appendChild(header);
  main.appendChild(contentViewport);

  appRoot.appendChild(sidebar);
  appRoot.appendChild(main);

  renderCurrentTab();
}

function handleTabSelect(tabId) {
  state.activeTab = tabId;

  // Update navigation highlighting
  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.toggle('active', item.getAttribute('data-tab') === tabId);
  });

  // Update header text
  const tabMeta = TAB_TITLES[tabId] || TAB_TITLES.dashboard;
  const pageTitle = document.getElementById('pageTitle');
  const pageSubtitle = document.getElementById('pageSubtitle');
  if (pageTitle) pageTitle.textContent = tabMeta.title;
  if (pageSubtitle) pageSubtitle.textContent = tabMeta.subtitle;

  renderCurrentTab();
}

/**
 * Handle real detection directly from Dashboard
 */
async function handleRunDetectionFromDashboard(options) {
  try {
    const result = await runRealSonarAnalysis({
      ...options,
      confidenceThreshold: 0.25,
      iouThreshold: 0.45
    });
    state.currentAnalysis = result;
    renderAppShell();
  } catch (err) {
    throw err;
  }
}

/**
 * Trigger analysis of a verified sample directly through the Python backend
 */
async function handleAnalyzeSample(sampleUrl, sampleFilename, footprint) {
  handleTabSelect('analysis');
  try {
    const resp = await fetch(sampleUrl);
    const blob = await resp.blob();

    const result = await runRealSonarAnalysis({
      imageBlob: blob,
      filename: sampleFilename,
      footprint: footprint,
      confidenceThreshold: 0.25,
      iouThreshold: 0.45,
      onProgress: (pct, msg) => {
        const msgEl = document.getElementById('progressMessage');
        const cardEl = document.getElementById('progressCard');
        if (cardEl) cardEl.style.display = 'block';
        if (msgEl) msgEl.textContent = `${msg} (${pct}%)`;
      }
    });

    state.currentAnalysis = result;
    renderAppShell();
    handleTabSelect('results');
  } catch (err) {
    alert(`AI Analysis Error:\n${err.message}`);
  }
}

function renderCurrentTab() {
  const viewport = document.getElementById('contentViewport');
  if (!viewport) return;
  viewport.innerHTML = '';

  switch (state.activeTab) {
    case 'dashboard':
      viewport.appendChild(renderDashboardView({
        currentAnalysis: state.currentAnalysis,
        onNavigate: (tabId) => handleTabSelect(tabId),
        onRunDetection: handleRunDetectionFromDashboard
      }));
      break;

    case 'analysis':
      viewport.appendChild(renderSonarAnalysisView({
        currentAnalysis: state.currentAnalysis,
        onAnalysisComplete: (realResult) => {
          state.currentAnalysis = realResult;
          renderAppShell();
          handleTabSelect('results');
        }
      }));
      break;

    case 'results':
      viewport.appendChild(renderDetectionResultsView({
        scanData: state.currentAnalysis,
        onReanalyze: () => handleTabSelect('analysis')
      }));
      break;

    case 'map':
      viewport.appendChild(renderGeospatialMapView({
        scanData: state.currentAnalysis
      }));
      break;

    case 'reports':
      viewport.appendChild(renderReportsView({
        scanData: state.currentAnalysis
      }));
      break;

    default:
      viewport.appendChild(renderDashboardView({
        currentAnalysis: state.currentAnalysis,
        onNavigate: (tabId) => handleTabSelect(tabId),
        onRunDetection: handleRunDetectionFromDashboard
      }));
  }
}

document.addEventListener('DOMContentLoaded', initApp);
