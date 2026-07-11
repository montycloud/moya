# Support Desk

A routed **multi-agent delegation** demo with **tools** and **memory**.

```
Customer ─▶ router ─▶ DelegationManager ─▶ billing_agent   (tools: refund_policy, lookup_order)
                                        └─▶ shipping_agent  (tool:  lookup_order)
                          shared CompositeMemory remembers the order across turns
```

- **Multiple agents** — `billing_agent` and `shipping_agent` live in an
  `AgentRegistry` and are driven by a `DelegationManager`.
- **Tools** — specialists call the Python functions in `tools.py` (a fake orders DB
  and the refund policy).
- **Memory** — a shared `CompositeMemory` remembers the conversation, so the second
  turn (“what’s the refund policy if I send *it* back?”) still knows the order id
  from the first turn — even though a **different agent** answered it.
- **Deterministic routing** — a tiny keyword router picks the specialist, so the demo
  behaves identically on any backend.

## Run

```bash
export OPENAI_API_KEY=sk-...            # optional; else local Ollama
python -m examples.support_desk.main

# Verify tools + routing + memory + build with no LLM call:
python -m examples.support_desk.main --check
```

Known order ids for the demo: `A1001`, `A1002`, `A1003`. Long-term memory is written
under `./moya_memory/support_desk`.

## Files
| File | What it is |
|---|---|
| `tools.py` | `lookup_order` + `refund_policy` (a fake orders database). |
| `main.py` | Builds the specialists/registry/manager/memory and runs a 2-turn demo. |
