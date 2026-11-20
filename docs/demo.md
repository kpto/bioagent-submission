# Demo: antimicrobial susceptibility

A clinical microbiology lab has four exports and one question:

> Which isolates are resistant to which antibiotics, and what evidence supports
> that call?

This is a life-science demo for the harness. It is deliberately small, and it is
not a clinical decision tool.

| File | Grain | Identity | Traps |
| --- | --- | --- | --- |
| `isolates.csv` | one isolate | `isolate_id` | none |
| `antibiotics.csv` | one antibiotic | `antibiotic` | class and target are labels, not keys |
| `susceptibility.csv` | one test result | `isolate_id` + `antibiotic` + `method` | `>32` is not a number; one value is empty; `mg/L` and `µg/mL` are both used; the last row repeats the third; `ISO-999` is not in `isolates.csv` |
| `resistance_genes.json` | one gene call | `isolate_id` + `gene` | `ISO-999` is not in `isolates.csv` |

The graph should keep `ISO-999` visible as an unresolved isolate, keep the
duplicate and empty results visible, and state whether `mg/L` and `µg/mL` are
comparable. A MIC is antibiotic-specific: the graph must not compare values
across antibiotics, apply a clinical breakpoint, or claim a treatment decision or
a clinical outcome.

To run it, open this folder in OpenCode and say:

```
/kbs_init read PURPOSE.md for what I want
```

`PURPOSE.md` is the lab lead's request in their own words: what they want to
understand, who will look at it, and what they are worried about. Use it as the
request.
