let DATA = {};
let ACTIVE_MODULE = 'overview';
const PAGE_STATE = {};
const DEFAULT_PAGE_SIZE = 10;
let loadingTaskCount = 0;

const ICON_CLASSES = {
  overview: 'ti-layout-dashboard',
  info_board: 'ti-speakerphone',
  data_pegawai: 'ti-users',
  arsip_sdm: 'ti-folder-open',
  dialog: 'ti-microphone',
  jadwal_siaran: 'ti-radio',
  program_siaran: 'ti-player-play',
  arsip_program: 'ti-folder-open',
  konten: 'ti-device-mobile',
  jadwal_tmb: 'ti-chart-bar',
  master_barang: 'ti-box',
  master_persediaan: 'ti-chart-line',
  persediaan_masuk: 'ti-arrow-down',
  persediaan_keluar: 'ti-arrow-up',
  produksi_paket: 'ti-package',
  bestcut_monitoring: 'ti-scissors',
  socmed_analytics: 'ti-chart-pie',
  tmb_working_progresss: 'ti-activity-heartbeat',
  master_ruangan: 'ti-building',
  bast_otomatis: 'ti-file-certificate',
  aset_tutup_buku: 'ti-book-2',
  aset_calbmn: 'ti-report-analytics',
  aset_wasdal: 'ti-shield-check',
  aset_rkbmn: 'ti-clipboard-list',
  aset_manajemen_risiko: 'ti-alert-triangle',
  aset_sisporja: 'ti-file-spreadsheet',
  pemeliharaan_aset: 'ti-tool',
  bmn_arsip: 'ti-archive',
  persediaan_tutup_buku: 'ti-book-2',
  persediaan_form_pengajuan: 'ti-forms',
  persediaan_pipk: 'ti-checklist',
  manage_users: 'ti-user-cog',
  manage_modules: 'ti-shield-check',
  sun: 'ti-sun',
  moon: 'ti-moon',
  app_settings: 'ti-settings',
  edit: 'ti-pencil',
  delete: 'ti-trash',
  link: 'ti-eye',
  search: 'ti-search'
};

function icon(name, size = 'w-4 h-4 text-base leading-none') {
  const iconClass = ICON_CLASSES[name];
  return iconClass ? `<i aria-hidden="true" class="ti ${iconClass} ${size}"></i>` : '';
}

let TIMELINE_EDIT_ROW = null;
let TIMELINE_SORT = { key: 'Tanggal Mulai', direction: 'asc' };
let TIMELINE_VIEW = 'table';
let TIMELINE_CALENDAR_MONTH = new Date(new Date().getFullYear(), new Date().getMonth(), 1);

const MODULE_NAV_CONFIG = [
  { key: 'overview', label: 'Overview', group: 'Utama', always: true },
  { key: 'info_board', label: 'Info Board', group: 'Utama' },
  { key: 'data_pegawai', label: 'Data Pegawai', group: 'SDM' },
  { key: 'arsip_sdm', label: 'Arsip SDM', group: 'SDM' },
  { key: 'jadwal_siaran', label: 'Jadwal Penyiar', group: 'Siaran' },
  { key: 'produksi_paket', label: 'Produksi Paket', group: 'Perencanaan' },
  { key: 'dialog', label: 'Jadwal Dialog', group: 'Perencanaan' },
  { key: 'program_siaran', label: 'Program Siaran', group: 'Perencanaan' },
  { key: 'arsip_program', label: 'Arsip Program', group: 'Perencanaan' },
  { key: 'konten', label: 'Content Planner', group: 'KMB' },
  { key: 'bestcut_monitoring', label: 'Bestcut Monitoring', group: 'KMB' },
  { key: 'socmed_analytics', label: 'Social Media Analytics', group: 'KMB' },
  { key: 'jadwal_tmb', label: 'Jadwal TMB', group: 'TMB' },
  { key: 'tmb_working_progresss', label: 'TMB Working Progress', group: 'TMB' },
  { key: 'master_ruangan', label: 'Daftar Barang Ruangan', group: 'BMN', section: 'ASET' },
  { key: 'master_barang', label: 'Kartu Inventaris Ruangan', group: 'BMN', section: 'ASET' },
  { key: 'bast_otomatis', label: 'BAST Otomatis', group: 'BMN', section: 'ASET' },
  { key: 'aset_tutup_buku', label: 'Tutup Buku', group: 'BMN', section: 'ASET' },
  { key: 'aset_calbmn', label: 'CALBMN', group: 'BMN', section: 'ASET' },
  { key: 'aset_wasdal', label: 'WASDAL', group: 'BMN', section: 'ASET' },
  { key: 'aset_rkbmn', label: 'RKBMN', group: 'BMN', section: 'ASET' },
  { key: 'aset_manajemen_risiko', label: 'Manajemen Risiko', group: 'BMN', section: 'ASET' },
  { key: 'aset_sisporja', label: 'SISPORJA', group: 'BMN', section: 'ASET' },
  { key: 'bmn_arsip', label: 'Dokumen BMN', group: 'BMN', section: 'ASET' },
  { key: 'pemeliharaan_aset', label: 'Monitoring Pemeliharaan Aset', group: 'BMN', section: 'ASET' },
  { key: 'persediaan_form_pengajuan', label: 'Form Pengajuan', group: 'BMN', section: 'Persediaan' },
  { key: 'master_persediaan', label: 'Monitoring Persediaan', group: 'BMN', section: 'Persediaan' },
  { key: 'persediaan_pipk', label: 'PIPK', group: 'BMN', section: 'Persediaan' },
  { key: 'persediaan_tutup_buku', label: 'Tutup Buku', group: 'BMN', section: 'Persediaan' },
  { key: 'manage_users', label: 'Manage User', group: 'Admin' },
  { key: 'manage_modules', label: 'Manage Module', group: 'Admin' },
  { key: 'app_settings', label: 'Pengaturan Aplikasi', group: 'Admin', adminOnly: true },
];

function showToast(message, type = 'success') {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const colorClasses = {
    success: 'bg-emerald-50 dark:bg-emerald-950/95 border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-200',
    error: 'bg-rose-50 dark:bg-rose-950/95 border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-200',
    warning: 'bg-amber-50 dark:bg-amber-950/95 border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-200',
    info: 'bg-sky-50 dark:bg-sky-950/95 border-sky-200 dark:border-sky-800 text-sky-800 dark:text-sky-200'
  };
  const toast = document.createElement('div');
  toast.className = `pointer-events-auto flex items-start gap-3 p-3.5 rounded-2xl shadow-xl border text-xs font-semibold transition-all duration-300 transform translate-y-2 opacity-0 ${
    colorClasses[type] || colorClasses.success
  }`;
  const text = document.createElement('div');
  text.className = 'flex-1 leading-snug';
  text.textContent = String(message ?? '');
  const closeButton = document.createElement('button');
  closeButton.type = 'button';
  closeButton.setAttribute('aria-label', 'Tutup notifikasi');
  closeButton.className = 'text-slate-400 hover:text-slate-700';
  closeButton.textContent = '✕';
  closeButton.addEventListener('click', () => toast.remove());
  toast.append(text, closeButton);
  container.appendChild(toast);
  requestAnimationFrame(() => toast.classList.remove('translate-y-2', 'opacity-0'));
  setTimeout(() => {
    toast.classList.add('opacity-0', 'translate-y-2');
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function showLoadingOverlay() {
  if (document.getElementById('globalLoadingOverlay')) return;
  const overlay = document.createElement('div');
  overlay.id = 'globalLoadingOverlay';
  overlay.className = 'fixed inset-0 z-[70] flex items-center justify-center bg-slate-950/45 backdrop-blur-sm';
  overlay.setAttribute('role', 'status');
  overlay.setAttribute('aria-live', 'polite');
  overlay.innerHTML = `
    <div class="flex items-center gap-3 rounded-2xl bg-white dark:bg-slate-900 px-5 py-4 shadow-xl border border-slate-200 dark:border-slate-700">
      <span aria-hidden="true" class="h-6 w-6 animate-spin rounded-full border-[3px] border-slate-200 dark:border-slate-700 border-t-teal-600 dark:border-t-teal-400"></span>
      <span class="text-sm font-bold text-slate-700 dark:text-slate-200">Sedang memproses...</span>
    </div>`;
  document.body.appendChild(overlay);
}

async function withLoadingOverlay(operation) {
  loadingTaskCount += 1;
  try {
    if (loadingTaskCount === 1) showLoadingOverlay();
    return await operation();
  } finally {
    loadingTaskCount = Math.max(0, loadingTaskCount - 1);
    if (loadingTaskCount === 0) document.getElementById('globalLoadingOverlay')?.remove();
  }
}

async function processWithLoading(operation, errorMessage = 'Gagal memproses permintaan') {
  try {
    return await withLoadingOverlay(operation);
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error);
    showToast(`${errorMessage}: ${detail}`, 'error');
    return null;
  }
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, char => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  })[char]);
}

function paginateArray(tableKey, rows, pagContainerId, rerenderFnName) {
  if (!PAGE_STATE[tableKey]) PAGE_STATE[tableKey] = { page: 1, size: DEFAULT_PAGE_SIZE };
  const st = PAGE_STATE[tableKey];
  const total = rows.length;
  const totalPages = Math.max(1, Math.ceil(total / st.size));
  if (st.page > totalPages) st.page = totalPages;
  if (st.page < 1) st.page = 1;

  const startIdx = (st.page - 1) * st.size;
  const pageSlice = rows.slice(startIdx, startIdx + st.size);

  const box = document.getElementById(pagContainerId);
  if (box) {
    const fromNum = total === 0 ? 0 : startIdx + 1;
    const toNum = Math.min(startIdx + st.size, total);
    box.innerHTML = `
      <div class="flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500 dark:text-slate-400">
        <div class="flex items-center gap-2">
          <span>Menampilkan <strong>${fromNum}–${toNum}</strong> dari <strong>${total}</strong> data</span>
          <select onchange="changePageSize('${tableKey}', this.value, ${rerenderFnName})"
            class="px-2 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-semibold">
            ${[10, 25, 50, 100].map(sz => `<option value="${sz}" ${st.size === sz ? 'selected' : ''}>${sz} / hal</option>`).join('')}
          </select>
        </div>
        <div class="flex items-center gap-1.5">
          <button onclick="setTablePage('${tableKey}', ${st.page - 1}, ${rerenderFnName})" ${st.page <= 1 ? 'disabled' : ''}
            class="px-2.5 py-1 rounded-lg border border-slate-200 dark:border-slate-700 font-bold disabled:opacity-40 hover:bg-slate-200 dark:hover:bg-slate-800 transition">← Prev</button>
          <span class="px-2 font-bold text-slate-700 dark:text-slate-200">Hal ${st.page} / ${totalPages}</span>
          <button onclick="setTablePage('${tableKey}', ${st.page + 1}, ${rerenderFnName})" ${st.page >= totalPages ? 'disabled' : ''}
            class="px-2.5 py-1 rounded-lg border border-slate-200 dark:border-slate-700 font-bold disabled:opacity-40 hover:bg-slate-200 dark:hover:bg-slate-800 transition">Next →</button>
        </div>
      </div>
    `;
  }
  return pageSlice;
}

function setTablePage(tableKey, newPage, fn) {
  PAGE_STATE[tableKey] = PAGE_STATE[tableKey] || { page: 1, size: DEFAULT_PAGE_SIZE };
  PAGE_STATE[tableKey].page = newPage;
  if (typeof fn === 'function') fn();
}

function changePageSize(tableKey, newSize, fn) {
  PAGE_STATE[tableKey] = { page: 1, size: Number(newSize) || DEFAULT_PAGE_SIZE };
  if (typeof fn === 'function') fn();
}

function permLevel(modKey) {
  if ((USER.roles || []).some(r => r.toLowerCase() === 'admin')) return 'full';
  return (DATA.user?.permissions || USER.permissions || {})[modKey] || 'none';
}
function canView(modKey) { return ['view', 'update', 'full'].includes(permLevel(modKey)); }
function canUpdate(modKey) { return ['update', 'full'].includes(permLevel(modKey)); }
function canFull(modKey) { return permLevel(modKey) === 'full'; }
function isAdmin() { return (USER.roles || []).some(role => role.toLowerCase() === 'admin'); }

const THEME_STORAGE_KEY = 'dashboard_theme';

function getLocalTheme() {
  try {
    const mode = localStorage.getItem(THEME_STORAGE_KEY);
    return mode === 'light' || mode === 'dark' ? mode : null;
  } catch (_) {
    return null;
  }
}

function initTheme() {
  applyTheme(getLocalTheme() || APP_CONFIG.default_theme || 'dark');
}

function applyTheme(mode, saveToLocal = false) {
  const resolvedMode = mode === 'light' ? 'light' : 'dark';
  document.documentElement.classList.toggle('dark', resolvedMode === 'dark');
  document.documentElement.classList.toggle('light', resolvedMode !== 'dark');
  document.getElementById('themeIcon').innerHTML = icon(resolvedMode === 'light' ? 'sun' : 'moon', 'w-3.5 h-3.5 text-sm leading-none');
  document.getElementById('themeLabel').textContent = resolvedMode === 'dark' ? 'Dark' : 'Light';
  if (saveToLocal) {
    try {
      localStorage.setItem(THEME_STORAGE_KEY, resolvedMode);
    } catch (_) {}
  }
}

function toggleTheme() {
  applyTheme(document.documentElement.classList.contains('dark') ? 'light' : 'dark', true);
}
function toggleSidebar() { document.getElementById('sidebar').classList.toggle('-translate-x-full'); }
function openUserProfile() {
  document.getElementById('userMenu')?.classList.add('hidden');
  switchModule('user_profile');
}

async function loadDashboard() {
  ACTIVE_MODULE = getUrlModule() || ACTIVE_MODULE || 'overview';
  const requests = [fetch('/api/user')];
  if (ACTIVE_MODULE !== 'app_settings') {
    requests.push(fetch(`/api/module/${encodeURIComponent(ACTIVE_MODULE)}`));
  }
  const responses = await Promise.all(requests);
  const userPayload = await responses[0].json();
  DATA = userPayload;
  if (responses[1]) {
    if (!responses[1].ok) throw new Error('Gagal memuat data modul.');
    DATA = { ...DATA, ...(await responses[1].json()) };
  }
  applyTheme(getLocalTheme() || DATA.app_config?.default_theme || APP_CONFIG.default_theme || 'dark');
  buildRoleSidebar();
  activateModuleScreen(ACTIVE_MODULE);
  populateNipDatalist();
  applyActionButtonVisibility();
  clearModuleFilters(ACTIVE_MODULE);
  renderAllModules();
  updateBreadcrumb();
  updateModuleUrl(ACTIVE_MODULE, false);
}

function getUrlModule() {
  const match = window.location.pathname.match(/^\/dashboard\/([^/]+)\/?$/);
  return match ? decodeURIComponent(match[1]) : null;
}

function updateBreadcrumb() {
  const item = MODULE_NAV_CONFIG.find(i => i.key === ACTIVE_MODULE);
  const label = ACTIVE_MODULE === 'user_profile'
    ? 'Profil Pegawai'
    : (item?.label || ACTIVE_MODULE.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()));
  const section = item?.section ? `<span class="text-slate-300 dark:text-slate-600">/</span><span>${escapeHtml(item.section)}</span>` : '';
  const breadcrumb = document.getElementById('breadcrumbNav');
  if (breadcrumb) {
    breadcrumb.innerHTML = `
      <button type="button" onclick="switchModule('overview')" class="hover:text-teal-600 transition">Dashboard</button>
      ${item?.group ? `<span class="text-slate-300 dark:text-slate-600">/</span><span>${escapeHtml(item.group)}</span>` : ''}
      ${section}
      <span class="text-slate-300 dark:text-slate-600">/</span><span class="text-sm text-teal-600 dark:text-teal-300">${escapeHtml(label)}</span>
    `;
  }
  document.title = `${label}`;
}

function updateModuleUrl(modKey, push = true) {
  const nextUrl = `/dashboard/${encodeURIComponent(modKey)}`;
  if (push && window.location.pathname !== nextUrl) {
    window.history.pushState({ module: modKey }, '', nextUrl);
  } else if (!push) {
    window.history.replaceState({ module: modKey }, '', nextUrl);
  }
}

function activateModuleScreen(modKey) {
  document.querySelectorAll('.nav-pill').forEach(button => {
    button.classList.toggle('active', button.dataset.mod === modKey);
  });
  document.querySelectorAll('.mod-section').forEach(section => section.classList.add('hidden'));
  document.getElementById(`mod-${modKey}`)?.classList.remove('hidden');
}

function clearModuleFilters(modKey) {
  const section = document.getElementById(`mod-${modKey}`);
  if (!section) return;

  section.querySelectorAll(
    'input[id^="search"], input[id^="filter"], input[id*="Filter"], ' +
    'select[id^="filter"], select[id^="select"][id$="Periode"]'
  ).forEach(field => {
    if (field.tagName === 'SELECT') field.selectedIndex = 0;
    else field.value = '';
  });
}

function populateNipDatalist() {
  const dl = document.getElementById('pegawaiNipDatalist');
  if (dl) {
    dl.innerHTML = (DATA.employees || []).map(e =>
      `<option value="${e.NIP || e.nip_clean}">${e['Nama Pegawai']} — ${e.Posisi || e.Jabatan || ''}</option>`
    ).join('');
  }
}

let ACTIVE_SIDEBAR_SECTION = '';

function toggleSidebarSection(sectionKey) {
  const safeId = 'acc-section-' + sectionKey.replace(/[^a-zA-Z0-9]/g, '_');
  const body = document.getElementById(safeId);
  const icon = document.getElementById(safeId + '-icon');
  if (!body) return;

  const isCurrentlyHidden = body.classList.contains('hidden');
  document.querySelectorAll('.sidebar-acc-body').forEach(el => el.classList.add('hidden'));
  document.querySelectorAll('.sidebar-acc-icon').forEach(el => el.classList.remove('rotate-180'));

  if (isCurrentlyHidden) {
    body.classList.remove('hidden');
    if (icon) icon.classList.add('rotate-180');
    ACTIVE_SIDEBAR_SECTION = sectionKey;
  } else {
    ACTIVE_SIDEBAR_SECTION = '';
  }
}

