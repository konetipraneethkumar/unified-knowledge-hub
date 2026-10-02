(function () {
  const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  const stopWords = new Set([
    'find', 'my', 'the', 'a', 'an', 'where', 'is', 'show', 'me', 'documents', 'document', 'files', 'file',
    'about', 'and', 'for', 'of', 'to', 'from', 'search', 'with', 'in', 'on', 'what', 'it', 'this', 'that',
    'related', 'your', 'you', 'have', 'i', 'we', 'our', 'can', 'could', 'should', 'would'
  ]);

  const normalizeText = (value) => value.toLowerCase().replace(/[^a-z0-9\s]/g, ' ').replace(/\s+/g, ' ').trim();

  const tokenize = (value) => {
    return normalizeText(value)
      .split(' ')
      .filter(Boolean)
      .filter((token) => !stopWords.has(token));
  };

  const getDocumentById = (id) => {
    const match = window.ukhMockData.documents.find((item) => item.id === id);
    return match || null;
  };

  const getSearchCandidates = (query) => {
    const normalized = query.trim();
    if (!normalized) {
      return [];
    }

    const queryTokens = tokenize(query);
    if (!queryTokens.length) {
      return [];
    }

    return window.ukhMockData.documents.filter((item) => {
      const haystack = [
        item.title,
        item.summary,
        item.whyItMatched,
        item.originalLocation,
        item.source,
        item.tags.join(' '),
      ].join(' ');

      const haystackTokens = tokenize(haystack);
      return queryTokens.every((token) => haystackTokens.includes(token));
    });
  };

  window.ukhAPI = {
    async searchKnowledge(query) {
      await delay(500);
      const matched = getSearchCandidates(query);

      if (!matched.length) {
        return {
          query,
          total: 0,
          results: [],
          answer: null,
          status: 'No matches found for this query.'
        };
      }

      const answer = {
        header: 'I found one document that closely matches your description.',
        body: `It appears to be ${matched[0].title.replace(/\.[^.]+$/, '')}.`
      };

      return {
        query,
        total: matched.length,
        results: matched,
        answer,
        status: `Found ${matched.length} relevant results.`
      };
    },

    async getDocument(id) {
      await delay(180);
      return getDocumentById(id);
    },

    async getSources() {
      await delay(120);
      return window.ukhMockData.sources;
    },

    async getSearchHistory() {
      await delay(120);
      return window.ukhMockData.history;
    }
  };
})();
