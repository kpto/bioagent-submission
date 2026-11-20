"""Rule: a STRING interaction below the project threshold is uninformative."""

NAME = "string_below_700"
APPLIES_TO = ("interacts_with",)
CONFIDENCE = 0.90
REASON = "STRING interaction below the project threshold"
# Applicability is the planner's job (the component name); the predicate states
# only the evidence condition. Record relations carry no type column: the writer
# stamps kind and type from the artifact identity.
PREDICATE = (
    "list_contains(sources, 'STRINGDB')"
    " AND score IS NOT NULL AND score < 700"
)
