let DATA = {};
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
  konten: 'ti-device-mobile',
  jadwal_tmb: 'ti-chart-bar',
  master_barang: 'ti-box',
  master_persediaan: 'ti-chart-line',
  persediaan_masuk: 'ti-arrow-down',
  persediaan_keluar: 'ti-arrow-up',
  master_ruangan: 'ti-building',
  bmn_area: 'ti-tool',
  manage_users: 'ti-user-cog',
  manage_modules: 'ti-shield-check',
  sun: 'ti-sun',
  moon: 'ti-moon',
  app_settings: 'ti-settings',
  edit: 'ti-pencil',
  delete: 'ti-trash'
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
  { key: 'dialog', label: 'Dialog', group: 'Siaran & Perencanaan' },
  { key: 'jadwal_siaran', label: 'Jadwal Siaran', group: 'Siaran & Perencanaan' },
  { key: 'program_siaran', label: 'Program Siaran', group: 'Siaran & Perencanaan' },
  { key: 'konten', label: 'Content Planner', group: 'KMB' },
  { key: 'jadwal_tmb', label: 'Jadwal TMB', group: 'TMB' },
  { key: 'master_barang', label: 'Master Barang', group: 'BMN' },
  { key: 'master_persediaan', label: 'Master Persediaan', group: 'BMN' },
  { key: 'persediaan_masuk', label: 'Persediaan Masuk', group: 'BMN' },
  { key: 'persediaan_keluar', label: 'Persediaan Keluar', group: 'BMN' },
  { key: 'master_ruangan', label: 'Master Ruangan', group: 'BMN' },
  { key: 'bmn_area', label: 'BMN AREA', group: 'BMN' },
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
  const res = await fetch('/api/board');
  DATA = await res.json();
  applyTheme(getLocalTheme() || DATA.app_config?.default_theme || APP_CONFIG.default_theme || 'dark');
  buildRoleSidebar();
  populateNipDatalist();
  applyActionButtonVisibility();
  renderAllModules();
}

function populateNipDatalist() {
  const dl = document.getElementById('pegawaiNipDatalist');
  if (dl) {
    dl.innerHTML = (DATA.employees || []).map(e =>
      `<option value="${e.NIP || e.nip_clean}">${e['Nama Pegawai']} — ${e.Posisi || e.Jabatan || ''}</option>`
    ).join('');
  }
}

function buildRoleSidebar() {
  const visibleItems = MODULE_NAV_CONFIG.filter(item =>
    item.always || (item.adminOnly ? isAdmin() : canView(item.key))
  );
  document.getElementById('statAccessibleMods').textContent =
    visibleItems.filter(item => !item.always && !item.adminOnly).length;
  const groups = {};
  visibleItems.forEach(item => { (groups[item.group] = groups[item.group] || []).push(item); });

  document.getElementById('dynamicSidebarMenu').innerHTML = Object.entries(groups).map(([grp, items]) => `
    <div class="space-y-1">
      <p class="px-3 text-[10px] font-extrabold uppercase tracking-wider text-slate-400">${grp}</p>
      ${items.map(i => `
        <button onclick="switchModule('${i.key}')" data-mod="${i.key}"
          class="nav-pill ${i.key === 'overview' ? 'active' : ''} w-full flex items-center justify-between px-3.5 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800/70 transition">
          <span class="flex items-center gap-2.5 truncate">${icon(i.key, 'w-4 h-4 text-base leading-none shrink-0')}<span class="truncate">${i.label}</span></span>
        </button>
      `).join('')}
    </div>
  `).join('');
}

