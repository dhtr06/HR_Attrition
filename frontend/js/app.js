/**
 * TalentPulse AI – Enterprise HR Attrition Analytics Platform
 * Application Frontend Logic
 */

// Utility Selectors
const $ = (id) => document.getElementById(id);
const $$ = (selector) => document.querySelectorAll(selector);

// State Store
let employeesData = [];
let deptChartInstance = null;
let riskChartInstance = null;
let activeTab = 'dashboard';

// API Fetch Wrapper
async function api(url, options = {}) {
  try {
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
      ...options
    });
    const data = await res.json().catch(() => ({ detail: 'Lỗi phản hồi từ máy chủ' }));
    if (!res.ok) {
      throw new Error(data.detail || 'Có lỗi xảy ra trong quá trình xử lý');
    }
    return data;
  } catch (err) {
    console.error(`API Error on ${url}:`, err);
    throw err;
  }
}

// Number & String Formatters
const fmtNumber = (val) => (val === null || val === undefined || isNaN(val)) ? '—' : Number(val).toLocaleString('vi-VN');
const fmtCurrency = (val) => (val === null || val === undefined || isNaN(val)) ? '—' : '$' + Number(val).toLocaleString('en-US');
const fmtPct = (val) => (val === null || val === undefined || isNaN(val)) ? '0.0%' : (Number(val) * 100).toFixed(1) + '%';