function buildRoleSidebar() {
  const visibleItems = MODULE_NAV_CONFIG.filter(item => item.always || canView(item.key));
  document.getElementById('statAccessibleMods').textContent = visibleItems.length - 1;

  const groups = {};
  visibleItems.forEach(item => {
    groups[item.group] = groups[item.group] || { items: [], sections: {} };
    if (item.section) {
      groups[item.group].sections[item.section] = groups[item.group].sections[item.section] || [];
      groups[item.group].sections[item.section].push(item);
    } else {
      groups[item.group].items.push(item);
    }
  });

  const activeMod = ACTIVE_MODULE;
  const activeItemObj = visibleItems.find(i => i.key === activeMod);
  const activeSectionKey = activeItemObj?.section
    ? `${activeItemObj.group}__${activeItemObj.section}`
    : '';
  const sectionKeys = Object.entries(groups).flatMap(([group, groupData]) =>
    Object.keys(groupData.sections).map(section => `${group}__${section}`)
  );
  const openSection = activeSectionKey || (sectionKeys.includes(ACTIVE_SIDEBAR_SECTION) ? ACTIVE_SIDEBAR_SECTION : '');
  const renderModuleLink = item => `
    <button onclick="switchModule('${item.key}')" data-mod="${item.key}"
      class="nav-pill ${item.key === activeMod ? 'active' : ''} w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800/70 transition">
      ${icon(item.key)}<span class="truncate">${item.label}</span>
    </button>
  `;

  document.getElementById('dynamicSidebarMenu').innerHTML = Object.entries(groups).map(([group, groupData]) => `
    <section class="space-y-1">
      <p class="px-3 text-[10px] font-extrabold uppercase tracking-wider text-slate-400">${group}</p>
      ${groupData.items.map(renderModuleLink).join('')}
      ${Object.entries(groupData.sections).map(([section, items]) => {
        const sectionKey = `${group}__${section}`;
        const safeId = 'acc-section-' + sectionKey.replace(/[^a-zA-Z0-9]/g, '_');
        const isOpen = sectionKey === openSection;
        return `
          <div class="rounded-xl border border-slate-100 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-900/30 overflow-hidden">
            <button type="button" onclick="toggleSidebarSection('${sectionKey.replace(/'/g, "\\'")}')"
              class="w-full flex items-center justify-between px-3 py-2.5 text-left text-[11px] font-extrabold uppercase tracking-wider text-slate-500 dark:text-slate-300 hover:bg-slate-200/60 dark:hover:bg-slate-800/60 transition">
              <span class="truncate">${section}</span>
              <i id="${safeId}-icon" class="ti ti-chevron-down sidebar-acc-icon text-xs transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}"></i>
            </button>
            <div id="${safeId}" class="sidebar-acc-body ${isOpen ? '' : 'hidden'} px-1.5 pb-2 pt-0.5 space-y-1">
              ${items.map(renderModuleLink).join('')}
            </div>
          </div>
        `;
      }).join('')}
    </section>
  `).join('');
}

function applyActionButtonVisibility() {
  const toggle = (id, show) => { const el = document.getElementById(id); if (el) el.classList.toggle('hidden', !show); };
  toggle('btnAddTimeline', canFull('dialog'));
  toggle('btnAddInfoOverview', canFull('info_board'));
  toggle('btnAddInfoBoard', canFull('info_board'));
  toggle('btnAddPegawai', canFull('data_pegawai'));
  toggle('btnAddArsipSdm', canFull('arsip_sdm'));
  toggle('btnAddProduksiPaket', canFull('produksi_paket'));
  toggle('btnAddDialog', canFull('dialog'));
  toggle('btnAddSiaran', canFull('jadwal_siaran'));
  toggle('btnAddProgramSiaran', canFull('program_siaran'));
  toggle('btnAddArsipProgram', canFull('arsip_program'));
  toggle('btnAddKonten', canFull('konten'));
  toggle('btnAddSocmed', canFull('socmed_analytics'));
  toggle('btnAddTmb', canFull('jadwal_tmb'));
  toggle('btnAddMonitoringProd', canFull('tmb_working_progresss'));
  toggle('btnAddBarang', canFull('master_barang'));
  toggle('btnAddPemeliharaanHeader', canFull('pemeliharaan_aset'));
  toggle('btnAddPemeliharaanDetail', canFull('pemeliharaan_aset'));
  toggle('btnAddBmnArsip', canFull('bmn_arsip'));
  toggle('btnAddAsetTutupBuku', canFull('aset_tutup_buku'));
  toggle('btnAddCalbmn', canFull('aset_calbmn'));
  toggle('btnAddWasdal', canFull('aset_wasdal'));
  toggle('btnAddRkbmn', canFull('aset_rkbmn'));
  toggle('btnAddManRisiko', canFull('aset_manajemen_risiko'));
  toggle('btnAddSisporja', canFull('aset_sisporja'));
  toggle('btnAddPersediaan', canFull('master_persediaan'));
  toggle('btnAddStokTransaksi', canFull('master_persediaan'));
  toggle('btnModalAddTrxForItem', canFull('master_persediaan'));
  toggle('btnAddPersediaanTutupBuku', canFull('persediaan_tutup_buku'));
  toggle('btnAddPipk', canFull('persediaan_pipk'));
  toggle('btnAddRuangan', canFull('master_ruangan'));
}

async function switchModule(modKey, updateHistory = true) {
  ACTIVE_MODULE = modKey;
  updateModuleUrl(modKey, updateHistory);
  activateModuleScreen(modKey);
  const itemObj = MODULE_NAV_CONFIG.find(i => i.key === modKey);
  if (itemObj?.section) {
    const sectionKey = `${itemObj.group}__${itemObj.section}`;
    const safeId = 'acc-section-' + sectionKey.replace(/[^a-zA-Z0-9]/g, '_');
    const body = document.getElementById(safeId);
    if (body && body.classList.contains('hidden')) {
      toggleSidebarSection(sectionKey);
    }
  }
  if (window.innerWidth < 1024) document.getElementById('sidebar').classList.add('-translate-x-full');
  updateBreadcrumb();
  if (modKey !== 'app_settings') {
    await processWithLoading(async () => {
      const res = await fetch(`/api/module/${encodeURIComponent(modKey)}`);
      const payload = await res.json();
      if (!res.ok) throw new Error(payload.message || 'Gagal memuat modul.');
      DATA = { ...DATA, ...payload };
      clearModuleFilters(modKey);
      renderAllModules();
    }, 'Gagal memuat data modul');
  } else {
    clearModuleFilters(modKey);
    renderAllModules();
  }
}

function renderAllModules() {
  document.getElementById('syncStatusLabel').textContent = DATA.status_msg || '-';
  document.getElementById('syncTimeLabel').textContent = DATA.server_time || '';
  document.getElementById('statInfoCount').textContent = (DATA.info_board || []).length;

  if (ACTIVE_MODULE === 'overview') {
    renderTimelineModule();
  } else if (ACTIVE_MODULE === 'info_board') {
    renderInfoBoard();
  } else if (ACTIVE_MODULE === 'data_pegawai') renderDataPegawai();
  else if (ACTIVE_MODULE === 'arsip_sdm') renderArsipSdm();
  else if (ACTIVE_MODULE === 'produksi_paket') renderProduksiPaket();
  else if (ACTIVE_MODULE === 'dialog') {
    renderTimelineModule();
    renderDialogModule();
  } else if (ACTIVE_MODULE === 'jadwal_siaran') renderJadwalSiaran();
  else if (ACTIVE_MODULE === 'program_siaran') renderProgramSiaran();
  else if (ACTIVE_MODULE === 'arsip_program') renderArsipProgram();
  else if (ACTIVE_MODULE === 'konten') renderKonten();
  else if (ACTIVE_MODULE === 'bestcut_monitoring') renderBestcutMonitoring();
  else if (ACTIVE_MODULE === 'socmed_analytics') renderSocmedAnalytics();
  else if (ACTIVE_MODULE === 'jadwal_tmb') renderJadwalTmb();
  else if (ACTIVE_MODULE === 'tmb_working_progresss') renderMonitoringProduksi();
  else if (ACTIVE_MODULE === 'master_barang') renderMasterBarang();
  else if (ACTIVE_MODULE === 'bast_otomatis') initBastSelectors();
  else if (ACTIVE_MODULE === 'pemeliharaan_aset') renderPemeliharaanAset();
  // else if (ACTIVE_MODULE === 'bmn_arsip') renderBmnArsip();
  else if (ACTIVE_MODULE === 'bmn_arsip') renderBmnDokumenView('Aset', 'Arsip', 'filterBmnArsip', 'tbodyBmnArsip', 'pagBmnArsip', 'selectBmnArsipPeriode');
  else if (ACTIVE_MODULE === 'aset_tutup_buku') renderBmnDokumenView('Aset', 'Tutup Buku', 'filterAsetTutupBukuPeriode', 'tbodyAsetTutupBuku', 'pagAsetTutupBuku', 'selectAsetTutupBukuPeriode');
  else if (ACTIVE_MODULE === 'aset_calbmn') renderBmnDokumenView('Aset', 'CALBMN', 'filterCalbmnPeriode', 'tbodyCalbmn', 'pagCalbmn', 'selectCalbmnPeriode');
  else if (ACTIVE_MODULE === 'aset_wasdal') renderBmnDokumenView('Aset', 'WASDAL', 'filterWasdalPeriode', 'tbodyWasdal', 'pagWasdal', 'selectWasdalPeriode');
  else if (ACTIVE_MODULE === 'aset_rkbmn') renderBmnDokumenView('Aset', 'RKBMN', 'filterRkbmnPeriode', 'tbodyRkbmn', 'pagRkbmn', 'selectRkbmnPeriode');
  else if (ACTIVE_MODULE === 'aset_manajemen_risiko') renderBmnDokumenView('Aset', 'Manajemen Risiko', 'filterManRisikoPeriode', 'tbodyManRisiko', 'pagManRisiko', 'selectManRisikoPeriode');
  else if (ACTIVE_MODULE === 'aset_sisporja') renderBmnDokumenView('Aset', 'SISPORJA', 'filterSisporjaPeriode', 'tbodySisporja', 'pagSisporja', 'selectSisporjaPeriode');
  else if (ACTIVE_MODULE === 'master_persediaan') renderMasterPersediaan();
  else if (ACTIVE_MODULE === 'persediaan_tutup_buku') renderBmnDokumenView('Persediaan', 'Tutup Buku', 'filterPersediaanTutupBukuPeriode', 'tbodyPersediaanTutupBuku', 'pagPersediaanTutupBuku', 'selectPersediaanTutupBukuPeriode');
  else if (ACTIVE_MODULE === 'persediaan_form_pengajuan') renderBmnDokumenView('Persediaan', 'Form Pengajuan', 'filterPengajuanPeriode', 'tbodyPengajuanPersediaan', 'pagPengajuanPersediaan', 'selectPengajuanPeriode');
  else if (ACTIVE_MODULE === 'persediaan_pipk') renderBmnDokumenView('Persediaan', 'PIPK', 'filterPipkPeriode', 'tbodyPipk', 'pagPipk', 'selectPipkPeriode');
  else if (ACTIVE_MODULE === 'master_ruangan') renderMasterRuangan();
  else if (ACTIVE_MODULE === 'manage_users') renderManageUsers();
  else if (ACTIVE_MODULE === 'manage_modules') renderManageModules();
  else if (ACTIVE_MODULE === 'app_settings' && isAdmin()) renderAppSettings();
}

function renderAppSettings() {
  const config = DATA.app_config || APP_CONFIG;
  document.getElementById('appTimezone').value = config.timezone || 'Asia/Makassar';
  document.getElementById('appLanguage').value = config.language || 'id';
  document.getElementById('appDefaultTheme').value = config.default_theme || 'light';
  document.getElementById('appActiveYear').value = config.active_year || APP_CONFIG.active_year;
  if (document.getElementById('appDriveRootFolderId')) document.getElementById('appDriveRootFolderId').value = config.drive_root_folder_id || '';
  if (document.getElementById('appBastTemplateDocId')) document.getElementById('appBastTemplateDocId').value = config.bast_template_doc_id || '';
  if (document.getElementById('appDriveBridgeUrl')) document.getElementById('appDriveBridgeUrl').value = config.drive_bridge_url || '';
  if (document.getElementById('appDriveBridgeSecret')) document.getElementById('appDriveBridgeSecret').value = config.drive_bridge_secret || 'beacon-rri-secret-2026';
}

async function submitAppSettings(event) {
  event.preventDefault();
  const button = document.getElementById('btnSaveAppSettings');
  button.disabled = true;
  const settings = {
    timezone: document.getElementById('appTimezone').value,
    language: document.getElementById('appLanguage').value,
    default_theme: document.getElementById('appDefaultTheme').value,
    active_year: document.getElementById('appActiveYear').value,
    drive_root_folder_id: (document.getElementById('appDriveRootFolderId')?.value || '').trim(),
    bast_template_doc_id: (document.getElementById('appBastTemplateDocId')?.value || '').trim(),
    drive_bridge_url: (document.getElementById('appDriveBridgeUrl')?.value || '').trim(),
    drive_bridge_secret: (document.getElementById('appDriveBridgeSecret')?.value || '').trim()
  };
  try {
    const result = await processWithLoading(async () => {
      const response = await fetch('/api/admin/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ settings })
      });
      const result = await response.json();
      if (result.ok) {
        DATA.app_config = result.app_config;
        applyTheme(result.app_config.default_theme);
        await loadDashboard();
      }
      return result;
    }, 'Gagal menyimpan pengaturan');
    if (result) showToast(result.message, result.ok ? 'success' : 'error');
  } finally {
    button.disabled = false;
  }
}

