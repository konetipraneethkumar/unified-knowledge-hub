(function () {
  const robot = document.getElementById('robot');
  const speechBubble = document.getElementById('speechBubble');
  const searchForm = document.getElementById('searchForm');
  const searchInput = document.getElementById('searchInput');
  const libraryPanel = document.getElementById('libraryPanel');
  const resultCard = document.getElementById('resultCard');
  const statusItems = Array.from(document.querySelectorAll('.status-item'));
  const quickChips = Array.from(document.querySelectorAll('.chip'));
  const themeToggle = document.getElementById('themeToggle');
  const statusHeading = document.getElementById('statusHeading');
  const statusPill = document.getElementById('statusPill');
  let activeSearch = 0;

  function setRobotState(state) {
    if (!robot) return;
    robot.className = `robot ${state}`;
    robot.setAttribute('aria-label', `Knowledge Hub assistant, ${state.replace('-', ' ')}`);
  }

  function setSpeech(message) {
    if (!speechBubble) return;
    speechBubble.innerHTML = message;
  }

  function setStatusStage(index) {
    statusItems.forEach((item, itemIndex) => {
      item.classList.toggle('active', itemIndex === index);
    });
  }

  function setTheme(isDark) {
    document.body.classList.toggle('light-theme', !isDark);
    if (themeToggle) {
      themeToggle.textContent = isDark ? '☼' : '☾';
      themeToggle.setAttribute('aria-label', isDark ? 'Switch to light theme' : 'Switch to dark theme');
    }
  }

  function setIdleState() {
    document.body.classList.remove('is-searching', 'is-result');
    setRobotState('idle');
    setSpeech('<strong>Hi! 👋 What are you looking for today?</strong><span>I can search your knowledge for you.</span>');
    setStatusStage(0);
  }

  function handleInputFocus() {
    if (document.body.classList.contains('is-searching') || document.body.classList.contains('is-result')) return;
    setRobotState('attentive');
    setSpeech('<strong>I’m listening.</strong><span>Tell me what you need to find.</span>');
  }

  function updateResult(documentItem) {
    const matchScores = {
      'mentor-progress-report': 96,
      'dccn-assignment': 93,
      'internship-documents': 91,
      'machine-learning-presentation': 94,
    };
    const title = documentItem.title || 'Untitled file';
    const fileType = documentItem.fileType || title.split('.').pop().toUpperCase();
    document.getElementById('resultTitle').textContent = title;
    document.getElementById('resultFileIcon').textContent = fileType;
    document.querySelector('.robot-document').textContent = fileType;
    document.getElementById('resultType').textContent = `${fileType} file`;
    document.getElementById('resultLocation').textContent = `${documentItem.source} · ${documentItem.originalLocation}`;
    document.getElementById('resultDate').textContent = documentItem.modified || documentItem.created;
    document.getElementById('resultSummary').textContent = documentItem.summary;
    document.getElementById('resultScore').textContent = `${matchScores[documentItem.id] || 88}% match`;
    document.getElementById('openFileButton').href = `document.html?id=${encodeURIComponent(documentItem.id)}`;
  }

  async function handleSearch(query) {
    const trimmedQuery = query.trim();
    if (!trimmedQuery) {
      searchInput?.focus();
      return;
    }

    const searchId = ++activeSearch;
    document.body.classList.remove('is-result');
    document.body.classList.add('is-searching');
    resultCard?.classList.add('hidden');
    libraryPanel?.classList.remove('hidden');
    statusHeading.textContent = 'Your librarian is on it';
    statusPill.innerHTML = '<span class="dot"></span> IN PROGRESS';
    setRobotState('thinking');
    setSpeech('<strong>Let me find that for you.</strong><span>I’m looking through your library now.</span>');
    setStatusStage(0);

    await new Promise((resolve) => setTimeout(resolve, 500));
    if (searchId !== activeSearch) return;
    setRobotState('searching');
    setStatusStage(1);

    await new Promise((resolve) => setTimeout(resolve, 650));
    if (searchId !== activeSearch) return;
    setRobotState('scanning');
    setStatusStage(2);
    const response = await window.ukhAPI.searchKnowledge(trimmedQuery);

    await new Promise((resolve) => setTimeout(resolve, 700));
    if (searchId !== activeSearch) return;
    setStatusStage(3);
    statusPill.innerHTML = '<span class="dot"></span> SEARCH COMPLETE';

    const match = response.results[0];
    if (!match) {
      document.body.classList.remove('is-searching');
      setStatusStage(2);
      statusPill.innerHTML = '<span class="dot"></span> NO MATCH';
      setRobotState('no-result');
      setSpeech('<strong>No close match this time.</strong><span>Try another phrase and I’ll look again.</span>');
      statusHeading.textContent = 'No matching files found';
      return;
    }

    updateResult(match);
    document.body.classList.remove('is-searching');
    document.body.classList.add('is-result');
    setRobotState('result');
    setSpeech('<strong>I found the one you’re looking for.</strong><span>Here’s the closest match in your library.</span>');
    statusHeading.textContent = 'A relevant file is ready';
    resultCard?.classList.remove('hidden');
  }

  function bindEvents() {
    if (searchInput) {
      searchInput.addEventListener('focus', handleInputFocus);
      searchInput.addEventListener('blur', () => {
        if (!document.body.classList.contains('is-searching') && !document.body.classList.contains('is-result')) setIdleState();
      });
    }

    if (searchForm) {
      searchForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const value = searchInput?.value || '';
        handleSearch(value);
      });
    }

    quickChips.forEach((chip) => {
      chip.addEventListener('click', () => {
        const value = chip.getAttribute('data-query');
        if (searchInput && value) {
          searchInput.value = value;
          handleSearch(value);
        }
      });
    });

    if (themeToggle) {
      themeToggle.addEventListener('click', () => {
        const isDark = !document.body.classList.contains('light-theme');
        setTheme(!isDark);
      });
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    setTheme(true);
    setIdleState();
    bindEvents();
  });
})();
