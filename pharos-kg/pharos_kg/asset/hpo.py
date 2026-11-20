"""The pinned Human Phenotype Ontology release, read as four tables."""

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

from pharos_kg.asset.release import HPO_RELEASE

SOURCE_ROOT = Path(__file__).resolve().parents[2] / "data" / "source" / "hpo"


class Hpo(Asset):
    """The Human Phenotype Ontology release and its disease cross-references.

    The release is published as text: an OBO ontology, a tab-separated
    annotation table and a gene annotation table. This asset is the reading the
    project consumes, with MONDO's own cross-references as a fourth table so
    that mapping an annotation's disease identifier to a graph key is a declared
    join rather than a rewritten column. ``HPO_RELEASE`` in :mod:`release` pins the
    four source files, each table's row count and the reader's assumptions.
    """

    release = HPO_RELEASE

    options = AssetOptions(
        name="hpo",
        website="https://hpo.jax.org/data/annotations",
        version="2026-09-02",
        profile=AssetProfile(
            subject="disease phenotypes, gene phenotypes and the phenotype ontology",
            coverage="every disease and gene the release annotates",
            authority=AssetAuthority.REFERENCE,
            basis="the ontology consortium's own annotation tables",
        ),
        layout=AssetLayout(
            kind="directory",
            locator=str(SOURCE_ROOT),
            format="parquet",
            selector="{table}.parquet",
            members={
                "hpo_term": "hp_term.parquet",
                "hpo_disease_phenotype": "disease_phenotype.parquet",
                "hpo_gene_phenotype": "gene_phenotype.parquet",
                "mondo_xref": "mondo_xref.parquet",
            },
            properties={"reader": "hpo"},
        ),
        governance=AssetGovernance(
            license=AssetLicense(
                "CC-BY-4.0",
                url="https://hpo.jax.org/data/annotations",
                attribution="Human Phenotype Ontology consortium and the MONDO team",
            ),
            owner="pharos-kg data",
            metadata={
                "attribution": "HPO and MONDO",
                "release": "hp.obo 2026-09-02, phenotype.hpoa 2026-09-02",
            },
        ),
        meaning=Meaning(
            purpose=Purpose(
                "Give a disease the phenotypes its patients were recorded with, and "
                "give a gene the phenotypes its variants were recorded with, so that "
                "a reader can reach a disease through the body rather than only "
                "through a target-disease row.",
                limitations=(
                    Limitation(
                        "An HPO annotation is a clinical observation recorded in a "
                        "cohort, not a mechanism."
                    ),
                    Limitation(
                        "Annotation coverage is uneven: rare diseases are annotated "
                        "densely, common diseases barely."
                    ),
                    Limitation(
                        "The release writes disease identifiers in OMIM and Orphanet; "
                        "the MONDO cross-reference table is the release's own mapping, "
                        "and an identifier absent from it stays unmapped."
                    ),
                    Limitation(
                        "A gene annotation's disease column names the disease it was "
                        "recorded in, so a gene-phenotype row can restate a target-"
                        "disease association; the project records that overlap rather "
                        "than hiding it."
                    ),
                ),
            ),
            claims=(
                Claim("One source relation reads one table, one row per table row."),
                Claim("No source relation selects, renames, joins or aggregates."),
                Claim("Identifiers are read as the release writes them."),
            ),
        ),
    )
