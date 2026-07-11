# ADR-007: Keep Tool and Skill as separate node types, with user-defined Skills Library

## Status
Accepted

## Date
2026-05-19

## Context

The node palette currently has 8 distinct types including both **Tool** and **Skill** nodes. A question arose during redesign: should these be merged into a single "Capability" node type to simplify the palette?

The Moya framework distinguishes them clearly:

| Concept | Moya definition | Typical use |
|---|---|---|
| **Tool** | A Python callable exposed to an agent's tool registry; the LLM decides when to call it | Search, calculator, API call, file read |
| **Skill** | A reusable bundle of tools + a prompt snippet injected into the agent's system prompt | "Travel safety advisor", "Code reviewer", "Data analyst persona" |

Arguments for merging:
- Fewer node types = simpler palette for new users
- Both ultimately attach capabilities to an Agent node
- Users unfamiliar with Moya may not know the distinction

Arguments for keeping separate:
- The distinction is real and meaningful — merging would hide a core architectural concept
- Tools are stateless callables; Skills carry prompt context that shapes agent behavior
- In the flow graph, a Tool connects to an Agent's tool registry; a Skill modifies the Agent's system prompt — these are different edges with different semantics
- Merging requires a sub-type selector inside the node, recreating the same cognitive load inside the node instead of at the palette level
- The Moya documentation and Python SDK use these terms consistently — a visual tool that renames them would create a vocabulary mismatch for users who also read the docs

A second question arose: the system ships with no built-in skills. Users need a way to **define and register their own skills** so they can attach them to agents in the flow canvas.

Options evaluated:

| Option | Description | Rejected because |
|---|---|---|
| **Keep separate** (current) | Tool and Skill remain distinct node types | ✓ Chosen |
| Merge into "Capability" | Single node type with sub-type toggle | Hides real distinction; vocabulary mismatch with SDK |
| Merge under "Tool", rename Skill to "Prompt Skill" | Keeps distinction but under unified label | Still confusing; non-standard Moya terminology |

## Decision

### Part 1 — Node types stay separate

**Tool and Skill remain as separate node types** in the Advanced tier of the palette.

To reduce confusion without merging:
- Tooltips on each node type clearly explain the difference: "Tool — a callable function the agent can invoke" vs "Skill — a reusable capability bundle with tools and a system prompt snippet"
- In the Inspector panel, Tool nodes show a "Function" field; Skill nodes show a "Skill Name" field with a note about the prompt snippet
- The connection rules are visually reinforced: Tool nodes connect to Agent nodes via a `uses_tool` edge (dashed); Skill nodes connect via a `has_skill` edge (solid teal)

### Part 2 — User-defined Skills Library

Users can define their own skills via a **Skills Library** accessible from the Builder toolbar (book icon, `⊞ Skills`). This opens a slide-in panel (from the left, distinct from the Inspector which slides from the right).

#### Skill definition schema

Each user-defined skill has:

```json
{
  "id": "uuid-v4",
  "name": "Travel Safety Advisor",
  "description": "Adds travel safety guidance to any agent",
  "prompt_snippet": "## Travel Safety\nAlways include relevant safety tips...",
  "tools": ["get_travel_advisory", "get_emergency_contacts"],
  "created_at": "2026-05-19T10:00:00Z"
}
```

- **name** — display name shown on the Skill node in the canvas
- **description** — one-line summary shown in the Skills Library list
- **prompt_snippet** — the text injected into the agent's system prompt; supports Markdown
- **tools** — optional list of tool function names this skill bundles; may be empty (prompt-only skill)

#### Skills Library panel

The panel has two tabs:

1. **My Skills** — skills the user has defined; each entry shows name + description + Edit / Delete buttons
2. **Drag to canvas** — a user can drag any skill from the list directly onto the canvas to create a pre-configured Skill node

A **+ New Skill** button opens the Skill Editor modal.

#### Skill Editor modal

Fields:
- Name (required, text input)
- Description (required, text input)
- Prompt Snippet (required, multiline textarea with a Markdown hint)
- Tools (optional, comma-separated function names)

On Save, the skill is added to the library and immediately available on the canvas.

#### Storage

Skills are stored in **`localStorage`** under the key `moya_skills_library` in v1.

This is intentional — skills are personal to the user's browser session and do not require a backend. When the user publishes a flow to the Marketplace, the skills used by that flow are **embedded in the flow's `AgentListing.flow` payload** so recipients have full definitions without needing the original user's localStorage.

#### Skill node behavior in the canvas

When a user drags a Skill node from the palette (Advanced tier), the Inspector opens with a **Skill Name dropdown** populated from the Skills Library. The user selects which defined skill this node represents. If no skills are defined yet, the Inspector shows: *"No skills defined. Open the Skills Library (⊞) to create one."*

## Consequences

### Positive
- Preserves the exact vocabulary of the Moya Python SDK — no cognitive dissonance for users who also write code
- Users are not locked into a fixed set of skills — they can create domain-specific skills for their use case
- Skill definitions are portable: embedded in published flows, so Marketplace recipients get the full definition
- localStorage for v1 means zero backend changes for the Skills Library itself

### Negative / Trade-offs
- Two nodes in the Advanced tier instead of one — slightly longer palette
- Skills are browser-local in v1 — a user who switches browsers or clears localStorage loses their skill definitions. Mitigated by the fact that published flows embed skill definitions, giving an indirect export path
- The Skill Editor modal requires users to write a `prompt_snippet` — this is a mildly technical task. A future enhancement could offer skill templates to guide authoring
- Tools listed in a skill are referenced by name only in v1; there is no validation that the named function exists in the backend. Runtime errors will surface during Real execution