function applyActionButtonVisibility() {
  const toggle = (id, show) => { const el = document.getElementById(id); if (el) el.classList.toggle('hidden', !show); };
  toggle('btnAddTimeline', canFull('dialog'));
  toggle('btnAddInfoOverview', canFull('info_board'));
  toggle('btnAddInfoBoard', canFull('info_board'));
  toggle('btnAddPegawai', canFull('data_pegawai'));
  toggle('btnAddArsipSdm', canFull('arsip_sdm'));
  toggle('btnAddDialog', canFull('dialog'));
  toggle('btnAddSiaran', canFull('jadwal_siaran'));
  toggle('btnAddProgramSiaran', canFull('program_siaran'));
  toggle('btnAddKonten', canFull('konten'));
  toggle('btnAddTmb', canFull('jadwal_tmb'));
  toggle('btnAddBarang', canFull('master_barang'));
  toggle('btnAddPersediaan', canFull('master_persediaan'));
  toggle('btnAddStokMasuk', canFull('persediaan_masuk'));
  toggle('btnAddStokKeluar', canFull('persediaan_keluar'));
  toggle('btnAddRuangan', canFull('master_ruangan'));
}

function switchModule(modKey) {
  document.querySelectorAll('.nav-pill').forEach(b => b.classList.toggle('active', b.dataset.mod === modKey));
  document.querySelectorAll('.mod-section').forEach(s => s.classList.add('hidden'));
  document.getElementById(`mod-${modKey}`)?.classList.remove('hidden');
  if (window.innerWidth < 1024) document.getElementById('sidebar').classList.add('-translate-x-full');
}

function renderAllModules() {
  document.getElementById('syncStatusLabel').textContent = DATA.status_msg || '-';
  document.getElementById('syncTimeLabel').textContent = DATA.server_time || '';
  document.getElementById('statInfoCount').textContent = (DATA.info_board || []).length;

  renderTimelineModule();
  renderInfoBoard();
  if (canView('data_pegawai')) renderDataPegawai();
  if (canView('arsip_sdm')) renderArsipSdm();
  if (canView('dialog')) renderDialogModule();
  if (canView('jadwal_siaran')) renderJadwalSiaran();
  if (canView('program_siaran')) renderProgramSiaran();
  if (canView('konten')) renderKonten();
  if (canView('jadwal_tmb')) renderJadwalTmb();
  if (canView('master_barang')) renderMasterBarang();
  if (canView('master_persediaan')) renderMasterPersediaan();
  if (canView('persediaan_masuk')) renderPersediaanMasuk();
  if (canView('persediaan_keluar')) renderPersediaanKeluar();
  if (canView('master_ruangan')) renderMasterRuangan();
  if (canFull('manage_users')) renderManageUsers();
  if (canFull('manage_modules')) renderManageModules();
  if (isAdmin()) renderAppSettings();
}

function renderAppSettings() {
  const config = DATA.app_config || APP_CONFIG;
  document.getElementById('appTimezone').value = config.timezone || 'Asia/Makassar';
  document.getElementById('appLanguage').value = config.language || 'id';
  document.getElementById('appDefaultTheme').value = config.default_theme || 'light';
  document.getElementById('appActiveYear').value = config.active_year || APP_CONFIG.active_year;
}

async function submitAppSettings(event) {
  event.preventDefault();
  const button = document.getElementById('btnSaveAppSettings');
  button.disabled = true;
  const settings = {
    timezone: document.getElementById('appTimezone').value,
    language: document.getElementById('appLanguage').value,
    default_theme: document.getElementById('appDefaultTheme').value,
    active_year: document.getElementById('appActiveYear').value
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
  if (!confirm(`Hapus ${label}?`)) return;
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
      <td class="py-3 px-3 font-bold">${s.Tanggal || '-'}</td>
      <td class="py-3 px-3 text-xs">${s.Shift || '-'}</td>
      <td class="py-3 px-3 font-bold text-teal-600">${s.Programa || '-'}</td>
      <td class="py-3 px-3 font-semibold">${s.Penyiar || '-'}</td>
      <td class="py-3 px-3">${s.Operator || '-'}</td>
      <td class="py-3 px-3"><span class="px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-300">${s.Status || '-'}</span></td>
    </tr>
  `).join('');
}

function renderProgramSiaran() {
  const rows = paginateArray('program_siaran', DATA.program_siaran || [], 'pagProgramSiaran', 'renderProgramSiaran');
  document.getElementById('tbodyProgramSiaran').innerHTML = rows.map(p => `
    <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
      <td class="py-3 px-3 font-mono text-xs text-slate-500">${p['Kode Program'] || '-'}</td>
      <td class="py-3 px-3 font-bold text-teal-600">${p.Programa || '-'}</td>
      <td class="py-3 px-3 font-extrabold">${p['Nama Program'] || '-'}</td>
      <td class="py-3 px-3 text-xs">${p.Hari || '-'}</td>
      <td class="py-3 px-3 text-xs font-semibold">${p.Jam || '-'}</td>
      <td class="py-3 px-3 text-xs">${p.Format || '-'}</td>
      <td class="py-3 px-3 text-xs">${p.Produser || '-'}</td>
      <td class="py-3 px-3"><span class="px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-300">${p.Status || 'Aktif'}</span></td>
    </tr>
  `).join('');
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
      <td class="py-3 px-3 font-bold">${t.Tanggal || '-'}</td>
      <td class="py-3 px-3 text-xs">${t.Shift || '-'}</td>
      <td class="py-3 px-3 font-bold text-indigo-600">${t['Lokasi Pemancar'] || '-'}</td>
      <td class="py-3 px-3 font-semibold">${t['Teknisi TMB'] || '-'}</td>
      <td class="py-3 px-3 text-xs">${t.Tugas || '-'}</td>
      <td class="py-3 px-3"><span class="px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-300">${t.Status || '-'}</span></td>
    </tr>
  `).join('');
}

