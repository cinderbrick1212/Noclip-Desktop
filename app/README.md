# Open Interface

### Usage
```commandline
python3 app.py
```

### System Diagram

**Standard mode** (single LLM — GPT-5, GPT-4o, Gemini, etc.):
```
+--------------------------------------------------------------------+
| App                                                                |
|                                                                    |
|    +-------+                                                       |
|    |  GUI  |                                                       |
|    +-------+                                                       |
|        ^                                                           |
|        | (via MP Queues)                                           |
|        v                                                           |
|  +-----------+  (Screenshot + Goal)  +-----------+                 |
|  |           | --------------------> |           |                 |
|  |    Core   |                       |    LLM    |                 |
|  |           | <-------------------- | (GPT-5/…) |                 |
|  +-----------+    (Instructions)     +-----------+                 |
|        |                                                           |
|        v                                                           |
|  +-------------+                                                   |
|  | Interpreter |                                                   |
|  +-------------+                                                   |
+--------------------------------------------------------------------+
```

**Moondream2 Hybrid mode** (2-LLM pipeline — local vision + remote planning):
```
+--------------------------------------------------------------------+
| App                                                                |
|                                                                    |
|    +-------+                                                       |
|    |  GUI  |                                                       |
|    +-------+                                                       |
|        ^                                                           |
|        | (via MP Queues)                                           |
|        v                                                           |
|  +-----------+         +------------------------------------------+|
|  |           |         | MoondreamHybrid                          ||
|  |           |         |                                          ||
|  |           |  Goal   |  Screenshot ──► Moondream2 (local/cloud) ||
|  |    Core   | ------> |                   caption() ─┐ parallel  ||
|  |           |         |                   query()  ──┤           ||
|  |           |         |                              v           ||
|  |           |         |              Text description            ||
|  |           |         |                     │                    ||
|  |           |         |                     v                    ||
|  |           | <------ |          Planning LLM (text-only)        ||
|  +-----------+  JSON   |            (gpt-4o-mini / etc.)          ||
|        |               +------------------------------------------+|
|        v                                                           |
|  +-------------+                                                   |
|  | Interpreter | ──► pyautogui (mouse + keyboard)                  |
|  +-------------+                                                   |
+--------------------------------------------------------------------+
```

### Performance pipeline (Moondream2 Hybrid)

Between automation steps, the vision analysis for step N+1 is
**prefetched in a background thread** while commands for step N execute:

```
Step N:  [Moondream ∥ caption+query] → [Planning LLM] → [Execute cmds] ─╮
Step N+1:                                                 [Prefetch ∥]  ─╯→ [Planning LLM] → [Execute] ─╮
Step N+2:                                                                    [Prefetch ∥]  ─────────────╯→ ...
```

### Architecture decision: why vision/planning split, not mouse/keyboard

We evaluated splitting the local model into a "mouse LLM" and a "keyboard
LLM" and concluded the **vision/planning split is superior**:

| Criterion | Vision / Planning split ✅ | Mouse / Keyboard split ❌ |
|-----------|:---:|:---:|
| Coordination needed | Minimal (text handoff) | High (focus, modifiers, state) |
| Memory on 8 GB | 1 local model | 2 local models (~2× RAM) |
| Covers all tasks | 100% | ~75-85% without workarounds |
| Modifier combos (ctrl+click) | Handled by single planner | Requires cross-model sync |
| Click-to-focus → type | Single plan, sequential | Needs handshake protocol |
| Latency overhead | Low (async prefetch) | High (coordination round-trips) |