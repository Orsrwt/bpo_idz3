const API = 'http://localhost:8000';

async function apiFetch(path, opts = {}) {
  const res = await fetch(API + path, {
    headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
    ...opts,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

function showSection(name) {
  document.querySelectorAll('.section').forEach(el => el.classList.add('hidden'));
  document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
  document.getElementById(`section-${name}`).classList.remove('hidden');
  document.querySelector(`.nav-link[data-section="${name}"]`).classList.add('active');
  loaders[name] && loaders[name]();
}

document.querySelectorAll('.nav-link').forEach(link => {
  link.addEventListener('click', e => {
    e.preventDefault();
    showSection(link.dataset.section);
  });
});

function escHtml(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function actionBtns(editCb, deleteCb) {
  const wrap = document.createElement('td');
  wrap.className = 'px-4 py-3 text-right';
  wrap.innerHTML = `
    <button class="text-xs text-accent hover:underline mr-3 edit-btn">Изменить</button>
    <button class="text-xs text-red-500 hover:underline delete-btn">Удалить</button>`;
  wrap.querySelector('.edit-btn').addEventListener('click', editCb);
  wrap.querySelector('.delete-btn').addEventListener('click', deleteCb);
  return wrap;
}

let targetsCache = [];
let templatesCache = [];

async function loadTargets() {
  targetsCache = await apiFetch('/api/targets');
  const tbody = document.getElementById('targets-table-body');
  const empty = document.getElementById('targets-empty');
  tbody.innerHTML = '';
  if (!targetsCache.length) {
    empty.classList.remove('hidden');
    return;
  }
  empty.classList.add('hidden');
  targetsCache.forEach(t => {
    const tr = document.createElement('tr');
    tr.className = 'hover:bg-gray-50';
    tr.innerHTML = `
      <td class="px-4 py-3">${escHtml(t.last_name)}</td>
      <td class="px-4 py-3">${escHtml(t.first_name)}</td>
      <td class="px-4 py-3 text-gray-500">${escHtml(t.patronymic || '—')}</td>
      <td class="px-4 py-3">${escHtml(t.email)}</td>`;
    tr.appendChild(actionBtns(
      () => openTargetForm(t),
      async () => {
        if (confirm('Удалить цель?')) {
          await apiFetch(`/api/targets/${t.id}`, { method: 'DELETE' });
          loadTargets();
        }
      }
    ));
    tbody.appendChild(tr);
  });
}

function openTargetForm(target = null) {
  document.getElementById('target-form-title').textContent = target ? 'Редактировать цель' : 'Новая цель';
  document.getElementById('target-last-name').value = target?.last_name || '';
  document.getElementById('target-first-name').value = target?.first_name || '';
  document.getElementById('target-patronymic').value = target?.patronymic || '';
  document.getElementById('target-email').value = target?.email || '';
  document.getElementById('target-edit-id').value = target?.id || '';
  document.getElementById('target-form-wrap').classList.remove('hidden');
}

document.getElementById('btn-add-target').addEventListener('click', () => openTargetForm());
document.getElementById('btn-cancel-target').addEventListener('click', () => {
  document.getElementById('target-form-wrap').classList.add('hidden');
});
document.getElementById('btn-save-target').addEventListener('click', async () => {
  const id = document.getElementById('target-edit-id').value;
  const body = {
    last_name: document.getElementById('target-last-name').value.trim(),
    first_name: document.getElementById('target-first-name').value.trim(),
    patronymic: document.getElementById('target-patronymic').value.trim() || null,
    email: document.getElementById('target-email').value.trim(),
  };
  try {
    if (id) {
      await apiFetch(`/api/targets/${id}`, { method: 'PUT', body: JSON.stringify(body) });
    } else {
      await apiFetch('/api/targets', { method: 'POST', body: JSON.stringify(body) });
    }
    document.getElementById('target-form-wrap').classList.add('hidden');
    loadTargets();
  } catch (e) {
    alert('Ошибка: ' + e.message);
  }
});

async function loadTemplates() {
  templatesCache = await apiFetch('/api/templates');
  const tbody = document.getElementById('templates-table-body');
  const empty = document.getElementById('templates-empty');
  tbody.innerHTML = '';
  if (!templatesCache.length) {
    empty.classList.remove('hidden');
    return;
  }
  empty.classList.add('hidden');
  templatesCache.forEach(t => {
    const tr = document.createElement('tr');
    tr.className = 'hover:bg-gray-50';
    tr.innerHTML = `
      <td class="px-4 py-3 text-gray-400 text-xs">${t.id}</td>
      <td class="px-4 py-3 font-medium">${escHtml(t.name)}</td>`;
    tr.appendChild(actionBtns(
      () => openTemplateForm(t),
      async () => {
        if (confirm('Удалить шаблон?')) {
          await apiFetch(`/api/templates/${t.id}`, { method: 'DELETE' });
          loadTemplates();
        }
      }
    ));
    tbody.appendChild(tr);
  });
}

function openTemplateForm(tmpl = null) {
  document.getElementById('template-form-title').textContent = tmpl ? 'Редактировать шаблон' : 'Новый шаблон';
  document.getElementById('template-name').value = tmpl?.name || '';
  document.getElementById('template-html').value = tmpl?.html_content || '';
  document.getElementById('template-edit-id').value = tmpl?.id || '';
  document.getElementById('template-form-wrap').classList.remove('hidden');
}

document.getElementById('btn-add-template').addEventListener('click', () => openTemplateForm());
document.getElementById('btn-cancel-template').addEventListener('click', () => {
  document.getElementById('template-form-wrap').classList.add('hidden');
});
document.getElementById('btn-save-template').addEventListener('click', async () => {
  const id = document.getElementById('template-edit-id').value;
  const body = {
    name: document.getElementById('template-name').value.trim(),
    html_content: document.getElementById('template-html').value,
  };
  try {
    if (id) {
      await apiFetch(`/api/templates/${id}`, { method: 'PUT', body: JSON.stringify(body) });
    } else {
      await apiFetch('/api/templates', { method: 'POST', body: JSON.stringify(body) });
    }
    document.getElementById('template-form-wrap').classList.add('hidden');
    loadTemplates();
  } catch (e) {
    alert('Ошибка: ' + e.message);
  }
});

async function loadCampaignForm() {
  const [templates, targets, landings] = await Promise.all([
    apiFetch('/api/templates'),
    apiFetch('/api/targets'),
    apiFetch('/api/landings'),
  ]);
  templatesCache = templates;
  targetsCache = targets;

  const tSelect = document.getElementById('camp-template');
  tSelect.innerHTML = '<option value="">— выберите шаблон —</option>';
  templates.forEach(t => {
    const o = document.createElement('option');
    o.value = t.id;
    o.textContent = t.name;
    tSelect.appendChild(o);
  });

  const lSelect = document.getElementById('camp-landing');
  lSelect.innerHTML = '';
  landings.forEach(l => {
    const o = document.createElement('option');
    o.value = l.slug;
    o.textContent = l.name;
    lSelect.appendChild(o);
  });

  const tList = document.getElementById('camp-targets-list');
  tList.innerHTML = '';
  if (!targets.length) {
    tList.innerHTML = '<span class="text-gray-400">Нет добавленных целей</span>';
    return;
  }
  targets.forEach(t => {
    const label = document.createElement('label');
    label.className = 'flex items-center gap-2 cursor-pointer';
    label.innerHTML = `
      <input type="checkbox" value="${t.id}" class="w-4 h-4 accent-blue-600" />
      <span>${escHtml(t.last_name)} ${escHtml(t.first_name)}${t.patronymic ? ' ' + escHtml(t.patronymic) : ''} <span class="text-gray-400">&lt;${escHtml(t.email)}&gt;</span></span>`;
    tList.appendChild(label);
  });
}

document.getElementById('btn-launch-campaign').addEventListener('click', async () => {
  const name = document.getElementById('camp-name').value.trim();
  const senderName = document.getElementById('camp-sender-name').value.trim();
  const senderEmail = document.getElementById('camp-sender-email').value.trim();
  const templateId = parseInt(document.getElementById('camp-template').value);
  const landingSlug = document.getElementById('camp-landing').value;
  const checkedBoxes = document.querySelectorAll('#camp-targets-list input[type=checkbox]:checked');
  const targetIds = Array.from(checkedBoxes).map(cb => parseInt(cb.value));

  if (!name || !senderName || !senderEmail || !templateId || !landingSlug || !targetIds.length) {
    alert('Заполните все поля и выберите хотя бы одну цель.');
    return;
  }

  const btn = document.getElementById('btn-launch-campaign');
  btn.disabled = true;
  btn.textContent = 'Отправка...';

  const resultEl = document.getElementById('campaign-result');
  try {
    const camp = await apiFetch('/api/campaigns', {
      method: 'POST',
      body: JSON.stringify({
        name,
        sender_name: senderName,
        sender_email: senderEmail,
        template_id: templateId,
        landing_slug: landingSlug,
        target_ids: targetIds,
      }),
    });
    resultEl.className = 'mt-4 p-4 rounded-lg text-sm bg-green-50 border border-green-200 text-green-800';
    resultEl.textContent = `Кампания "${camp.name}" запущена (ID: ${camp.id}). Отправлено писем: ${targetIds.length}.`;
    resultEl.classList.remove('hidden');
    document.getElementById('camp-name').value = '';
    checkedBoxes.forEach(cb => cb.checked = false);
  } catch (e) {
    resultEl.className = 'mt-4 p-4 rounded-lg text-sm bg-red-50 border border-red-200 text-red-700';
    resultEl.textContent = 'Ошибка: ' + e.message;
    resultEl.classList.remove('hidden');
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> Запустить атаку`;
  }
});

const STATUS_LABELS = {
  sent: 'Отправлено',
  clicked: 'Переход по ссылке',
  submitted: 'Данные введены',
};

const STATUS_ORDER = ['sent', 'clicked', 'submitted'];

async function loadReports() {
  const campaigns = await apiFetch('/api/campaigns');
  const container = document.getElementById('reports-list');
  const empty = document.getElementById('reports-empty');
  container.innerHTML = '';
  if (!campaigns.length) {
    empty.classList.remove('hidden');
    return;
  }
  empty.classList.add('hidden');

  for (const camp of campaigns) {
    const report = await apiFetch(`/api/campaigns/${camp.id}/report`);
    const card = document.createElement('div');
    card.className = 'border border-gray-200 rounded-lg overflow-hidden';

    const convRate = report.total > 0 ? Math.round((report.submitted / report.total) * 100) : 0;

    card.innerHTML = `
      <div class="bg-gray-50 border-b border-gray-200 px-5 py-4">
        <div class="flex items-start justify-between mb-3">
          <div>
            <span class="font-semibold text-sm">${escHtml(camp.name)}</span>
            <span class="ml-3 text-xs text-gray-400">от: ${escHtml(camp.sender_name)} &lt;${escHtml(camp.sender_email)}&gt;</span>
            <span class="ml-3 text-xs text-gray-400">лендинг: ${camp.landing_slug === 'vk' ? 'ВКонтакте' : 'Mail.ru'}</span>
          </div>
          <span class="text-xs text-gray-400">Конверсия: <strong class="text-gray-700">${convRate}%</strong></span>
        </div>
        <div class="flex gap-3 text-xs">
          <span class="px-2.5 py-1 rounded-md status-sent font-medium">Отправлено: ${report.total}</span>
          <span class="px-2.5 py-1 rounded-md status-clicked font-medium">Перешли по ссылке: ${report.clicked}</span>
          <span class="px-2.5 py-1 rounded-md status-submitted font-medium">Ввели данные: ${report.submitted}</span>
        </div>
      </div>
      <table class="w-full text-sm">
        <thead class="bg-white border-b border-gray-100">
          <tr>
            <th class="text-left px-4 py-2.5 font-medium text-gray-600 text-xs">Цель</th>
            <th class="text-left px-4 py-2.5 font-medium text-gray-600 text-xs">Email</th>
            <th class="text-left px-4 py-2.5 font-medium text-gray-600 text-xs">Статус</th>
            <th class="text-left px-4 py-2.5 font-medium text-gray-600 text-xs">Введённые данные</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          ${report.stats.map(s => `
            <tr class="hover:bg-gray-50">
              <td class="px-4 py-2.5 font-medium">${escHtml(s.full_name)}</td>
              <td class="px-4 py-2.5 text-gray-500">${escHtml(s.email)}</td>
              <td class="px-4 py-2.5">
                <span class="px-2 py-0.5 rounded text-xs status-${s.status}">${STATUS_LABELS[s.status] || s.status}</span>
              </td>
              <td class="px-4 py-2.5 text-xs text-gray-500 font-mono">
                ${s.submitted_data
                  ? Object.entries(s.submitted_data).map(([k, v]) =>
                      `<span class="inline-block mr-3"><span class="text-gray-400">${escHtml(k)}:</span> ${escHtml(v)}</span>`
                    ).join('')
                  : '<span class="text-gray-300">—</span>'}
              </td>
            </tr>`).join('')}
        </tbody>
      </table>`;
    container.appendChild(card);
  }
}

const loaders = {
  targets: loadTargets,
  templates: loadTemplates,
  campaigns: loadCampaignForm,
  reports: loadReports,
};

showSection('targets');