function renderMasterBarang() {
  const q = (document.getElementById('searchBarang')?.value || '').toLowerCase();
  const filtered = (DATA.assets || []).filter(a => Object.values(a).some(v => String(v).toLowerCase().includes(q)));
  const rows = paginateArray('barang', filtered, 'pagBarang', 'renderMasterBarang');
  document.getElementById('tbodyBarang').innerHTML = rows.map(a => `
    <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
      <td class="py-3 px-3 font-bold">${a['Kode Ruang'] || '-'} <span class="block text-[10px] text-slate-400">${a['Nama Ruangan'] || ''}</span></td>
      <td class="py-3 px-3 font-mono text-slate-500">${a['Nomor Kode Barang'] || '-'}</td>
      <td class="py-3 px-3 font-bold">${a['Nama Barang'] || '-'}</td>
      <td class="py-3 px-3">${a['Merk Model'] || '-'}</td>
      <td class="py-3 px-3">${a.Tahun || '-'}</td>
      <td class="py-3 px-3 font-bold">${a.NUP || '-'}</td>
      <td class="py-3 px-3 font-bold ${String(a.Kondisi).toLowerCase() === 'baik' ? 'text-emerald-600' : 'text-rose-500'}">${a.Kondisi || '-'}</td>
      <td class="py-3 px-3 text-amber-600">${a['Tindak Lanjut'] || '-'}</td>
    </tr>
  `).join('');
}

function renderMasterPersediaan() {
  const rows = paginateArray('persediaan', DATA.stock_master || [], 'pagPersediaan', 'renderMasterPersediaan');
  document.getElementById('tbodyPersediaan').innerHTML = rows.map(s => `
    <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
      <td class="py-3 px-3 font-mono text-xs text-slate-400">${s['Kode Barang'] || '-'}</td>
      <td class="py-3 px-3 font-bold">${s['Nama Barang']}</td>
      <td class="py-3 px-3 text-slate-400">${s.Unit || '-'}</td>
      <td class="py-3 px-3 text-right">${s['Stok Awal']}</td>
      <td class="py-3 px-3 text-right text-emerald-600 font-bold">+${s['Barang Masuk']}</td>
      <td class="py-3 px-3 text-right text-amber-600 font-bold">-${s['Barang Keluar']}</td>
      <td class="py-3 px-3 text-right font-extrabold">${s['Stok Akhir']}</td>
    </tr>
  `).join('');
}

