"""One row per phenotype term the release defines."""

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


class HpoTerm(SourceRelation[Hpo]):

    options = SourceRelationOptions(
        name="hpo_term",
        contract=Contract(
            definition=Definition(
                grain="one row per phenotype term",
                identity=("hpo_id",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Read the phenotype ontology's terms so that a phenotype in the "
                    "graph carries the name the ontology gives it, not only its "
                    "accession.",
                    limitations=(
                        Limitation(
                            "Only the identifier and the label are read; the "
                            "ontology's hierarchy and synonyms are not part of this "
                            "reading."
                        ),
                        Limitation(
                            "Obsolete terms are absent from the release's own term "
                            "list, so a phenotype that only an obsolete term names "
                            "cannot be labelled from here."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one phenotype term in the release."),
                    Claim("No term is filtered, joined or renamed here."),
                ),
            ),
        ),
    )

    hpo_id: Field[str] = field(
        definition=FieldDefinition("The term's accession, such as HP:0001250."),
        meaning=Omitted,
    )
    name: Field[str] = field(
        definition=FieldDefinition(
            "The term's label.",
            null_meaning="Absent when the release gives no label.",
        ),
        meaning=Omitted,
    )
