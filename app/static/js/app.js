const jobsEl = document.querySelector('#jobs');
const countEl = document.querySelector('#count');
const emptyEl = document.querySelector('#empty');

const escapeHtml = (value = '') => value.replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[char]));

async function loadJobs(params = new URLSearchParams()) {
  jobsEl.innerHTML = '';
  countEl.textContent = 'Loading jobs…';
  const response = await fetch(`/api/v1/jobs?${params}`);
  const data = await response.json();
  countEl.textContent = `${data.total} ${data.total === 1 ? 'role' : 'roles'} found`;
  emptyEl.hidden = data.total !== 0;
  jobsEl.innerHTML = data.items.map(job => `
    <article class="job">
      <span class="tag">${escapeHtml(job.source || 'job board')}</span>
      <h3>${escapeHtml(job.title)}</h3>
      <p class="company">${escapeHtml(job.company)}</p>
      <div class="job-footer"><span>⌖ ${escapeHtml(job.location || 'Flexible')}</span><a href="${escapeHtml(job.url)}" target="_blank" rel="noopener">Apply ↗</a></div>
    </article>`).join('');
}

document.querySelector('#search-form').addEventListener('submit', event => {
  event.preventDefault();
  const params = new URLSearchParams();
  const search = document.querySelector('#search').value.trim();
  const location = document.querySelector('#location').value.trim();
  if (search) params.set('search', search);
  if (location) params.set('location', location);
  loadJobs(params);
});

document.querySelector('#add-form').addEventListener('submit', async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const message = document.querySelector('#form-message');
  const payload = Object.fromEntries(new FormData(form));
  payload.source = 'community';
  const response = await fetch('/api/v1/jobs', {method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload)});
  const result = await response.json();
  if (!response.ok) { message.textContent = result.error || 'Could not save the job.'; return; }
  form.reset();
  message.textContent = 'Job published successfully.';
  loadJobs();
});

loadJobs();