async function deleteRecord(targetKey, rowNum, label = 'data ini') {
  if (!rowNum) { showToast('Nomor baris tidak ditemukan.', 'error'); return; }
  const isLinkedBast = targetKey === 'DB_BAST'
    || (targetKey === 'DB_BMN_Dokumen' && /bast/i.test(label));
  const confirmation = isLinkedBast
    ? `Hapus ${label} dan baris BAST terkait dari kedua modul?`
    : `Hapus ${label}?`;
  if (!confirm(confirmation)) return;
  const out = await processWithLoading(async () => {
    const res = await fetch(`/api/delete/${targetKey}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ row_num: rowNum })
    });
    const out = await res.json();
    if (out.ok) await loadDashboard();
    return out;
  }, 'Gagal menghapus data');
  if (out) showToast(out.message, out.ok ? 'success' : 'error');
}

function renderInfoBoard() {
  const deletable = canFull('info_board');
  const cards = (DATA.info_board || []).map(i => `
    <div class="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700 space-y-1.5">
      <div class="flex items-center justify-between text-[11px]">
        <span class="font-extrabold px-2 py-0.5 rounded-full ${String(i.Prioritas).toLowerCase() === 'urgent' ? 'bg-rose-100 text-rose-700' : 'bg-teal-100 text-teal-700'}">${i.Prioritas || 'Info'}</span>
        <div class="flex items-center gap-2">
          <span class="text-slate-400">${i.Tanggal || ''} • ${i['Target Divisi'] || 'Semua'}</span>
          ${deletable && i._row_num ? `<button type="button" title="Hapus pengumuman" aria-label="Hapus pengumuman" onclick="deleteRecord('DB_Info_Board', ${i._row_num}, '${(i.Judul || '').replace(/'/g, '')}')" class="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-rose-50 dark:bg-rose-900/70 text-rose-600 dark:text-rose-200 hover:bg-rose-100 dark:hover:bg-rose-800 transition">${icon('delete')}</button>` : ''}
        </div>
      </div>
      <h4 class="font-extrabold text-sm">${i.Judul || ''}</h4>
      <p class="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">${i.Isi || ''}</p>
    </div>
  `).join('') || `<p class="text-xs text-slate-400">Belum ada pengumuman di Info Board.</p>`;
  const overviewList = document.getElementById('overviewInfoList');
  const fullList = document.getElementById('fullInfoBoardList');
  if (overviewList) overviewList.innerHTML = cards;
  if (fullList) fullList.innerHTML = cards;
}

function renderTimelineModule() {
  const body = document.getElementById('tbodyTimeline');
  if (!body) return;
  const canEdit = canUpdate('dialog');
  const canDelete = canFull('dialog');
  const query = (document.getElementById('searchTimeline')?.value || '').trim().toLowerCase();
  const startFilter = document.getElementById('timelineFilterStart')?.value || '';
  const endFilter = document.getElementById('timelineFilterEnd')?.value || '';
  const filtered = (DATA.timeline || []).filter(item => {
    const searchValues = [
      item.Kegiatan, item.Tahapan, item['Tanggal Mulai'], item['Start Date'],
      item['Tanggal Selesai'], item['End Date'], item.Tanggal, item.Keterangan
    ];
    const matchesSearch = !query || searchValues.some(value => String(value || '').toLowerCase().includes(query));
    const itemDate = dateValueForInput(item['Tanggal Mulai'] || item['Start Date'] || item.Tanggal || '');
    const matchesDateRange = (!startFilter || (itemDate && itemDate >= startFilter)) &&
      (!endFilter || (itemDate && itemDate <= endFilter));
    return matchesSearch && matchesDateRange;
  });
  filtered.sort((a, b) => {
    const getValue = item => TIMELINE_SORT.key === 'Tanggal Mulai'
      ? dateValueForInput(item['Tanggal Mulai'] || item['Start Date'] || item.Tanggal || '')
      : String(item[TIMELINE_SORT.key] || '').trim();
    const aValue = getValue(a);
    const bValue = getValue(b);
    if (!aValue) return bValue ? 1 : 0;
    if (!bValue) return -1;
    const order = aValue.localeCompare(bValue, 'id', { numeric: true, sensitivity: 'base' });
    return TIMELINE_SORT.direction === 'asc' ? order : -order;
  });
  const sortIndicators = {
    Kegiatan: 'sortTimelineKegiatan',
    Tahapan: 'sortTimelineTahapan',
    'Tanggal Mulai': 'sortTimelineDate',
    Keterangan: 'sortTimelineKeterangan'
  };
  Object.entries(sortIndicators).forEach(([key, id]) => {
    const indicator = document.getElementById(id);
    if (indicator) indicator.textContent = TIMELINE_SORT.key === key
      ? (TIMELINE_SORT.direction === 'asc' ? '↑' : '↓')
      : '';
  });
  const rows = paginateArray('timeline', filtered, 'pagTimeline', 'renderTimelineModule');
  body.innerHTML = rows.map(item => {
    const rowNum = Number(item._row_num);
    const startDate = item['Tanggal Mulai'] || item['Start Date'] || item.Tanggal || '';
    const endDate = item['Tanggal Selesai'] || item['End Date'] || '';
    const dateLabel = startDate && endDate && startDate !== endDate
      ? `${startDate} — ${endDate}`
      : startDate || endDate || '-';
    const actions = [
      canEdit && rowNum >= 2
        ? `<button type="button" title="Edit kegiatan" aria-label="Edit kegiatan" onclick="openTimelineModalByRow(${rowNum})" class="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-100 hover:bg-slate-200 dark:hover:bg-teal-700 transition">${icon('edit')}</button>`
        : '',
      canDelete && rowNum >= 2
        ? `<button type="button" title="Hapus kegiatan" aria-label="Hapus kegiatan" onclick="deleteRecord('DB_Timeline', ${rowNum}, 'kegiatan ini')" class="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-rose-50 dark:bg-rose-900/70 text-rose-600 dark:text-rose-200 hover:bg-rose-100 dark:hover:bg-rose-800 transition">${icon('delete')}</button>`
        : ''
    ].filter(Boolean).join(' ');
    return `
      <tr class="hover:bg-slate-200/50 dark:hover:bg-slate-800/50 transition border-b border-slate-100 dark:border-slate-800">
        <td class="py-3 px-3 font-extrabold">${escapeHtml(item.Kegiatan || '-')}</td>
        <td class="py-3 px-3">${escapeHtml(item.Tahapan || '-')}</td>
        <td class="py-3 px-3 whitespace-nowrap">${escapeHtml(dateLabel)}</td>
        <td class="py-3 px-3 text-slate-500">${escapeHtml(item.Keterangan || '-')}</td>
        <td class="py-3 px-3 text-right whitespace-nowrap space-x-1">${actions || '-'}</td>
      </tr>
    `;
  }).join('') || '<tr><td colspan="5" class="py-8 text-center text-xs text-slate-400">Belum ada data timeline.</td></tr>';
  renderTimelineCalendar(filtered);
  renderDashboardHorizontalTimeline(filtered);
  setTimelineView(TIMELINE_VIEW);
}

function filterTimelineTable() {
  PAGE_STATE.timeline = PAGE_STATE.timeline || { page: 1, size: DEFAULT_PAGE_SIZE };
  PAGE_STATE.timeline.page = 1;
  renderTimelineModule();
}

function sortTimelineTable(key) {
  if (TIMELINE_SORT.key === key) {
    TIMELINE_SORT.direction = TIMELINE_SORT.direction === 'asc' ? 'desc' : 'asc';
  } else {
    TIMELINE_SORT = { key, direction: 'asc' };
  }
  PAGE_STATE.timeline = PAGE_STATE.timeline || { page: 1, size: DEFAULT_PAGE_SIZE };
  PAGE_STATE.timeline.page = 1;
  renderTimelineModule();
}

function setTimelineView(view) {
  TIMELINE_VIEW = view;
  const views = {
    table: ['timelineTableTab', 'timelineTableView'],
    calendar: ['timelineCalendarTab', 'timelineCalendarView'],
    horizontal: ['timelineHorizontalTab', 'timelineHorizontalView']
  };
  Object.entries(views).forEach(([key, [tabId, panelId]]) => {
    const active = key === view;
    const tab = document.getElementById(tabId);
    const panel = document.getElementById(panelId);
    if (tab) {
      tab.setAttribute('aria-selected', String(active));
      tab.classList.toggle('bg-teal-600', active);
      tab.classList.toggle('text-white', active);
      tab.classList.toggle('border-teal-600', active);
      tab.classList.toggle('bg-slate-100', !active);
      tab.classList.toggle('text-slate-600', !active);
      tab.classList.toggle('dark:bg-slate-800', !active);
      tab.classList.toggle('dark:text-slate-300', !active);
      tab.classList.toggle('border-slate-200', !active);
      tab.classList.toggle('dark:border-slate-700', !active);
    }
    if (panel) panel.classList.toggle('hidden', !active);
    if (TIMELINE_VIEW === 'horizontal') { 
      const scroller = document.getElementById('dashboardTimelineScroll');
      if (scroller) scroller.scrollTo({ left: scroller.scrollWidth, behavior: 'smooth' });
    }
  });
}

function changeTimelineMonth(offset) {
  TIMELINE_CALENDAR_MONTH = new Date(
    TIMELINE_CALENDAR_MONTH.getFullYear(),
    TIMELINE_CALENDAR_MONTH.getMonth() + offset,
    1
  );
  renderTimelineModule();
}

function timelineDateObject(value) {
  const isoDate = dateValueForInput(value);
  if (!isoDate) return null;
  const [year, month, day] = isoDate.split('-').map(Number);
  return new Date(year, month - 1, day);
}

function timelineDateKey(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

function renderTimelineCalendar(items) {
  const grid = document.getElementById('timelineCalendarGrid');
  const title = document.getElementById('timelineCalendarMonth');
  if (!grid || !title) return;
  const year = TIMELINE_CALENDAR_MONTH.getFullYear();
  const month = TIMELINE_CALENDAR_MONTH.getMonth();
  title.textContent = new Intl.DateTimeFormat('id-ID', { month: 'long', year: 'numeric' }).format(TIMELINE_CALENDAR_MONTH);

  const eventsByDate = new Map();
  items.forEach(item => {
    const date = timelineDateObject(item['Tanggal Mulai'] || item['Start Date'] || item.Tanggal || '');
    if (!date) return;
    const key = timelineDateKey(date);
    eventsByDate.set(key, [...(eventsByDate.get(key) || []), item]);
  });

  const firstDayOffset = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const cellCount = Math.ceil((firstDayOffset + daysInMonth) / 7) * 7;
  const todayKey = timelineDateKey(new Date());
  grid.innerHTML = Array.from({ length: cellCount }, (_, index) => {
    const day = index - firstDayOffset + 1;
    const date = new Date(year, month, day);
    const inMonth = day > 0 && day <= daysInMonth;
    const key = timelineDateKey(date);
    const dayEvents = inMonth ? (eventsByDate.get(key) || []) : [];
    const eventRows = dayEvents.slice(0, 3).map(item => `
      <div title="${escapeHtml(item.Kegiatan || '')}${item.Tahapan ? ` — ${escapeHtml(item.Tahapan)}` : ''}"
        class="mt-1 px-1.5 py-1 rounded-md bg-teal-50 dark:bg-teal-950/60 border border-teal-100 dark:border-teal-900 text-teal-800 dark:text-teal-200">
        <p class="font-extrabold truncate">${escapeHtml(item.Kegiatan || 'Kegiatan')}</p>
        ${item.Tahapan ? `<p class="truncate opacity-80">${escapeHtml(item.Tahapan)}</p>` : ''}
      </div>
    `).join('');
    const moreEvents = dayEvents.length > 3
      ? `<p class="mt-1 text-[9px] font-bold text-slate-400">+${dayEvents.length - 3} kegiatan</p>`
      : '';
    return `
      <div class="min-h-[115px] border-r border-b border-slate-200 dark:border-slate-700 p-1.5 ${inMonth ? '' : 'bg-slate-50/70 dark:bg-slate-900/40'}">
        <div class="text-right text-[10px] font-bold ${!inMonth ? 'text-slate-300 dark:text-slate-600' : key === todayKey ? 'text-teal-600' : 'text-slate-500 dark:text-slate-400'}">${date.getDate()}</div>
        ${eventRows}${moreEvents}
      </div>
    `;
  }).join('');
}

function renderDashboardHorizontalTimeline(items) {
  const track = document.getElementById('dashboardTimelineTrack');
  if (!track) return;
  const ordered = [...items].sort((a, b) => {
    const aDate = dateValueForInput(a['Tanggal Mulai'] || a['Start Date'] || a.Tanggal || '');
    const bDate = dateValueForInput(b['Tanggal Mulai'] || b['Start Date'] || b.Tanggal || '');
    if (!aDate) return bDate ? 1 : 0;
    if (!bDate) return -1;
    return aDate.localeCompare(bDate);
  });
  if (!ordered.length) {
    track.innerHTML = '<div class="w-full text-center py-12 text-xs text-slate-400">Tidak ada tahapan kegiatan ditemukan.</div>';
    return;
  }
  track.innerHTML = ordered.map((item, index) => {
    const isBottom = index % 2 === 0;
    const startDate = item.Tanggal || item['Tanggal Mulai'] || item['Start Date'] || '';
    const dateLabel = startDate;
    const card = `<div class="w-[215px] min-h-[76px] flex flex-col items-center justify-center text-center p-3 rounded-xl bg-white dark:bg-slate-800 border border-sky-300 dark:border-sky-800 shadow-sm"><div class="text-xs font-extrabold text-teal-700 dark:text-teal-300">${escapeHtml(item.Kegiatan || '')}</div><div class="text-[11px] text-slate-600 dark:text-slate-300 mt-1">${escapeHtml(item.Tahapan || '')}</div></div>`;
    return `
      <div class="relative flex flex-col items-center w-[235px] shrink-0 select-none">
        <div class="h-[105px] flex flex-col items-center justify-end w-full">${!isBottom ? `${card}<div class="w-[2px] h-5 bg-sky-300"></div>` : ''}</div>
        <div class="relative w-full flex items-center justify-center h-6"><div class="w-full h-[3px] bg-slate-300 dark:bg-slate-600"></div><div class="absolute w-5 h-5 rounded-full bg-white dark:bg-slate-800 border-[3px] border-slate-500 dark:border-slate-300 z-10"></div></div>
        <div class="mt-1.5 text-xs font-extrabold text-slate-700 dark:text-slate-200">${escapeHtml(dateLabel)}</div>
        <div class="h-[105px] flex flex-col items-center justify-start w-full">${isBottom ? `<div class="w-[2px] h-5 bg-sky-300 mt-1"></div>${card}` : ''}</div>
      </div>
    `;
  }).join('');
}

function renderDataPegawai() {
  const q = (document.getElementById('searchPegawai')?.value || '').toLowerCase();
  const editable = canUpdate('data_pegawai');
  const deletable = canFull('data_pegawai');
  const filtered = (DATA.employees || []).filter(e => Object.values(e).some(v => String(v).toLowerCase().includes(q)));
  const rows = paginateArray('pegawai', filtered, 'pagPegawai', 'renderDataPegawai');
  const itemOffset = (PAGE_STATE.pegawai.page - 1) * PAGE_STATE.pegawai.size;

  document.getElementById('tbodyPegawai').innerHTML = rows.map((e, index) => `
    <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
      <td class="py-3 px-3 text-slate-400">${itemOffset + index + 1}</td>
      <td class="py-3 px-3 font-extrabold">${e['Nama Pegawai'] || '-'}</td>
      <td class="py-3 px-3 font-mono text-xs text-slate-500">${e.NIP || '-'}</td>
      <td class="py-3 px-3 text-xs">${e['Pangkat Golongan'] || '-'}</td>
      <td class="py-3 px-3 text-xs">${e.Jabatan || '-'}</td>
      <td class="py-3 px-3 text-xs font-semibold">${e.Posisi || '-'}</td>
      <td class="py-3 px-3">
        <span class="px-2 py-0.5 rounded-full text-[11px] font-bold ${String(e.Status || 'Aktif').toLowerCase() === 'aktif' ? 'bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-300' : 'bg-amber-50 dark:bg-amber-950 text-amber-600 dark:text-amber-300'}">${e.Status || 'Aktif'}</span>
      </td>
      <td class="py-3 px-3 text-right whitespace-nowrap space-x-1">
        ${editable ? `<button type="button" title="Edit pegawai" aria-label="Edit pegawai" onclick="openEmpEditByRow(${Number(e._row_num)})" class="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-100 hover:bg-slate-200 dark:hover:bg-teal-700 transition">${icon('edit')}</button>` : ''}
        ${deletable && e._row_num ? `<button type="button" title="Hapus pegawai" aria-label="Hapus pegawai" onclick="deleteRecord('DB_Pegawai', ${e._row_num}, '${(e['Nama Pegawai'] || '').replace(/'/g, '')}')" class="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-rose-50 dark:bg-rose-900/70 text-rose-600 dark:text-rose-200 hover:bg-rose-100 dark:hover:bg-rose-800 transition">${icon('delete')}</button>` : ''}
      </td>
    </tr>
  `).join('');
}

function openEmpEditByRow(rowNum) {
  const emp = (DATA.employees || []).find(item => Number(item._row_num) === rowNum);
  if (emp) openEmpEdit(emp);
}

function openEmpEdit(emp) {
  document.getElementById('editEmpRowNum').value = emp._row_num || '';
  document.getElementById('editEmpNip').value = emp.NIP || '';
  document.getElementById('editEmpNama').value = emp['Nama Pegawai'] || '';
  document.getElementById('editEmpPangkat').value = emp['Pangkat Golongan'] || '';
  document.getElementById('editEmpJabatan').value = emp.Jabatan || '';
  document.getElementById('editEmpPosisi').value = emp.Posisi || '';
  document.getElementById('editEmpStatus').value = emp.Status || 'Aktif';
  const m = document.getElementById('empEditModal');
  m.classList.remove('hidden'); m.classList.add('flex');
}
function closeEmpEditModal() { const m = document.getElementById('empEditModal'); m.classList.add('hidden'); m.classList.remove('flex'); }
async function submitEmpUpdate(e) {
  e.preventDefault();
  const row_num = document.getElementById('editEmpRowNum').value;
  const updates = {
    'NIP': document.getElementById('editEmpNip').value,
    'Nama Pegawai': document.getElementById('editEmpNama').value,
    'Pangkat Golongan': document.getElementById('editEmpPangkat').value,
    'Jabatan': document.getElementById('editEmpJabatan').value,
    'Posisi': document.getElementById('editEmpPosisi').value,
    'Status': document.getElementById('editEmpStatus').value,
  };
  const out = await processWithLoading(async () => {
    const res = await fetch('/api/employees/update', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ row_num, updates }) });
    const out = await res.json();
    if (out.ok) { closeEmpEditModal(); await loadDashboard(); }
    return out;
  }, 'Gagal memperbarui pegawai');
  if (out) showToast(out.message, out.ok ? 'success' : 'error');
}

function renderArsipSdm() {
  const q = (document.getElementById('searchArsipSdm')?.value || '').toLowerCase();
  const filtered = (DATA.arsip_sdm || []).filter(a => Object.values(a).some(v => String(v).toLowerCase().includes(q)));
  const rows = paginateArray('arsip_sdm', filtered, 'pagArsipSdm', 'renderArsipSdm');
  document.getElementById('tbodyArsipSdm').innerHTML = rows.map(a => `
    <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
      <td class="py-3 px-3 font-mono text-xs font-bold">${a['Nomor Dokumen'] || '-'}</td>
      <td class="py-3 px-3 font-bold">${a['Nama Dokumen'] || '-'}</td>
      <td class="py-3 px-3 text-xs text-slate-500">${a.Tanggal || '-'}</td>
      <td class="py-3 px-3"><span class="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-200">${a.Jenis || '-'}</span></td>
      <td class="py-3 px-3">${a.Link ? `<a href="${a.Link}" target="_blank" class="text-xs font-bold text-teal-600 hover:underline">Buka ↗</a>` : '-'}</td>
    </tr>
  `).join('');
}

function renderDialogModule() {
  const q = (document.getElementById('searchDialog')?.value || '').toLowerCase();
  const editable = canUpdate('dialog');
  const filtered = (DATA.dialogs || []).filter(d => Object.values(d).some(v => String(v).toLowerCase().includes(q)));
  const rows = paginateArray('dialog', filtered, 'pagDialog', 'renderDialogModule');
  document.getElementById('tbodyDialog').innerHTML = rows.map(d => {
    const bestcut = d.Bestcut || '';
    const bestcutCell = bestcut.startsWith('http')
      ? `<a href="${bestcut}" target="_blank" class="text-xs font-bold text-teal-600 hover:underline">Bestcut ↗</a>`
      : `<span class="text-xs text-slate-400">${bestcut || '-'}</span>`;
    return `
      <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
        <td class="py-3 px-3 text-xs font-bold whitespace-nowrap">${d.Tanggal || '-'}</td>
        <td class="py-3 px-3 text-xs font-bold text-sky-600">${d.Program || '-'}</td>
        <td class="py-3 px-3 text-xs font-semibold max-w-xs">${d.Topik || '-'}</td>
        <td class="py-3 px-3 text-xs">${d.Narasumber || '-'}</td>
        <td class="py-3 px-3 text-xs">${d.Kehadiran || '-'}</td>
        <td class="py-3 px-3 text-xs font-bold">${d.Keterlaksanaan || '-'}</td>
        <td class="py-3 px-3 whitespace-nowrap">${bestcutCell}</td>
        <td class="py-3 px-3">${editable && d._row_num ? `<button type="button" title="Update dialog" aria-label="Update dialog" onclick='openDialogEdit(${JSON.stringify(d)})' class="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-100 hover:bg-slate-200 dark:hover:bg-teal-700 transition">${icon('edit')}</button>` : '-'}</td>
      </tr>
    `;
  }).join('');
}

function renderJadwalSiaran() {
  const rows = paginateArray('siaran', DATA.siaran || [], 'pagSiaran', 'renderJadwalSiaran');
  document.getElementById('tbodySiaran').innerHTML = rows.map(s => `
    <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
      <td class="py-3 px-3 font-mono text-xs text-slate-500">${escapeHtml(s['ID Jadwal'] || '-')}</td>
      <td class="py-3 px-3 font-bold">${escapeHtml(s.Tanggal || '-')}</td>
      <td class="py-3 px-3 text-xs">${escapeHtml(s.Shift || '-')}</td>
      <td class="py-3 px-3 font-bold text-teal-600">${escapeHtml(s.Bidang || s.Programa || '-')}</td>
      <td class="py-3 px-3 font-semibold">${escapeHtml(s['Pegawai Nama'] || s.Penyiar || '-')}</td>
      <td class="py-3 px-3 text-xs text-slate-500">${escapeHtml(s['Pegawai Jabatan'] || s.Operator || '-')}</td>
      <td class="py-3 px-3"><span class="px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-300">${escapeHtml(s.Status || '-')}</span></td>
    </tr>
  `).join('') || '<tr><td colspan="7" class="py-8 text-center text-xs text-slate-400">Belum ada jadwal siaran.</td></tr>';
}

function renderProgramSiaran() {
  const rows = paginateArray('program_siaran', DATA.program_siaran || [], 'pagProgramSiaran', 'renderProgramSiaran');
  document.getElementById('tbodyProgramSiaran').innerHTML = rows.map(p => `
    <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
      <td class="py-3 px-3 font-mono text-xs text-slate-500">${escapeHtml(p['Kode Program'] || '-')}</td>
      <td class="py-3 px-3 font-bold text-teal-600">${escapeHtml(p.Programa || '-')}</td>
      <td class="py-3 px-3 font-extrabold">${escapeHtml(p['Nama Program'] || '-')}</td>
      <td class="py-3 px-3 text-xs">${escapeHtml(p.Hari || '-')}</td>
      <td class="py-3 px-3 text-xs font-semibold">${escapeHtml(p.Jam || '-')}</td>
      <td class="py-3 px-3 text-xs">${escapeHtml(p.Kategori || p.Format || '-')}</td>
      <td class="py-3 px-3"><span class="px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-300">${escapeHtml(p.Status || 'Aktif')}</span></td>
    </tr>
  `).join('');
}

function renderArsipProgram() {
  const tbody = document.getElementById('tbodyArsipProgram');
  if (!tbody) return;
  const query = (document.getElementById('searchArsipProgram')?.value || '').toLowerCase();
  const filtered = (DATA.arsip_program || []).filter(a =>
    Object.values(a).some(value => String(value ?? '').toLowerCase().includes(query))
  );
  const rows = paginateArray('arsip_program', filtered, 'pagArsipProgram', 'renderArsipProgram');
  tbody.innerHTML = rows.map(a => `
    <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
      <td class="py-3 px-3 font-mono text-xs font-bold text-teal-600">${escapeHtml(a['ID Dokumen'] || '-')}</td>
      <td class="py-3 px-3 text-xs font-bold">${escapeHtml(a.Kategori || '-')}</td>
      <td class="py-3 px-3"><span class="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-xs font-semibold">${escapeHtml(a.Jenis || '-')}</span></td>
      <td class="py-3 px-3 text-xs text-slate-500 whitespace-nowrap">${escapeHtml(a['Tanggal Upload'] || '-')}</td>
      <td class="py-3 px-3 font-bold">${escapeHtml(a['Nama Dokumen'] || '-')}</td>
      <td class="py-3 px-3 text-xs text-slate-400">${escapeHtml(a.Keterangan || '-')}</td>
      <td class="py-3 px-3">${a.Link ? `<a href="${escapeHtml(a.Link)}" target="_blank" rel="noopener" class="text-xs font-bold text-teal-600 hover:underline">Buka ↗</a>` : '-'}</td>
    </tr>
  `).join('') || '<tr><td colspan="7" class="py-8 text-center text-xs text-slate-400">Belum ada arsip program.</td></tr>';
}

function renderKonten() {
  document.getElementById('gridKonten').innerHTML = (DATA.content_planner || []).map(p => `
    <div class="bg-white dark:bg-[#111827] rounded-3xl border border-slate-200/80 dark:border-slate-800 p-5 space-y-2 hover:bg-slate-200/40 transition">
      <div class="flex justify-between text-xs font-bold">
        <span class="text-teal-600">${p.Akun || p.Platform}</span>
        <span class="px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800">${p.Status || '-'}</span>
      </div>
      <h4 class="font-extrabold text-sm">${p['Judul Konten'] || '-'}</h4>
      <p class="text-xs text-slate-400">${p['Tanggal Tayang'] || ''} • ${p.Jenis || ''} • PIC: ${p.PIC || '-'}</p>
      ${p['Link Asset'] ? `<a href="${p['Link Asset']}" target="_blank" class="inline-block text-xs font-bold text-sky-600 hover:underline pt-1">Lihat Asset ↗</a>` : ''}
    </div>
  `).join('');
}

function renderJadwalTmb() {
  const rows = paginateArray('jadwal_tmb', DATA.jadwal_tmb || [], 'pagTmb', 'renderJadwalTmb');
  document.getElementById('tbodyTmb').innerHTML = rows.map(t => `
    <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
      <td class="py-3 px-3 font-mono text-xs text-slate-500">${escapeHtml(t['ID Jadwal'] || '-')}</td>
      <td class="py-3 px-3 font-bold">${escapeHtml(t.Tanggal || '-')}</td>
      <td class="py-3 px-3 text-xs">${escapeHtml(t.Shift || '-')}</td>
      <td class="py-3 px-3 font-bold text-indigo-600">${escapeHtml(t.Bidang || t['Lokasi Pemancar'] || '-')}</td>
      <td class="py-3 px-3 font-semibold">${escapeHtml(t['Pegawai Nama'] || t['Teknisi TMB'] || '-')}</td>
      <td class="py-3 px-3 text-xs text-slate-500">${escapeHtml(t['Pegawai Jabatan'] || t.Tugas || '-')}</td>
      <td class="py-3 px-3"><span class="px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-300">${escapeHtml(t.Status || '-')}</span></td>
    </tr>
  `).join('') || '<tr><td colspan="7" class="py-8 text-center text-xs text-slate-400">Belum ada jadwal TMB.</td></tr>';
}

function renderMasterBarang() {
  const q = (document.getElementById('searchBarang')?.value || '').toLowerCase();
  const cat = (document.getElementById('filterAsetKategori')?.value || 'all').toLowerCase();
  const editable = canUpdate('master_barang');
  const deletable = canFull('master_barang');
  const filtered = (DATA.assets || []).filter(a => {
    const matchText = Object.values(a).some(v => String(v).toLowerCase().includes(q));
    const matchCat = cat === 'all' || String(a['Tindak Lanjut'] || '').toLowerCase().includes(cat);
    return matchText && matchCat;
  });
  const rows = paginateArray('barang', filtered, 'pagBarang', 'renderMasterBarang');
  document.getElementById('tbodyBarang').innerHTML = rows.map(a => {
    const safeAsset = encodeURIComponent(JSON.stringify(a));
    const rowNum = a._row_num ?? a.row_num;
    return `
      <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
        <td class="py-3 px-3 text-[10px] font-semibold">${escapeHtml(a['Kode Ruang'] || '-')} <span class="block text-slate-400">${escapeHtml(a['Nama Ruangan'] || '')}</span></td>
        <td class="py-3 px-3"><span class="px-2.5 py-0.5 rounded-lg bg-slate-900 dark:bg-slate-700 text-white text-xs font-extrabold">${escapeHtml(a['Kode Barang'] || '-')}</span></td>
        <td class="py-3 px-3 font-semibold text-indigo-600 dark:text-indigo-400">${escapeHtml(a['Nama Barang'] || '-')}</td>
        <td class="py-3 px-3 text-xs text-slate-500">${escapeHtml(a['Merk Model'] || '-')}</td>
        <td class="py-3 px-3 text-xs text-slate-500">${escapeHtml(a.Tipe || '-')}</td>
        <td class="py-3 px-3">${escapeHtml(a.Tahun || '-')}</td>
        <td class="py-3 px-3 font-bold">${escapeHtml(a.NUP || '-')}</td>
        <td class="py-3 px-3 font-bold ${String(a.Kondisi).toLowerCase() === 'baik' ? 'text-emerald-600' : 'text-rose-500'}">${escapeHtml(a.Kondisi || '-')}</td>
        <td class="py-3 px-3 text-amber-600">${escapeHtml(a['Tindak Lanjut'] || '-')}</td>
        <td class="py-3 px-3 text-right whitespace-nowrap">
          ${editable && rowNum ? `<button type="button" title="Edit barang" aria-label="Edit barang" onclick="openAssetModal(JSON.parse(decodeURIComponent('${safeAsset}')))" class="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-100 hover:bg-slate-200 dark:hover:bg-teal-700 transition">${icon('edit')}</button>` : ''}
          ${deletable && rowNum ? `<button type="button" title="Hapus barang" aria-label="Hapus barang" onclick="deleteRecord('DB_Aset', ${rowNum}, '${escapeHtml(a['Nama Barang'] || 'barang ini').replace(/'/g, '')}')" class="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-rose-50 dark:bg-rose-900/70 text-rose-600 dark:text-rose-200 hover:bg-rose-100 dark:hover:bg-rose-800 transition">${icon('delete')}</button>` : ''}
        </td>
      </tr>
    `;
  }).join('');
}

let CURRENT_STOK_ITEM = null;

function renderMasterPersediaan() {
  const q = (document.getElementById('searchPersediaan')?.value || '').toLowerCase();
  const filtered = (DATA.stock_master || []).filter(s =>
    String(s['Kode Barang'] || '').toLowerCase().includes(q) ||
    String(s['Nama Barang'] || '').toLowerCase().includes(q)
  );
  const rows = paginateArray('persediaan', filtered, 'pagPersediaan', 'renderMasterPersediaan');
  document.getElementById('tbodyPersediaan').innerHTML = rows.map(s => {
    const safeItem = encodeURIComponent(JSON.stringify(s));
    return `
      <tr onclick="openStokItemDetailModal(JSON.parse(decodeURIComponent('${safeItem}')))"
        class="cursor-pointer hover:bg-teal-50/60 dark:hover:bg-slate-800/70 transition">
        <td class="py-3 px-3 font-mono text-xs text-slate-400">${escapeHtml(s['Kode Barang'] || '-')}</td>
        <td class="py-3 px-3 font-bold text-teal-700 dark:text-teal-300 underline decoration-dotted underline-offset-4">${escapeHtml(s['Nama Barang'])}</td>
        <td class="py-3 px-3 text-slate-400">${escapeHtml(s.Unit || '-')}</td>
        <td class="py-3 px-3 text-right">${escapeHtml(String(s['Stok Awal']))}</td>
        <td class="py-3 px-3 text-right text-emerald-600 font-bold">+${escapeHtml(String(s['Barang Masuk']))}</td>
        <td class="py-3 px-3 text-right text-amber-600 font-bold">-${escapeHtml(String(s['Barang Keluar']))}</td>
        <td class="py-3 px-3 text-right font-extrabold">${escapeHtml(String(s['Stok Akhir']))}</td>
        <td class="py-3 px-3 text-right">
          <span class="px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-[11px] font-bold text-slate-600 dark:text-slate-300">Detail Mutasi</span>
        </td>
      </tr>
    `;
  }).join('') || `<tr><td colspan="8" class="py-8 text-center text-xs text-slate-400">Belum ada data persediaan.</td></tr>`;
}

function openStokItemDetailModal(itemObj) {
  CURRENT_STOK_ITEM = itemObj;
  document.getElementById('detailStokKode').textContent = itemObj['Kode Barang'] || 'PERSEDIAAN';
  document.getElementById('detailStokNama').textContent = itemObj['Nama Barang'] || 'Detail Persediaan';
  document.getElementById('detailStokSummary').textContent =
    `Stok Awal: ${itemObj['Stok Awal']} ${itemObj.Unit || ''}  •  Masuk: +${itemObj['Barang Masuk']}  •  Keluar: -${itemObj['Barang Keluar']}  •  Stok Akhir: ${itemObj['Stok Akhir']} ${itemObj.Unit || ''}`;

  renderStokItemDetailRows();
  const m = document.getElementById('stokItemDetailModal');
  m.classList.remove('hidden');
  m.classList.add('flex');
}

function closeStokItemDetailModal() {
  CURRENT_STOK_ITEM = null;
  const m = document.getElementById('stokItemDetailModal');
  m.classList.add('hidden');
  m.classList.remove('flex');
}

function renderStokItemDetailRows() {
  if (!CURRENT_STOK_ITEM) return;
  const targetName = String(CURRENT_STOK_ITEM['Nama Barang'] || '').trim().toLowerCase();
  const editable = canUpdate('master_persediaan');
  const deletable = canFull('master_persediaan');

  const txList = (DATA.stock_details || []).filter(tx =>
    String(tx['Nama Barang'] || '').trim().toLowerCase() === targetName
  );

  const tbody = document.getElementById('tbodyStokItemDetails');
  tbody.innerHTML = txList.map(tx => {
    const isMasuk = String(tx['Jenis'] || '').toLowerCase() !== 'keluar';
    const safeTx = encodeURIComponent(JSON.stringify(tx));
    return `
      <tr class="hover:bg-slate-100/70 dark:hover:bg-slate-800/50 transition">
        <td class="py-2.5 px-3 font-mono text-slate-400">${escapeHtml(tx['ID Transaksi'] || '-')}</td>
        <td class="py-2.5 px-3 whitespace-nowrap font-semibold">${escapeHtml(tx.Tanggal || '-')}</td>
        <td class="py-2.5 px-3">
          <span class="px-2 py-0.5 rounded-full text-[10px] font-extrabold ${isMasuk ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'}">
            ${isMasuk ? 'Masuk' : 'Keluar'}
          </span>
        </td>
        <td class="py-2.5 px-3 text-right font-extrabold ${isMasuk ? 'text-emerald-600' : 'text-amber-600'}">
          ${isMasuk ? '+' : '-'}${escapeHtml(String(tx.Jumlah || tx.Pcs || 0))}
        </td>
        <td class="py-2.5 px-3 text-slate-400">${escapeHtml(tx.Unit || '-')}</td>
        <td class="py-2.5 px-3">${escapeHtml(tx.Bidang || '-')}</td>
        <td class="py-2.5 px-3 font-semibold">${escapeHtml(tx['Penanggung Jawab'] || '-')}</td>
        <td class="py-2.5 px-3 text-slate-400">${escapeHtml(tx.Keterangan || '-')}</td>
        <td class="py-2.5 px-3 text-right whitespace-nowrap space-x-1">
          ${editable && tx._row_num ? `<button onclick="openStokTransaksiModal(JSON.parse(decodeURIComponent('${safeTx}')))" class="px-2 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 font-bold">Edit</button>` : ''}
          ${deletable && tx._row_num ? `<button onclick="deleteStokDetailRow(${tx._row_num}, '${escapeHtml(tx['ID Transaksi'] || 'transaksi ini')}')" class="px-2 py-1 rounded-lg bg-rose-50 text-rose-600 hover:bg-rose-100 font-bold">Hapus</button>` : ''}
        </td>
      </tr>
    `;
  }).join('') || `<tr><td colspan="9" class="py-8 text-center text-xs text-slate-400">Belum ada riwayat transaksi untuk barang ini.</td></tr>`;
}

function openStokTransaksiForCurrentItem() {
  openStokTransaksiModal(null, CURRENT_STOK_ITEM ? CURRENT_STOK_ITEM['Nama Barang'] : null);
}

function openStokTransaksiModal(existingTx = null, presetItemName = null) {
  const sel = document.getElementById('stokTrxBarangSelect');
  const items = DATA.stock_master || [];
  sel.innerHTML = items.map(it =>
    `<option value="${escapeHtml(it['Nama Barang'])}" data-kode="${escapeHtml(it['Kode Barang'] || '')}" data-unit="${escapeHtml(it.Unit || 'Pcs')}">${escapeHtml(it['Kode Barang'] || '-')} — ${escapeHtml(it['Nama Barang'])}</option>`
  ).join('');

  document.getElementById('stokTrxModalTitle').textContent = existingTx ? 'Edit Transaksi Persediaan' : 'Catat Transaksi Persediaan';
  document.getElementById('stokTrxRowNum').value = existingTx?._row_num || '';
  document.getElementById('stokTrxId').value = existingTx?.['ID Transaksi'] || '';
  document.getElementById('stokTrxTanggal').value = existingTx?.Tanggal || new Date().toISOString().slice(0, 10);
  document.getElementById('stokTrxJenis').value = existingTx?.['Jenis'] || 'Masuk';

  if (existingTx?.['Nama Barang']) {
    sel.value = existingTx['Nama Barang'];
  } else if (presetItemName) {
    sel.value = presetItemName;
  }

  document.getElementById('stokTrxJumlah').value = existingTx?.Jumlah || '';
  document.getElementById('stokTrxUnit').value = existingTx?.Unit || sel.selectedOptions[0]?.dataset?.unit || 'Pcs';
  document.getElementById('stokTrxPcs').value = existingTx?.Pcs || existingTx?.Jumlah || '';
  document.getElementById('stokTrxBidang').value = existingTx?.Bidang || '';
  document.getElementById('stokTrxPic').value = existingTx?.['Penanggung Jawab'] || '';
  document.getElementById('stokTrxKet').value = existingTx?.Keterangan || '';

  const m = document.getElementById('stokTransaksiModal');
  m.classList.remove('hidden');
  m.classList.add('flex');
}

function closeStokTransaksiModal() {
  const m = document.getElementById('stokTransaksiModal');
  m.classList.add('hidden');
  m.classList.remove('flex');
}

function syncStokTrxItemMeta() {
  const sel = document.getElementById('stokTrxBarangSelect');
  const unit = sel?.selectedOptions[0]?.dataset?.unit;
  if (unit) document.getElementById('stokTrxUnit').value = unit;
}

async function submitStokTransaksi(e) {
  e.preventDefault();
  const rowNum = document.getElementById('stokTrxRowNum').value;
  const sel = document.getElementById('stokTrxBarangSelect');
  const kodeBarang = sel?.selectedOptions[0]?.dataset?.kode || '';
  const namaBarang = sel?.value || '';

  const payload = {
    'ID Transaksi': document.getElementById('stokTrxId').value,
    'Tanggal': document.getElementById('stokTrxTanggal').value,
    'Jenis': document.getElementById('stokTrxJenis').value,
    'Kode Barang': kodeBarang,
    'Nama Barang': namaBarang,
    'Jumlah': document.getElementById('stokTrxJumlah').value,
    'Unit': document.getElementById('stokTrxUnit').value,
    'Pcs': document.getElementById('stokTrxPcs').value,
    'Bidang': document.getElementById('stokTrxBidang').value,
    'Penanggung Jawab': document.getElementById('stokTrxPic').value,
    'Keterangan': document.getElementById('stokTrxKet').value,
  };

  const url = rowNum ? '/api/stok-detail/update' : '/api/add/DB_Stok_Detail';
  const body = rowNum ? { row_num: rowNum, updates: payload } : payload;

  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  const out = await res.json();
  showToast(out.message, out.ok ? 'success' : 'error');
  if (out.ok) {
    closeStokTransaksiModal();
    await loadDashboard();
    if (CURRENT_STOK_ITEM) {
      const refreshed = (DATA.stock_master || []).find(s => s['Nama Barang'] === CURRENT_STOK_ITEM['Nama Barang']);
      if (refreshed) openStokItemDetailModal(refreshed);
    }
  }
}

async function deleteStokDetailRow(rowNum, label) {
  if (!confirm(`Hapus transaksi ${label}?`)) return;
  const res = await fetch('/api/delete/DB_Stok_Detail', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ row_num: rowNum })
  });
  const out = await res.json();
  showToast(out.message, out.ok ? 'success' : 'error');
  if (out.ok) {
    await loadDashboard();
    if (CURRENT_STOK_ITEM) {
      const refreshed = (DATA.stock_master || []).find(s => s['Nama Barang'] === CURRENT_STOK_ITEM['Nama Barang']);
      if (refreshed) openStokItemDetailModal(refreshed);
    }
  }
}

function renderMasterRuangan() {
  const q = (document.getElementById('searchRuangan')?.value || '').toLowerCase();
  const editable = canUpdate('master_ruangan');
  const deletable = canFull('master_ruangan');
  const employeesByNip = new Map((DATA.employees || []).map(e => [
    String(e.NIP || '').replace(/\D/g, ''), e
  ]).filter(([nip]) => nip));
  const filtered = (DATA.rooms || []).filter(r => Object.values(r).some(v => String(v).toLowerCase().includes(q)));
  const rows = paginateArray('ruangan', filtered, 'pagRuangan', 'renderMasterRuangan');

  document.getElementById('tbodyRuangan').innerHTML = rows.map(r => {
    const rawPjNip = r['NIP Penanggung Jawab'] || r.pj_nip || '';
    const nipClean = String(rawPjNip).replace(/\D/g, '');
    const emp = employeesByNip.get(nipClean);
    const rowNum = r._row_num ?? r.row_num ?? ((DATA.rooms || []).indexOf(r) + 2);
    const safeRoom = encodeURIComponent(JSON.stringify(r));
    const roomCode = String(r['Nomor Ruangan'] || '').trim();
    return `
      <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
        <td class="py-3 px-3"><span class="px-2.5 py-0.5 rounded-lg bg-slate-900 dark:bg-slate-700 text-white text-xs font-semibold">${roomCode}</span></td>
        <td class="py-3 px-3">${roomCode
          ? `<span onclick="openRoomAssetsModal(this)" data-room-code="${escapeHtml(roomCode)}" data-room-name="${escapeHtml(r['Nama Ruangan'] || '')}" class="font-bold text-indigo-600 dark:text-indigo-400 hover:underline cursor-pointer transition">${escapeHtml(r['Nama Ruangan'] || '')}</span>`
          : `<span class="ont-bold text-indigo-600 dark:text-indigo-400">${escapeHtml(r['Nama Ruangan'] || '-')}</span>`}</td>
        <td class="py-3 px-3 text-xs font-semibold">${escapeHtml(r.Lokasi || '-')}</td>
        <td class="py-3 px-3 font-mono text-xs text-slate-500">${escapeHtml(rawPjNip || '-')}</td>
        <td class="py-3 px-3 font-bold text-teal-700 dark:text-teal-300">${escapeHtml(emp?.['Nama Pegawai'] || r.pj_nama || '-')}</td>
        <td class="py-3 px-3 text-xs font-semibold">${escapeHtml(emp?.Jabatan || emp?.Posisi || r.pj_jabatan || '-')}</td>
        <td class="py-3 px-3 text-right">
          ${editable && rowNum > 1 ? `<button type="button" title="Edit ruangan" aria-label="Edit ruangan" onclick="openRoomModal(JSON.parse(decodeURIComponent('${safeRoom}')))" class="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-100 hover:bg-slate-200 dark:hover:bg-teal-700 transition">${icon('edit')}</button>` : ''}
          ${deletable && rowNum > 1 ? `<button type="button" title="Hapus ruangan" aria-label="Hapus ruangan" onclick="deleteRecord('DB_Ruangan', ${rowNum}, '${(r['Nama Ruangan'] || '').replace(/'/g, '')}')" class="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-rose-50 dark:bg-rose-900/70 text-rose-600 dark:text-rose-200 hover:bg-rose-100 dark:hover:bg-rose-800 transition">${icon('delete')}</button>` : ''}
        </td>
      </tr>
    `;
  }).join('');
}

let ACTIVE_ROOM_ASSETS_CODE = '';

function renderRoomAssetsModal() {
  const roomCode = ACTIVE_ROOM_ASSETS_CODE;
  if (!roomCode) return;

  const assets = (DATA.assets || []).filter(asset =>
    String(asset['Kode Ruang'] || '').trim() === roomCode
  );
  const rows = paginateArray(`room_assets_${roomCode}`, assets, 'pagRoomAssets', 'renderRoomAssetsModal');

  document.getElementById('tbodyRoomAssets').innerHTML = rows.map(asset => `
    <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
      <td class="py-3 px-3"><span class="px-2.5 py-0.5 rounded-lg bg-slate-900 dark:bg-slate-700 text-white text-xs font-semibold">${escapeHtml(asset['Kode Barang'] || '-')}</span></td>
      <td class="py-3 px-3 font-semibold text-indigo-600 dark:text-indigo-400">${escapeHtml(asset['Nama Barang'] || '-')}</td>
      <td class="py-3 px-3 text-xs">${escapeHtml(asset['Merk Model'] || '-')}</td>
      <td class="py-3 px-3 text-xs">${escapeHtml(asset.Tipe || '-')}</td>
      <td class="py-3 px-3">${escapeHtml(asset.Tahun || '-')}</td>
      <td class="py-3 px-3 font-bold">${escapeHtml(asset.NUP || '-')}</td>
      <td class="py-3 px-3 font-bold ${String(asset.Kondisi).toLowerCase() === 'baik' ? 'text-emerald-600' : 'text-rose-500'}">${escapeHtml(asset.Kondisi || '-')}</td>
      <td class="py-3 px-3 text-amber-600">${escapeHtml(asset['Tindak Lanjut'] || '-')}</td>
    </tr>
  `).join('') || '<tr><td colspan="8" class="py-8 text-center text-xs text-slate-400">Belum ada aset untuk ruangan ini.</td></tr>';
}

function openRoomAssetsModal(button) {
  const modal = document.getElementById('roomAssetsModal');
  const roomCode = String(button?.dataset.roomCode || '').trim();
  if (!modal || !roomCode) return;

  document.getElementById('roomAssetsModalTitle').textContent = button.dataset.roomName || 'Aset Ruangan';
  document.getElementById('roomAssetsModalCode').innerHTML = `Ruangan: <span class="px-2.5 py-0.5 rounded-lg bg-teal-900 dark:bg-teal-700 text-white text-xs font-semibold">${escapeHtml(roomCode)}</span>`;
  const notice = document.getElementById('roomAssetsNotice');
  const tableContainer = document.getElementById('roomAssetsTableContainer');

  if (!canView('master_barang')) {
    notice.textContent = 'Anda tidak memiliki akses untuk melihat data aset.';
    notice.classList.remove('hidden');
    tableContainer.classList.add('hidden');
  } else {
    notice.classList.add('hidden');
    tableContainer.classList.remove('hidden');

    let pagination = document.getElementById('pagRoomAssets');
    if (!pagination) {
      pagination = document.createElement('div');
      pagination.id = 'pagRoomAssets';
      pagination.className = 'pt-3';
      tableContainer.appendChild(pagination);
    }

    ACTIVE_ROOM_ASSETS_CODE = roomCode;
    PAGE_STATE[`room_assets_${roomCode}`] = PAGE_STATE[`room_assets_${roomCode}`] || { page: 1, size: DEFAULT_PAGE_SIZE };
    renderRoomAssetsModal();
  }

  modal.classList.remove('hidden');
  modal.classList.add('flex');
}

function closeRoomAssetsModal() {
  const modal = document.getElementById('roomAssetsModal');
  modal?.classList.add('hidden');
  modal?.classList.remove('flex');
}

function renderManageUsers() {
  const rows = paginateArray('users', DATA.users_list || [], 'pagUsers', 'renderManageUsers');
  document.getElementById('tbodyUsers').innerHTML = rows.map(u => `
    <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
      <td class="py-3 px-3 font-mono text-xs font-bold">${u.NIP}</td>
      <td class="py-3 px-3 font-extrabold">${u.Nama}</td>
      <td class="py-3 px-3 text-xs text-slate-500">${u.Posisi}</td>
      <td class="py-3 px-3">
        <div class="flex flex-wrap gap-1">
          ${(u.roles_list || []).map(r => `<span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-teal-50 dark:bg-teal-950 text-teal-700 dark:text-teal-300">${r}</span>`).join('')}
        </div>
      </td>
      <td class="py-3 px-3 text-right">
        <button type="button" title="Edit role dan password" aria-label="Edit role dan password" onclick='openUserModal(${JSON.stringify(u)})' class="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-100 hover:bg-slate-200 dark:hover:bg-teal-700 transition">${icon('edit')}</button>
      </td>
    </tr>
  `).join('');
}

function openUserModal(existingUser = null) {
  document.getElementById('usrNip').value = existingUser ? existingUser.nip_clean : '';
  document.getElementById('usrPassword').value = '';
  const activeRoles = existingUser ? (existingUser.roles_list || []) : [];
  document.getElementById('roleCheckboxes').innerHTML = (DATA.all_roles || []).map(r => `
    <label class="flex items-center gap-2 text-xs font-semibold cursor-pointer">
      <input type="checkbox" name="roleChk" value="${r}" ${activeRoles.includes(r) ? 'checked' : ''} class="rounded text-teal-600" />
      <span>${r}</span>
    </label>
  `).join('');
  const m = document.getElementById('userModal'); m.classList.remove('hidden'); m.classList.add('flex');
}
function closeUserModal() { const m = document.getElementById('userModal'); m.classList.add('hidden'); m.classList.remove('flex'); }
async function submitUserForm(e) {
  e.preventDefault();
  const nip = document.getElementById('usrNip').value;
  const password = document.getElementById('usrPassword').value;
  const roles = Array.from(document.querySelectorAll('input[name="roleChk"]:checked')).map(c => c.value);
  const out = await processWithLoading(async () => {
    const res = await fetch('/api/admin/users', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ nip, password, roles }) });
    const out = await res.json();
    if (out.ok) { closeUserModal(); await loadDashboard(); }
    return out;
  }, 'Gagal menyimpan pengguna');
  if (out) showToast(out.message, out.ok ? 'success' : 'error');
}

function renderManageModules() {
  const roles = (DATA.all_roles || []).filter(r => r !== 'Admin');
  const modules = (DATA.all_modules || []).filter(m => !['manage_users', 'manage_modules'].includes(m.key));
  const matrix = DATA.role_matrix || {};

  document.getElementById('matrixHeaderRow').innerHTML =
    `<th class="py-3 px-3 sticky left-0 bg-slate-50 dark:bg-slate-800">Role</th>` +
    modules.map(m => `<th class="py-3 px-2 whitespace-nowrap">${m.label}</th>`).join('');

  document.getElementById('matrixBodyRows').innerHTML = roles.map(role => `
    <tr class="hover:bg-slate-200/50 dark:hover:bg-slate-800/40 transition">
      <td class="py-2.5 px-3 font-extrabold whitespace-nowrap sticky left-0 bg-white dark:bg-[#111827]">${role}</td>
      ${modules.map(m => {
        const cur = (matrix[role] || {})[m.key] || 'none';
        return `
          <td class="py-2 px-2">
            <select onchange="updateRoleModule('${role}', '${m.key}', this.value)"
              class="text-[11px] font-bold px-2 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-200 transition">
              <option value="none" ${cur === 'none' ? 'selected' : ''}>None</option>
              <option value="view" ${cur === 'view' ? 'selected' : ''}>View</option>
              <option value="update" ${cur === 'update' ? 'selected' : ''}>Update</option>
              <option value="full" ${cur === 'full' ? 'selected' : ''}>Full</option>
            </select>
          </td>
        `;
      }).join('')}
    </tr>
  `).join('');
}

async function updateRoleModule(role, module_key, level) {
  const out = await processWithLoading(async () => {
    const res = await fetch('/api/admin/role-modules', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ role, module_key, level }) });
    return await res.json();
  }, 'Gagal memperbarui hak akses');
  if (out) showToast(out.message, out.ok ? 'success' : 'error');
}

function openDialogEdit(rowObj) {
  document.getElementById('editDialogRowNum').value = rowObj._row_num;
  document.getElementById('editDialogTopik').value = rowObj.Topik || '';
  document.getElementById('editDialogNarasumber').value = rowObj.Narasumber || '';
  document.getElementById('editDialogKehadiran').value = rowObj.Kehadiran || '';
  document.getElementById('editDialogStatus').value = rowObj.Keterlaksanaan || '';
  document.getElementById('editDialogFlyer').value = rowObj.Flyer || '';
  document.getElementById('editDialogBestcut').value = rowObj.Bestcut || '';
  const m = document.getElementById('dialogEditModal'); m.classList.remove('hidden'); m.classList.add('flex');
}
function closeDialogEditModal() { const m = document.getElementById('dialogEditModal'); m.classList.add('hidden'); m.classList.remove('flex'); }
async function submitDialogUpdate(e) {
  e.preventDefault();
  const row_num = document.getElementById('editDialogRowNum').value;
  const updates = {
    'Topik': document.getElementById('editDialogTopik').value,
    'Narasumber': document.getElementById('editDialogNarasumber').value,
    'Kehadiran': document.getElementById('editDialogKehadiran').value,
    'Keterlaksanaan': document.getElementById('editDialogStatus').value,
    'Flyer': document.getElementById('editDialogFlyer').value,
    'Bestcut': document.getElementById('editDialogBestcut').value,
  };
  const out = await processWithLoading(async () => {
    const res = await fetch('/api/dialog/update', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ row_num, updates }) });
    const out = await res.json();
    if (out.ok) { closeDialogEditModal(); await loadDashboard(); }
    return out;
  }, 'Gagal memperbarui dialog');
  if (out) showToast(out.message, out.ok ? 'success' : 'error');
}

const SCHEMAS = {
  DB_Info_Board: { title: 'Posting Info Board', fields: ['Tanggal', 'Prioritas', 'Judul', 'Isi', 'Target Divisi', 'Lampiran'] },
  DB_Pegawai: { title: 'Tambah Data Pegawai', fields: ['Nama Pegawai', 'NIP', 'Pangkat Golongan', 'Jabatan', 'Status', 'Posisi'] },
  DB_Arsip_Program: { title: 'Tambah Arsip Program & Perencanaan', fields: ['Kategori', 'Jenis', 'Tanggal Upload', 'Nama Dokumen', 'Keterangan', 'Link'] },
  DB_SDM_Arsip: { title: 'Tambah Arsip SDM', fields: ['Nomor Dokumen', 'Nama Dokumen', 'Tanggal', 'Jenis', 'Link'] },
  DB_Arsip_SDM: { title: 'Tambah Arsip SDM', fields: ['Nomor Dokumen', 'Nama Dokumen', 'Tanggal', 'Jenis', 'Link'] },
  DB_Dialog: { title: 'Tambah Agenda Dialog', fields: ['Tanggal Surat', 'Tanggal Dialog', 'Program', 'Topik', 'Narasumber', 'Instansi', 'Kehadiran', 'PIC Narasumber', 'Operator', 'Penyiar', 'Flyer', 'Bestcut', 'Link Live', 'Status', 'Catatan'] },
  DB_Flyer: { title: 'Tambah Flyer Dialog', fields: ['ID Dialog', 'Nama File', 'Link Flyer'] },
  DB_Jadwal_Operasional: { title: 'Tambah Jadwal Penyiar / TMB', fields: ['Tanggal', 'Shift', 'Bidang', 'Pegawai', 'Status'] },
  DB_Program: { title: 'Tambah Program Siaran', fields: ['Kode Program', 'Programa', 'Nama Program', 'Hari', 'Jam', 'Kategori', 'Status'] },
  DB_Konten: { title: 'Tambah Konten (Planner)', fields: ['Tanggal Tayang', 'Platform', 'Akun', 'Judul Konten', 'Jenis', 'Keterangan', 'PIC', 'Status', 'Link Asset', 'Catatan'] },
  DB_Aset: { title: 'Tambah Barang', fields: ['Kode Barang', 'Kode Ruang', 'Tipe', 'Nama Barang', 'Merk Model', 'Tahun', 'NUP', 'Kondisi', 'Tindak Lanjut', 'Keterangan'] },
  DB_Ruangan: { title: 'Tambah Daftar Barang Ruangan', fields: ['Nomor Ruangan', 'Nama Ruangan', 'Lokasi', 'NIP Penanggung Jawab', 'Nama', 'Jabatan'] },
  DB_Stok_Master: { title: 'Tambah Master Persediaan', fields: ['Kode Barang', 'Nama Barang', 'Unit', 'Stok Awal', 'Keterangan'] },
  DB_Stok_Masuk: { title: 'Catat Persediaan Masuk', fields: ['Tanggal', 'Penanggung Jawab', 'Nama Barang', 'Jumlah Masuk', 'Unit', 'Pcs', 'Keterangan'] },
  DB_Stok_Keluar: { title: 'Catat Persediaan Keluar', fields: ['Tanggal', 'Nama Barang', 'Bidang', 'Penerima Barang', 'Jumlah Keluar', 'Unit', 'Pcs', 'Keterangan'] },
  DB_Produksi_Paket: { title: 'Tambah Produksi Paket', fields: ['Tanggal', 'Program', 'Judul Paket', 'Jenis Paket', 'Produser', 'Reporter', 'Editor', 'Status', 'Link File'] },
  DB_Socmed_Analytics: { title: 'Input Laporan Analitik', fields: ['Periode', 'Platform', 'Akun', 'Followers', 'Reach', 'Engagement', 'Top Konten', 'Catatan'] },
  DB_TMB_Working_Progress: { title: 'Tambah Produksi', fields: ['Judul', 'Jenis', 'Tanggal Record', 'Record', 'Editing', 'PIC TMB', 'PIC Penyiaran', 'Progress', 'Deadline', 'Kendala', 'Link', 'Status'] },
  DB_Pemeliharaan_Header: { title: 'Tambah Jadwal Pemeliharaan Aset', fields: ['Tanggal', 'Judul Pemeliharaan', 'Lokasi', 'Teknisi Vendor', 'Status', 'Keterangan'] },
  DB_Pemeliharaan_Detail: { title: 'Tambah Detail Aset Dipelihara', fields: ['ID Jadwal', 'Kode Barang', 'Nama Barang', 'NUP', 'Kondisi Sebelum', 'Tindakan', 'Kondisi Sesudah', 'Biaya'] },
  DB_BMN_Arsip: { title: 'Tambah Arsip BMN (Surat & Nodin)', fields: ['Nomor Dokumen', 'Jenis', 'Judul Dokumen', 'Tanggal', 'Keterangan', 'Link'] },
  DB_BMN_Dokumen: { title: 'Upload Dokumen Pelaporan BMN', fields: ['Group', 'Sub Menu', 'Periode', 'Kategori Item', 'Judul Dokumen', 'Tanggal Buat', 'Link File', 'Keterangan'] },
};

function dateValueForInput(value) {
  const text = String(value || '').trim();
  if (/^\d{4}-\d{2}-\d{2}$/.test(text)) return text;
  const parts = text.match(/^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$/);
  if (!parts) return '';
  let month = Number(parts[1]);
  let day = Number(parts[2]);
  const year = Number(parts[3]);
  if (month > 12) [day, month] = [month, day];
  const parsed = new Date(Date.UTC(year, month - 1, day));
  if (parsed.getUTCFullYear() !== year || parsed.getUTCMonth() !== month - 1 || parsed.getUTCDate() !== day) return '';
  return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}

function openTimelineModal(item = null) {
  TIMELINE_EDIT_ROW = item;
  document.getElementById('timelineModalTitle').textContent = item ? 'Edit Kegiatan' : 'Tambah Kegiatan';
  document.getElementById('timelineActivity').value = item?.Kegiatan || '';
  document.getElementById('timelinePhase').value = item?.Tahapan || '';
  document.getElementById('timelineStartDate').value = dateValueForInput(item?.['Tanggal Mulai'] || item?.['Start Date'] || '');
  document.getElementById('timelineEndDate').value = dateValueForInput(item?.['Tanggal Selesai'] || item?.['End Date'] || '');
  document.getElementById('timelineDescription').value = item?.Keterangan || '';
  const modal = document.getElementById('timelineModal');
  modal.classList.remove('hidden');
  modal.classList.add('flex');
}

function openTimelineModalByRow(rowNum) {
  const item = (DATA.timeline || []).find(row => Number(row._row_num) === rowNum);
  if (item) openTimelineModal(item);
}

function closeTimelineModal() {
  const modal = document.getElementById('timelineModal');
  modal.classList.add('hidden');
  modal.classList.remove('flex');
  document.getElementById('timelineForm').reset();
  TIMELINE_EDIT_ROW = null;
}

async function submitTimeline(event) {
  event.preventDefault();
  const form = event.target;
  const payload = Object.fromEntries(new FormData(form).entries());
  if (payload['Tanggal Selesai'] && payload['Tanggal Selesai'] < payload['Tanggal Mulai']) {
    showToast('Tanggal selesai tidak boleh sebelum tanggal mulai.', 'error');
    return;
  }
  const editing = Boolean(TIMELINE_EDIT_ROW);
  const url = editing ? '/api/timeline/update' : '/api/add/DB_Timeline';
  const rowNum = editing ? TIMELINE_EDIT_ROW._row_num : null;
  const out = await processWithLoading(async () => {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(editing ? { row_num: rowNum, updates: payload } : payload)
    });
    const out = await res.json();
    if (out.ok) {
      closeTimelineModal();
      await loadDashboard();
    }
    return out;
  }, editing ? 'Gagal memperbarui kegiatan' : 'Gagal menyimpan kegiatan');
  if (out) showToast(out.message, out.ok ? 'success' : 'error');
}

function handleRoomNipLookup(nipInputEl) {
  const clean = String(nipInputEl.value || '').replace(/\D/g, '');
  if (!clean) return;
  const emp = (DATA.employees || []).find(e => e.nip_clean === clean);
  if (emp) {
    const form = nipInputEl.closest('form');
    const namaInput = form.querySelector('input[name="Nama"]');
    const jabInput = form.querySelector('input[name="Jabatan"]');
    if (namaInput) namaInput.value = emp['Nama Pegawai'] || '';
    if (jabInput) jabInput.value = emp.Jabatan || emp.Posisi || '';
  }
}

function openRoomModal(room = null) {
  const editing = Boolean(room);
  document.getElementById('genericModalTitle').textContent = editing ? 'Edit Ruangan' : 'Tambah Ruangan';
  const form = document.getElementById('genericAddForm');
  form.dataset.targetKey = 'DB_Ruangan';
  form.dataset.editRowNum = editing ? String(room._row_num || room.row_num || '') : '';

  const selectedNip = String(room?.['NIP Penanggung Jawab'] || room?.pj_nip || '').replace(/\D/g, '');
  const employeeOptions = (DATA.employees || []).map(employee => {
    const nip = String(employee.NIP || employee.nip_clean || '').replace(/\D/g, '');
    if (!nip) return '';
    const name = String(employee['Nama Pegawai'] || '').trim();
    const selected = nip === selectedNip ? ' selected' : '';
    return `<option value="${escapeHtml(nip)}"${selected}>${escapeHtml(nip)}${name ? ` - ${escapeHtml(name)}` : ''}</option>`;
  }).join('');

  form.innerHTML = `
    <div>
      <label class="block font-bold mb-1">Nomor Ruangan</label>
      <input type="text" name="Nomor Ruangan" value="${escapeHtml(room?.['Nomor Ruangan'] || '')}" ${editing ? 'readonly' : 'required'}
        class="w-full px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 ${editing ? 'opacity-70 cursor-not-allowed' : ''}" />
    </div>
    <div>
      <label class="block font-bold mb-1">Nama Ruangan</label>
      <input type="text" name="Nama Ruangan" value="${escapeHtml(room?.['Nama Ruangan'] || '')}" required
        class="w-full px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700" />
    </div>
    <div>
      <label class="block font-bold mb-1">Lokasi</label>
      <input type="text" name="Lokasi" value="${escapeHtml(room?.Lokasi || '')}"
        class="w-full px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700" />
    </div>
    <div>
      <label class="block font-bold mb-1">NIP Penanggung Jawab</label>
      <select name="NIP Penanggung Jawab" class="w-full px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
        <option value="">Pilih Pegawai</option>${employeeOptions}
      </select>
    </div>
    <button type="submit" class="w-full py-3 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold">${editing ? 'Simpan Perubahan' : 'Simpan Ruangan'}</button>
  `;

  const modal = document.getElementById('genericAddModal');
  modal.classList.remove('hidden');
  modal.classList.add('flex');
}

function openAssetModal(asset = null) {
  const editing = Boolean(asset);
  document.getElementById('genericModalTitle').textContent = editing ? 'Edit Barang' : 'Tambah Barang';
  const form = document.getElementById('genericAddForm');
  form.dataset.targetKey = 'DB_Aset';
  form.dataset.editRowNum = editing ? String(asset._row_num || asset.row_num || '') : '';

  const roomOptions = (DATA.rooms || []).map(room => {
    const code = String(room['Nomor Ruangan'] || '').trim();
    const name = String(room['Nama Ruangan'] || '').trim();
    if (!code) return '';
    const selected = code === String(asset?.['Kode Ruang'] || '').trim() ? ' selected' : '';
    return `<option value="${escapeHtml(code)}"${selected}>${escapeHtml(code)}${name ? ` - ${escapeHtml(name)}` : ''}</option>`;
  }).join('');
  const selectOptions = (values, selectedValue) => values.map(value =>
    `<option value="${escapeHtml(value)}"${value === String(selectedValue || '') ? ' selected' : ''}>${escapeHtml(value)}</option>`
  ).join('');

  form.innerHTML = `
    <div>
      <label class="block font-bold mb-1">Kode Barang</label>
      <input type="text" name="Kode Barang" value="${escapeHtml(asset?.['Kode Barang'] || '')}" ${editing ? 'readonly' : 'required'}
        class="w-full px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 ${editing ? 'opacity-70 cursor-not-allowed' : ''}" />
    </div>
    <div>
      <label class="block font-bold mb-1">Kode Ruang</label>
      <select name="Kode Ruang" required class="w-full px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
        <option value="">Pilih Ruangan</option>${roomOptions}
      </select>
    </div>
    <div>
      <label class="block font-bold mb-1">Tipe</label>
      <input type="text" name="Tipe" value="${escapeHtml(asset?.Tipe || '')}" class="w-full px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700" />
    </div>
    <div>
      <label class="block font-bold mb-1">Nama Barang</label>
      <input type="text" name="Nama Barang" value="${escapeHtml(asset?.['Nama Barang'] || '')}" required class="w-full px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700" />
    </div>
    <div>
      <label class="block font-bold mb-1">Merk Model</label>
      <input type="text" name="Merk Model" value="${escapeHtml(asset?.['Merk Model'] || '')}" class="w-full px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700" />
    </div>
    <div class="grid grid-cols-2 gap-2">
      <div>
        <label class="block font-bold mb-1">Tahun</label>
        <input type="number" name="Tahun" value="${escapeHtml(asset?.Tahun || '')}" min="0" step="1" class="w-full px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700" />
      </div>
      <div>
        <label class="block font-bold mb-1">NUP</label>
        <input type="number" name="NUP" value="${escapeHtml(asset?.NUP || '')}" min="0" step="1" class="w-full px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700" />
      </div>
    </div>
    <div>
      <label class="block font-bold mb-1">Kondisi</label>
      <select name="Kondisi" required class="w-full px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
        <option value="">Pilih Kondisi</option>
        ${selectOptions(['Baik', 'Rusak Ringan', 'Rusak Berat'], asset?.Kondisi)}
      </select>
    </div>
    <div>
      <label class="block font-bold mb-1">Tindak Lanjut</label>
      <select name="Tindak Lanjut" class="w-full px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
        <option value="">Pilih Tindak Lanjut</option>
        ${selectOptions(['Penggunaan', 'Penyewaan', 'Peminjaman', 'Penghapusan', 'Pemeliharaan', 'Pengadaan', 'Reklas BMN'], asset?.['Tindak Lanjut'])}
      </select>
    </div>
    <div>
      <label class="block font-bold mb-1">Keterangan</label>
      <textarea name="Keterangan" rows="2" class="w-full px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">${escapeHtml(asset?.Keterangan || '')}</textarea>
    </div>
    <button type="submit" class="w-full py-3 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold">${editing ? 'Simpan Perubahan' : 'Simpan Barang'}</button>
  `;

  const modal = document.getElementById('genericAddModal');
  modal.classList.remove('hidden');
  modal.classList.add('flex');
}

function openAddModal(key) {
  const s = SCHEMAS[key];
  if (!s) return;
  document.getElementById('genericModalTitle').textContent = s.title;
  const form = document.getElementById('genericAddForm');
  form.dataset.targetKey = key;
  form.innerHTML = s.fields.map(f => {
    const isRoomNip = ['NIP Penanggung Jawab', 'Pegawai', 'Record', 'Editing', 'PIC TMB', 'PIC Penyiaran', 'PIC Narasumber', 'Operator', 'Penyiar'].includes(f);
    const extraAttrs = isRoomNip
      ? 'list="pegawaiNipDatalist" oninput="handleRoomNipLookup(this)" onchange="handleRoomNipLookup(this)"'
      : '';
    return `
      <div>
        <label class="block font-bold mb-1">${f}${isRoomNip ? ' <span class="text-teal-600 font-normal">(Auto-Lookup Pegawai)</span>' : ''}</label>
        <input type="text" name="${f}" ${extraAttrs} placeholder="Isi ${f}"
          class="w-full px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700" />
      </div>
    `;
  }).join('') + `<button type="submit" class="w-full py-3 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold">Simpan</button>`;
  const m = document.getElementById('genericAddModal'); m.classList.remove('hidden'); m.classList.add('flex');
}
function closeGenericModal() {
  const m = document.getElementById('genericAddModal');
  m.classList.add('hidden');
  m.classList.remove('flex');
  const form = document.getElementById('genericAddForm');
  if (form) {
    form.reset();
    form.dataset.editRowNum = '';
  }
  selectedBmnFile = null;
  const modalPanel = document.querySelector('#genericAddModal > div');
  if (modalPanel) modalPanel.classList.replace('max-w-lg', 'max-w-md');
}

async function submitBmnDocument(event) {
  const form = event.target;
  const payload = Object.fromEntries(new FormData(form).entries());
  const source = payload.BmnSource || 'upload';
  delete payload.BmnSource;

  let linkFile = '';
  if (source === 'upload') {
    if (!selectedBmnFile) {
      showToast('Pilih atau seret file yang akan diunggah.', 'error');
      return;
    }
    const uploadData = new FormData();
    Object.entries(payload).forEach(([key, value]) => uploadData.append(key, String(value)));
    uploadData.append('file', selectedBmnFile);
    const uploadOut = await processWithLoading(async () => {
      const res = await fetch('/api/upload/bmn', { method: 'POST', body: uploadData });
      const result = await res.json();
      if (!res.ok) throw new Error(result.message || 'Gagal mengunggah dokumen.');
      if (result.ok) {
        closeGenericModal();
        await loadDashboard();
      }
      return result;
    }, 'Mengunggah dokumen ke Google Drive');
    if (!uploadOut?.ok) {
      showToast(uploadOut?.message || 'Gagal mengunggah dokumen.', 'error');
      return;
    }
    showToast(uploadOut.message, 'success');
    return;
  } else {
    linkFile = (document.getElementById('bmnDriveLink')?.value || '').trim();
    if (!/^https?:\/\/\S+/i.test(linkFile)) {
      showToast('Masukkan link Google Drive yang valid.', 'error');
      return;
    }
  }

  payload['Link File'] = linkFile;
  const out = await processWithLoading(async () => {
    const res = await fetch('/api/add/DB_BMN_Dokumen', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (result.ok) {
      closeGenericModal();
      await loadDashboard();
    }
    return result;
  }, 'Menyimpan dokumen');
  if (out) showToast(out.message, out.ok ? 'success' : 'error');
}

async function submitGenericRecord(e) {
  e.preventDefault();
  const key = e.target.dataset.targetKey;
  if (key === 'DB_BMN_Dokumen') {
    await submitBmnDocument(e);
    return;
  }
  const payload = Object.fromEntries(new FormData(e.target).entries());
  const editRowNum = e.target.dataset.editRowNum;
  if (key === 'DB_Aset' && editRowNum) delete payload['Kode Barang'];
  if (key === 'DB_Ruangan' && editRowNum) delete payload['Nomor Ruangan'];
  const out = await processWithLoading(async () => {
    const url = key === 'DB_Aset' && editRowNum
      ? '/api/assets/update'
      : key === 'DB_Ruangan' && editRowNum
        ? '/api/rooms/update'
        : `/api/add/${key}`;
    const body = (key === 'DB_Aset' || key === 'DB_Ruangan') && editRowNum
      ? { row_num: Number(editRowNum), updates: payload }
      : payload;
    const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const out = await res.json();
    if (out.ok) { closeGenericModal(); await loadDashboard(); }
    return out;
  }, 'Gagal menyimpan data');
  if (out) showToast(out.message, out.ok ? 'success' : 'error');
}

async function refreshAll() {
  const result = await processWithLoading(async () => {
    const response = await fetch('/api/refresh', { method: 'POST' });
    const result = await response.json();
    if (result.ok) await loadDashboard();
    return result;
  }, 'Gagal menyinkronkan data');
  if (result) showToast(result.message || 'Data berhasil disinkronkan', result.ok ? 'success' : 'error');
}

async function logoutUser() {
  await processWithLoading(async () => {
    const response = await fetch('/api/logout', { method: 'POST' });
    const result = await response.json();
    if (!result.ok) throw new Error(result.message || 'Logout gagal.');
    window.location.href = '/';
  }, 'Gagal keluar');
}


// =========================================================
// NEW MODULES: PRODUKSI PAKET, BESTCUT, SOCMED, TMB MON, BMN TOOLS
// =========================================================
let PAKET_VIEW = 'table';
let PAKET_CAL_MONTH = new Date(new Date().getFullYear(), new Date().getMonth(), 1);

function setPaketView(mode) {
  PAKET_VIEW = mode;
  document.getElementById('paketTableView')?.classList.toggle('hidden', mode !== 'table');
  document.getElementById('paketCalendarView')?.classList.toggle('hidden', mode !== 'calendar');
  renderProduksiPaket();
}

function changePaketMonth(delta) {
  PAKET_CAL_MONTH = new Date(PAKET_CAL_MONTH.getFullYear(), PAKET_CAL_MONTH.getMonth() + delta, 1);
  renderProduksiPaket();
}

function renderProduksiPaket() {
  const q = (document.getElementById('searchProduksiPaket')?.value || '').toLowerCase();
  const filtered = (DATA.produksi_paket || []).filter(p => Object.values(p).some(v => String(v).toLowerCase().includes(q)));

  if (PAKET_VIEW === 'calendar') {
    const year = PAKET_CAL_MONTH.getFullYear();
    const month = PAKET_CAL_MONTH.getMonth();
    const titleEl = document.getElementById('paketCalendarMonth');
    if (titleEl) titleEl.textContent = PAKET_CAL_MONTH.toLocaleDateString('id-ID', { month: 'long', year: 'numeric' });
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    let cells = '';
    for (let i = 0; i < firstDay; i++) {
      cells += `<div class="min-h-[96px] p-2 border-r border-b border-slate-200 dark:border-slate-700 bg-slate-50/40 dark:bg-slate-900/30"></div>`;
    }
    for (let d = 1; d <= daysInMonth; d++) {
      const iso = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
      const dayItems = filtered.filter(p => String(p.Tanggal || '').startsWith(iso));
      cells += `
        <div class="min-h-[96px] p-2 border-r border-b border-slate-200 dark:border-slate-700 space-y-1">
          <div class="text-[11px] font-extrabold text-slate-400">${d}</div>
          ${dayItems.map(it => `<div class="px-2 py-1 rounded-lg bg-teal-50 dark:bg-teal-950 text-teal-800 dark:text-teal-200 text-[10px] font-bold truncate" title="${escapeHtml(it['Judul Paket'])}">${escapeHtml(it.Program)}: ${escapeHtml(it['Judul Paket'])}</div>`).join('')}
        </div>`;
    }
    const grid = document.getElementById('paketCalendarGrid');
    if (grid) grid.innerHTML = cells;
    return;
  }

  const rows = paginateArray('produksi_paket', filtered, 'pagProduksiPaket', 'renderProduksiPaket');
  const tbody = document.getElementById('tbodyProduksiPaket');
  if (!tbody) return;
  tbody.innerHTML = rows.map(p => `
    <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
      <td class="py-3 px-3 font-mono text-xs text-slate-500">${escapeHtml(p.ID || '-')}</td>
      <td class="py-3 px-3 font-bold whitespace-nowrap">${escapeHtml(p.Tanggal || '-')}</td>
      <td class="py-3 px-3 font-bold text-teal-600">${escapeHtml(p.Program || '-')}</td>
      <td class="py-3 px-3 font-extrabold">${escapeHtml(p['Judul Paket'] || '-')}</td>
      <td class="py-3 px-3 text-xs">${escapeHtml(p['Jenis Paket'] || '-')}</td>
      <td class="py-3 px-3 text-xs">${escapeHtml(p.Produser || '-')}</td>
      <td class="py-3 px-3"><span class="px-2 py-0.5 rounded-full text-xs font-bold bg-sky-50 dark:bg-sky-950 text-sky-700">${escapeHtml(p.Status || '-')}</span></td>
      <td class="py-3 px-3">${p['Link File'] ? `<a href="${escapeHtml(p['Link File'])}" target="_blank" class="text-xs font-bold text-teal-600 hover:underline">Buka ↗</a>` : '-'}</td>
    </tr>
  `).join('');
}

function renderBestcutMonitoring() {
  const filter = document.getElementById('filterBestcutStatus')?.value || 'all';
  const allDialogs = DATA.dialogs || [];
  const withBestcut = allDialogs.filter(d => String(d.Bestcut || '').trim().startsWith('http'));
  if (document.getElementById('statBestcutTotal')) document.getElementById('statBestcutTotal').textContent = allDialogs.length;
  if (document.getElementById('statBestcutDone')) document.getElementById('statBestcutDone').textContent = withBestcut.length;
  if (document.getElementById('statBestcutPending')) document.getElementById('statBestcutPending').textContent = allDialogs.length - withBestcut.length;

  const filtered = allDialogs.filter(d => {
    const hasLink = String(d.Bestcut || '').trim().startsWith('http');
    if (filter === 'ready') return hasLink;
    if (filter === 'missing') return !hasLink;
    return true;
  });
  const rows = paginateArray('bestcut', filtered, 'pagBestcut', 'renderBestcutMonitoring');
  const tbody = document.getElementById('tbodyBestcut');
  if (!tbody) return;
  tbody.innerHTML = rows.map(d => {
    const hasLink = String(d.Bestcut || '').trim().startsWith('http');
    return `
      <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
        <td class="py-3 px-3 text-xs font-bold whitespace-nowrap">${escapeHtml(d.Tanggal || '-')}</td>
        <td class="py-3 px-3 text-xs font-bold text-sky-600">${escapeHtml(d.Program || '-')}</td>
        <td class="py-3 px-3 text-xs font-semibold max-w-xs">${escapeHtml(d.Topik || '-')}</td>
        <td class="py-3 px-3 text-xs">${escapeHtml(d.Narasumber || '-')}</td>
        <td class="py-3 px-3"><span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold ${hasLink ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'}">${hasLink ? 'Tersedia' : 'Belum Upload'}</span></td>
        <td class="py-3 px-3">${hasLink ? `<a href="${escapeHtml(d.Bestcut)}" target="_blank" class="text-xs font-bold text-teal-600 hover:underline">Buka Bestcut ↗</a>` : '-'}</td>
        <td class="py-3 px-3 text-right">${d._row_num ? `<button onclick='openDialogEdit(${JSON.stringify(d)})' class="text-xs font-bold px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 transition">Set Link</button>` : '-'}</td>
      </tr>`;
  }).join('');
}

function renderSocmedAnalytics() {
  const list = DATA.socmed_analytics || [];
  const cardsEl = document.getElementById('socmedCardsGrid');
  if (cardsEl) {
    cardsEl.innerHTML = list.slice(0, 4).map(s => `
      <div class="bg-white dark:bg-[#111827] rounded-3xl border border-slate-200/80 dark:border-slate-800 p-5 space-y-1">
        <div class="flex justify-between text-xs font-bold text-teal-600"><span>${escapeHtml(s.Platform)}</span><span>${escapeHtml(s.Periode)}</span></div>
        <p class="text-sm font-extrabold">${escapeHtml(s.Akun)}</p>
        <p class="text-2xl font-extrabold pt-1">${escapeHtml(s.Followers)} <span class="text-xs font-normal text-slate-400">followers</span></p>
        <p class="text-[11px] text-slate-400">Reach: ${escapeHtml(s.Reach)} • ER: ${escapeHtml(s.Engagement)}</p>
      </div>
    `).join('');
  }
  const rows = paginateArray('socmed', list, 'pagSocmed', 'renderSocmedAnalytics');
  const tbody = document.getElementById('tbodySocmed');
  if (!tbody) return;
  tbody.innerHTML = rows.map(s => `
    <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
      <td class="py-3 px-3 font-bold">${escapeHtml(s.Periode || '-')}</td>
      <td class="py-3 px-3 font-bold text-teal-600">${escapeHtml(s.Platform || '-')}</td>
      <td class="py-3 px-3 font-mono text-xs">${escapeHtml(s.Akun || '-')}</td>
      <td class="py-3 px-3 text-right font-bold">${escapeHtml(s.Followers || '0')}</td>
      <td class="py-3 px-3 text-right">${escapeHtml(s.Reach || '0')}</td>
      <td class="py-3 px-3 text-right font-bold text-emerald-600">${escapeHtml(s.Engagement || '-')}</td>
      <td class="py-3 px-3 text-xs">${escapeHtml(s['Top Konten'] || '-')}</td>
      <td class="py-3 px-3 text-xs text-slate-400">${escapeHtml(s.Catatan || '-')}</td>
    </tr>
  `).join('');
}

function renderMonitoringProduksi() {
  const rows = paginateArray('mon_prod', DATA.tmb_working_progresss || [], 'pagMonitoringProd', 'renderMonitoringProduksi');
  const tbody = document.getElementById('tbodyMonitoringProd');
  if (!tbody) return;
  tbody.innerHTML = rows.map(m =>{
    const hasLink = String(m.Link || '').trim().startsWith('http');
    return `<tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
      <td class="py-3 px-3">${escapeHtml(m.Judul || '-')}</td>
      <td class="py-3 px-3">
        <span class="px-2 py-0.5 rounded-full text-[11px] font-bold ${String(m.Jenis || 'Video').toLowerCase() === 'video' ? 'bg-teal-50 dark:bg-teal-950 text-teal-600 dark:text-teal-300' : 'bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-300'}">${m.Jenis || '-'}</span>
      </td>
      <td class="py-3 px-3 font-semibold whitespace-nowrap">${escapeHtml(m['Tanggal Record'] || '-')}</td>
      <td class="py-3 px-3 text-[11px]">${escapeHtml(m.Record || '-')}</td>
      <td class="py-3 px-3 text-[11px]">${escapeHtml(m.Editing || '-')}</td>
      <td class="py-3 px-3 text-[11px]">${escapeHtml(m['PIC TMB'] || '-')}</td>
      <td class="py-3 px-3 text-[11px]">${escapeHtml(m['PIC Penyiaran'] || '-')}</td>
      <td class="py-3 px-3 text-mono">
        <span class="px-2 py-0.5 rounded-full text-[11px] font-bold ${(m.Progress || 0) == 100 ?
           'bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-300' : 
           m.Progress || 50  >= 50 ? 'bg-amber-50 dark:bg-amber-950 text-amber-600 dark:text-amber-300' :'bg-red-50 dark:bg-red-950 text-red-600 dark:text-red-300'}">${m.Progress || 0}</span>
      </td>
      <td class="py-3 px-3 font-semibold whitespace-nowrap">${escapeHtml(m.Deadline || '-')}</td>
      <td class="py-3 px-3 whitespace-nowrap">${escapeHtml(m.Kendala || '-')}</td>
      <td class="py-3 px-3">
        ${hasLink ? `<a href="${escapeHtml(m.Link)}" target="_blank" rel="noopener" class="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-amber-100 dark:bg-amber-700 text-slate-700 dark:text-slate-100 hover:bg-amber-200 dark:hover:bg-amber-600 transition">${icon('link')}</a>` : ''}
      </td>
      <td class="py-3 px-3">
        <span class="px-2 py-0.5 rounded-full text-[11px] font-bold ${String(m.Status || 'Done').toLowerCase() === 'done' ?
           'bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-300' : 
           String(m.Status || 'Editing').toLowerCase() === 'editing' ? 'bg-amber-50 dark:bg-amber-950 text-amber-600 dark:text-amber-300' :'bg-red-50 dark:bg-red-950 text-red-600 dark:text-red-300'}">${m.Status || '-'}</span>
      </td>
    </tr>`
  }).join('');
}

let BAST_RECORDS = [];
let BAST_EDIT_ROW = null;

async function initBastSelectors() {
  await loadBastRecords();
  if (!document.getElementById('bastTanggal')?.value) {
    document.getElementById('bastTanggal').value = new Date().toISOString().slice(0, 10);
  }
}

function openBastGenerateModal(row = null) {
  if (row) fillBastForm(row, row._row_num || 0);
  if (!document.getElementById('bastNip')?.options.length || document.getElementById('bastNip')?.options.length === 1) initBastSelects();
  if (!row) {
    document.getElementById('bastRowIndex').value = '';
    BAST_EDIT_ROW = null;
    const submitButton = document.querySelector('#bastGenerateForm button[type="submit"]');
    if (submitButton) submitButton.textContent = 'Generate Dokumen & PDF';
    document.querySelector('#bastGenerateModal h3').textContent = 'Input / Generate BAST';
  }
  const modal = document.getElementById('bastGenerateModal');
  modal?.classList.remove('hidden');
  modal?.classList.add('flex');
}

function closeBastGenerateModal() {
  const modal = document.getElementById('bastGenerateModal');
  modal?.classList.add('hidden');
  modal?.classList.remove('flex');
  BAST_EDIT_ROW = null;
}

function initBastSelects(selectedNip = '', selectedAssetCode = '', selectedNup = '') {
  const nipSelect = document.getElementById('bastNip');
  const assetSelect = document.getElementById('bastNomorBarang');
  if (nipSelect) {
    nipSelect.innerHTML = '<option value="">Pilih Pegawai</option>' + (DATA.employees || []).map(emp => {
      const nip = emp.NIP || emp.nip_clean || '';
      const selected = String(nip).replace(/\D/g, '') === String(selectedNip).replace(/\D/g, '') ? ' selected' : '';
      return `<option value="${escapeHtml(nip)}"${selected}>${escapeHtml(nip)} - ${escapeHtml(emp['Nama Pegawai'] || '')}</option>`;
    }).join('');
  }
  if (assetSelect) {
    assetSelect.innerHTML = '<option value="">Pilih Barang</option>' + (DATA.assets || []).map(asset => {
      const idBarang = String(asset['ID Barang'] || '').trim();
      const code = String(asset['Kode Barang'] || '').trim();
      const nup = String(asset.NUP || '').trim();
      const optVal = idBarang || code;
      const isMatch = (idBarang && idBarang === String(selectedAssetCode).trim()) ||
                      (code && code === String(selectedAssetCode).trim() && (!selectedNup || nup === String(selectedNup).trim()));
      const selected = isMatch ? ' selected' : '';
      return `<option value="${escapeHtml(optVal)}"${selected}>${escapeHtml(code)} — ${escapeHtml(asset['Nama Barang'] || '')}${nup ? ` (NUP ${escapeHtml(nup)})` : ''}</option>`;
    }).join('');
  }
  if (selectedNup) document.getElementById('bastNup').value = selectedNup;
  syncBastEmployee();
  syncBastAsset();
  if (selectedNup) document.getElementById('bastNup').value = selectedNup;
}

function syncBastEmployee() {
  const nip = document.getElementById('bastNip')?.value || '';
  const clean = String(nip).replace(/\D/g, '');
  const emp = (DATA.employees || []).find(item => {
    const empClean = String(item.NIP || item.nip_clean || '').replace(/\D/g, '');
    return empClean === clean || (clean.length >= 15 && empClean.slice(0, 15) === clean.slice(0, 15));
  });
  if (document.getElementById('bastNama')) document.getElementById('bastNama').value = emp?.['Nama Pegawai'] || '';
  if (document.getElementById('bastPangkat')) document.getElementById('bastPangkat').value = emp?.['Pangkat Golongan'] || '';
  if (document.getElementById('bastJabatan')) document.getElementById('bastJabatan').value = emp?.Jabatan || emp?.Posisi || '';
}

function syncBastAsset() {
  const refVal = String(document.getElementById('bastNomorBarang')?.value || '').trim();
  const asset = (DATA.assets || []).find(item =>
    String(item['ID Barang'] || '').trim() === refVal ||
    String(item['Kode Barang'] || '').trim() === refVal
  );
  if (!asset) return;
  document.getElementById('bastNup').value = asset.NUP || '';
  document.getElementById('bastBarang').value = asset['Nama Barang'] || '';
  document.getElementById('bastMerk').value = asset['Merk Model'] || '';
  document.getElementById('bastTipe').value = asset.Tipe || '';
  const roomCode = String(asset['Kode Ruang'] || '').trim();
  const room = (DATA.rooms || []).find(item => String(item['Nomor Ruangan'] || '').trim() === roomCode);
  document.getElementById('bastLetak').value = room?.['Nama Ruangan'] || roomCode || '';
}

async function loadBastRecords(force = false) {
  const out = await processWithLoading(async () => {
    const res = await fetch(`/api/bast/records${force ? '?force=true' : ''}`);
    return res.json();
  }, 'Gagal memuat daftar BAST');
  if (!out?.ok) {
    if (out) showToast(out.message, 'error');
    return;
  }
  BAST_RECORDS = out.records || [];
  const tbody = document.getElementById('tbodyBast');
  if (!tbody) return;
  const rows = paginateArray('bast', BAST_RECORDS, 'pagBast', 'loadBastRecords');
  const editable = canUpdate('bast_otomatis');
  const deletable = canFull('bast_otomatis') && canFull('aset_tutup_buku');
  tbody.innerHTML = rows.map((row, index) => {
    const safeRow = encodeURIComponent(JSON.stringify(row));
    const status = String(row.Status || '').trim();
    const link = row['Link PDF'] || '';
    return `
      <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/50">
        <td class="py-2.5 px-2 font-mono font-semibold text-indigo-600 dark:text-indigo-400 whitespace-nowrap">${escapeHtml(row['Nomor BAST'] || '-')}</td>
        <td class="py-2.5 px-2 font-bold font-mono text-xs text-slate-500">${escapeHtml(row.NIP || '-')}</td>
        <td class="py-2.5 px-2 font-bold">${escapeHtml(row.Nama || '-')}</td>
        <td class="py-2.5 px-2 text-xs text-slate-500">${escapeHtml(row.Pangkat || '-')}</td>
        <td class="py-2.5 px-2 text-xs text-slate-500">${escapeHtml(row.Jabatan || '-')}</td>
        <td class="py-2.5 px-2 font-mono text-xs text-slate-500">${escapeHtml(row['Nomor Barang'] || '-')}</td>
        <td class="py-2.5 px-2 font-bold">${escapeHtml(row.NUP || '-')}</td>
        <td class="py-2.5 px-2 font-semibold text-teal-600 dark:text-teal-400">${escapeHtml(row.Barang || '-')}</td>
        <td class="py-2.5 px-2 text-xs font-semibold">${escapeHtml(row.Letak || '-')}</td>
        <td class="py-2.5 px-2">
          <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${status === 'DONE' ? 'bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-300' : 'bg-amber-50 dark:bg-amber-950 text-amber-600 dark:text-amber-300'}">${escapeHtml(status || 'PENDING')}</span>
        </td>
        <td class="py-2.5 px-2 text-right whitespace-nowrap">
          ${link ? `<a href="${escapeHtml(link)}" target="_blank" rel="noopener" class="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-amber-100 dark:bg-amber-700 text-slate-700 dark:text-slate-100 hover:bg-amber-200 dark:hover:bg-amber-600 transition">${icon('link')}</a>` : ''}
          ${editable ? `<button type="button" title="Edit BAST" onclick="fillBastForm(JSON.parse(decodeURIComponent('${safeRow}')), ${row._row_num || 0}, true)" class="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-100 hover:bg-slate-200 dark:hover:bg-teal-700 transition">${icon('edit')}</button>` : ''}
          ${deletable ? `<button type="button" title="Hapus BAST" onclick="deleteRecord('DB_BAST', ${row._row_num || 0}, 'BAST ${escapeHtml(row['Nomor BAST'] || '').replace(/'/g, '')}') " class="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-rose-50 dark:bg-rose-900/70 text-rose-600 dark:text-rose-200 hover:bg-rose-100 dark:hover:bg-rose-800 transition">${icon('delete')}</button>` : ''}
        </td>
      </tr>
    `;
  }).join('') || '<tr><td colspan="11" class="py-8 text-center text-slate-400">Belum ada data BAST.</td></tr>';
}

function fillBastForm(row, sheetRowIndex, editMode = false) {
  document.getElementById('bastRowIndex').value = sheetRowIndex;
  BAST_EDIT_ROW = editMode ? Number(sheetRowIndex || 0) : null;
  document.getElementById('bastNomor').value = row['Nomor BAST'] || '';
  document.getElementById('bastTanggal').value = new Date().toISOString().slice(0, 10);
  initBastSelects(row.NIP || '', row['Nomor Barang'] || '', row.NUP || '');
  syncBastEmployee();
  syncBastAsset();
  document.getElementById('bastNup').value = row.NUP || document.getElementById('bastNup').value;
  document.getElementById('bastNilai').value = row.Nilai || '';
  document.getElementById('bastJumlah').value = row.Jumlah || '';
  const submitButton = document.querySelector('#bastGenerateForm button[type="submit"]');
  if (submitButton) submitButton.textContent = editMode ? 'Simpan Perubahan BAST' : 'Generate Dokumen & PDF';
  document.querySelector('#bastGenerateModal h3').textContent = editMode ? 'Edit Data BAST' : 'Input / Generate BAST';
  const modal = document.getElementById('bastGenerateModal');
  modal?.classList.remove('hidden');
  modal?.classList.add('flex');
}

async function generateBastDocument(event) {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(event.target).entries());
  payload.sheet_row = Number(document.getElementById('bastRowIndex').value || 0);
  if (BAST_EDIT_ROW) {
    const updates = {
      'Nomor BAST': payload.nomor_bast,
      'NIP': payload.nip,
      'Nomor Barang': payload.nomor_barang,
      'NUP': payload.nup,
      'Nilai': payload.nilai,
      'Jumlah': payload.jumlah,
    };
    const out = await processWithLoading(async () => {
      const res = await fetch('/api/bast/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ row_num: BAST_EDIT_ROW, updates })
      });
      return res.json();
    }, 'Gagal memperbarui data BAST');
    showToast(out?.message || 'Gagal memperbarui data BAST', out?.ok ? 'success' : 'error');
    if (out?.ok) {
      closeBastGenerateModal();
      await loadBastRecords(true);
    }
    return;
  }
  const out = await processWithLoading(async () => {
    const res = await fetch('/api/bast/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return res.json();
  }, 'Gagal generate BAST');
  if (!out) return;
  showToast(out.message, out.ok ? 'success' : 'error');
  if (out.ok) {
    closeBastGenerateModal();
    await loadBastRecords(true);
  }
}

function renderPemeliharaanAset() {
  const th = document.getElementById('tbodyPemeliharaanHeader');
  const td = document.getElementById('tbodyPemeliharaanDetail');
  if (th) {
    th.innerHTML = (DATA.pemeliharaan_header || []).map(h => `
      <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
        <td class="py-2.5 px-3 font-mono font-bold text-teal-600">${escapeHtml(h['Kode Jadwal'] || h['ID Jadwal'] || '-')}</td>
        <td class="py-2.5 px-3 font-bold">${escapeHtml(h.Tanggal || '-')}</td>
        <td class="py-2.5 px-3 font-extrabold">${escapeHtml(h['Judul Pemeliharaan'] || '-')}</td>
        <td class="py-2.5 px-3">${escapeHtml(h.Lokasi || '-')}</td>
        <td class="py-2.5 px-3">${escapeHtml(h['Teknisi Vendor'] || '-')}</td>
        <td class="py-2.5 px-3"><span class="px-2 py-0.5 rounded-full font-bold bg-emerald-50 text-emerald-700">${escapeHtml(h.Status || '-')}</span></td>
      </tr>
    `).join('');
  }
  if (td) {
    td.innerHTML = (DATA.pemeliharaan_detail || []).map(d => `
      <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
        <td class="py-2.5 px-3 font-mono font-bold text-slate-500">${escapeHtml(d['Kode Detail Pemeliharaan'] || '-')}</td>
        <td class="py-2.5 px-3 font-mono font-bold text-indigo-600">${escapeHtml(d['Kode Jadwal'] || d['ID Jadwal'] || '-')}</td>
        <td class="py-2.5 px-3 font-mono">${escapeHtml(d['Nomor Kode Barang'] || d['Kode Barang'] || '-')}</td>
        <td class="py-2.5 px-3 font-bold">${escapeHtml(d['Nama Barang'] || '-')}</td>
        <td class="py-2.5 px-3">${escapeHtml(d.NUP || '-')}</td>
        <td class="py-2.5 px-3">${escapeHtml(d['Kondisi Sebelum'] || '-')}</td>
        <td class="py-2.5 px-3">${escapeHtml(d.Tindakan || '-')}</td>
        <td class="py-2.5 px-3 font-bold text-emerald-600">${escapeHtml(d['Kondisi Sesudah'] || '-')}</td>
        <td class="py-2.5 px-3 text-right">${escapeHtml(d.Biaya || '0')}</td>
      </tr>
    `).join('');
  }
}

// function renderBmnArsip() {
//   const rows = paginateArray('bmn_arsip', DATA.bmn_arsip || [], 'pagBmnArsip', 'renderBmnArsip');
//   const tbody = document.getElementById('tbodyBmnArsip');
//   if (!tbody) return;
//   tbody.innerHTML = rows.map(a => `
//     <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
//       <td class="py-3 px-3 font-mono text-xs font-bold">${escapeHtml(a['Nomor Dokumen'] || '-')}</td>
//       <td class="py-3 px-3"><span class="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-xs font-bold">${escapeHtml(a.Jenis || '-')}</span></td>
//       <td class="py-3 px-3 font-bold">${escapeHtml(a['Judul Dokumen'] || '-')}</td>
//       <td class="py-3 px-3 text-xs font-semibold whitespace-nowrap">${escapeHtml(a.Tanggal || '-')}</td>
//       <td class="py-3 px-3 text-xs text-slate-400">${escapeHtml(a.Keterangan || '-')}</td>
//       <td class="py-3 px-3">${a.Link ? `<a href="${escapeHtml(a.Link)}" target="_blank" class="text-xs font-bold text-teal-600 hover:underline">Buka ↗</a>` : '-'}</td>
//     </tr>
//   `).join('');
// }

function openBmnDokModal(groupName, subMenuName = '', categoryOptions = []) {
  const form = document.getElementById('genericAddForm');
  if (!form) return;
  selectedBmnFile = null;
  form.dataset.targetKey = 'DB_BMN_Dokumen';
  form.dataset.editRowNum = '';

  const periodPlaceholder = subMenuName === 'CALBMN' || subMenuName === 'WASDAL'
    ? 'Contoh: Semester I 2026'
    : subMenuName === 'Tutup Buku'
      ? 'Contoh: November 2026'
      : 'Contoh: 2026';
  const isArsip = subMenuName === 'Arsip';
  const categorySelect = categoryOptions.map(option =>
    `<option value="${escapeHtml(option)}">${escapeHtml(option)}</option>`
  ).join('');

  form.innerHTML = `
    <input type="hidden" name="Group" value="${escapeHtml(groupName)}" />
    <input type="hidden" name="Sub Menu" value="${escapeHtml(subMenuName)}" />

    <div>
      <label class="block font-bold mb-1">Periode</label>
      <input type="text" name="Periode" placeholder="${periodPlaceholder}"
        class="w-full px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700" />
    </div>
    ${ isArsip ? `
      <div>
      <label class="block font-bold mb-1">Nomor Dokumen</label>
      <input type="text" name="Keterangan" required placeholder="Nomor dokumen"
        class="w-full px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700" />
      </div>` : ''
    }
    <div>
      <label class="block font-bold mb-1">${ isArsip ? 'Jenis Dokumen' : 'Kategori Item' }</label>
      <select name="Kategori Item" class="w-full px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
        ${categorySelect}
      </select>
    </div>
    <div>
      <label class="block font-bold mb-1">Judul Dokumen</label>
      <input type="text" name="Judul Dokumen" required placeholder="Judul dokumen"
        class="w-full px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700" />
    </div>
    <div>
      <label class="block font-bold mb-1">Tanggal</label>
      <input type="date" name="Tanggal Buat" required
        class="w-full px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700" />
    </div>

    <fieldset>
      <legend class="block font-bold mb-2">Sumber File</legend>
      <div class="grid grid-cols-2 gap-2">
        <label class="cursor-pointer">
          <input type="radio" name="BmnSource" value="upload" checked class="peer sr-only" onchange="toggleBmnFileSource(this.value)" />
          <span class="block text-center px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 peer-checked:border-teal-600 peer-checked:bg-teal-50 peer-checked:text-teal-700 dark:peer-checked:bg-teal-900/30 dark:peer-checked:text-teal-300">Upload File</span>
        </label>
        <label class="cursor-pointer">
          <input type="radio" name="BmnSource" value="drive" class="peer sr-only" onchange="toggleBmnFileSource(this.value)" />
          <span class="block text-center px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 peer-checked:border-teal-600 peer-checked:bg-teal-50 peer-checked:text-teal-700 dark:peer-checked:bg-teal-900/30 dark:peer-checked:text-teal-300">Link Google Drive</span>
        </label>
      </div>
    </fieldset>

    <div id="bmnUploadSource">
      <label id="bmnDropZone" for="bmnFileInput"
        class="flex min-h-28 cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/60 px-4 py-5 text-center hover:border-teal-500 transition">
        <i class="ti ti-cloud-upload text-2xl text-teal-600"></i>
        <span class="mt-1 font-bold">Seret file ke sini</span>
        <span class="text-slate-400">atau klik Browse</span>
        <span id="bmnFileName" class="mt-2 hidden font-bold text-teal-600"></span>
      </label>
      <input id="bmnFileInput" type="file" accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.jpg,.jpeg,.png,.zip" class="hidden"
        onchange="handleBmnFileSelection(this.files?.[0])" />
    </div>
    <div id="bmnDriveSource" class="hidden">
      <label class="block font-bold mb-1">Link Google Drive</label>
      <input type="url" id="bmnDriveLink" placeholder="https://drive.google.com/file/d/..."
        class="w-full px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700" />
    </div>
    ${ isArsip ? '' : `
      <div>
        <label class="block font-bold mb-1">Keterangan</label>
        <textarea name="Keterangan" rows="3" placeholder="Tambahkan keterangan"
          class="w-full resize-y px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"></textarea>
      </div>` 
    }
    <input type="hidden" name="Link File" id="bmnLinkFile" value="" />
    <button type="submit" class="w-full py-3 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold">Simpan Dokumen</button>
  `;

  const dateInput = form.querySelector('input[name="Tanggal Buat"]');
  if (dateInput) dateInput.value = new Date().toISOString().slice(0, 10);

  const modalPanel = document.querySelector('#genericAddModal > div');
  if (modalPanel) modalPanel.classList.replace('max-w-md', 'max-w-lg');
  const dropZone = document.getElementById('bmnDropZone');
  if (dropZone) {
    ['dragenter', 'dragover'].forEach(eventName => dropZone.addEventListener(eventName, event => {
      event.preventDefault();
      dropZone.classList.add('border-teal-500', 'bg-teal-50', 'dark:bg-teal-900/20');
    }));
    ['dragleave', 'drop'].forEach(eventName => dropZone.addEventListener(eventName, event => {
      event.preventDefault();
      dropZone.classList.remove('border-teal-500', 'bg-teal-50', 'dark:bg-teal-900/20');
    }));
    dropZone.addEventListener('drop', event => {
      event.preventDefault();
      const file = event.dataTransfer?.files?.[0];
      if (file) handleBmnFileSelection(file);
    });
  }

  document.getElementById('genericModalTitle').textContent = `Upload Dokumen ${subMenuName || groupName}`;
  const modal = document.getElementById('genericAddModal');
  modal.classList.remove('hidden');
  modal.classList.add('flex');
}

function toggleBmnFileSource(source) {
  document.getElementById('bmnUploadSource')?.classList.toggle('hidden', source !== 'upload');
  document.getElementById('bmnDriveSource')?.classList.toggle('hidden', source !== 'drive');
}

let selectedBmnFile = null;

function handleBmnFileSelection(file) {
  if (!file) return;
  selectedBmnFile = file;
  const nameElement = document.getElementById('bmnFileName');
  if (nameElement) {
    nameElement.textContent = file.name;
    nameElement.classList.remove('hidden');
  }
  const titleInput = document.querySelector('#genericAddForm input[name="Judul Dokumen"]');
  if (titleInput && !titleInput.value.trim()) {
    titleInput.value = file.name.replace(/\.[^/.]+$/, '');
  }
}

function renderBmnDokumenView(groupName, subMenuName, filterInputId, tbodyId, pagId, periodSelectId = '') {
  const searchTerm = (document.getElementById(filterInputId)?.value || '').trim().toLocaleLowerCase();
  const periodSelect = periodSelectId ? document.getElementById(periodSelectId) : null;
  const moduleDocuments = (DATA.bmn_dokumen || []).filter(d => {
    if (String(d.Group || '').toLowerCase() !== groupName.toLowerCase()) return false;
    if (String(d['Sub Menu'] || '').toLowerCase() !== subMenuName.toLowerCase()) return false;
    return true;
  });
  let dateFromInput = null;
  let dateToInput = null;
  if (periodSelect) {
    periodSelect.classList.add('hidden');
    const rangeId = `${periodSelectId}DateRange`;
    let range = document.getElementById(rangeId);
    if (!range) {
      range = document.createElement('div');
      range.id = rangeId;
      range.className = 'flex items-end gap-3';
      range.innerHTML = `
        <label class="flex items-center gap-2 text-xs font-bold">Tanggal
          <input type="date" id="${rangeId}From" class="rounded-xl border border-slate-200 bg-slate-100 px-3 py-2 dark:border-slate-700 dark:bg-slate-800" />
        </label>
        <label class="flex items-center gap-2 text-xs font-bold">s/d
          <input type="date" id="${rangeId}To" class="rounded-xl border border-slate-200 bg-slate-100 px-3 py-2 dark:border-slate-700 dark:bg-slate-800" />
        </label>
        <button type="button" aria-label="Cari" title="Cari" class="inline-flex items-center justify-center rounded-xl bg-blue-600 p-2 text-white hover:bg-blue-700">
          ${icon('search', 'w-5 h-5 text-base leading-none')}
        </button>`;
      periodSelect.insertAdjacentElement('afterend', range);
      range.querySelector('button').addEventListener('click', () => {
        PAGE_STATE[pagKey] = PAGE_STATE[pagKey] || { page: 1, size: DEFAULT_PAGE_SIZE };
        PAGE_STATE[pagKey].page = 1;
        renderBmnDokumenView(groupName, subMenuName, filterInputId, tbodyId, pagId, periodSelectId);
      });
    }
    dateFromInput = document.getElementById(`${rangeId}From`);
    dateToInput = document.getElementById(`${rangeId}To`);
  }
  const dateFrom = dateFromInput?.value || '';
  const dateTo = dateToInput?.value || '';
  const list = moduleDocuments.filter(d => {
    const matchesKeterangan = subMenuName.toLowerCase() === 'arsip'
      && String(d.Keterangan || '').toLocaleLowerCase().includes(searchTerm);
    if (periodSelect) {
      const documentDate = dateValueForInput(d['Tanggal Buat'] || '');
      if (dateFrom && (!documentDate || documentDate < dateFrom)) return false;
      if (dateTo && (!documentDate || documentDate > dateTo)) return false;
      if (searchTerm && !String(d['Judul Dokumen'] || '').toLocaleLowerCase().includes(searchTerm) && !matchesKeterangan) return false;
    } else if (searchTerm && !String(d.Periode || '').toLowerCase().includes(searchTerm) && !matchesKeterangan) {
      return false;
    }
    return true;
  });

  const pagKey = `${groupName}_${subMenuName}`.replace(/[^a-zA-Z0-9]/g, '_');
  const rerenderFn = `() => renderBmnDokumenView('${groupName}', '${subMenuName}', '${filterInputId}', '${tbodyId}', '${pagId}', '${periodSelectId}')`;
  const rows = paginateArray(pagKey, list, pagId, rerenderFn);
  const tbody = document.getElementById(tbodyId);
  if (!tbody) return;
  const permissionKeys = {
    'Aset|Tutup Buku': 'aset_tutup_buku',
    'Aset|CALBMN': 'aset_calbmn',
    'Aset|WASDAL': 'aset_wasdal',
    'Aset|RKBMN': 'aset_rkbmn',
    'Aset|Manajemen Risiko': 'aset_manajemen_risiko',
    'Aset|SISPORJA': 'aset_sisporja',
    'Aset|Arsip': 'bmn_arsip',
    'Persediaan|Tutup Buku': 'persediaan_tutup_buku',
    'Persediaan|Form Pengajuan': 'persediaan_form_pengajuan',
    'Persediaan|PIPK': 'persediaan_pipk'
  };
  const moduleKey = permissionKeys[`${groupName}|${subMenuName}`];
  tbody.innerHTML = rows.map(d => {
    const linkedBast = groupName === 'Aset'
      && subMenuName === 'Tutup Buku'
      && String(d['Kategori Item'] || '').trim().toLowerCase() === 'bast';
    const deletable = Boolean(moduleKey && canFull(moduleKey) && (!linkedBast || canFull('bast_otomatis')));
    const label = linkedBast ? 'BAST Dokumen' : 'Dokumen';
    return `
    <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
      ${groupName === 'Persediaan' ? `<td class="py-3 px-3 text-xs font-semibold whitespace-nowrap">${escapeHtml(d.Periode || '-')}</td>` : ''}
      ${subMenuName === 'Arsip' ? ` <td class="py-3 px-3 font-mono font-bold">${escapeHtml(d['Keterangan'] || '-')}</td>` : ''}
      <td class="py-3 px-3 font-bold text-teal-600">${escapeHtml(d['Judul Dokumen'] || '-')}</td>
      <td class="py-3 px-3"><span class="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-xs font-bold">${escapeHtml(d['Kategori Item'] || '-')}</span></td>
      <td class="py-3 px-3 text-xs font-semibold whitespace-nowrap">${escapeHtml(d['Tanggal Buat'] || '-')}</td>
      ${subMenuName != 'Arsip' ? `<td class="py-3 px-3 text-xs text-slate-400">${escapeHtml(d.Keterangan || '-')}</td>` : ''}
      <td class="py-3 px-3">
        ${d['Link File'] ? `<a href="${escapeHtml(d['Link File'])}" target="_blank" rel="noopener" class="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-amber-100 dark:bg-amber-700 text-slate-700 dark:text-slate-100 hover:bg-amber-200 dark:hover:bg-amber-600 transition">${icon('link')}</a>` : '-'}
        ${deletable ? `<button type="button" title="Hapus Dokumen" onclick="deleteRecord('DB_BMN_Dokumen', ${d._row_num || 0}, '${label} ${escapeHtml(d['Judul Dokumen'] || '').replace(/'/g, '')}') " class="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-rose-50 dark:bg-rose-900/70 text-rose-600 dark:text-rose-200 hover:bg-rose-100 dark:hover:bg-rose-800 transition">${icon('delete')}</button>` : ''}
      </td>
    </tr>
  `;
  }).join('') || `<tr><td colspan="${groupName === 'Persediaan' ? 6 : 5}" class="py-8 text-center text-xs text-slate-400">Belum ada dokumen ${escapeHtml(subMenuName)} yang diunggah.</td></tr>`;
}


function resetPengajuanForm() {
  const form = document.getElementById('formPengajuanPersediaan');
  if (!form) return;
  form.reset();
  const namaInput = document.getElementById('pengajuanNama');
  if (namaInput && typeof USER !== 'undefined' && USER.nama) {
    namaInput.value = USER.nama;
  }
}

async function submitPengajuanPersediaan(event) {
  event.preventDefault();
  const form = event.target;
  const btn = document.getElementById('btnSubmitPengajuan');
  if (btn) btn.disabled = true;

  try {
    const formData = new FormData(form);
    const out = await processWithLoading(async () => {
      const res = await fetch('/api/persediaan/pengajuan', {
        method: 'POST',
        body: formData
      });
      return res.json();
    }, 'Gagal mengirim pengajuan persediaan');

    if (!out) return;
    showToast(out.message, out.ok ? 'success' : 'error');
    if (out.ok) {
      resetPengajuanForm();
      await loadDashboard();
    }
  } finally {
    if (btn) btn.disabled = false;
  }
}

initTheme();
window.addEventListener('popstate', () => {
  const modKey = getUrlModule() || 'overview';
  switchModule(modKey, false);
});
processWithLoading(loadDashboard, 'Gagal memuat dashboard');