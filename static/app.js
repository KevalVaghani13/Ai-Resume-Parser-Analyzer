const form = document.getElementById('screening-form');
const filesInput = document.getElementById('files');
const jobTitleInput = document.getElementById('job-title');
const jobDescInput = document.getElementById('job-description');
const statusEl = document.getElementById('status');
const runBtn = document.getElementById('run-btn');
const refreshBtn = document.getElementById('refresh-btn');
const clearHistoryBtn = document.getElementById('clear-history-btn');
const resultsBody = document.getElementById('results-body');
const totalCandidatesEl = document.getElementById('total-candidates');
const historyCardsEl = document.getElementById('history-cards');

function setStatus(text, type = '') {
  statusEl.textContent = text;
  statusEl.className = `status ${type}`.trim();
}

function tagList(items, type) {
  if (!items || items.length === 0) return '<span class="tag">-</span>';
  return `<div class="tags">${items.map((x) => `<span class="tag ${type}">${x}</span>`).join('')}</div>`;
}

function renderQuestions(items) {
  if (!items || items.length === 0) {
    return '<li>-</li>';
  }

  return items.slice(0, 3).map((q) => {
    if (typeof q === 'string') {
      return `<li>${q}</li>`;
    }
    // Only render the question text (topic-related). Drop difficulty label from UI.
    const text = q.question || '-';
    return `<li>${text}</li>`;
  }).join('');
}

function renderResults(results) {
  if (!results || results.length === 0) {
    totalCandidatesEl.textContent = '0 candidates';
    resultsBody.innerHTML = '<tr><td colspan="7" class="empty">No candidates matched yet.</td></tr>';
    return;
  }

  totalCandidatesEl.textContent = `${results.length} candidates`;
  resultsBody.innerHTML = results
    .map((r, idx) => {
      const q = renderQuestions(r.suggested_questions || []);
      const breakdown = r.score_breakdown || {};
      const feedback = r.feedback || {};
      
      let feedbackHtml = '';
      if (feedback.strengths && feedback.strengths.length > 0) {
        feedbackHtml += `<div class="fb-item ok">✔ ${feedback.strengths[0]}</div>`;
      }
      if (feedback.weaknesses && feedback.weaknesses.length > 0) {
        feedbackHtml += `<div class="fb-item warn">⚠ ${feedback.weaknesses[0]}</div>`;
      }
      if (feedback.suggestions && feedback.suggestions.length > 0) {
        feedbackHtml += `<div class="fb-item info">💡 ${feedback.suggestions[0]}</div>`;
      }
      
      return `
      <tr>
        <td><strong>${idx + 1}</strong></td>
        <td><strong>${r.candidate_name || r.filename || '-'}</strong></td>
        <td class="score-cell">
          <div class="score-badge">${Number(r.score || 0).toFixed(1)}%</div>
          <div class="score-detail">
            <span>Key: ${Number(breakdown.keyword_score || 0).toFixed(0)}%</span>
            <span>Exp: ${Number(breakdown.experience_relevance || 0).toFixed(0)}%</span>
          </div>
        </td>
        <td>${tagList(r.matched_skills || [], 'ok')}</td>
        <td>${tagList(r.missing_skills || [], 'miss')}</td>
        <td class="feedback-cell">${feedbackHtml || '<span class="tag">-</span>'}</td>
        <td><ol style="margin:0; padding-left:18px;">${q || '<li>-</li>'}</ol></td>
      </tr>
      `;
    })
    .join('');
}

function renderHistory(items) {
  if (!items || items.length === 0) {
    historyCardsEl.innerHTML = '<div class="history-card"><p>No history yet.</p></div>';
    return;
  }

  historyCardsEl.innerHTML = items
    .map((it) => {
      return `
      <article class="history-card">
        <h4>${it.candidate_name || 'Unknown Candidate'}</h4>
        <p><strong>Job:</strong> ${it.job_title || '-'}</p>
        <p><strong>Score:</strong> ${Number(it.score || 0).toFixed(2)}%</p>
        <p><strong>Matched:</strong> ${(it.matched_skills || []).join(', ') || '-'}</p>
        <p><strong>Missing:</strong> ${(it.missing_skills || []).join(', ') || '-'}</p>
      </article>
      `;
    })
    .join('');
}

async function loadHistory() {
  try {
    const res = await fetch('/matches/?limit=20');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderHistory(data.items || []);
  } catch (err) {
    setStatus(`Failed to load history: ${err.message}`, 'error');
  }
}

async function clearHistory() {
  const ok = window.confirm('This will permanently remove stored match history. Continue?');
  if (!ok) return;

  try {
    clearHistoryBtn.disabled = true;
    const res = await fetch('/matches/clear', { method: 'POST' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    resultsBody.innerHTML = '<tr><td colspan="7" class="empty">No analysis yet.</td></tr>';
    totalCandidatesEl.textContent = '0 candidates';
    await loadHistory();
    setStatus('History cleared successfully.', 'ok');
  } catch (err) {
    setStatus(`Failed to clear history: ${err.message}`, 'error');
  } finally {
    clearHistoryBtn.disabled = false;
  }
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const files = filesInput.files;
  if (!files || files.length === 0) {
    setStatus('Please choose at least one resume.', 'error');
    return;
  }

  const fd = new FormData();
  for (const f of files) fd.append('files', f);
  fd.append('job_title', jobTitleInput.value.trim());
  fd.append('job_description', jobDescInput.value.trim());

  runBtn.disabled = true;
  setStatus('Analyzing resumes... This can take a little time for first run.', '');

  try {
    const res = await fetch('/analyze-batch/', {
      method: 'POST',
      body: fd,
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || `HTTP ${res.status}`);
    }

    const data = await res.json();
    renderResults(data.results || []);
    setStatus(`Analysis completed for ${data.total_candidates || 0} candidate(s).`, 'ok');
    await loadHistory();
  } catch (err) {
    setStatus(`Analysis failed: ${err.message}`, 'error');
  } finally {
    runBtn.disabled = false;
  }
});

refreshBtn.addEventListener('click', loadHistory);
clearHistoryBtn.addEventListener('click', clearHistory);

loadHistory();
