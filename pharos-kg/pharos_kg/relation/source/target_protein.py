"""One row per target-to-protein link, as the release stores it."""

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

from pharos_kg.asset.pharos_source import PharosDump


class TargetProtein(SourceRelation[PharosDump]):

    options = SourceRelationOptions(
        name="target_protein",
        contract=Contract(
            definition=Definition(
                grain="one row per target and protein link",
                identity=("target_id", "protein_id"),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Read the release's own link between a target and the protein it "
                    "names, so that joining a target-scoped fact to a protein key is "
                    "a declared join rather than an assumption.",
                    limitations=(
                        Limitation(
                            "A target can name more than one protein; the graph must "
                            "state how it chooses, and this relation does not choose."
                        ),
                        Limitation(
                            "nucleic_acid_id is not read; it is a separate identifier "
                            "space the graph does not use."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one target-protein link in Pharos 3.19."),
                    Claim("No link is preferred or deduplicated here."),
                ),
            ),
        ),
    )

    target_id: Field[int] = field(
        definition=FieldDefinition("The release's target key."),
        meaning=Omitted,
    )
    protein_id: Field[int] = field(
        definition=FieldDefinition("The release's protein key."),
        meaning=Omitted,
    )
