"""One row per identifier the platform lists for a target."""

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

from pharos_kg.asset.opentargets import OpenTargets


class OtTargetProtein(SourceRelation[OpenTargets]):

    options = SourceRelationOptions(
        name="ot_target_protein",
        contract=Contract(
            definition=Definition(
                grain="one row per target and identifier",
                identity=("ensembl_id", "protein_id", "source"),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Publish the platform's nested target identifiers as a link "
                    "table, so that the mapping from its Ensembl target to a UniProt "
                    "protein is a declared join rather than an assumption.",
                    limitations=(
                        Limitation(
                            "A target lists identifiers from several namespaces; only "
                            "the Swiss-Prot rows are a reviewed protein identity."
                        ),
                        Limitation(
                            "The release stores these identifiers as a nested column; "
                            "the project adapter publishes them as one table."
                        ),
                        Limitation(
                            "An identifier that is absent here is unmapped, not "
                            "unknown to biology."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one identifier of one target."),
                    Claim("No identifier is filtered by namespace here."),
                ),
            ),
        ),
    )

    ensembl_id: Field[str] = field(
        definition=FieldDefinition("The Ensembl gene identifier of the target."),
        meaning=Omitted,
    )
    protein_id: Field[str] = field(
        definition=FieldDefinition("The identifier itself, in its own namespace."),
        meaning=Omitted,
    )
    source: Field[str] = field(
        definition=FieldDefinition(
            "The namespace the identifier belongs to, such as uniprot_swissprot."
        ),
        meaning=Omitted,
    )
