window.ukhMockData = {
  documents: [
    {
      id: 'mentor-progress-report',
      title: 'Mentor-Mentee Progress Report.pdf',
      fileType: 'PDF',
      source: 'Google Drive',
      originalLocation: 'Academic / Mentor-Mentee',
      created: '2025-02-19',
      modified: '18 Aug 2026',
      lastIndexed: 'Today, 14:32',
      summary: 'Contains mentor-mentee meeting records and academic progress observations across the semester.',
      whyItMatched: 'Matches because the document contains mentor-mentee meeting notes and academic progress details associated with your coursework.',
      sourceLocation: 'Google Drive / Academic / Mentor-Mentee',
      fileHistory: [
        'Updated after mentor review on 18 Aug 2026',
        'Academic notes consolidated from weekly meetings',
        'Shared with advisor and coursework committee'
      ],
      relatedDocuments: ['Academic Progress Review.docx', 'Internship Mentor Notes.pdf'],
      tags: ['mentor', 'mentee', 'academic progress', 'report'],
      relevance: 'High relevance'
    },
    {
      id: 'dccn-assignment',
      title: 'DCCN Assignment Brief.docx',
      fileType: 'DOCX',
      source: 'Local Files',
      originalLocation: 'Courses / DCCN / Fall Semester',
      created: '2025-09-12',
      modified: '21 Sep 2025',
      lastIndexed: 'Yesterday, 09:46',
      summary: 'Assignments, deadline notes and technical requirements for the Data Communication and Computer Networks course.',
      whyItMatched: 'Matches because the file is clearly tagged with DCCN coursework details and assignment instructions.',
      sourceLocation: 'Local Files / Courses / DCCN / Fall Semester',
      fileHistory: [
        'Updated with final rubric notes',
        'Original draft created in September 2025',
        'Backed up to local university folder'
      ],
      relatedDocuments: ['DCCN Lab Checklist.pdf', 'Networking Notes.pdf'],
      tags: ['dccn', 'assignment', 'networking', 'coursework'],
      relevance: 'High relevance'
    },
    {
      id: 'internship-documents',
      title: 'Internship Reflection Notes.pdf',
      fileType: 'PDF',
      source: 'Google Drive',
      originalLocation: 'Career / Internship / Summer 2026',
      created: '2026-07-11',
      modified: '12 Jul 2026',
      lastIndexed: 'Today, 08:14',
      summary: 'Learning outcomes, reflections and project notes about your internship experience and responsibilities.',
      whyItMatched: 'Matches because it references internship responsibilities, reflections and project outcomes similar to your description.',
      sourceLocation: 'Google Drive / Career / Internship / Summer 2026',
      fileHistory: [
        'Updated after final internship reflection',
        'Matched with mentor feedback and outcomes',
        'Added to portfolio archive'
      ],
      relatedDocuments: ['Summer Internship Presentation.pdf', 'Company Mentor Feedback.docx'],
      tags: ['internship', 'reflection', 'project', 'career'],
      relevance: 'Medium relevance'
    },
    {
      id: 'machine-learning-presentation',
      title: 'Machine Learning Presentation Deck.pptx',
      fileType: 'PPTX',
      source: 'Google Drive',
      originalLocation: 'Projects / Machine Learning / Presentations',
      created: '2026-03-02',
      modified: '04 Mar 2026',
      lastIndexed: 'Mon, 11:40',
      summary: 'Presentation slides summarizing a machine learning project, methodology and results for class review.',
      whyItMatched: 'Matches because the presentation includes machine learning project slides and discussion content as described.',
      sourceLocation: 'Google Drive / Projects / Machine Learning / Presentations',
      fileHistory: [
        'Revised after final presentation rehearsal',
        'Includes comments from project supervisor',
        'Saved as a final deck version'
      ],
      relatedDocuments: ['ML Research Summary.pdf', 'Model Evaluation Notes.docx'],
      tags: ['machine learning', 'presentation', 'project', 'slides'],
      relevance: 'High relevance'
    }
  ],
  sources: [
    {
      id: 'local-files',
      name: 'Local Files',
      status: 'Connected',
      indexed: '1,248 items',
      lastSync: 'Today, 09:42',
      indexingStatus: 'Indexed',
      description: 'Documents, notes and coursework archives stored on your device.'
    },
    {
      id: 'drive',
      name: 'Google Drive',
      status: 'Connected',
      indexed: '3,420 items',
      lastSync: 'Today, 14:32',
      indexingStatus: 'Synced',
      description: 'Shared files and academic folders aggregated for semantic search.'
    },
    {
      id: 'gmail',
      name: 'Gmail',
      status: 'Not Connected',
      indexed: '0 items',
      lastSync: 'Not synced',
      indexingStatus: 'Awaiting connection',
      description: 'Emails can be indexed for message-level retrieval in the future.'
    }
  ],
  history: [
    { day: 'Today', items: [
      { id: 'mentor-progress-report', query: 'Find my mentor-mentee report', time: '12:30' },
      { id: 'internship-documents', query: 'Find my internship documents', time: '09:18' }
    ] },
    { day: 'Yesterday', items: [
      { id: 'dccn-assignment', query: 'Find my DCCN assignment', time: '18:42' }
    ] },
    { day: 'Sep 28', items: [
      { id: 'machine-learning-presentation', query: 'Machine learning project files', time: '14:52' }
    ] }
  ]
};
