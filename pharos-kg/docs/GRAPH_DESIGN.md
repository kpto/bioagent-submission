# Graph design rules

These rules govern the graph's shape. They are authoring constraints, not model
claims; the argument for each record is in `docs/KG.md`.

## Authoring rules

1. **One canonical target-disease edge per pair**, with evidence, confidence,
   sources and source counts attached. Redundant near-edges blur the
   association pattern and the provenance.
2. **Keep relation types and direction.** Do not flatten `binds`,
   `interacts_with`, `participates_in`, `translates_to` and
   `associated_with`.
3. **Keep the core small and precise.** Do not import weak associations to raise
   coverage. Degree is already the dominant shortcut.
4. **Put HPO, MONDO, Reactome and STRING in a background layer**, not the main
   graph. Background context belongs in features, cold-node explanation and
   separate typed relations.
5. **Author disease-intrinsic content.** HPO phenotypes and MONDO ancestry are
   the tested route to a disease that has no association of its own. Add them as
   typed background relations or properties.
6. **Author target context with confidence.** Keep PPI scores, ligand activity,
   GO terms, family and TDL. An observation is a source's assertion, not
   efficacy or mechanism.
7. **Record degree and source diversity.** A graph is read through hubs; state
   the degree distribution and do not rely on random negatives to describe it.
8. **Normalize provenance without erasing it.** A source list and a source count
   do not exist across every relation type: activity uses PMIDs, PPI uses
   scores, GO uses evidence codes. Keep relation-specific fields, and do not
   treat repeated rows from one source as independent support.
9. **Prune defects, not evidence.** A rule removes a null, a duplicate, a wrong
   endpoint or an impossible value. It does not remove a low-evidence
   association because the association is inconvenient.

## Ontology

Ontology is useful for identity, standards and explanation, but it is not a free
ranking boost:

- identifiers, validation and explanation: yes;
- HPO/MONDO background features for a disease with no association: yes;
- raw HPO overlap on ordinary ranking: nearly flat;
- dense ontology edges in the core: not supported.

The current graph therefore keeps HPO phenotype nodes and the two hierarchy
relations (`subclass_of`, `process_subclass_of`) as typed background, while the
core remains the target-disease, ligand, interaction, process, pathway,
expression and translation relations declared in `pharos_kg/graph/`.
