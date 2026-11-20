# The Pharos kinase graph — design and exploration

This is the detailed account of the graph's argument and of the design work that
produced it. It states the current model, not a change history. The ledger in
`journal/events/` is the record of how the model was reached; this document is
the reading of it.

The graph answers one question:

> Why is a kinase linked to a disease, a compound, another kinase or a biological
> process — and what does that link not mean?

It is built from typed declarations by `kg-build-system` over the Pharos 3.19
kinase family, with HPO and Open Targets as independent evidence. It is an
experimental research artifact, not a clinical or deployment claim.

## 1. The argument

The graph declaration in `pharos_kg/graph/` carries the purpose, one claim per
thing the graph asserts, and the limitations that bound the answer.

The claims:

- a target is a UniProt protein; a gene is a separate HGNC locus joined by
  `translates_to`;
- an edge is one assertion the release reports for one pair, not a claim of
  causation;
- an experimental interaction is a pair at least one non-STRING source reports;
  a predicted interaction is one only STRING reports;
- evidence is carried beside the edge so a reader can see the source record;
- a compound is identified by the release's LyChI hash where it states one, and
  by the source compound identifier otherwise;
- a maximum confidence or score is the largest value among the rows a source
  contributed, not a probability.

The limits that matter first:

- a symbol is a label; only the accession is an identity;
- an association is evidence that a source reports a relation, not a mechanism;
- a binding measurement is not efficacy, selectivity or safety;
- an interaction is undirected, and most interactions carry no probability;
- a GO annotation is an assertion with an evidence code, not a causal
  explanation;
- disease associations, interactions and compound measurements carry every row
  the release holds for the kinase slice; GO annotations and gene links still
  come from a per-target capped view;
- a disease identity is a CURIE when the release states one and a name-derived
  key otherwise, which is less stable;
- a missing edge means the release does not report the assertion; it does not
  prove absence.

Every node, edge, property, relation, binding and asset carries a purpose and
its limitations, or an explicit claims-only meaning. A declaration without a
meaning is a defect under the project's philosophy gate.

## 2. Records

Ten node declarations: nine concrete kinds and one abstract category. Thirteen
edge declarations: twelve concrete kinds and one abstract category. The two
abstract declarations (`annotated_record_node`, `annotated_record_edge`) carry
the pruning fields every concrete record shares; they produce no record of their
own.

### Node kinds

| Kind | What a reader uses it for |
| --- | --- |
| `protein` | Ligand binding, interactions and disease associations; identity is `PHAROS:<uniprot>` |
| `gene` | The HGNC locus and gene-disease literature; joined to a protein by `translates_to` |
| `disease` | The condition, including diseases no target in the slice reaches |
| `ligand` | The chemical entity for measured binding activity against a kinase |
| `biological_process` | GO functional context around a kinase |
| `phenotype` | An observed model phenotype after kinase perturbation |
| `hpo_term` | A clinical phenotype term, with the disease and gene vocabularies |
| `pathway` | A curated pathway membership, named by its database |
| `anatomical_entity` | Where a kinase is detected, from expression observations |

### Edge kinds

| Edge | What it asserts |
| --- | --- |
| `translates_to` | The HGNC gene encodes the UniProt protein |
| `associated_with` | A source reports a target-disease association, with its evidence types, sources and Open Targets evidence class |
| `binds` | A measured ligand activity against a kinase |
| `interacts_with` | The release reports a kinase-kinase interaction; the source mix says experimental or predicted |
| `participates_in` | A kinase is annotated to a GO term, with its evidence code and assigners |
| `has_phenotype` | A kinase perturbation is associated with an observed phenotype |
| `participates_in_pathway` | A kinase belongs to a curated pathway |
| `expressed_in` | A kinase is detected in an anatomical structure |
| `subclass_of` | One published disease is a kind of another |
| `process_subclass_of` | One published biological process is a kind of another |
| `disease_has_phenotype` | A published disease is recorded with a phenotype term |
| `has_hpo_phenotype` | A kinase's variants are recorded with a phenotype term |

