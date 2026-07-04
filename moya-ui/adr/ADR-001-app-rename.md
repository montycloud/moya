# ADR-001: App renamed to Moya Agent Studio

## Status
Accepted

## Date
2026-05-19

## Context

The existing application was named **MOYA Flow Builder**. This name:
- Emphasises the mechanism ("flow builder") rather than the outcome ("building agents")
- Is too developer-centric — implies you need to understand flows and pipelines before you can get value
- Does not communicate the Marketplace concept that is being added
- Does not align with the broader goal of making Moya accessible to non-developers

Alternative names considered:
| Name | Reason rejected |
|---|---|
| Moya Agent Development Portal | Too long; "portal" sounds enterprise-heavy |
| Moya Builder | Too generic |
| Moya Forge | Evocative but unclear |
| Moya Studio | ✓ Short, warm, creative — implies a workspace for building |

## Decision

The application will be renamed to **Moya Agent Studio**.

- Displayed in the top-left of the navigation bar
- Referenced in all documentation, the `README.md`, and `package.json` `name` field
- The URL path structure and directory name (`moya-ui/`) remain unchanged to avoid breaking existing references

## Consequences

### Positive
- Name communicates the purpose (building agents) rather than the implementation (flows)
- "Studio" implies a creative workspace — approachable for non-developers
- Short enough to fit comfortably in a nav bar and page title
- Pairs naturally with "Agent Marketplace" as the companion feature

### Negative / Trade-offs
- Existing documentation and screenshots reference "Flow Builder" — all must be updated
- No technical changes required; cost is purely documentation