function renderPersediaanMasuk() {
  const q = (document.getElementById('searchStokIn')?.value || '').toLowerCase();
  const filtered = (DATA.stock_in || []).filter(r => Object.values(r).some(v => String(v).toLowerCase().includes(q)));
  const rows = paginateArray('stok_in', filtered, 'pagStokIn', 'renderPersediaanMasuk');
  document.getElementById('tbodyStokIn').innerHTML = rows.map(r => `
    <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
      <td class="py-3 px-3 whitespace-nowrap">${r.Tanggal || '-'}</td>
      <td class="py-3 px-3 text-slate-500">${r['Penanggung Jawab'] || '-'}</td>
      <td class="py-3 px-3 font-bold">${r['Nama Barang'] || '-'}</td>
      <td class="py-3 px-3 text-right font-bold text-emerald-600">+${r['Jumlah Masuk'] || 0}</td>
      <td class="py-3 px-3">${r.Unit || '-'}</td>
      <td class="py-3 px-3 text-right font-bold">${r.Pcs || r['Jumlah Masuk'] || 0}</td>
      <td class="py-3 px-3 text-xs text-slate-400">${r.Keterangan || '-'}</td>
    </tr>
  `).join('');
}

function renderPersediaanKeluar() {
  const q = (document.getElementById('searchStokOut')?.value || '').toLowerCase();
  const filtered = (DATA.stock_out || []).filter(r => Object.values(r).some(v => String(v).toLowerCase().includes(q)));
  const rows = paginateArray('stok_out', filtered, 'pagStokOut', 'renderPersediaanKeluar');
  document.getElementById('tbodyStokOut').innerHTML = rows.map(r => `
    <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
      <td class="py-3 px-3 whitespace-nowrap">${r.Tanggal || '-'}</td>
      <td class="py-3 px-3 font-bold">${r['Nama Barang'] || '-'}</td>
      <td class="py-3 px-3 text-slate-500">${r.Bidang || '-'}</td>
      <td class="py-3 px-3 font-semibold">${r['Penerima Barang'] || '-'}</td>
      <td class="py-3 px-3 text-right font-bold text-amber-600">-${r['Jumlah Keluar'] || 0}</td>
      <td class="py-3 px-3">${r.Unit || '-'}</td>
      <td class="py-3 px-3 text-right font-bold">${r.Pcs || r['Jumlah Keluar'] || 0}</td>
      <td class="py-3 px-3 text-xs text-slate-400">${r.Keterangan || '-'}</td>
    </tr>
  `).join('');
}