The graph has **165 declared properties** across its records. Direction is part
of an edge's meaning; where an edge is logically undirected, its relation type
and source mix state that, and no reverse edge is stored.

## 3. Assets, relations and identity

Three assets supply the graph. The asset declaration pins the release files and
their digests; each table's row count and the reader's assumptions are declared
beside it.

| Asset | Release | Licence | Tables read |
| --- | --- | --- | --- |
| `pharos319` | Pharos 3.19 MySQL dump | CC-BY-SA-4.0 | 15: target, protein, t2tc, xref, disease, ncats_ligands, ncats_ligand_activity, ncats_ppi, go, goa, go_parent, mondo_parent, pathway, phenotype, expression |
| `hpo` | HPO 2026-09-02 | CC-BY-4.0 | 4: hp_term, disease_phenotype, gene_phenotype, mondo_xref |
| `opentargets2609` | Open Targets 26.09 | CC0-1.0 | 3: association, target_protein, disease |

Each asset's source step keeps its declared reading in `data/source/<asset>`.
When a table is missing, the step fetches the pinned release, verifies every
source file against the digest in the asset declaration, decodes the reader's
columns and checks the row count. A present cache is not downloaded again.

There are **22 source relations** and **44 derived relations**. A source relation
reads one table, one row per row: it decodes and casts, and carries no domain
join, filter, identifier translation, deduplication or aggregation. Those
operations belong to a derived relation or a value operation. A derived relation
states the relation it scans and the shape and grain it produces; a private
`Stage` composes inside one published relation and is not a consumer contract.

Identity is a stable key: `PHAROS:<uniprot>`, `HGNC:<id>`,
`MONDO:`/`DOID:`/`UMLS:`/`MESH:`/`OMIM:`/`NAME:<slug>`, `GO:<id>`, `MP:<id>`,
`UBERON:<id>`, or the source database CURIE for a pathway. Open Targets writes
`MONDO_0005148`; the reading stores `MONDO:0005148` and rewrites no other
identifier. A display label is never a key.

## 4. Bindings and the build

There are **21 bindings**. A binding states the fulfilment between a relation and
a record: it names the record's use, then says how the relation answers it —
grain, identity and coverage — and where it falls short. A binding is never the
parent of either side; the record's meaning stays on the record and the
relation's meaning on the relation.

The workflow plan has **251 steps** over the three assets. The output chain is:

```text
relations ──▶ publish_annotated_records
                    │  every candidate record, verdict=keep, empty marks
                    ▼
              annotate_rule_matches
                    │  one step per rule and component; mark a matching record
                    ▼
              project_kept_records
                    │  verdict=keep, schema intact
                    ├──────────────▶ write_annotated_graph  (graph.annotated.jsonl)
                    └──────────────▶ write_facts_graph      (graph.jsonl, no annotation fields)
                                             │
                                      reconcile_outputs
                                 annotated − pruned = facts, per kind
```

Each pruning rule is one module with its own predicate, confidence, reason and
boundary tests; adding a rule adds an annotator step and changes no other step.
The four annotation fields are declared on every node and edge, inherited from
the two abstract categories:

| Field | Meaning |
| --- | --- |
| `verdict` | `keep` or `prune` |
| `annotation_rule` | the rule or rules that marked the record |
| `annotation_confidence` | the rule confidence, not a probability that the biology is true |
| `annotation_reason` | the stated reason |

Every binding seeds a record with `keep` and three empty arrays. The facts graph
omits the four fields at the file boundary; it does not narrow the relation
schema.

## 5. What is shipped

The current build:

| Artifact | Records | Contents |
| --- | ---: | --- |
| `build/graph.annotated.jsonl` | 74,747 nodes / 239,939 edges | every candidate, with the four annotation fields |
| `build/graph.jsonl` | 28,359 nodes / 150,856 edges | the facts graph: `verdict=keep`, no annotation fields |
| `build/evidence.jsonl` | 179,215 entries | one occurrence-evidence entry per shipped record |