function escapeHtml(str) {
  return String(str ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

// Avatar color generator based on name
function getAvatarBg(name) {
  const colors = [
    'linear-gradient(135deg, #3b82f6, #1d4ed8)',
    'linear-gradient(135deg, #10b981, #047857)',
    'linear-gradient(135deg, #8b5cf6, #6d28d9)',
    'linear-gradient(135deg, #f59e0b, #b45309)',
    'linear-gradient(135deg, #ec4899, #be185d)',
    'linear-gradient(135deg, #06b6d4, #0e7490)'
  ];
  let hash = 0;
  for (let i = 0; i < (name || '').length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}

// Toast Notifications System
function showToast(message, type = 'success') {
  const container = $('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  const icon = type === 'success' ? '✔' : type === 'danger' ? '✖' : '⚠';
  toast.innerHTML = `
    <span style="font-weight: 800; font-size: 14px;">${icon}</span>
    <span class="toast-msg">${escapeHtml(message)}</span>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(-10px)';
    setTimeout(() => toast.remove(), 250);
  }, 3500);
}

// Debounce helper
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// ==========================================================================
// Tab Navigation & Routing
// ==========================================================================
function switchTab(tabId) {
  activeTab = tabId;

  // Update nav item active states
  $$('.sidebar-nav .nav-item').forEach(item => {
    if (item.getAttribute('data-tab') === tabId) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });

  // Update tab pane visibility
  $$('.tab-pane').forEach(pane => {
    if (pane.id === tabId) {
      pane.classList.add('active');
    } else {
      pane.classList.remove('active');
    }
  });

  // Update Breadcrumb & Header Title
  const titles = {
    dashboard: { title: 'Bảng điều khiển Tổng quan', crumb: 'Quản trị Nhân sự / Tổng quan' },
    employees: { title: 'Quản lý Hồ sơ Nhân sự', crumb: 'Quản trị Nhân sự / Danh sách Nhân viên' },
    prediction: { title: 'Dự đoán Nguy cơ Nghỉ việc (AI)', crumb: 'Trí tuệ Nhân tạo / Phân tích Rủi ro' },
    history: { title: 'Lịch sử & Báo cáo Dự đoán', crumb: 'Báo cáo / Nhật ký AI' },
    system: { title: 'Thông số Kỹ thuật & Mô hình AI', crumb: 'Hệ thống / Chẩn đoán Engine' }
  };

  const info = titles[tabId] || titles.dashboard;
  $('headerTitle').textContent = info.title;
  $('headerBreadcrumb').textContent = info.crumb;

  // Close mobile sidebar if open
  $('appLayoutSidebar')?.classList.remove('mobile-open');

  // Trigger relevant data load
  if (tabId === 'dashboard') loadSummary();
  if (tabId === 'employees') loadEmployees();
  if (tabId === 'history') loadHistory();
  if (tabId === 'system') loadSystemStatus();
}

// Setup Nav clicks
document.addEventListener('DOMContentLoaded', () => {
  $$('.sidebar-nav .nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const tabId = item.getAttribute('data-tab');
      window.location.hash = tabId;
      switchTab(tabId);
    });
  });

  // Handle URL hash routing
  const initialHash = (window.location.hash || '#dashboard').replace('#', '');
  switchTab(initialHash || 'dashboard');

  // Mobile menu toggle
  $('mobileMenuToggle')?.addEventListener('click', () => {
    document.querySelector('.sidebar')?.classList.toggle('mobile-open');
  });

  // Initialize all data
  loadAll();
});

// ==========================================================================
// Dashboard Logic & Interactive Charts
// ==========================================================================
async function loadSummary() {
  try {
    const data = await api('/api/dashboard/summary');

    $('statTotalEmployees').textContent = fmtNumber(data.total_employees);
    $('statTotalPredictions').textContent = fmtNumber(data.total_predictions);
    $('statHighRisk').textContent = fmtNumber(data.high_risk_predictions);
    $('statAvgSatisfaction').innerHTML = `${data.avg_satisfaction} <small>/ 4.0</small>`;
    $('badgeEmpCount').textContent = data.total_employees;

    // Render Charts
    renderDeptChart(data.departments || []);
    renderRiskDonutChart(data);

    // Render Attention List
    renderAttentionList(data.attention_list || []);

  } catch (err) {
    console.error('Failed to load summary:', err);
  }
}

function renderDeptChart(departments) {
  const ctx = $('deptChart')?.getContext('2d');
  if (!ctx) return;

  const labels = departments.map(d => d.department);
  const counts = departments.map(d => d.count);
  const otCounts = departments.map(d => d.ot_count);

  if (deptChartInstance) {
    deptChartInstance.destroy();
  }

  if (typeof Chart === 'undefined') return;

  deptChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels.length ? labels : ['Sales', 'R&D', 'HR'],
      datasets: [
        {
          label: 'Tổng nhân sự',
          data: counts.length ? counts : [4, 6, 2],
          backgroundColor: '#4f46e5',
          borderRadius: 6
        },
        {
          label: 'Nhân sự làm OT (Yes)',
          data: otCounts.length ? otCounts : [2, 3, 1],
          backgroundColor: '#f59e0b',
          borderRadius: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: { font: { family: 'Plus Jakarta Sans', size: 12 } }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { stepSize: 1 }
        }
      }
    }
  });
}

function renderRiskDonutChart(data) {
  const ctx = $('riskDonutChart')?.getContext('2d');
  if (!ctx) return;

  const low = data.low_risk_predictions || 2;
  const med = data.medium_risk_predictions || 1;
  const high = data.high_risk_predictions || 2;

  if (riskChartInstance) {
    riskChartInstance.destroy();
  }

  if (typeof Chart === 'undefined') return;

  riskChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Nguy cơ Thấp (<35%)', 'Trung bình (35-65%)', 'Nguy cơ Cao (>65%)'],
      datasets: [{
        data: [low, med, high],
        backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
        borderWidth: 2,
        borderColor: '#ffffff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '70%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: { font: { family: 'Plus Jakarta Sans', size: 11 }, padding: 14 }
        }
      }
    }
  });
}

function renderAttentionList(list) {
  const tbody = $('attentionRows');
  if (!tbody) return;

  if (!list || !list.length) {
    tbody.innerHTML = `<tr><td colspan="9" class="text-center py-4" style="color: var(--text-muted)">Không có nhân sự nào trong diện cảnh báo rủi ro cao.</td></tr>`;
    return;
  }

  tbody.innerHTML = list.map(item => {
    return `
      <tr>
        <td><strong>${escapeHtml(item.employee_code)}</strong></td>
        <td>
          <div class="emp-cell">
            <div class="emp-avatar" style="background: ${getAvatarBg(item.full_name)}">${(item.full_name || 'U').charAt(0)}</div>
            <div>
              <div class="emp-name">${escapeHtml(item.full_name)}</div>
              <div class="emp-sub">${item.years_at_company} năm thâm niên</div>
            </div>
          </div>
        </td>
        <td><span class="badge badge-dept">${escapeHtml(item.department)}</span></td>
        <td>${escapeHtml(item.job_role)}</td>
        <td><strong>${fmtCurrency(item.monthly_income)}</strong></td>
        <td><span class="badge badge-ot-yes">Có OT</span></td>
        <td><span class="rating-stars">${'★'.repeat(item.job_satisfaction || 1)}${'☆'.repeat(4 - (item.job_satisfaction || 1))}</span></td>
        <td><span class="badge badge-risk-high">${escapeHtml(item.reason)}</span></td>
        <td>
          <button class="action-btn predict-btn" onclick="quickPredictEmployee(${item.id})">
            ⚡ Dự đoán AI
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

// ==========================================================================
// Employee Management (CRUD, Search, Filter, Export)
// ==========================================================================
async function loadEmployees() {
  const tbody = $('employeeRows');
  if (!tbody) return;

  const q = $('employeeSearch')?.value || '';
  const dept = $('filterDepartment')?.value || 'All';
  const ot = $('filterOvertime')?.value || 'All';

  let url = `/api/employees?q=${encodeURIComponent(q)}`;
  if (dept !== 'All') url += `&department=${encodeURIComponent(dept)}`;
  if (ot !== 'All') url += `&overtime=${encodeURIComponent(ot)}`;

  try {
    const list = await api(url);
    employeesData = list;

    // Update Employee selector in Prediction tab
    populateEmployeeDropdown(list);

    if ($('badgeEmpCount')) $('badgeEmpCount').textContent = list.length;
    if ($('employeeCountText')) $('employeeCountText').textContent = `Hiển thị ${list.length} nhân viên`;

    if (!list.length) {
      tbody.innerHTML = `<tr><td colspan="11" class="text-center py-6" style="color: var(--text-muted)">Không tìm thấy nhân viên phù hợp với tiêu chí lọc.</td></tr>`;
      return;
    }

    tbody.innerHTML = list.map(emp => {
      const isOt = (emp.overtime || '').toLowerCase() === 'yes';
      const otBadge = isOt
        ? '<span class="badge badge-ot-yes">Có OT</span>'
        : '<span class="badge badge-ot-no">Không</span>';

      const satStars = '★'.repeat(emp.job_satisfaction || 1) + '☆'.repeat(4 - (emp.job_satisfaction || 1));
      const wlbStars = '★'.repeat(emp.work_life_balance || 1) + '☆'.repeat(4 - (emp.work_life_balance || 1));

      return `
        <tr>
          <td>
            <div class="emp-cell">
              <div class="emp-avatar" style="background: ${getAvatarBg(emp.full_name)}">${(emp.full_name || 'U').charAt(0)}</div>
              <div>
                <div class="emp-name">${escapeHtml(emp.full_name)}</div>
                <div class="emp-sub">${emp.age || '—'} tuổi</div>
              </div>
            </div>
          </td>
          <td><strong>${escapeHtml(emp.employee_code)}</strong></td>
          <td><span class="badge badge-dept">${escapeHtml(emp.department || '—')}</span></td>
          <td>${escapeHtml(emp.job_role || '—')}</td>
          <td>${emp.age || '—'}</td>
          <td><strong>${fmtCurrency(emp.monthly_income)}</strong></td>
          <td>${emp.years_at_company != null ? emp.years_at_company + ' năm' : '—'}</td>
          <td>${otBadge}</td>
          <td><span class="rating-stars">${satStars}</span></td>
          <td><span class="rating-stars" style="color: #6366f1;">${wlbStars}</span></td>
          <td class="text-right">
            <div class="table-actions">
              <button class="action-btn predict-btn" title="Dự đoán rủi ro nghỉ việc" onclick="quickPredictEmployee(${emp.id})">
                ⚡ Dự đoán
              </button>
              <button class="action-btn" title="Chỉnh sửa hồ sơ" onclick="openEditModal(${emp.id})">
                ✏️ Sửa
              </button>
              <button class="action-btn delete-btn" title="Xóa nhân viên" onclick="deleteEmployee(${emp.id}, '${escapeHtml(emp.full_name)}')">
                🗑️
              </button>
            </div>
          </td>
        </tr>
      `;
    }).join('');

  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="11" class="text-center py-6 danger-text">${escapeHtml(err.message)}</td></tr>`;
  }
}

// Modal Form: Add or Edit Employee
function openAddModal() {
  $('modalEmployeeTitle').textContent = 'Thêm hồ sơ Nhân viên mới';
  $('modalEmployeeId').value = '';
  $('modalEmployeeForm').reset();
  $('employeeModal').hidden = false;
}

function openEditModal(empId) {
  const emp = employeesData.find(x => x.id === empId);
  if (!emp) return;

  $('modalEmployeeTitle').textContent = `Chỉnh sửa hồ sơ: ${emp.full_name}`;
  $('modalEmployeeId').value = emp.id;
  $('modalEmpCode').value = emp.employee_code || '';
  $('modalFullName').value = emp.full_name || '';
  $('modalAge').value = emp.age || '';
  $('modalDepartment').value = emp.department || 'Sales';
  $('modalJobRole').value = emp.job_role || 'Sales Executive';
  $('modalIncome').value = emp.monthly_income || '';
  $('modalYears').value = emp.years_at_company || '';
  $('modalOvertime').value = emp.overtime || 'No';
  $('modalJobSatisfaction').value = emp.job_satisfaction || 3;
  $('modalWlb').value = emp.work_life_balance || 3;

  $('employeeModal').hidden = false;
}

function closeEmployeeModal() {
  $('employeeModal').hidden = true;
}

// Save Employee (POST or PUT)
$('modalEmployeeForm')?.addEventListener('submit', async (e) => {
  e.preventDefault();

  const empId = $('modalEmployeeId').value;
  const payload = {
    employee_code: $('modalEmpCode').value.trim(),
    full_name: $('modalFullName').value.trim(),
    age: $('modalAge').value ? Number($('modalAge').value) : null,
    department: $('modalDepartment').value,
    job_role: $('modalJobRole').value,
    monthly_income: $('modalIncome').value ? Number($('modalIncome').value) : null,
    years_at_company: $('modalYears').value ? Number($('modalYears').value) : null,
    overtime: $('modalOvertime').value,
    job_satisfaction: Number($('modalJobSatisfaction').value),
    work_life_balance: Number($('modalWlb').value)
  };

  const btn = $('btnSaveEmployee');
  btn.disabled = true;
  btn.textContent = 'Đang lưu...';

  try {
    if (empId) {
      await api(`/api/employees/${empId}`, {
        method: 'PUT',
        body: JSON.stringify(payload)
      });
      showToast('Cập nhật thông tin nhân viên thành công!');
    } else {
      await api('/api/employees', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      showToast('Thêm nhân viên mới thành công!');
    }

    closeEmployeeModal();
    loadAll();
  } catch (err) {
    showToast(err.message, 'danger');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Lưu hồ sơ';
  }
});

// Delete Employee
async function deleteEmployee(id, name) {
  if (!confirm(`Bạn có chắc chắn muốn xóa nhân viên "${name}" khỏi hệ thống?`)) return;

  try {
    await api(`/api/employees/${id}`, { method: 'DELETE' });
    showToast(`Đã xóa nhân viên "${name}".`);
    loadAll();
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

// Export Employees to CSV
function exportEmployeesCSV() {
  if (!employeesData.length) {
    showToast('Chưa có dữ liệu nhân viên để xuất', 'warning');
    return;
  }

  const headers = ['Mã NV', 'Họ tên', 'Tuổi', 'Phòng ban', 'Chức vụ', 'Lương tháng ($)', 'Thâm niên (năm)', 'Làm thêm giờ', 'Hài lòng (1-4)', 'WLB (1-4)'];
  const rows = employeesData.map(e => [
    `"${e.employee_code || ''}"`,
    `"${e.full_name || ''}"`,
    e.age || '',
    `"${e.department || ''}"`,
    `"${e.job_role || ''}"`,
    e.monthly_income || '',
    e.years_at_company || '',
    `"${e.overtime || 'No'}"`,
    e.job_satisfaction || '',
    e.work_life_balance || ''
  ]);

  const csvContent = "\uFEFF" + [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `danh_sach_nhan_vien_${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  showToast('Đã xuất file CSV thành công!');
}

// ==========================================================================
// AI Prediction Logic & Simulation Presets
// ==========================================================================
function populateEmployeeDropdown(list) {
  const select = $('selectEmpToPredict');
  if (!select) return;

  const currentVal = select.value;
  select.innerHTML = '<option value="">-- Chọn nhân viên để tự động điền form --</option>' +
    list.map(e => `<option value="${e.id}">${e.employee_code} - ${e.full_name} (${e.department})</option>`).join('');
  
  if (currentVal) select.value = currentVal;
}

function onSelectEmployeeToPredict(empId) {
  if (!empId) return;
  const emp = employeesData.find(x => x.id === Number(empId));
  if (!emp) return;

  $('predEmployeeId').value = emp.id;
  $('predAge').value = emp.age || 30;
  $('predYears').value = emp.years_at_company != null ? emp.years_at_company : 3.0;
  $('predDept').value = emp.department || 'Sales';
  $('predRole').value = emp.job_role || 'Sales Executive';
  $('predIncome').value = emp.monthly_income || 5000;
  $('predOvertime').value = emp.overtime || 'No';
  $('predSatisfaction').value = emp.job_satisfaction || 3;
  $('predWlb').value = emp.work_life_balance || 3;

  showToast(`Đã nạp hồ sơ của: ${emp.full_name}`);
}

function quickPredictEmployee(empId) {
  switchTab('prediction');
  $('selectEmpToPredict').value = empId;
  onSelectEmployeeToPredict(empId);
  // Auto-submit prediction form
  setTimeout(() => {
    $('predictionForm')?.requestSubmit();
  }, 100);
}

// Preset button handlers
function applyPreset(type) {
  $('predEmployeeId').value = '';
  $('selectEmpToPredict').value = '';

  if (type === 'high_risk') {
    $('predAge').value = 26;
    $('predYears').value = 1.2;
    $('predDept').value = 'Sales';
    $('predRole').value = 'Sales Executive';
    $('predIncome').value = 2900;
    $('predOvertime').value = 'Yes';
    $('predSatisfaction').value = 1;
    $('predWlb').value = 1;
    showToast('Đã áp dụng trường hợp mẫu: Nguy cơ rất cao');
  } else if (type === 'low_risk') {
    $('predAge').value = 42;
    $('predYears').value = 8.5;
    $('predDept').value = 'Research & Development';
    $('predRole').value = 'Research Scientist';
    $('predIncome').value = 11500;
    $('predOvertime').value = 'No';
    $('predSatisfaction').value = 4;
    $('predWlb').value = 4;
    showToast('Đã áp dụng trường hợp mẫu: Nguy cơ thấp / Gắn bó cao');
  } else if (type === 'medium_risk') {
    $('predAge').value = 32;
    $('predYears').value = 3.0;
    $('predDept').value = 'Human Resources';
    $('predRole').value = 'HR Specialist';
    $('predIncome').value = 5200;
    $('predOvertime').value = 'No';
    $('predSatisfaction').value = 2;
    $('predWlb').value = 2;
    showToast('Đã áp dụng trường hợp mẫu: Trung bình / Cần theo dõi');
  }

  $('predictionForm')?.requestSubmit();
}

// Prediction Form Submit
$('predictionForm')?.addEventListener('submit', async (e) => {
  e.preventDefault();

  const payload = {
    employee_id: $('predEmployeeId').value ? Number($('predEmployeeId').value) : null,
    age: Number($('predAge').value),
    years_at_company: Number($('predYears').value),
    department: $('predDept').value,
    job_role: $('predRole').value,
    monthly_income: Number($('predIncome').value),
    overtime: $('predOvertime').value,
    job_satisfaction: Number($('predSatisfaction').value),
    work_life_balance: Number($('predWlb').value)
  };

  // Switch display state to loading
  $('predictionEmptyState').hidden = true;
  $('predictionResultDisplay').hidden = true;
  $('predictionLoadingState').hidden = false;

  const btn = $('btnRunPrediction');
  btn.disabled = true;

  try {
    const result = await api('/api/predictions', {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    displayPredictionResult(result);
    showToast('Đã hoàn tất phân tích dự báo AI!');
    loadSummary(); // Refresh stats
  } catch (err) {
    showToast(err.message, 'danger');
    $('predictionLoadingState').hidden = true;
    $('predictionEmptyState').hidden = false;
  } finally {
    btn.disabled = false;
  }
});

function displayPredictionResult(res) {
  $('predictionLoadingState').hidden = true;
  $('predictionResultDisplay').hidden = false;

  // Percentage & Tier
  const pct = (res.probability * 100).toFixed(1) + '%';
  $('resultProbabilityVal').textContent = pct;
  $('resultModelName').textContent = res.model_name || 'AI Pipeline';

  const card = $('riskScoreCard');
  card.className = 'risk-score-card';

  if (res.risk_level === 'Cao') {
    card.classList.add('high-risk');
    $('resultTierPill').textContent = 'NGUY CƠ RỜI ĐI CAO (HIGH RISK)';
  } else if (res.risk_level === 'Trung bình') {
    card.classList.add('medium-risk');
    $('resultTierPill').textContent = 'NGUY CƠ TRUNG BÌNH (MEDIUM RISK)';
  } else {
    card.classList.add('low-risk');
    $('resultTierPill').textContent = 'NGUY CƠ RỜI ĐI THẤP (LOW RISK)';
  }

  // Key Drivers / Factors
  const factorsList = $('resultFactorsList');
  if (res.key_factors && res.key_factors.length) {
    factorsList.innerHTML = res.key_factors.map(f => `
      <div class="factor-card ${f.impact}">
        <div class="factor-title">${escapeHtml(f.title)}</div>
        <div class="factor-desc">${escapeHtml(f.desc)}</div>
      </div>
    `).join('');
  } else {
    factorsList.innerHTML = `<div class="factor-card positive"><div class="factor-title">Chỉ số ổn định</div><div class="factor-desc">Không phát hiện yếu tố tiêu cực bất thường trong các đặc trưng đầu vào.</div></div>`;
  }

  // Retention Recommendations
  const recsList = $('resultRecommendationsList');
  if (res.recommendations && res.recommendations.length) {
    recsList.innerHTML = res.recommendations.map(r => `<li>${escapeHtml(r)}</li>`).join('');
  } else {
    recsList.innerHTML = `<li>Duy trì môi trường làm việc cởi mở và chính sách khen thưởng hiện tại.</li>`;
  }

  $('resultNoticeText').textContent = res.notice || 'Dự báo thống kê hỗ trợ quyết định quản trị nhân sự.';
}

// ==========================================================================
// Prediction History Logic
// ==========================================================================
async function loadHistory() {
  const tbody = $('historyRows');
  if (!tbody) return;

  try {
    const list = await api('/api/predictions/history');

    if (!list.length) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center py-6" style="color: var(--text-muted)">Chưa có lịch sử dự đoán nào được ghi nhận.</td></tr>`;
      return;
    }

    tbody.innerHTML = list.map(item => {
      const isHigh = item.risk_level === 'Cao';
      const isMed = item.risk_level === 'Trung bình';
      const badgeClass = isHigh ? 'badge-risk-high' : isMed ? 'badge-risk-medium' : 'badge-risk-low';

      const timeStr = item.created_at ? new Date(item.created_at).toLocaleString('vi-VN') : '—';
      const pct = (item.probability * 100).toFixed(1) + '%';

      return `
        <tr>
          <td><strong>#${item.id}</strong></td>
          <td>${timeStr}</td>
          <td>
            <div style="display: flex; align-items: center; gap: 8px;">
              <strong>${pct}</strong>
              <div style="width: 60px; height: 6px; background: #e2e8f0; border-radius: 4px; overflow: hidden;">
                <div style="width: ${pct}; height: 100%; background: ${isHigh ? '#ef4444' : isMed ? '#f59e0b' : '#10b981'};"></div>
              </div>
            </div>
          </td>
          <td><span class="badge ${badgeClass}">${escapeHtml(item.risk_level)}</span></td>
          <td><small class="text-muted">${escapeHtml(item.model_name || 'AI Engine')}</small></td>
          <td class="text-right">
            <button class="action-btn delete-btn" title="Xóa bản ghi" onclick="deleteHistoryItem(${item.id})">
              🗑️ Xóa
            </button>
          </td>
        </tr>
      `;
    }).join('');

  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center py-6 danger-text">${escapeHtml(err.message)}</td></tr>`;
  }
}

async function deleteHistoryItem(id) {
  try {
    await api(`/api/predictions/history/${id}`, { method: 'DELETE' });
    showToast(`Đã xóa lượt dự đoán #${id}`);
    loadHistory();
    loadSummary();
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

async function clearAllHistory() {
  if (!confirm('Bạn có chắc chắn muốn xóa toàn bộ lịch sử dự đoán?')) return;
  try {
    await api('/api/predictions/history', { method: 'DELETE' });
    showToast('Đã xóa toàn bộ lịch sử');
    loadHistory();
    loadSummary();
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

function exportHistoryCSV() {
  api('/api/predictions/history').then(list => {
    if (!list.length) {
      showToast('Chưa có dữ liệu lịch sử để xuất', 'warning');
      return;
    }

    const headers = ['Mã lượt', 'Thời gian', 'Xác suất (%)', 'Mức rủi ro', 'Mô hình'];
    const rows = list.map(item => [
      item.id,
      `"${item.created_at || ''}"`,
      (item.probability * 100).toFixed(2),
      `"${item.risk_level || ''}"`,
      `"${item.model_name || ''}"`
    ]);

    const csvContent = "\uFEFF" + [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `lich_su_du_doan_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    showToast('Đã xuất lịch sử dự đoán ra CSV!');
  });
}

// ==========================================================================
// System Status & Seed Data
// ==========================================================================
async function loadSystemStatus() {
  try {
    const data = await api('/api/system/status');
    $('sysDbType').textContent = data.database?.type || 'SQLite';
    $('sysEmpCount').textContent = `${data.database?.total_employees || 0} hồ sơ`;
    $('sysPredCount').textContent = `${data.database?.total_predictions || 0} lượt`;

    if (data.ai_engine?.model_loaded) {
      $('sysModelStatus').innerHTML = '<span class="status-val success">● Sẵn sàng (Ready - Scikit-Learn Joblib)</span>';
      $('sidebarStatusText').textContent = 'AI Model: Ready';
    } else {
      $('sysModelStatus').innerHTML = '<span class="status-val warning">● Đang chạy Chế độ Mô phỏng Heuristic</span>';
      $('sidebarStatusText').textContent = 'AI Model: Heuristic';
    }
  } catch (err) {
    console.error('System status failed:', err);
  }
}

async function seedDemoData() {
  try {
    const res = await api('/api/employees/seed', { method: 'POST' });
    showToast(res.message);
    loadAll();
  } catch (err) {
    showToast(err.message, 'danger');
  }
}

// Global Refresh Helper
function loadAll() {
  loadSummary();
  loadEmployees();
  loadHistory();
  loadSystemStatus();
  showToast('Đã đồng bộ dữ liệu mới nhất!', 'success');
}
