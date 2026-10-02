import {
  mockKnowledgeDocuments,
  type MockKnowledgeDocument,
} from "../data/mockKnowledge";

export type MockSearchStatus = "success" | "no-results" | "error";

export type MockSearchResponse = {
  query: string;
  status: MockSearchStatus;
  answer: string;
  documents: MockKnowledgeDocument[];
  error?: string;
};

function normalizeQuery(query: string) {
  const stopWords = new Set([
    "a",
    "about",
    "across",
    "after",
    "all",
    "an",
    "and",
    "any",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "did",
    "do",
    "document",
    "documents",
    "does",
    "find",
    "for",
    "from",
    "have",
    "how",
    "i",
    "if",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "recent",
    "related",
    "search",
    "show",
    "that",
    "the",
    "their",
    "them",
    "there",
    "these",
    "they",
    "this",
    "those",
    "to",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
    "work",
    "you",
    "your",
  ]);

  const terms = query
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter(Boolean);

  return Array.from(new Set(terms.filter((term) => !stopWords.has(term))));
}

function scoreDocument(query: string, document: MockKnowledgeDocument) {
  const terms = normalizeQuery(query);
  if (terms.length === 0) {
    return 0;
  }

  const haystack = [
    document.title,
    document.summary,
    document.content,
    document.category,
    ...document.tags,
  ]
    .join(" ")
    .toLowerCase();

  const weightedMatches = terms.reduce((total, term) => {
    const exactTerm = new RegExp(`\\b${term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`, "i");
    if (exactTerm.test(document.title)) {
      return total + 5;
    }
    if (exactTerm.test(document.summary)) {
      return total + 4;
    }
    if (exactTerm.test(document.content)) {
      return total + 3;
    }
    if (haystack.includes(term)) {
      return total + 2;
    }
    return total;
  }, 0);

  return weightedMatches;
}

function buildAnswer(query: string, documents: MockKnowledgeDocument[]) {
  const initial = documents[0];
  const supporting = documents.slice(1, 3).map((document) => document.title);
  const focus = query.toLowerCase();

  if (focus.includes("mentor") || focus.includes("academic")) {
    return `This is mock/demo data, but the local knowledge index suggests that your mentor discussions centered on academic momentum, milestone planning, and the project direction. The strongest matching material includes ${initial.title}${supporting.length ? ` and ${supporting.join(", ")}` : ""}.`;
  }

  if (focus.includes("capstone") || focus.includes("project")) {
    return `This is mock/demo data, but the project-related memory indicates the main focus was the capstone vision, product direction, and the knowledge system roadmap. The most relevant sources are ${initial.title}${supporting.length ? `, ${supporting.join(", ")}` : ""}.`;
  }

  if (focus.includes("retrieval") || focus.includes("search")) {
    return `This is mock/demo data, but the retrieval-related notes show work on hybrid search, ranking choices, and evaluation heuristics. The clearest references are ${initial.title}${supporting.length ? ` and ${supporting.join(", ")}` : ""}.`;
  }

  return `This is mock/demo data, but the local index suggests a clear connection to ${initial.title}${supporting.length ? ` and related materials like ${supporting.join(", ")}` : ""}. The referenced notes point to progress, planning, and the broader project context.`;
}

export async function resolveMockSearch(query: string): Promise<MockSearchResponse> {
  const trimmedQuery = query.trim();

  if (!trimmedQuery) {
    throw new Error("Please enter a valid search query.");
  }

  await new Promise((resolve) => window.setTimeout(resolve, 450));

  if (trimmedQuery.toLowerCase().includes("error")) {
    return {
      query: trimmedQuery,
      status: "error",
      answer:
        "The mock search layer hit a temporary issue while checking the local knowledge index. Please retry the query.",
      documents: [],
      error: "Mock retrieval failure",
    };
  }

  const matches = mockKnowledgeDocuments
    .map((document) => ({
      document,
      score: scoreDocument(trimmedQuery, document),
    }))
    .filter(({ score }) => score > 0)
    .sort((left, right) => right.score - left.score)
    .map(({ document }) => document)
    .slice(0, 3);

  if (matches.length === 0) {
    return {
      query: trimmedQuery,
      status: "no-results",
      answer:
        "I could not find any matching mock documents for that query in the local demo index. This is a frontend-only response, so nothing relevant was returned.",
      documents: [],
    };
  }

  return {
    query: trimmedQuery,
    status: "success",
    answer: buildAnswer(trimmedQuery, matches),
    documents: matches,
  };
}