Audit on the shipped graph: **0 duplicate keys, 0 null keys, 0 dangling
endpoints**, and one evidence entry per record (coverage 1.0). The evidence entry
names the source files and tables, the record's identifying values and the source
labels that produced it.

The shipped graph is the one to submit as the KG. The annotated candidate is the
audit surface: it contains the records the project itself marks `prune`, so it is
not the asserted graph. The pruning verdicts are a separate report, not extra
edges in the KG.

### Evidence provenance

Every entry names the files and tables its binding read, resolved from the asset
declarations and each binding's relation closure rather than from a hand-kept
map. The HPO phenotype records, the two hierarchy relations and the Open Targets
contribution are therefore named. `sources` lists each file and table;
`source.files` and `source.tables` are the same set, deduplicated, and
`source.row` carries the record's own locating and evidence values. The Open
Targets class travels on the `associated_with` edge as `evidence_class` and in
the entry's row.

A record produced by a join names every table the join read. That set is the
provenance; it is not a single origin.

## 6. Evaluation

The ledger has **24 evaluation protocols** and **388 runs**:

- two gate protocols: the project gate run (audit, pruning, graph QA and
  held-out link prediction; earlier runs also covered explainability) and the
  held-out link-prediction protocol;
- nine test designs: committed shared split, fair per-positive, degree-matched,
  hard negatives, target cold start, disease cold start, fixed held-out,
  exact-degree/permutation checks, per-relation held-out, hard-negative training;
- thirteen prediction methods: heuristic scores, degree baselines, logistic
  regression, histogram gradient boosting, IDF-weighted SVD, full-graph SVD,
  ontology-borrowed SVD, GraphSAGE, GATv2, TransformerConv, R-GCN, rank
  ensembles, feature baselines.

A run links to its method and to the build revision it measured, and references
the test design that says how it was evaluated. Its result carries the graph arm,
configuration, seeds, every reported metric and the report path. The ledger detail is on the console.

Representative results, with the protocol stated:

| Design | Result |
| --- | --- |
| Committed shared five negatives | R-GCN 0.9761 / 0.9644 macro/micro; GraphSAGE 0.947 / 0.940; GATv2+GraphSAGE 0.9643 / 0.9660 |
| Fair per-positive | degree alone 0.7354; histogram 0.6834 / 0.6201; degree+SVD 70/30 0.7747 / 0.7732; SVD 0.5646 / 0.6471; GNNs 0.09–0.30 |
| Degree-matched | disease degree 0.2712 / 0.2482; histogram 0.2894 / 0.2866; IDF-SVD 0.4439 / 0.4994; hard-negative SVD 0.4532 / 0.5230 |
| Exact-degree and permutation | SVD 0.4218 / 0.5222 vs degree 0.1675 / 0.1680; permutation 0.2802 / 0.2525 vs real 0.4389 / 0.4955 |
| Target cold start | histogram 0.5006 / 0.4888; degree-matched cold 0.2879 / 0.3136; smoothed 0.3431 / 0.3913 |
| Disease cold start | ontology-borrowed SVD 0.4586 / 0.5388; raw ontology 0.2245 / 0.1972; base 0.1709 / 0.1718 |
| Context gain | R-GCN degree-matched 0.3789 → 0.4452; fair 0.8300 → 0.8751 |

How to read the table:

- The **committed shared-negative protocol is not deployment performance**. It
  has a 46.3% positive base rate, and 2,085 of 2,685 evaluation negatives are
  reused in training. Its 0.97 is a within-protocol ranking result.
- On **fair per-positive negatives**, disease degree alone is strong (0.7354);
  the IDF-SVD signal beats it on degree-matched and hard negatives, which is the
  first result that separates graph signal from the degree prior.
- The GNNs collapse on fair negatives; the histogram feature model is the best
  of the neural/nonlinear set there. Context features help the R-GCN on
  degree-matched and fair pairs, but do not make it a deployment model.
