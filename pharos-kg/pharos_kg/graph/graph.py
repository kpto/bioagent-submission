"""The one Pharos kinase graph declaration and its root meaning."""

from kg_build_system import Claim, Graph, GraphOptions, Limitation, Meaning, Purpose


class PharosKinaseGraph(Graph):

    options = GraphOptions(
        name="pharos_kinase",
        meaning=Meaning(
            purpose=Purpose(
                "Answer why a kinase is linked to a disease, a compound, another kinase "
                "or a biological process, and state what that link does not mean.",
                limitations=(
                    Limitation(
                        "A symbol is a label; only the accession is an identity."
                    ),
                    Limitation(
                        "An association is evidence that a source reports a relation, "
                        "not a mechanism."
                    ),
                    Limitation(
                        "A binding measurement is not efficacy, selectivity or safety."
                    ),
                    Limitation(
                        "An interaction is undirected; its relation type states "
                        "whether an experiment or an inference reports it, and most "
                        "interactions carry no probability."
                    ),
                    Limitation(
                        "A GO annotation is an assertion with an evidence code, not a "
                        "causal explanation."
                    ),
                    Limitation(
                        "Disease associations, interactions and compound measurements "
                        "carry every row the release holds for the kinase slice; GO "
                        "annotations and gene links still come from a per-target "
                        "capped view of the release."
                    ),
                    Limitation(
                        "A disease identity is a CURIE when the release states one and "
                        "a name-derived key otherwise; the latter is less stable."
                    ),
                    Limitation(
                        "A missing edge means the release does not report the "
                        "assertion; it does not prove absence."
                    ),
                ),
            ),
            claims=(
                Claim(
                    "A target is a UniProt protein; a gene is a separate HGNC locus "
                    "joined by translates_to."
                ),
                Claim(
                    "An edge is one assertion the release reports for one pair, not a "
                    "claim of causation."
                ),
                Claim(
                    "An experimental interaction is a pair at least one non-STRING "
                    "source reports; a predicted interaction is one only STRING "
                    "reports."
                ),
                Claim(
                    "Evidence is carried beside the edge so a reader can see which "
                    "source record produced it."
                ),
                Claim(
                    "A compound is identified by the release's LyChI hash where it "
                    "states one, and by the source compound identifier otherwise."
                ),
                Claim(
                    "A maximum confidence or score is the largest value among the "
                    "rows a source contributed, not a probability."
                ),
            ),
        ),
    )
