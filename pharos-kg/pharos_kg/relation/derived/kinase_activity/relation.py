"""Attach the kinase target and the ligand record to each activity row."""

from typing import Any, cast

from kg_build_system import (
    Claim, Contract, Definition, DerivedRelation, DerivedRelationOptions,
    Limitation, Meaning, Omitted, Purpose, computed_field,
)

from pharos_kg.relation.derived.kinase_protein.relation import KinaseProtein
from pharos_kg.relation.source.ncats_ligand import NcatsLigand
from pharos_kg.relation.source.ncats_ligand_activity import NcatsLigandActivity

first = NcatsLigandActivity.row_source().join(
    NcatsLigand.row_source(),
    on=lambda activity, ligand: (activity.ncats_ligand_id, ligand.id),
)
rows = first.join(
    KinaseProtein.row_source(),
    on=lambda pair, kinase: (pair.left.extract(lambda value: value.target_id),
                             kinase.target_id),
)

shape = cast(Any, rows.shape)
activity = shape.left.extract(lambda value: value.left)
ligand = shape.left.extract(lambda value: value.right)
kinase = shape.right


class KinaseActivity(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="kinase_activity",
        contract=Contract(
            definition=Definition(
                grain="one row per activity measurement against a kinase target",
                identity=("row_id",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "State what the release measured for a ligand against a kinase, "
                    "and on what citation.",
                    limitations=(
                        Limitation(
                            "A measurement against a target outside the kinase slice "
                            "is absent."
                        ),
                        Limitation(
                            "Assay types differ and are not converted; a value is "
                            "reported as the source stated it."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one measurement whose target is a kinase."),
                    Claim("No measurement is filtered by assay type or potency."),
                ),
            ),
        ),
    )

    row_id = computed_field(activity.extract(lambda value: value.id),
                            meaning=Omitted)
    target_key = computed_field(kinase.extract(lambda value: value.uniprot),
                                meaning=Omitted)
    ligand_identifier = computed_field(
        ligand.extract(lambda value: value.identifier), meaning=Omitted
    )
    compound_name = computed_field(ligand.extract(lambda value: value.name),
                                   meaning=Omitted)
    isdrug = computed_field(ligand.extract(lambda value: value.isdrug),
                            meaning=Omitted)
    smiles = computed_field(ligand.extract(lambda value: value.smiles),
                            meaning=Omitted)
    pubchem = computed_field(ligand.extract(lambda value: value.pubchem),
                             meaning=Omitted)
    chembl = computed_field(ligand.extract(lambda value: value.chembl),
                            meaning=Omitted)
    act_value = computed_field(activity.extract(lambda value: value.act_value),
                               meaning=Omitted)
    act_type = computed_field(activity.extract(lambda value: value.act_type),
                              meaning=Omitted)
    reference = computed_field(activity.extract(lambda value: value.reference),
                               meaning=Omitted)
    pubmed_ids = computed_field(
        activity.extract(lambda value: value.pubmed_ids), meaning=Omitted
    )