function renderMasterRuangan() {
  const q = (document.getElementById('searchRuangan')?.value || '').toLowerCase();
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
    return `
      <tr class="hover:bg-slate-200/60 dark:hover:bg-slate-800/50 transition">
        <td class="py-3 px-3"><span class="px-2.5 py-0.5 rounded-lg bg-slate-900 dark:bg-slate-700 text-white text-xs font-extrabold">${r['Nomor Ruangan'] || '-'}</span></td>
        <td class="py-3 px-3 font-extrabold">${r['Nama Ruangan'] || '-'}</td>
        <td class="py-3 px-3 text-xs text-slate-500">${r.Lokasi || '-'}</td>
        <td class="py-3 px-3 font-mono text-xs text-slate-500">${rawPjNip || '-'}</td>
        <td class="py-3 px-3 font-bold text-teal-700 dark:text-teal-300">${emp?.['Nama Pegawai'] || r.pj_nama || '-'}</td>
        <td class="py-3 px-3 text-xs font-semibold">${emp?.Jabatan || emp?.Posisi || r.pj_jabatan || '-'}</td>
        <td class="py-3 px-3 text-right">
          ${deletable && rowNum > 1 ? `<button type="button" title="Hapus ruangan" aria-label="Hapus ruangan" onclick="deleteRecord('DB_Ruangan', ${rowNum}, '${(r['Nama Ruangan'] || '').replace(/'/g, '')}')" class="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-rose-50 dark:bg-rose-900/70 text-rose-600 dark:text-rose-200 hover:bg-rose-100 dark:hover:bg-rose-800 transition">${icon('delete')}</button>` : '-'}
        </td>
      </tr>
    `;
  }).join('');
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
  DB_Arsip_SDM: { title: 'Tambah Arsip SDM', fields: ['Nomor Dokumen', 'Nama Dokumen', 'Tanggal', 'Jenis', 'Link'] },
  DB_Dialog: { title: 'Tambah Agenda Dialog', fields: ['Tanggal', 'Program', 'Topik', 'Narasumber', 'Jabatan', 'Kehadiran', 'PIC Narasumber', 'Flyer', 'Bestcut', 'Keterlaksanaan', 'Kendala'] },
  DB_Siaran: { title: 'Tambah Jadwal Siaran', fields: ['Tanggal', 'Shift', 'Programa', 'Penyiar', 'Operator', 'Status'] },
  DB_Program: { title: 'Tambah Program Siaran', fields: ['Kode Program', 'Programa', 'Nama Program', 'Hari', 'Jam', 'Format', 'Produser', 'Status'] },
  DB_Konten: { title: 'Tambah Konten (Planner)', fields: ['Tanggal Tayang', 'Platform', 'Akun', 'Judul Konten', 'Jenis', 'Divisi', 'PIC', 'Status', 'Link Asset'] },
  DB_Jadwal_TMB: { title: 'Tambah Jadwal TMB', fields: ['Tanggal', 'Shift', 'Lokasi Pemancar', 'Teknisi TMB', 'Tugas', 'Status'] },
  DB_Aset: { title: 'Tambah Master Barang', fields: ['Nomor Kode Barang', 'Kode Ruang', 'Nama Barang', 'Merk Model', 'Tahun', 'NUP', 'Kondisi', 'Tindak Lanjut', 'Keterangan'] },
  DB_Ruangan: { title: 'Tambah Master Ruangan', fields: ['Nomor Ruangan', 'Nama Ruangan', 'Lokasi', 'NIP Penanggung Jawab', 'Nama', 'Jabatan'] },
  DB_Stok_Master: { title: 'Tambah Master Persediaan', fields: ['Kode Barang', 'Nama Barang', 'Unit', 'Stok Awal', 'Keterangan'] },
  DB_Stok_Masuk: { title: 'Catat Persediaan Masuk', fields: ['Tanggal', 'Penanggung Jawab', 'Nama Barang', 'Jumlah Masuk', 'Unit', 'Pcs', 'Keterangan'] },
  DB_Stok_Keluar: { title: 'Catat Persediaan Keluar', fields: ['Tanggal', 'Nama Barang', 'Bidang', 'Penerima Barang', 'Jumlah Keluar', 'Unit', 'Pcs', 'Keterangan'] },
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

function openAddModal(key) {
  const s = SCHEMAS[key];
  if (!s) return;
  document.getElementById('genericModalTitle').textContent = s.title;
  const form = document.getElementById('genericAddForm');
  form.dataset.targetKey = key;
  form.innerHTML = s.fields.map(f => {
    const isRoomNip = (key === 'DB_Ruangan' && f === 'NIP Penanggung Jawab');
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
function closeGenericModal() { const m = document.getElementById('genericAddModal'); m.classList.add('hidden'); m.classList.remove('flex'); }
async function submitGenericRecord(e) {
  e.preventDefault();
  const key = e.target.dataset.targetKey;
  const payload = Object.fromEntries(new FormData(e.target).entries());
  const out = await processWithLoading(async () => {
    const res = await fetch(`/api/add/${key}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    const out = await res.json();
    if (out.ok) { closeGenericModal(); await loadDashboard(); }
    return out;
  }, 'Gagal menyimpan data');
  if (out) showToast(out.message, out.ok ? 'success' : 'error');
}

function openInitModal() { const m = document.getElementById('initModal'); m.classList.remove('hidden'); m.classList.add('flex'); }
function closeInitModal() { const m = document.getElementById('initModal'); m.classList.add('hidden'); m.classList.remove('flex'); }
async function runInitData() {
  const btn = document.getElementById('btnRunInit');
  btn.disabled = true;
  const include_samples = document.getElementById('initIncludeSamples').checked;
  try {
    const out = await processWithLoading(async () => {
      const res = await fetch('/api/init-data', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ include_samples }) });
      const out = await res.json();
      if (out.ok) { closeInitModal(); await loadDashboard(); }
      return out;
    }, 'Gagal menjalankan inisialisasi');
    if (out) showToast(out.message, out.ok ? 'success' : 'error');
  } finally {
    btn.disabled = false;
  }
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

initTheme();
processWithLoading(loadDashboard, 'Gagal memuat dashboard');
