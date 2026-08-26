/**
 * The Lenny Growth Assistant — Client Application Logic
 */

(function () {
  'use strict';

  // ---------------------------------------------------------------------------
  // State
  // ---------------------------------------------------------------------------
  const state = {
    activeSessionId: null,
    activeProvider: 'ollama', // Default: Local (Ollama)
    sessions: [],
    currentArtifact: null,
    isLoading: false,
    abortController: null,
  };

  // ---------------------------------------------------------------------------
  // DOM Elements
  // ---------------------------------------------------------------------------
  const elements = {
    // Nav & Provider
    sessionsToggleBtn: document.getElementById('sessionsToggleBtn'),
    sessionCountBadge: document.getElementById('sessionCountBadge'),
    providerSelector: document.querySelector('.provider-selector'),
    providerLocalBtn: document.getElementById('providerLocalBtn'),
    providerCloudBtn: document.getElementById('providerCloudBtn'),
    activeProviderLabel: document.getElementById('activeProviderLabel'),

    // Workspace & Messages
    activeSessionTitle: document.getElementById('activeSessionTitle'),
    newChatTopBtn: document.getElementById('newChatTopBtn'),
    messagesContainer: document.getElementById('messagesContainer'),
    chatThread: document.getElementById('chatThread'),
    emptyState: document.getElementById('emptyState'),
    suggestionChips: document.querySelectorAll('.chip'),

    // Composer
    chatForm: document.getElementById('chatForm'),
    promptInput: document.getElementById('promptInput'),
    sendBtn: document.getElementById('sendBtn'),
    stopBtn: document.getElementById('stopBtn'),
    contextChipsContainer: document.getElementById('contextChipsContainer'),

    // Session Drawer
    sessionDrawer: document.getElementById('sessionDrawer'),
    drawerBackdrop: document.getElementById('drawerBackdrop'),
    closeDrawerBtn: document.getElementById('closeDrawerBtn'),
    newChatDrawerBtn: document.getElementById('newChatDrawerBtn'),
    deleteAllChatsBtn: document.getElementById('deleteAllChatsBtn'),
    sessionList: document.getElementById('sessionList'),

    // Artifact Modal
    artifactModal: document.getElementById('artifactModal'),
    artifactModalBackdrop: document.getElementById('artifactModalBackdrop'),
    modalArtifactBadge: document.getElementById('modalArtifactBadge'),
    modalSanitizedBadge: document.getElementById('modalSanitizedBadge'),
    modalArtifactTitle: document.getElementById('modalArtifactTitle'),
    downloadArtifactBtn: document.getElementById('downloadArtifactBtn'),
    downloadBtnLabel: document.getElementById('downloadBtnLabel'),
    closeModalBtn: document.getElementById('closeModalBtn'),
    artifactIframe: document.getElementById('artifactIframe'),
    markdownArtifactContainer: document.getElementById('markdownArtifactContainer'),
    rejectedArtifactView: document.getElementById('rejectedArtifactView'),
    rejectedReason: document.getElementById('rejectedReason'),

    // Confirmation Dialogs (Delete & Rename)
    confirmModalBackdrop: document.getElementById('confirmModalBackdrop'),
    confirmDialog: document.getElementById('confirmDialog'),
    confirmCancelBtn: document.getElementById('confirmCancelBtn'),
    confirmDeleteBtn: document.getElementById('confirmDeleteBtn'),

    renameModalBackdrop: document.getElementById('renameModalBackdrop'),
    renameDialog: document.getElementById('renameDialog'),
    renameInput: document.getElementById('renameInput'),
    renameCancelBtn: document.getElementById('renameCancelBtn'),
    renameSaveBtn: document.getElementById('renameSaveBtn'),

    // Toast Container
    toastContainer: document.getElementById('toastContainer'),
  };

  // ---------------------------------------------------------------------------
  // Toast Notifications
  // ---------------------------------------------------------------------------
  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    elements.toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 4500);
  }

  // ---------------------------------------------------------------------------
  // Provider Selection (Local ● Cloud)
  // ---------------------------------------------------------------------------
  function setProvider(provider) {
    state.activeProvider = provider;
    try {
      localStorage.setItem('lenny_active_provider', provider);
    } catch {}

    if (provider === 'gemini') {
      elements.providerSelector.classList.add('cloud-active');
      elements.providerCloudBtn.classList.add('active');
      elements.providerCloudBtn.setAttribute('aria-checked', 'true');
      elements.providerLocalBtn.classList.remove('active');
      elements.providerLocalBtn.setAttribute('aria-checked', 'false');
      elements.activeProviderLabel.textContent = 'Cloud (Gemini 2.5 Flash)';
    } else {
      elements.providerSelector.classList.remove('cloud-active');
      elements.providerLocalBtn.classList.add('active');
      elements.providerLocalBtn.setAttribute('aria-checked', 'true');
      elements.providerCloudBtn.classList.remove('active');
      elements.providerCloudBtn.setAttribute('aria-checked', 'false');
      elements.activeProviderLabel.textContent = 'Local (Ollama)';
    }
  }

  // ---------------------------------------------------------------------------
  // Session Drawer Management
  // ---------------------------------------------------------------------------
  function openDrawer() {
    elements.sessionDrawer.classList.add('open');
    elements.sessionDrawer.setAttribute('aria-hidden', 'false');
    elements.drawerBackdrop.classList.add('open');
    elements.drawerBackdrop.setAttribute('aria-hidden', 'false');
    loadSessions();
  }

  function closeDrawer() {
    elements.sessionDrawer.classList.remove('open');
    elements.sessionDrawer.setAttribute('aria-hidden', 'true');
    elements.drawerBackdrop.classList.remove('open');
    elements.drawerBackdrop.setAttribute('aria-hidden', 'true');
    closeAllDropdowns();
  }

  function closeAllDropdowns() {
    document.querySelectorAll('.session-dropdown.open').forEach((d) => d.classList.remove('open'));
  }

  async function loadSessions() {
    try {
      const res = await fetch('/sessions');
      if (!res.ok) return;
      const data = await res.json();
      state.sessions = data || [];
      elements.sessionCountBadge.textContent = state.sessions.length;
      renderSessionList();
    } catch (err) {
      console.warn('Failed to fetch sessions:', err);
    }
  }

  function renderSessionList() {
    elements.sessionList.innerHTML = '';
    if (state.sessions.length === 0) {
      elements.sessionList.innerHTML = '<p style="color: var(--text-muted); font-size: 0.85rem; padding: 1rem 0; text-align: center;">No previous conversations found.</p>';
      return;
    }

    state.sessions.forEach((s) => {
      const item = document.createElement('div');
      item.className = `session-item ${s.session_id === state.activeSessionId ? 'active' : ''}`;
      const title = s.metadata?.title || `Session ${s.session_id.substring(8, 16)}`;
      const dateStr = s.updated_at ? new Date(s.updated_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) : '';
      const count = s.message_count || 0;

      item.innerHTML = `
        <div class="session-item-header">
          <span class="session-item-title">${escapeHtml(title)}</span>
          <button type="button" class="session-menu-btn" title="Session Options" aria-label="Session Options">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
              <circle cx="12" cy="5" r="2"></circle>
              <circle cx="12" cy="12" r="2"></circle>
              <circle cx="12" cy="19" r="2"></circle>
            </svg>
          </button>
        </div>
        <div class="session-dropdown" id="dropdown-${s.session_id}">
          <button type="button" class="dropdown-item rename">
            <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 20h9"></path>
              <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
            </svg>
            <span>Rename</span>
          </button>
          <button type="button" class="dropdown-item delete">
            <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"></polyline>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
            <span>Delete</span>
          </button>
        </div>
        <div class="session-item-meta">
          <span>${dateStr}</span>
          <span>${count} msg${count === 1 ? '' : 's'}</span>
        </div>
      `;

      // Select Session on click (excluding menu clicks)
      item.addEventListener('click', (e) => {
        if (e.target.closest('.session-menu-btn') || e.target.closest('.session-dropdown')) {
          return;
        }
        selectSession(s.session_id, title);
        closeDrawer();
      });

      // Three dots toggle
      const menuBtn = item.querySelector('.session-menu-btn');
      const dropdown = item.querySelector('.session-dropdown');

      menuBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = dropdown.classList.contains('open');
        closeAllDropdowns();
        if (!isOpen) {
          dropdown.classList.add('open');
          // Check if dropdown extends near bottom of drawer-list
          const rect = dropdown.getBoundingClientRect();
          const drawerRect = elements.sessionDrawer.getBoundingClientRect();
          if (rect.bottom > drawerRect.bottom - 20) {
            dropdown.classList.add('dropup');
          } else {
            dropdown.classList.remove('dropup');
          }
        }
      });

      // Rename Action
      const renameBtn = item.querySelector('.dropdown-item.rename');
      renameBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        closeAllDropdowns();
        const newTitle = await showRenameDialog(title);
        if (newTitle && newTitle.trim() && newTitle.trim() !== title) {
          await renameSession(s.session_id, newTitle.trim());
        }
      });

      // Delete Action
      const deleteBtn = item.querySelector('.dropdown-item.delete');
      deleteBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        closeAllDropdowns();
        const confirmed = await showDeleteConfirmationDialog();
        if (confirmed) {
          await deleteSession(s.session_id);
        }
      });

      elements.sessionList.appendChild(item);
    });
  }

  // ---------------------------------------------------------------------------
  // Custom Rename Modal
  // ---------------------------------------------------------------------------
  function showRenameDialog(currentTitle = '') {
    return new Promise((resolve) => {
      const backdrop = elements.renameModalBackdrop || document.getElementById('renameModalBackdrop');
      const dialog = elements.renameDialog || document.getElementById('renameDialog');
      const input = elements.renameInput || document.getElementById('renameInput');
      const cancelBtn = elements.renameCancelBtn || document.getElementById('renameCancelBtn');
      const saveBtn = elements.renameSaveBtn || document.getElementById('renameSaveBtn');

      if (!dialog || !backdrop || !input || !cancelBtn || !saveBtn) {
        resolve(window.prompt('Enter new conversation title:', currentTitle));
        return;
      }

      input.value = currentTitle;

      function cleanup() {
        dialog.classList.remove('open');
        backdrop.classList.remove('open');
        dialog.setAttribute('aria-hidden', 'true');
        backdrop.setAttribute('aria-hidden', 'true');
        cancelBtn.removeEventListener('click', onCancel);
        saveBtn.removeEventListener('click', onSave);
        backdrop.removeEventListener('click', onCancel);
        input.removeEventListener('keydown', onInputKeyDown);
        document.removeEventListener('keydown', onGlobalKeyDown);
      }

      function onCancel() {
        cleanup();
        resolve(null);
      }

      function onSave() {
        const val = input.value.trim();
        cleanup();
        resolve(val ? val : null);
      }

      function onInputKeyDown(e) {
        if (e.key === 'Enter') {
          e.preventDefault();
          onSave();
        }
      }

      function onGlobalKeyDown(e) {
        if (e.key === 'Escape') {
          onCancel();
        }
      }

      cancelBtn.addEventListener('click', onCancel);
      saveBtn.addEventListener('click', onSave);
      backdrop.addEventListener('click', onCancel);
      input.addEventListener('keydown', onInputKeyDown);
      document.addEventListener('keydown', onGlobalKeyDown);

      backdrop.classList.add('open');
      dialog.classList.add('open');
      dialog.setAttribute('aria-hidden', 'false');
      backdrop.setAttribute('aria-hidden', 'false');

      setTimeout(() => {
        input.focus();
        input.select();
      }, 50);
    });
  }

  // ---------------------------------------------------------------------------
  // Custom Delete Confirmation Modal
  // ---------------------------------------------------------------------------
  function showDeleteConfirmationDialog(
    title = 'Delete this conversation?',
    desc = 'This will permanently remove the chat and its messages. You won’t be able to recover it.'
  ) {
    return new Promise((resolve) => {
      const backdrop = elements.confirmModalBackdrop || document.getElementById('confirmModalBackdrop');
      const dialog = elements.confirmDialog || document.getElementById('confirmDialog');
      const titleEl = document.getElementById('confirmTitle');
      const descEl = document.getElementById('confirmDesc');
      const cancelBtn = elements.confirmCancelBtn || document.getElementById('confirmCancelBtn');
      const deleteBtn = elements.confirmDeleteBtn || document.getElementById('confirmDeleteBtn');

      if (!dialog || !backdrop || !cancelBtn || !deleteBtn) {
        resolve(window.confirm(title));
        return;
      }

      if (titleEl) titleEl.textContent = title;
      if (descEl) descEl.textContent = desc;

      function cleanup() {
        dialog.classList.remove('open');
        backdrop.classList.remove('open');
        dialog.setAttribute('aria-hidden', 'true');
        backdrop.setAttribute('aria-hidden', 'true');
        cancelBtn.removeEventListener('click', onCancel);
        deleteBtn.removeEventListener('click', onConfirm);
        backdrop.removeEventListener('click', onCancel);
        document.removeEventListener('keydown', onKeyDown);
      }

      function onCancel() {
        cleanup();
        resolve(false);
      }

      function onConfirm() {
        cleanup();
        resolve(true);
      }

      function onKeyDown(e) {
        if (e.key === 'Escape') {
          onCancel();
        }
      }

      cancelBtn.addEventListener('click', onCancel);
      deleteBtn.addEventListener('click', onConfirm);
      backdrop.addEventListener('click', onCancel);
      document.addEventListener('keydown', onKeyDown);

      backdrop.classList.add('open');
      dialog.classList.add('open');
      dialog.setAttribute('aria-hidden', 'false');
      backdrop.setAttribute('aria-hidden', 'false');
      cancelBtn.focus();
    });
  }

  async function renameSession(sessionId, newTitle) {
    try {
      const res = await fetch(`/sessions/${sessionId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTitle }),
      });

      if (!res.ok) {
        showToast('Failed to rename session.', 'error');
        return;
      }

      if (state.activeSessionId === sessionId) {
        elements.activeSessionTitle.textContent = newTitle;
      }
      showToast('Conversation renamed.');
      await loadSessions();
    } catch (err) {
      showToast('Network error renaming session.', 'error');
    }
  }

  async function deleteSession(sessionId) {
    try {
      const res = await fetch(`/sessions/${sessionId}`, {
        method: 'DELETE',
      });

      if (!res.ok) {
        showToast('Failed to delete session.', 'error');
        return;
      }

      showToast('Conversation deleted.');
      try {
        if (localStorage.getItem('lenny_active_session_id') === sessionId) {
          localStorage.removeItem('lenny_active_session_id');
        }
      } catch {}
      if (state.activeSessionId === sessionId) {
        startNewConversation();
      }
      await loadSessions();
    } catch (err) {
      showToast('Network error deleting session.', 'error');
    }
  }

  async function deleteAllSessions() {
    if (!state.sessions || state.sessions.length === 0) {
      showToast('No conversations to delete.');
      return;
    }
    const confirmed = await showDeleteConfirmationDialog(
      'Delete all conversations?',
      'Are you sure you want to delete all stored conversations? This action cannot be undone.'
    );
    if (!confirmed) return;

    try {
      const res = await fetch('/sessions', { method: 'DELETE' });
      if (!res.ok) {
        showToast('Failed to delete all conversations.', 'error');
        return;
      }
      try {
        localStorage.removeItem('lenny_active_session_id');
      } catch {}
      showToast('All conversations deleted.');
      startNewConversation();
      await loadSessions();
    } catch (err) {
      showToast('Network error deleting conversations.', 'error');
    }
  }

  // ---------------------------------------------------------------------------
  // Contextual Follow-up Chips (Directly Above Input Box)
  // ---------------------------------------------------------------------------
  function showContextChips(chips) {
    if (!elements.contextChipsContainer) return;
    if (!chips || chips.length === 0) {
      elements.contextChipsContainer.style.display = 'none';
      elements.contextChipsContainer.innerHTML = '';
      return;
    }
    elements.contextChipsContainer.innerHTML = '';
    chips.forEach((promptText) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'context-chip';
      btn.innerHTML = `<span>&ldquo;${escapeHtml(promptText)}&rdquo;</span>`;
      btn.addEventListener('click', () => {
        elements.promptInput.value = promptText;
        elements.promptInput.focus();
        handleSendMessage();
      });
      elements.contextChipsContainer.appendChild(btn);
    });
    elements.contextChipsContainer.style.display = 'flex';
  }

  function hideContextChips() {
    if (elements.contextChipsContainer) {
      elements.contextChipsContainer.style.display = 'none';
      elements.contextChipsContainer.innerHTML = '';
    }
  }

  function generateContextualChips(userPrompt, assistantResponse, sources) {
    const combined = ((userPrompt || '') + ' ' + (assistantResponse || '')).toLowerCase();
    const suggestions = [];

    if (combined.includes('pmf') || combined.includes('product-market fit') || combined.includes('product market fit') || combined.includes('market fit')) {
      suggestions.push('What are key metrics for PMF?');
      suggestions.push('Which guests share PMF stories?');
      suggestions.push('Turn this into a Ship 30 essay');
    } else if (combined.includes('mvp') || combined.includes('minimum viable') || combined.includes('prototype')) {
      suggestions.push('What are common MVP mistakes?');
      suggestions.push('How fast should we build an MVP?');
      suggestions.push('Turn what we learned into an essay');
    } else if (combined.includes('retention') || combined.includes('churn') || combined.includes('growth loop') || combined.includes('growth')) {
      suggestions.push('How to improve 30-day retention?');
      suggestions.push('What are top B2B growth loops?');
      suggestions.push('Summarize key growth takeaways');
    } else if (combined.includes('pricing') || combined.includes('monetization')) {
      suggestions.push('How often should pricing change?');
      suggestions.push('What is the best pricing model?');
      suggestions.push('Write a Ship 30 essay on pricing');
    } else if (combined.includes('hire') || combined.includes('hiring') || combined.includes('interview')) {
      suggestions.push('How to interview a founding PM?');
      suggestions.push('What traits make a great PM?');
      suggestions.push('Turn hiring lessons into an essay');
    } else if (combined.includes('burnout') || combined.includes('mental health')) {
      suggestions.push('What are early burnout warning signs?');
      suggestions.push('How do founders recover from burnout?');
      suggestions.push('Turn this into an essay');
    } else {
      const guestNames = (sources || []).map((s) => s.guest).filter(Boolean);
      if (guestNames.length > 0) {
        suggestions.push(`What else does ${guestNames[0]} recommend?`);
        suggestions.push('Turn what we learned into a Ship 30 essay');
        suggestions.push('Create a visual HTML card for this');
      } else {
        suggestions.push('What are the key takeaways?');
        suggestions.push('Turn what we learned into a Ship 30 essay');
        suggestions.push('What do other guests say?');
      }
    }
    return suggestions.slice(0, 3);
  }

  async function selectSession(sessionId, title = '') {
    state.activeSessionId = sessionId;
    try {
      localStorage.setItem('lenny_active_session_id', sessionId);
    } catch {}

    elements.activeSessionTitle.textContent = title || `Session ${sessionId.substring(8, 16)}`;
    if (elements.chatThread) {
      elements.chatThread.innerHTML = '';
    }
    if (elements.emptyState) {
      elements.emptyState.style.display = 'none';
    }
    hideContextChips();

    try {
      const res = await fetch(`/sessions/${sessionId}/messages`);
      if (!res.ok) {
        showToast('Could not load session history.', 'error');
        return;
      }
      const messages = await res.json();
      if (messages.length === 0) {
        if (elements.emptyState) {
          elements.emptyState.style.display = 'flex';
        }
      } else {
        let lastUserMsg = '';
        let lastAssistantMsg = '';
        let lastSources = [];
        messages.forEach((m) => {
          if (m.role === 'user') {
            lastUserMsg = m.content;
            appendUserMessage(m.content);
          } else {
            lastAssistantMsg = m.content;
            const meta = m.metadata || {};
            lastSources = meta.sources || [];
            appendAssistantMessage({
              response: m.content,
              provider: meta.provider || state.activeProvider,
              model: meta.model || '',
              sources: meta.sources || [],
              artifact: meta.artifact || null,
            });
          }
        });
        const chips = generateContextualChips(lastUserMsg, lastAssistantMsg, lastSources);
        showContextChips(chips);
        scrollToBottom();
      }
    } catch (err) {
      showToast('Network error loading messages.', 'error');
    }
  }

  function startNewConversation() {
    state.activeSessionId = null;
    try {
      localStorage.removeItem('lenny_active_session_id');
    } catch {}
    elements.activeSessionTitle.textContent = 'New Conversation';
    if (elements.chatThread) {
      elements.chatThread.innerHTML = '';
    }
    if (elements.emptyState) {
      elements.emptyState.style.display = 'flex';
    }
    hideContextChips();
    elements.promptInput.value = '';
    elements.promptInput.focus();
    closeDrawer();
  }

  // ---------------------------------------------------------------------------
  // Message Rendering
  // ---------------------------------------------------------------------------
  function appendUserMessage(text) {
    if (elements.emptyState) {
      elements.emptyState.style.display = 'none';
    }
    hideContextChips();
    const row = document.createElement('div');
    row.className = 'message-row user';
    row.innerHTML = `<div class="user-bubble">${escapeHtml(text)}</div>`;
    const target = elements.chatThread || elements.messagesContainer;
    target.appendChild(row);
    scrollToBottom();
  }

  function appendAssistantMessage(data) {
    if (elements.emptyState) {
      elements.emptyState.style.display = 'none';
    }
    const row = document.createElement('div');
    row.className = 'message-row assistant';

    const providerName = data.provider === 'gemini' ? 'Gemini 2.5 Flash' : (data.model || 'Ollama Local');
    let responseText = data.response || '';
    if (data.artifact && data.artifact.type === 'html') {
      responseText = responseText
        .replace(/```(?:html)?\s*[\s\S]*?```/gi, '')
        .replace(/<!DOCTYPE[\s\S]*?<\/html>/gi, '')
        .replace(/<html[\s\S]*?<\/html>/gi, '')
        .replace(/<style[\s\S]*?<\/style>/gi, '')
        .replace(/<body[\s\S]*?<\/body>/gi, '')
        .replace(/<div[\s\S]*?<\/div>/gi, '')
        .replace(/<\/?(header|footer|main|section|article|p|span|h[1-6]|div|body|html|head|meta|link|style)[^>]*>/gi, '')
        .trim();

      if (!responseText || responseText.length < 10) {
        responseText = "I've created an interactive visual interface with cards showcasing the key points. Click **View Artifact** below to open and explore the visual.";
      }
    }
    let renderedMarkdown = typeof marked !== 'undefined' ? marked.parse(responseText) : escapeHtml(responseText);
    renderedMarkdown = renderedMarkdown.replace(/<table>/gi, '<div class="table-wrapper"><table>').replace(/<\/table>/gi, '</table></div>');

    // Render Sources
    let sourcesHtml = '';
    if (data.sources && data.sources.length > 0) {
      const count = data.sources.length;
      const countLabel = count === 1 ? '1 Verified Source' : `${count} Verified Sources`;
      const pills = data.sources.map((s) => {
        return `
          <a class="source-card" href="${escapeHtml(s.source_url)}" target="_blank" rel="noopener noreferrer" title="${escapeHtml(s.episode)}">
            <span class="source-guest">${escapeHtml(s.guest)}</span>
            <span class="source-time">${escapeHtml(s.timestamp)} &nearr;</span>
          </a>
        `;
      }).join('');

      sourcesHtml = `
        <div class="sources-container">
          <div class="sources-label">
            <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
              <line x1="12" y1="19" x2="12" y2="23"></line>
              <line x1="8" y1="23" x2="16" y2="23"></line>
            </svg>
            <span>${countLabel}</span>
          </div>
          <div class="source-pills-grid">${pills}</div>
        </div>
      `;
    }

    // Render Compact Artifact Card in Chat
    let artifactHtml = '';
    if (data.artifact) {
      const art = data.artifact;
      const typeLabel = art.type === 'html' ? 'HTML Visual' : 'Markdown Document';
      artifactHtml = `
        <div class="artifact-card-chat">
          <div class="artifact-info">
            <div class="artifact-icon-wrap">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
              </svg>
            </div>
            <div class="artifact-meta-text">
              <span class="artifact-tag">ARTIFACT &bull; ${typeLabel}</span>
              <span class="artifact-name">${escapeHtml(art.title || 'Generated Artifact')}</span>
            </div>
          </div>
          <button type="button" class="btn-view-artifact" data-art-id="${escapeHtml(art.artifact_id)}">
            <span>View Artifact</span>
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="9 18 15 12 9 6"></polyline>
            </svg>
          </button>
        </div>
      `;
    }

    row.innerHTML = `
      <div class="assistant-body">
        <div class="assistant-meta">
          <span class="onair-badge">
            <span class="brand-onair-dot" style="width: 5px; height: 5px;" aria-hidden="true"></span>
            On Air
          </span>
          <span class="model-tag">${escapeHtml(providerName)}</span>
        </div>
        <div class="assistant-text">${renderedMarkdown}</div>
        ${sourcesHtml}
        ${artifactHtml}
      </div>
    `;

    // Attach click handler to whole Artifact card and button
    if (data.artifact) {
      const card = row.querySelector('.artifact-card-chat');
      if (card) {
        card.setAttribute('role', 'button');
        card.setAttribute('tabindex', '0');
        card.setAttribute('aria-label', `View artifact: ${data.artifact.title || 'Generated Artifact'}`);
        card.addEventListener('click', () => {
          openArtifactModal(data.artifact);
        });
        card.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            openArtifactModal(data.artifact);
          }
        });
      }
    }

    const target = elements.chatThread || elements.messagesContainer;
    target.appendChild(row);
    scrollToBottom();
  }

  function appendLoadingIndicator() {
    const row = document.createElement('div');
    row.className = 'message-row assistant loading-row-container';
    row.id = 'activeLoadingRow';
    row.innerHTML = `
      <div class="loading-row">
        <div class="loading-bars">
          <span class="loading-bar"></span>
          <span class="loading-bar"></span>
          <span class="loading-bar"></span>
        </div>
        <span>Searching transcripts & generating grounded response...</span>
      </div>
    `;
    const target = elements.chatThread || elements.messagesContainer;
    target.appendChild(row);
    scrollToBottom();
  }

  function removeLoadingIndicator() {
    const loadingRow = document.getElementById('activeLoadingRow');
    if (loadingRow) loadingRow.remove();
  }

  function scrollToBottom() {
    window.scrollTo({
      top: document.body.scrollHeight,
      behavior: 'smooth',
    });
  }

  // ---------------------------------------------------------------------------
  // Artifact Modal Logic (Sandboxed Isolated Iframe / Markdown)
  // ---------------------------------------------------------------------------
  function openArtifactModal(artifact) {
    state.currentArtifact = artifact;
    elements.modalArtifactTitle.textContent = artifact.title || 'Generated Artifact';
    elements.modalArtifactBadge.textContent = artifact.type === 'html' ? 'HTML Visual' : 'Markdown Document';

    // Sanitized / Safe Badge
    if (artifact.validation_status === 'rejected') {
      elements.modalSanitizedBadge.style.display = 'inline-block';
      elements.modalSanitizedBadge.textContent = 'Blocked \u2022 Unsafe Code';
      elements.modalSanitizedBadge.className = 'sanitized-badge rejected';
    } else if (artifact.validation_status === 'sanitized' || artifact.original_modified) {
      elements.modalSanitizedBadge.style.display = 'inline-block';
      elements.modalSanitizedBadge.textContent = 'Sanitized \u2022 Safe';
      elements.modalSanitizedBadge.className = 'sanitized-badge';
    } else if (artifact.validation_status === 'valid') {
      elements.modalSanitizedBadge.style.display = 'inline-block';
      elements.modalSanitizedBadge.textContent = 'Verified Safe';
      elements.modalSanitizedBadge.className = 'sanitized-badge';
    } else {
      elements.modalSanitizedBadge.style.display = 'none';
    }

    // Set Download Button Label
    if (artifact.validation_status === 'rejected') {
      elements.downloadArtifactBtn.style.display = 'none';
    } else {
      elements.downloadArtifactBtn.style.display = 'inline-flex';
      elements.downloadBtnLabel.textContent = artifact.type === 'html' ? 'Download .html' : 'Download .md';
    }

    // Handle Content Rendering
    if (artifact.validation_status === 'rejected') {
      // Rejection State
      elements.artifactIframe.style.display = 'none';
      elements.markdownArtifactContainer.style.display = 'none';
      elements.rejectedArtifactView.style.display = 'flex';
      const rawError = artifact.validation_error || '';
      let friendlyError = 'Restricted script tags or executable code were detected.';
      if (rawError.includes('<script>')) {
        friendlyError = "Executable '<script>' tag detected in generated HTML.";
      } else if (rawError) {
        friendlyError = rawError;
      }
      elements.rejectedReason.textContent = friendlyError;
    } else if (artifact.type === 'html') {
      // HTML Visual Artifact inside Sandboxed Iframe (NO allow-scripts)
      elements.rejectedArtifactView.style.display = 'none';
      elements.markdownArtifactContainer.style.display = 'none';
      elements.artifactIframe.style.display = 'block';

      // Securely populate iframe using srcdoc (backend-sanitized HTML only)
      elements.artifactIframe.srcdoc = artifact.content || '<p style="padding: 20px; color: #666;">No content available.</p>';
    } else {
      // Markdown Artifact
      elements.rejectedArtifactView.style.display = 'none';
      elements.artifactIframe.style.display = 'none';
      elements.markdownArtifactContainer.style.display = 'block';
      // Show the source Markdown exactly as generated. The artifact card and
      // download remain available, while the preview no longer transforms it
      // into a rendered document.
      elements.markdownArtifactContainer.innerHTML = `<pre class="markdown-raw-view"><code>${escapeHtml(artifact.content || '')}</code></pre>`;
    }

    // Open Modal
    elements.artifactModal.classList.add('open');
    elements.artifactModal.setAttribute('aria-hidden', 'false');
    elements.artifactModalBackdrop.classList.add('open');
    elements.artifactModalBackdrop.setAttribute('aria-hidden', 'false');
  }

  function closeArtifactModal() {
    elements.artifactModal.classList.remove('open');
    elements.artifactModal.setAttribute('aria-hidden', 'true');
    elements.artifactModalBackdrop.classList.remove('open');
    elements.artifactModalBackdrop.setAttribute('aria-hidden', 'true');
    // Clear iframe srcdoc to free resources
    setTimeout(() => {
      elements.artifactIframe.srcdoc = '';
    }, 200);
  }

  function downloadCurrentArtifact() {
    if (!state.currentArtifact || !state.currentArtifact.content) {
      showToast('No artifact content available to download.', 'error');
      return;
    }

    const art = state.currentArtifact;
    const isHtml = art.type === 'html';
    const mimeType = isHtml ? 'text/html;charset=utf-8' : 'text/markdown;charset=utf-8';
    const ext = isHtml ? '.html' : '.md';
    const filename = (art.title || 'artifact').toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '') + ext;

    const blob = new Blob([art.content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    showToast(`Downloaded ${filename}`);
  }

  // ---------------------------------------------------------------------------
  // Sending Chat Requests (POST /chat)
  // ---------------------------------------------------------------------------
  async function handleSendMessage(promptText) {
    const cleanPrompt = promptText.trim();
    if (!cleanPrompt || state.isLoading) return;

    state.isLoading = true;
    state.abortController = new AbortController();
    elements.sendBtn.disabled = true;
    elements.sendBtn.hidden = true;
    elements.stopBtn.hidden = false;
    elements.promptInput.value = '';
    elements.promptInput.style.height = 'auto';

    appendUserMessage(cleanPrompt);
    appendLoadingIndicator();

    const payload = {
      prompt: cleanPrompt,
      session_id: state.activeSessionId,
      provider: state.activeProvider,
    };

    try {
      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: state.abortController.signal,
      });

      removeLoadingIndicator();

      if (!res.ok) {
        let errMessage = 'Failed to generate response.';
        try {
          const errText = await res.text();
          try {
            const errData = JSON.parse(errText);
            errMessage = errData.detail || errData.error || errMessage;
          } catch {
            if (errText) errMessage = errText;
          }
        } catch (readErr) {
          console.warn('Could not read error body:', readErr);
        }

        console.error('[Lenny Chat Error Detail]:', errMessage);

        if (res.status === 503 || res.status === 500) {
          if (state.activeProvider === 'ollama') {
            showToast('Local AI service is currently unreachable.', 'error');
            appendAssistantMessage({
              response: `**Local Provider Unavailable**\n\nI couldn't reach your local model. Please verify that Ollama is running on your machine, or switch to **Cloud** in the top right corner.`,
              provider: 'ollama',
              sources: [],
            });
          } else {
            showToast('Cloud AI service is currently unreachable.', 'error');
            appendAssistantMessage({
              response: `**Service Temporarily Unavailable**\n\nPlease verify your network connection and Gemini API key, or switch to **Local** mode.`,
              provider: 'gemini',
              sources: [],
            });
          }
        } else {
          showToast('Unable to complete request. Please try again.', 'error');
        }
        return;
      }

      const data = await res.json();
      state.activeSessionId = data.session_id;
      try {
        localStorage.setItem('lenny_active_session_id', data.session_id);
      } catch {}
      if (elements.activeSessionTitle.textContent === 'New Conversation') {
        elements.activeSessionTitle.textContent = cleanPrompt.substring(0, 50) + (cleanPrompt.length > 50 ? '...' : '');
      }

      appendAssistantMessage(data);

      // Generate and display 2-3 dynamic follow-up suggestion chips right above the input field
      const followUpChips = generateContextualChips(cleanPrompt, data.response, data.sources);
      showContextChips(followUpChips);

      // If response includes an artifact, update active artifact
      if (data.artifact) {
        state.currentArtifact = data.artifact;
      }

      // Refresh sessions in background
      loadSessions();

    } catch (err) {
      removeLoadingIndicator();
      if (err.name === 'AbortError') {
        appendAssistantMessage({ response: 'Response generation stopped. You can ask another question now.', provider: state.activeProvider });
      } else {
        showToast(`Network error: ${err.message}`, 'error');
      }
    } finally {
      const wasAborted = state.abortController?.signal.aborted;
      if (wasAborted) await new Promise((resolve) => setTimeout(resolve, 1000));
      state.isLoading = false;
      state.abortController = null;
      elements.sendBtn.disabled = false;
      elements.sendBtn.hidden = false;
      elements.stopBtn.hidden = true;
      elements.promptInput.focus();
    }
  }

  function stopResponseGeneration() {
    if (state.isLoading && state.abortController) {
      state.abortController.abort();
      showToast('Stopping response generation…');
    }
  }

  // ---------------------------------------------------------------------------
  // Utility: Escape HTML
  // ---------------------------------------------------------------------------
  function escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // ---------------------------------------------------------------------------
  // Event Listeners
  // ---------------------------------------------------------------------------
  function initEventListeners() {
    // Provider Selection
    elements.providerLocalBtn.addEventListener('click', () => setProvider('ollama'));
    elements.providerCloudBtn.addEventListener('click', () => setProvider('gemini'));

    // Drawer Toggle
    elements.sessionsToggleBtn.addEventListener('click', openDrawer);
    elements.closeDrawerBtn.addEventListener('click', closeDrawer);
    elements.drawerBackdrop.addEventListener('click', closeDrawer);
    // Delegated fallback keeps the close control working if the drawer header
    // is re-rendered or the click originates on the × text node.
    document.addEventListener('click', (e) => {
      if (e.target.closest('#closeDrawerBtn')) {
        e.preventDefault();
        e.stopPropagation();
        closeDrawer();
      }
    });
    elements.newChatDrawerBtn.addEventListener('click', startNewConversation);
    if (elements.deleteAllChatsBtn) {
      elements.deleteAllChatsBtn.addEventListener('click', deleteAllSessions);
    }
    elements.newChatTopBtn.addEventListener('click', startNewConversation);

    // Close dropdowns on outside click
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.session-item')) {
        closeAllDropdowns();
      }
    });

    // Artifact Modal
    elements.closeModalBtn.addEventListener('click', closeArtifactModal);
    elements.artifactModalBackdrop.addEventListener('click', closeArtifactModal);
    elements.downloadArtifactBtn.addEventListener('click', downloadCurrentArtifact);

    // Keyboard Shortcuts
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        if (elements.artifactModal.classList.contains('open')) {
          closeArtifactModal();
        } else if (elements.sessionDrawer.classList.contains('open')) {
          closeDrawer();
        }
      }
    });

    // Chat Form & Input
    elements.chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      handleSendMessage(elements.promptInput.value);
    });
    elements.stopBtn.addEventListener('click', stopResponseGeneration);

    elements.promptInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage(elements.promptInput.value);
      }
    });

    // Auto-grow textarea
    elements.promptInput.addEventListener('input', () => {
      elements.promptInput.style.height = 'auto';
      elements.promptInput.style.height = Math.min(elements.promptInput.scrollHeight, 160) + 'px';
    });

    // Suggestion Chips
    elements.suggestionChips.forEach((chip) => {
      chip.addEventListener('click', () => {
        const prompt = chip.getAttribute('data-prompt');
        if (prompt) {
          elements.promptInput.value = prompt;
          handleSendMessage(prompt);
        }
      });
    });
  }

  // ---------------------------------------------------------------------------
  // Live Application Readiness Status Polling
  // ---------------------------------------------------------------------------
  async function checkAppStatus() {
    try {
      const res = await fetch('/health');
      if (!res.ok) {
        setTimeout(checkAppStatus, 3000);
        return;
      }
      const data = await res.json();
      const dot = document.getElementById('statusDot');
      const text = document.getElementById('statusBadgeText');
      if (!dot || !text) return;

      if (data.app_status === 'ready') {
        dot.className = 'status-pulse-dot ready';
        text.textContent = 'Application: Ready';
      } else {
        dot.className = 'status-pulse-dot setting-up';
        text.textContent = 'Application: In progress...';
      }
      // Keep polling after readiness so dependency outages are reflected.
      setTimeout(checkAppStatus, data.app_status === 'ready' ? 3000 : 2000);
    } catch {
      setTimeout(checkAppStatus, 3000);
    }
  }

  // ---------------------------------------------------------------------------
  // Initialization
  // ---------------------------------------------------------------------------
  async function init() {
    initEventListeners();
    checkAppStatus();
    let savedProvider = 'ollama';
    try {
      savedProvider = localStorage.getItem('lenny_active_provider') || 'ollama';
    } catch {}
    setProvider(savedProvider);
    await loadSessions();

    try {
      const savedSessionId = localStorage.getItem('lenny_active_session_id');
      if (savedSessionId) {
        const match = state.sessions.find((s) => s.session_id === savedSessionId);
        if (match) {
          await selectSession(savedSessionId, match.metadata?.title || '');
        }
      }
    } catch (err) {
      console.warn('Failed to restore active session:', err);
    }
  }

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
