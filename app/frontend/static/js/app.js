let uploadedBase64Image = null;

document.addEventListener('DOMContentLoaded', () => {
  fetchStats();
  fetchCases();
  setInterval(() => {
    fetchStats();
    fetchCases();
  }, 2500);
});

function handleImagePreview(event) {
  const file = event.target.files[0];
  if (!file) {
    uploadedBase64Image = null;
    return;
  }
  const reader = new FileReader();
  reader.onload = (e) => {
    uploadedBase64Image = e.target.result;
    const preview = document.getElementById('image-preview');
    preview.src = uploadedBase64Image;
    preview.style.display = 'block';
  };
  reader.readAsDataURL(file);
}

async function fetchStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();
    document.getElementById('metric-total').textContent = data.total || 0;
    document.getElementById('metric-open').textContent = data.open || 0;
    document.getElementById('metric-investigating').textContent = data.investigating || 0;
    document.getElementById('metric-awaiting').textContent = data.awaiting_evidence || 0;
    document.getElementById('metric-escalated').textContent = data.escalated || 0;
    document.getElementById('metric-resolved').textContent = data.resolved || 0;
  } catch (err) {
    console.error('Error fetching stats:', err);
  }
}

async function fetchCases() {
  try {
    const res = await fetch('/api/cases');
    const cases = await res.json();
    const tbody = document.getElementById('cases-table-body');
    
    if (!cases || cases.length === 0) {
      return;
    }
    
    tbody.innerHTML = cases.map(c => {
      let badgeClass = 'badge-open';
      if (c.status === 'INVESTIGATING') badgeClass = 'badge-investigating';
      if (c.status === 'AWAITING_EVIDENCE') badgeClass = 'badge-awaiting';
      if (c.status === 'ESCALATED') badgeClass = 'badge-escalated';
      if (c.status === 'RESOLVED' || c.status === 'CLOSED') badgeClass = 'badge-resolved';

      let priorityClass = 'priority-medium';
      if (c.priority === 'HIGH' || c.priority === 'CRITICAL') priorityClass = 'priority-high';
      if (c.priority === 'LOW') priorityClass = 'priority-low';

      return `
        <tr class="clickable-row" onclick="inspectCase('${c.id}')">
          <td style="font-family: var(--font-mono); font-weight: 700; color: #60A5FA;">${c.id}</td>
          <td>${c.category}</td>
          <td class="${priorityClass}">${c.priority}</td>
          <td>${c.responsible_department || 'Unassigned'}</td>
          <td><span class="badge ${badgeClass}">${c.status}</span></td>
          <td style="color: var(--text-muted); font-size: 0.8rem;">${c.last_agent_action || 'Processing'}</td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    console.error('Error fetching cases:', err);
  }
}

async function handleReportSubmit(e) {
  e.preventDefault();
  const desc = document.getElementById('problem-description').value;
  const loc = document.getElementById('location-hint').value;
  const submitBtn = document.getElementById('btn-submit-report');

  submitBtn.disabled = true;
  submitBtn.textContent = '🤖 Agent Analyzing & Dispatching...';

  try {
    const res = await fetch('/api/orchestrator/process-report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        description: desc,
        location: loc,
        image_base64: uploadedBase64Image
      })
    });
    const data = await res.json();
    document.getElementById('report-form').reset();
    document.getElementById('image-preview').style.display = 'none';
    uploadedBase64Image = null;
    await fetchStats();
    await fetchCases();
    if (data.case && data.case.id) {
      inspectCase(data.case.id);
    }
  } catch (err) {
    alert('Failed to dispatch report: ' + err.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = '🚀 Submit & Dispatch Agent';
  }
}

async function runAutonomousDemo() {
  const banner = document.getElementById('demo-banner');
  const bannerTitle = document.getElementById('demo-banner-title');
  const bannerDesc = document.getElementById('demo-banner-desc');
  const btn = document.getElementById('btn-run-demo');

  btn.disabled = true;
  banner.classList.add('active');
  bannerTitle.textContent = '⚡ Running Autonomous Demo...';
  bannerDesc.textContent = '1. Ingesting community report -> 2. Gemini Reasoning -> 3. Catching premature claim -> 4. Rejecting blind trust -> 5. Verifying proof -> 6. Case closure';

  try {
    const res = await fetch('/api/orchestrator/run-demo', { method: 'POST' });
    const data = await res.json();
    bannerTitle.textContent = '✅ Autonomous Demo Completed Successfully!';
    bannerDesc.textContent = `Case ${data.case_id} was successfully verified and closed. All agent audit logs recorded.`;
    await fetchStats();
    await fetchCases();
    if (data.case_id) {
      inspectCase(data.case_id);
    }
  } catch (err) {
    bannerTitle.textContent = '❌ Demo Failed';
    bannerDesc.textContent = err.message;
  } finally {
    btn.disabled = false;
    setTimeout(() => banner.classList.remove('active'), 8000);
  }
}

async function inspectCase(caseId) {
  try {
    const res = await fetch(`/api/cases/${caseId}`);
    const caseData = await res.json();
    
    document.getElementById('modal-case-id').textContent = caseData.id;
    document.getElementById('modal-case-title').textContent = caseData.raw_description;
    document.getElementById('modal-category').textContent = caseData.category;
    document.getElementById('modal-priority').textContent = caseData.priority;
    document.getElementById('modal-status').textContent = caseData.status;
    document.getElementById('modal-department').textContent = caseData.responsible_department || 'Unassigned';

    // Analysis Box
    const analysisBox = document.getElementById('modal-analysis-box');
    if (caseData.analysis) {
      analysisBox.innerHTML = `
        <div><strong>Problem:</strong> ${caseData.analysis.problem_summary}</div>
        <div><strong>Location:</strong> ${caseData.analysis.location}</div>
        <div><strong>Severity:</strong> ${caseData.analysis.severity}</div>
        <div><strong>Missing Evidence Required:</strong> ${caseData.analysis.missing_evidence.join(', ') || 'None'}</div>
        <div style="margin-top: 0.35rem;"><strong>Recommended Actions:</strong> ${caseData.analysis.recommended_actions.join(' &bull; ')}</div>
      `;
    } else {
      analysisBox.textContent = 'Direct submission - Analyzed by heuristic orchestrator.';
    }

    // Evidence Box
    const evidenceBox = document.getElementById('modal-evidence-box');
    if (caseData.evidence && caseData.evidence.length > 0) {
      evidenceBox.innerHTML = caseData.evidence.map(e => `
        <div style="background: #0F172A; padding: 0.5rem; border-radius: 0.35rem; border: 1px solid var(--border-color); font-size: 0.75rem;">
          <div><strong>${e.evidence_type}</strong> (${e.id})</div>
          <div style="color: var(--text-muted);">${e.description}</div>
          ${e.image_base64 ? `<img src="${e.image_base64}" style="max-height: 80px; margin-top: 0.35rem; border-radius: 4px; display: block;" />` : ''}
        </div>
      `).join('');
    } else {
      evidenceBox.innerHTML = '<span style="font-size: 0.8rem; color: var(--text-muted);">No attached media.</span>';
    }

    // Audit Trail
    const auditBox = document.getElementById('modal-audit-trail');
    if (caseData.audit_trail && caseData.audit_trail.length > 0) {
      auditBox.innerHTML = caseData.audit_trail.map(a => {
        let itemClass = '';
        if (a.action.includes('SUCCESS') || a.action.includes('CLOSE')) itemClass = 'success';
        if (a.action.includes('REJECT') || a.action.includes('REQUEST_EVIDENCE')) itemClass = 'reject';
        return `
          <div class="audit-item ${itemClass}">
            <span style="color: var(--text-muted);">${a.timestamp.slice(11, 19)}</span>
            <strong style="color: #93C5FD;">[${a.actor}]</strong>
            <span style="color: #FCD34D;">${a.action}</span>:
            <span>${a.details}</span>
          </div>
        `;
      }).join('');
    }

    document.getElementById('case-modal').classList.add('active');
  } catch (err) {
    console.error('Error loading case modal:', err);
  }
}

function closeModal(event) {
  if (!event || event.target.id === 'case-modal' || event.target.classList.contains('modal-close')) {
    document.getElementById('case-modal').classList.remove('active');
  }
}
