ticket_id: "<ticket-id>"
change_id: "<change-id>"
confidence:
  overall: THAP
  code_graph: THAP
  database: THAP
  memory: THAP
sources:
  requirement: "{{ platform.framework_root }}/knowledge/active/REQUIREMENT.md"
  explore_context: "{{ platform.framework_root }}/knowledge/active/EXPLORE_CONTEXT.md"
  openspec: "openspec/changes/<change-id>/"
ua_kg:
  graph_status: "unavailable"
  graph_timestamp: null
  entry_points: []
  blast_radius: []
database:
  required: false
  evidence: []
architecture:
  boundaries: []
  risks: []
dna:
  hard_principles: []
  complexity_thresholds: {}
conventions:
  relevant_sections: []
memory:
  related_decisions: []

## Applicable DNA/Conventions
<!-- Orchestrator nhét slice rule-id khớp applies_to của node vào đây trước khi dispatch -->
