# Process Map

Current-state and future-state views of how a phantom inventory issue is caught today versus how this proof of concept proposes to catch it.

## Current state, manual and reactive

```mermaid
flowchart TD
    A[Inventory discrepancy occurs] --> B[System continues showing stock as available]
    B --> C{Discovered how?}
    C -->|Customer or staff happens to notice| D[Issue investigated ad hoc]
    C -->|Occasional manual audit| D
    C -->|Not discovered| E[Stock record stays wrong indefinitely]
    D --> F[Manual shelf check]
    F --> G[Record corrected if found]
```

**Key weakness:** discovery depends on chance or infrequent audits. Nothing prioritises which of thousands of SKUs to check first.

## Future state, statistically prioritised

```mermaid
flowchart TD
    A[Historical sales data] --> B[Monitoring velocity calculated per product]
    B --> C[Current hours without a sale tracked]
    C --> D[Anomaly score calculated via Poisson model]
    D --> E{Classification}
    E -->|Normal| F[No action]
    E -->|Warning| G[Monitor, no dispatch yet]
    E -->|Critical| H[Added to Priority Worklist]
    H --> I[Staff perform physical shelf check]
    I --> J{Outcome}
    J -->|Found| K[No record change needed]
    J -->|Misplaced| L[Item returned to correct location]
    J -->|Missing or damaged| M[Stock record corrected or written off]
    J -->|Unable to confirm| N[Escalated for further review]
```

**Key improvement:** staff attention is directed by evidence of unusual inactivity rather than chance discovery or blanket manual audits. The physical check remains the final confirmation step in both states, this system prioritises where to look, it doesn't replace looking.

**What this deliberately doesn't show:** the future-state diagram assumes live inventory and point-of-sale data feeding the monitoring step. In the current build, that step runs against a static historical dataset instead, this diagram shows the target process, not a claim that this proof of concept is fully wired into a live system already.
