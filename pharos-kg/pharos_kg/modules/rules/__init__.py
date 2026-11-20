"""The project's pruning rules: one module per rule, nothing shared but the list.

Each module states one decision: the edge components it governs, the predicate
over that component's evidence, its confidence and its reason. The workflow
contributes one annotator step per module, so adding a rule adds a step and
changes no other step.

The annotation fields are declared on every node and edge
(:mod:`pharos_kg.graph.annotated`); these names are the relation columns the
annotator steps write and the projection removes.
"""

from pharos_kg.modules.rules import single_target_ligand, string_below_700

RULES = (string_below_700, single_target_ligand)

VERDICT_COLUMN = "verdict"
RULE_COLUMN = "annotation_rule"
CONFIDENCE_COLUMN = "annotation_confidence"
REASON_COLUMN = "annotation_reason"
ANNOTATION_COLUMNS = (
    VERDICT_COLUMN,
    RULE_COLUMN,
    CONFIDENCE_COLUMN,
    REASON_COLUMN,
)
KEEP = "keep"
PRUNE = "prune"

__all__ = [
    "ANNOTATION_COLUMNS",
    "CONFIDENCE_COLUMN",
    "KEEP",
    "PRUNE",
    "REASON_COLUMN",
    "RULE_COLUMN",
    "RULES",
    "VERDICT_COLUMN",
]
