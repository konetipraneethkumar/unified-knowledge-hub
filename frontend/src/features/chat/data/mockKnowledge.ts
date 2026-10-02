export type MockKnowledgeDocument = {
  id: string;
  title: string;
  type: string;
  summary: string;
  date: string;
  category: string;
  tags: string[];
  content: string;
};

export const suggestedQueries = [
  "What did I discuss with my mentor?",
  "Find documents related to my capstone.",
  "What work did I do on retrieval?",
  "Show my recent academic documents.",
];

export const mockKnowledgeDocuments: MockKnowledgeDocument[] = [
  {
    id: "mentor-meeting-notes",
    title: "Mentor Meeting Notes",
    type: "Academic / PDF",
    summary:
      "Discussed project progress, academic milestones, and the direction for the next research phase.",
    date: "September 2026",
    category: "Mentorship",
    tags: ["mentor", "academics", "milestones", "project"],
    content:
      "The mentor discussed the capstone trajectory, the need to document progress clearly, and the importance of maintaining academic momentum. Follow-up items included a progress review, stronger literature synthesis, and refined milestones for the next term.",
  },
  {
    id: "academic-progress-report",
    title: "Academic Progress Report",
    type: "Academic / PDF",
    summary:
      "Tracked coursework, research focus, and the academic sequence supporting the capstone effort.",
    date: "August 2026",
    category: "Academics",
    tags: ["academic", "coursework", "research", "degree"],
    content:
      "This report captured the completed coursework, the progression of research ideas, and the alignment between the major project and academic objectives. It highlighted the development of an evidence-driven project narrative and a clearer roadmap for final deliverables.",
  },
  {
    id: "capstone-project-brief",
    title: "Capstone Project Brief",
    type: "Project / Notes",
    summary:
      "Outlined the system goals, the user experience priorities, and the technical plan for the knowledge hub.",
    date: "July 2026",
    category: "Project",
    tags: ["capstone", "project", "experience", "knowledge"],
    content:
      "The project brief described the Unified Knowledge Hub concept: a personal memory system, local-first indexing, retrieval flows, and a future AI interface for knowledge discovery. It emphasized user trust, minimal friction, and a calm information experience.",
  },
  {
    id: "retrieval-system-journal",
    title: "Retrieval System Journal",
    type: "Technical / Markdown",
    summary:
      "Recorded experiments with retrieval architecture, ranking heuristics, and the evaluation strategy.",
    date: "June 2026",
    category: "Engineering",
    tags: ["retrieval", "search", "ranking", "evaluation"],
    content:
      "The retrieval journal focused on hybrid search methods, metadata weighting, and the need for deterministic, explainable responses in a prototype settings. It captured how search quality was evaluated against familiar queries and system constraints.",
  },
  {
    id: "weekly-planning-notes",
    title: "Weekly Planning Notes",
    type: "Productivity / Notes",
    summary:
      "Summarized personal priorities, follow-up tasks, and weekly execution notes for the project lifecycle.",
    date: "October 2026",
    category: "Planning",
    tags: ["planning", "weekly", "tasks", "execution"],
    content:
      "The weekly notes captured goals for research, prototyping, synthesis, and stakeholder visibility. They emphasized task sequencing, documentation discipline, and maintaining momentum in a multi-week delivery cycle.",
  },
  {
    id: "project-meeting-recap",
    title: "Project Meeting Recap",
    type: "Meeting / Notes",
    summary:
      "Reviewed design choices, technical tradeoffs, and upcoming milestones for the unified experience.",
    date: "May 2026",
    category: "Meetings",
    tags: ["meetings", "design", "tradeoffs", "milestones"],
    content:
      "The meeting recap covered design direction for the product shell, the relationship between search and conversation, and the decision to keep the prototype lightweight and local. Notes also captured open questions around future integrations and the long-term architecture.",
  },
];
