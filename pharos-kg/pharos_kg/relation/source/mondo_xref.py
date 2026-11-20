"""One row per cross-reference MONDO publishes for its terms."""

from kg_build_system import (
    Claim,
    Contract,
    Definition,
    Field,
    FieldDefinition,
    Limitation,
    Meaning,
    Omitted,
    Purpose,
    SourceRelation,
    SourceRelationOptions,
    field,
)

from pharos_kg.asset.hpo import Hpo


class MondoXref(SourceRelation[Hpo]):

    options = SourceRelationOptions(
        name="mondo_xref",
        contract=Contract(
            definition=Definition(
                grain="one row per source identifier and MONDO term",
                identity=("source_id", "mondo_id"),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Read MONDO's own cross-references, so that an annotation written "
                    "against an OMIM or Orphanet disease can reach the MONDO identity "
                    "the graph uses without the project inventing a mapping.",
                    limitations=(
                        Limitation(
                            "The mapping is the ontology's assertion, not a curated "
                            "equivalence; one source disease can map to several MONDO "
                            "terms and the relation keeps every row."
                        ),
                        Limitation(
                            "Only OMIM and Orphanet references are read, because they "
                            "are the namespaces the annotation release uses."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one cross-reference in the release."),
                    Claim("No mapping is resolved, deduplicated or ranked here."),
                ),
            ),
        ),
    )

    source_id: Field[str] = field(
        definition=FieldDefinition(
            "The external identifier, such as OMIM:154700 or ORPHA:558."
        ),
        meaning=Omitted,
    )
    mondo_id: Field[str] = field(
        definition=FieldDefinition("The MONDO term the release maps it to."),
        meaning=Omitted,
    )