- Per relation, the picture is mixed: PPI 0.6216 vs degree 0.3085 and binds
  0.6339 vs 0.6137, but GO 0.4312 vs degree 0.5944. The graph is not uniformly
  informative.
- The reports contain no ComplEx result. TransE and RotatE appear in the
  narrative evaluation runs only; they have no report rows to reconstruct. The
  evaluated methods are the thirteen above.

## 7. The exploration

The ledger is the record of the design exploration. It is append-only: a
correction is a new finding or a withdrawal, and a revision adopts a proposal by
naming it.

Current shape:

| Event | Count |
| --- | ---: |
| events | 622 |
| revisions | 32 |
| findings created | 134 |
| finding withdrawals | 10 |
| proposals created | 28 |
| proposal withdrawals | 5 |
| evaluation protocols | 24 |
| evaluation runs | 388 |

The revisions fall into phases:

1. **First argument and extract** (B-1–B-6): the compiled Pharos blueprint, the
   pinned 3.19 extract with per-file digests, the first full build, and the
   machine-readable evaluation design.
2. **Context and scale** (B-7–B-16): the GNN experiment, the full and compact
   phenotype profiles and the extract refresh.
3. **Release-fed base and independent evidence** (B-17–B-30): the dump parser
   and Parquet cache, the target-disease migration, the ligand identity policy,
   Open Targets 26.09 with an evidence class on every association, the HPO
   disease and gene phenotypes, and the ontology hierarchies between published
   diseases and processes.
5. **Pruning and output** (B-31–B-32): the candidate-verdict prototype, then the
   post-processing design — one annotated graph, two outputs, reconciliation.

The decisions that govern the current graph:

- **P-13 / CD-0007** adopted the core five-relation graph as the earlier
  core graph; the release-fed revisions B-19–B-30 extended it to the
  current twelve relations. **P-14** recommended the two-profile package, with
  the compact phenotype layer as typed enrichment.
- **P-27** based the later designs on the release-fed base and ported the
  ontology, evidence and phenotype layers as separate revisions.
- **P-28 / CD-0006 / B-32** made pruning a post-processing projection: rules
  annotate a candidate graph, and the shipped file is the keep projection, not a
  filtered view of the relation declarations.
- **F-0080–F-0083** record the rule chain, the declared annotation fields, and
  the presentation boundary: the annotation is a schema field, omitted at the
  output file.

The compact phenotype profile remains an experiment on the earlier extract
(branch `phenotype-layer`); it is not in the current master build. Its findings are in the ledger.

The console is the reading surface:

- `kbs console` (or `kbs up`) serves the revision lineage, the catalog and the
  focused dependency diff, with the structured detail behind every card;
- `journal/events/` is the ledger itself.

## 8. Limits and non-claims

- The extract is a bounded-per-target sample for some layers; absence is not
  evidence of no relation.
- Scores and confidences are release values, not probabilities.
- A binding is a measurement, not efficacy, selectivity or safety.
- An association is a source's assertion, not a mechanism.
- The evidence sidecar names every table a binding read. A record produced by a
  join has several source tables; the set is the provenance, not a single
  origin.
- The committed-suite 0.97 is a protocol artifact; the fair and degree-matched
  results are the honest generalization accuracy, and even those are above a degree
  baseline by a small margin on some designs.
- No ComplEx evaluation exists in the reports. No deployment, clinical or
  whole-Pharos claim is made.
- The graph's purpose is the contract; the build, planner, executor and database
  are replaceable.

## 9. How to verify

```console
uv run kbs check --project pharos_kg
uv run kbs run --project pharos_kg
uv run pytest -q
```

`check` reads the argument back; `run` executes the 251-step plan and writes the
facts graph, the annotated candidate, the evidence sidecar and the plan; the
project test asserts no duplicate keys, no dangling endpoints, one evidence entry
per record and no entry without a source table. The framework validates each
ledger event when it is written and when the ledger is read.

The graph is an argument. The declaration is the product; the build is one
mechanism for delivering it.
