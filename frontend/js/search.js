(function () {
  const formatQuery = (value) => value.trim();

  const renderLoadingState = (message) => {
    const resultsPanel = document.getElementById('resultsPanel');
    const resultStatus = document.getElementById('resultStatus');
    if (!resultsPanel || !resultStatus) {
      return;
    }

    resultsPanel.classList.remove('hidden');
    resultStatus.classList.remove('hidden');
    resultStatus.innerHTML = `
      <div class="loading-copy">
        <strong>Searching your knowledge...</strong>
        <span>Understanding query • Searching metadata • Ranking results</span>
      </div>
    `;
    const list = document.getElementById('resultsList');
    if (list) {
      list.innerHTML = '';
    }
    const answerCard = document.getElementById('answerCard');
    if (answerCard) {
      answerCard.classList.add('hidden');
      answerCard.innerHTML = '';
    }
  };

  const renderResults = (payload) => {
    const resultsPanel = document.getElementById('resultsPanel');
    const resultStatus = document.getElementById('resultStatus');
    const list = document.getElementById('resultsList');
    const answerCard = document.getElementById('answerCard');
    if (!resultsPanel || !resultStatus || !list) {
      return;
    }

    resultsPanel.classList.remove('hidden');
    resultStatus.classList.remove('hidden');
    resultStatus.textContent = payload.status || 'Search complete.';

    if (payload.answer) {
      answerCard.classList.remove('hidden');
      answerCard.innerHTML = `
        <div class="answer-label">Answer</div>
        <h3>${payload.answer.header}</h3>
        <p>${payload.answer.body}</p>
      `;
    } else {
      answerCard.classList.add('hidden');
      answerCard.innerHTML = '';
    }

    if (!payload.results.length) {
      list.innerHTML = `
        <div class="empty-state">
          <h3>No matching knowledge found.</h3>
          <p>Try a broader description or connect another source.</p>
        </div>
      `;
      return;
    }

    list.innerHTML = payload.results
      .map(
        (item) => `
          <article class="result-item">
            <div class="result-topline">
              <span class="file-pill">${item.fileType}</span>
              <span class="relevance">${item.relevance}</span>
            </div>
            <h3>${item.title}</h3>
            <p class="result-summary">${item.whyItMatched}</p>

            <div class="result-meta">
              <div class="meta-block">
                <label>Source</label>
                <span>${item.source}</span>
              </div>
              <div class="meta-block">
                <label>Modified</label>
                <span>${item.modified}</span>
              </div>
              <div class="meta-block">
                <label>Location</label>
                <span>${item.originalLocation}</span>
              </div>
            </div>

            <div class="result-location">${item.sourceLocation}</div>

            <div class="result-actions">
              <a class="button primary" href="document.html?id=${item.id}">Open file</a>
              <a class="button secondary" href="document.html?id=${item.id}">View details</a>
              <button class="button ghost" type="button" data-copy-location="${item.sourceLocation}">Copy location</button>
            </div>
          </article>
        `
      )
      .join('');

    list.querySelectorAll('[data-copy-location]').forEach((button) => {
      button.addEventListener('click', async () => {
        const text = button.getAttribute('data-copy-location');
        try {
          await navigator.clipboard.writeText(text);
          button.textContent = 'Copied';
          setTimeout(() => {
            button.textContent = 'Copy location';
          }, 1200);
        } catch (error) {
          button.textContent = 'Copy failed';
        }
      });
    });
  };

  const handleSearchSubmit = async (event) => {
    event.preventDefault();
    const input = document.getElementById('searchInput');
    if (!input) {
      return;
    }

    const query = formatQuery(input.value);
    if (!query) {
      input.focus();
      return;
    }

    renderLoadingState();
    const result = await window.ukhAPI.searchKnowledge(query);
    const title = document.getElementById('resultsTitle');
    if (title) {
      title.textContent = result.total ? `Found ${result.total} relevant results` : 'Search results';
    }
    renderResults(result);
  };

  const renderSources = async () => {
    const list = document.getElementById('sourcesList');
    if (!list) {
      return;
    }

    const sources = await window.ukhAPI.getSources();
    list.innerHTML = sources
      .map(
        (source) => `
          <article class="source-card">
            <div class="source-card-header">
              <h2 class="source-name">${source.name}</h2>
              <span class="status-chip ${source.status.toLowerCase() === 'connected' ? 'connected' : 'disconnected'}">
                ${source.status}
              </span>
            </div>
            <dl>
              <div>
                <dt>Indexed items</dt>
                <dd>${source.indexed}</dd>
              </div>
              <div>
                <dt>Last synchronization</dt>
                <dd>${source.lastSync}</dd>
              </div>
              <div>
                <dt>Indexing status</dt>
                <dd>${source.indexingStatus}</dd>
              </div>
            </dl>
          </article>
        `
      )
      .join('');
  };

  const renderHistory = async () => {
    const list = document.getElementById('historyList');
    if (!list) {
      return;
    }

    const groups = await window.ukhAPI.getSearchHistory();
    list.innerHTML = groups
      .map(
        (group) => `
          <div class="history-group">
            <h2>${group.day}</h2>
            ${group.items
              .map(
                (item) => `
                  <div class="history-item">
                    <button type="button" data-history-query="${item.query}">${item.query}</button>
                    <span class="time-label">${item.time}</span>
                  </div>
                `
              )
              .join('')}
          </div>
        `
      )
      .join('');

    list.querySelectorAll('[data-history-query]').forEach((button) => {
      button.addEventListener('click', () => {
        const query = button.getAttribute('data-history-query');
        if (query) {
          window.location.href = `index.html?q=${encodeURIComponent(query)}`;
        }
      });
    });
  };

  const renderDocument = async () => {
    const container = document.getElementById('documentPageContent');
    if (!container) {
      return;
    }

    const params = new URLSearchParams(window.location.search);
    const id = params.get('id');
    const item = await window.ukhAPI.getDocument(id || 'mentor-progress-report');

    if (!item) {
      container.innerHTML = `
        <div class="empty-state">
          <h3>Document not found.</h3>
          <p>The requested file could not be located in your knowledge index.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div class="document-shell">
        <article class="document-main">
          <div class="document-header">
            <div>
              <div class="kicker-row">
                <span class="file-pill">${item.fileType}</span>
                <span class="status-chip connected">${item.source}</span>
              </div>
              <h1 class="document-title">${item.title}</h1>
            </div>
            <div class="result-actions">
              <button class="button secondary" type="button">Open Original</button>
              <button class="button ghost" type="button">Copy Location</button>
            </div>
          </div>

          <section class="detail-section">
            <h3>Overview</h3>
            <p>${item.summary}</p>
          </section>

          <section class="detail-section">
            <h3>Why this matched</h3>
            <p>${item.whyItMatched}</p>
          </section>

          <div class="metadata-grid">
            <div class="metadata-item">
              <label>Source</label>
              <strong>${item.source}</strong>
            </div>
            <div class="metadata-item">
              <label>Original location</label>
              <strong>${item.originalLocation}</strong>
            </div>
            <div class="metadata-item">
              <label>Created</label>
              <strong>${item.created}</strong>
            </div>
            <div class="metadata-item">
              <label>Modified</label>
              <strong>${item.modified}</strong>
            </div>
            <div class="metadata-item">
              <label>Last indexed</label>
              <strong>${item.lastIndexed}</strong>
            </div>
            <div class="metadata-item">
              <label>Related documents</label>
              <strong>${item.relatedDocuments.length}</strong>
            </div>
          </div>

          <section class="detail-section">
            <h3>File history</h3>
            <ul>
              ${item.fileHistory.map((entry) => `<li>${entry}</li>`).join('')}
            </ul>
          </section>
        </article>

        <aside class="document-aside">
          <div class="stack">
            <div class="aside-card">
              <h4>Semantic summary</h4>
              <p>${item.summary}</p>
            </div>
            <div class="aside-card">
              <h4>Why it matched</h4>
              <p>${item.whyItMatched}</p>
            </div>
            <div class="aside-card">
              <h4>Related knowledge</h4>
              <ul class="related-list">
                ${item.relatedDocuments
                  .map((entry) => `<li><a href="document.html?id=${entry.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/-$/, '')}">${entry}</a></li>`)
                  .join('')}
              </ul>
            </div>
            <div class="aside-card">
              <h4>Metadata</h4>
              <div class="tag-list">
                ${item.tags.map((tag) => `<span class="tag">${tag}</span>`).join('')}
              </div>
            </div>
          </div>
        </aside>
      </div>
    `;
  };

  const initializeHomePage = () => {
    const searchForm = document.getElementById('searchForm');
    const input = document.getElementById('searchInput');
    if (searchForm) {
      searchForm.addEventListener('submit', handleSearchSubmit);
    }

    document.querySelectorAll('.example-query').forEach((button) => {
      button.addEventListener('click', () => {
        const query = button.getAttribute('data-query');
        if (input && query) {
          input.value = query;
          searchForm.requestSubmit();
        }
      });
    });

    const params = new URLSearchParams(window.location.search);
    const query = params.get('q');
    if (query && input) {
      input.value = query;
      setTimeout(() => {
        searchForm.requestSubmit();
      }, 150);
    }
  };

  document.addEventListener('DOMContentLoaded', () => {
    const page = document.body.dataset.page;

    if (page === 'home') {
      initializeHomePage();
      return;
    }

    if (page === 'document') {
      renderDocument();
      return;
    }

    if (page === 'sources') {
      renderSources();
      return;
    }

    if (page === 'history') {
      renderHistory();
    }
  });
})();
