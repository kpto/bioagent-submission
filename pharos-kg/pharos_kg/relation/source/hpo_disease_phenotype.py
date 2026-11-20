"""One row per disease-phenotype annotation, as the release stores it."""

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


class HpoDiseasePhenotype(SourceRelation[Hpo]):

    options = SourceRelationOptions(
        name="hpo_disease_phenotype",
        contract=Contract(
            definition=Definition(
                grain="one row per disease, phenotype and reference",
                identity=("disease_id", "hpo_id", "evidence"),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Read the release's disease annotations as they stand, so that a "
                    "disease can state the phenotypes its patients were recorded "
                    "with.",
                    limitations=(
                        Limitation(
                            "The disease identifier is the release's, usually OMIM or "
                            "Orphanet; mapping it to MONDO is a declared join."
                        ),
                        Limitation(
                            "A NOT-qualified row states that a phenotype was "
                            "excluded; it is read here and filtered by the "
                            "declaration, not by the reader."
                        ),
                        Limitation(
                            "Frequency is the release's text, such as 5/10 or "
                            "HP:0040281, not a probability."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one annotation in the release."),
                    Claim("No row is filtered by qualifier, evidence or frequency."),
                ),
            ),
        ),
    )

    disease_id: Field[str] = field(
        definition=FieldDefinition("The disease identifier as the release writes it."),
        meaning=Omitted,
    )
    qualifier: Field[str] = field(
        definition=FieldDefinition(
            "The annotation's qualifier; NOT marks an excluded phenotype.",
            null_meaning="Absent when the row carries no qualifier.",
        ),
        meaning=Omitted,
    )
    hpo_id: Field[str] = field(
        definition=FieldDefinition("The phenotype term's accession."),
        meaning=Omitted,
    )
    evidence: Field[str] = field(
        definition=FieldDefinition(
            "The evidence code or reference the annotation cites.",
            null_meaning="Absent when the row cites no evidence.",
        ),
        meaning=Omitted,
    )
    frequency: Field[str] = field(
        definition=FieldDefinition(
            "The frequency as the release states it.",
            null_meaning="Absent when the release states no frequency.",
        ),
        meaning=Omitted,
    )
