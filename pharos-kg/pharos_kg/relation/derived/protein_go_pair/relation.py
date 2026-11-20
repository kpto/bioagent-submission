"""Publish one row per kinase, GO term and evidence code."""

from kg_build_system import (
    Claim, Contract, Definition, DerivedRelation, DerivedRelationOptions,
    FieldDefinition, Limitation, Meaning, Omitted, Purpose, computed_field,
)

from pharos_kg.modules.row_operations import protein_go_pairs
from pharos_kg.relation.derived.kinase_go_term.relation import KinaseGoTerm

rows = KinaseGoTerm.row_source().custom_op(protein_go_pairs)


class ProteinGoPair(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="protein_go_pair",
        contract=Contract(
            definition=Definition(
                grain="one row per target, term and evidence code",
                identity=("target_key", "go_key", "evidence"),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "State that the release annotates a kinase with a process, "
                    "function or component, and on which evidence code.",
                    limitations=(
                        Limitation(
                            "An annotation is a source's assertion, not a causal "
                            "explanation of any other relation."
                        ),
                        Limitation(
                            "Evidence codes are kept apart and not weighted; an "
                            "electronic annotation counts as one assertion."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one target, term and evidence code."),
                    Claim("count is the number of annotations behind the row."),
                ),
            ),
        ),
    )

    target_key = computed_field(
        rows.shape.target_key,
        definition=FieldDefinition("The UniProt accession of the kinase."),
        meaning=Omitted,
    )
    go_key = computed_field(
        rows.shape.go_key,
        definition=FieldDefinition("The GO term identifier."),
        meaning=Omitted,
    )
    evidence = computed_field(
        rows.shape.evidence,
        definition=FieldDefinition(
            "The evidence code, or 'unspecified' when the release states none."
        ),
        meaning=Omitted,
    )
    count = computed_field(
        rows.shape.count,
        definition=FieldDefinition("The number of annotations behind the row."),
        meaning=Omitted,
    )
    assigners = computed_field(
        rows.shape.assigners,
        definition=FieldDefinition(
            "The distinct assigning groups, sorted ascending."
        ),
        meaning=Omitted,
    )
