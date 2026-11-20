"""The pinned Pharos 3.19 database dump and the tables read from it."""

from pathlib import Path

from kg_build_system import (
    Asset,
    AssetAuthority,
    AssetGovernance,
    AssetLayout,
    AssetLicense,
    AssetOptions,
    AssetProfile,
    Claim,
    Limitation,
    Meaning,
    Purpose,
)

SOURCE_ROOT = Path(__file__).resolve().parents[2]
DUMP = SOURCE_ROOT / "data" / "source" / "pharos319.sql.gz"
CACHE = SOURCE_ROOT / "data" / "source" / "pharos319"
ARCHIVE_SHA256 = (
    "86ebfffdd5fd03bcc23ef43a31251d40572ccd7feec62dadd3215f276f8b0953"
)
ARCHIVE_BYTES = 2_257_847_063


class PharosDump(Asset):
    """The MySQL dump NCATS publishes for Pharos 3.19.

    The archive is the asset: one MySQL dump, one row per source row. The
    project's dump adapter decodes the table a declaration names and may keep a
    Parquet reading in ``data/source/pharos319`` as a cache; each extracted table
    carries a small marker with the archive digest, its row count and its own
    digest. The cache is the adapter's business, not the contract.
    """

    options = AssetOptions(
        name="pharos319",
        website="https://opendata.ncats.nih.gov/public/pharos/archive/",
        version="3.19 (TCRD 6.13.4)",
        profile=AssetProfile(
            subject="targets, diseases, ligands, annotations and their evidence",
            coverage="the complete Pharos 3.19 database",
            authority=AssetAuthority.PRIMARY,
            basis="the vendor's own database dump, not a query result",
        ),
        layout=AssetLayout(
            kind="mysqldump",
            locator=str(DUMP),
            format="mysqldump",
            selector="{table}",
            members={
                "disease_evidence": "disease",
                "gene_xref": "xref",
                "go_annotation_record": "goa",
                "go_term_record": "go",
                "expression_record": "expression",
                "ncats_ligand": "ncats_ligands",
                "ncats_ligand_activity": "ncats_ligand_activity",
                "pathway_record": "pathway",
                "phenotype_record": "phenotype",
                "protein": "protein",
                "protein_interaction": "ncats_ppi",
                "target": "target",
                "target_protein": "t2tc",
                "mondo_parent": "mondo_parent",
                "go_parent": "go_parent",
            },
            properties={
                "cache": str(CACHE),
                "archive_url": (
                    "https://opendata.ncats.nih.gov/public/pharos/archive/"
                    "pharos319.sql.gz"
                ),
            },
        ),
        governance=AssetGovernance(
            license=AssetLicense("CC-BY-SA-4.0"),
            owner="pharos-kg data",
            metadata={
                "attribution": "Pharos / TCRD, NCATS and the University of New Mexico",
                "archive": "pharos319.sql.gz",
            },
        ),
        meaning=Meaning(
            purpose=Purpose(
                "Read the released database itself, so that every selection, "
                "join and aggregation the graph performs is a declared step a "
                "reader can inspect, rather than a property of a vendor query.",
                limitations=(
                    Limitation(
                        "The tables are decoded by the project's dump adapter; the "
                        "cache marker states that reader's assumptions."
                    ),
                    Limitation(
                        "The archive may be absent from a checkout that carries only "
                        "the adapter's Parquet cache; each cache marker records the "
                        "archive digest it was read from."
                    ),
                    Limitation(
                        "Decimal columns are read as double and temporal columns "
                        "as text, keeping the dump's own representation."
                    ),
                    Limitation(
                        "TCRD aggregates upstream sources whose individual "
                        "licences still apply to the rows they contributed."
                    ),
                ),
            ),
            claims=(
                Claim(
                    "One source relation reads one table, one row per table row."
                ),
                Claim(
                    "No source relation selects, renames, joins or aggregates."
                ),
            ),
        ),
    )
