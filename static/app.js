(function () {
  // --- Delete confirmation modal ---
  var _form = null;
  var overlay    = document.getElementById('delete-modal');
  var msgEl      = document.getElementById('delete-modal-msg');
  var confirmBtn = document.getElementById('delete-confirm-btn');
  var cancelBtn  = document.getElementById('delete-cancel-btn');

  function showDeleteModal(btn) {
    _form = btn.closest('form');
    msgEl.textContent = btn.dataset.message || 'This action cannot be undone.';
    overlay.removeAttribute('hidden');
    document.body.style.overflow = 'hidden';
    cancelBtn.focus();
  }

  function closeDeleteModal() {
    overlay.setAttribute('hidden', '');
    document.body.style.overflow = '';
    _form = null;
  }

  if (confirmBtn) confirmBtn.addEventListener('click', function () { if (_form) _form.submit(); });
  if (cancelBtn)  cancelBtn.addEventListener('click', closeDeleteModal);
  if (overlay)    overlay.addEventListener('click', function (e) { if (e.target === overlay) closeDeleteModal(); });

  // --- Dash detail modal ---
  var dashModal      = document.getElementById('dash-modal');
  var dashModalClose = document.getElementById('dash-modal-close');

  function openDashModal() {
    if (dashModal) { dashModal.removeAttribute('hidden'); document.body.style.overflow = 'hidden'; }
  }
  function closeDashModal() {
    if (dashModal) { dashModal.setAttribute('hidden', ''); document.body.style.overflow = ''; }
  }

  if (dashModalClose) dashModalClose.addEventListener('click', closeDashModal);
  if (dashModal) dashModal.addEventListener('click', function (e) { if (e.target === dashModal) closeDashModal(); });

  document.body.addEventListener('htmx:beforeRequest', function (e) {
    if (e.detail.target && e.detail.target.id === 'dash-modal-body') {
      e.detail.target.innerHTML = '<p class="detail-loading">Loading…</p>';
      openDashModal();
    }
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      if (overlay && !overlay.hasAttribute('hidden')) closeDeleteModal();
      if (dashModal && !dashModal.hasAttribute('hidden')) closeDashModal();
    }
  });

  // Trigger modal for any button that carries data-message
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('button[data-message]');
    if (btn) showDeleteModal(btn);
  });

  // --- Toggle checkboxes: submit their enclosing form (skip if HTMX handles it) ---
  document.addEventListener('change', function (e) {
    if (e.target.classList.contains('toggle') && e.target.form && !e.target.hasAttribute('hx-post')) {
      e.target.form.submit();
    }
  });

  // --- Shoot search filter ---
  function filterShoots(q) {
    var term = q.toLowerCase();
    document.querySelectorAll('#shoots-tbody tr').forEach(function (row) {
      var cell = row.querySelector('td:first-child');
      var desc = cell ? cell.textContent.toLowerCase() : '';
      row.style.display = desc.includes(term) ? '' : 'none';
    });
  }

  document.addEventListener('input', function (e) {
    if (e.target.id === 'shoot-search') filterShoots(e.target.value);
  });
})();
