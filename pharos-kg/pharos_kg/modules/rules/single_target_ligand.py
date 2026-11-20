"""Rule: a compound measured against one kinase carries no target evidence.

The ligand policy used to live in the relation SQL (``HAVING count(*) >= 2``),
where the excluded compounds never reached the graph and nothing recorded the
decision. The relations now carry ``target_count`` for every candidate, and this
module states the exclusion.
"""

NAME = "single_target_ligand"
APPLIES_TO = ("binds", "ligand")
CONFIDENCE = 0.85
REASON = "compound measured against a single kinase in this extract"
PREDICATE = "target_count < 2"
