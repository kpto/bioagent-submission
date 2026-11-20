"""The pinned Open Targets Platform 26.09 release, read as three tables."""

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

from pharos_kg.asset.release import OPENTARGETS_RELEASE

SOURCE_ROOT = Path(__file__).resolve().parents[2] / "data" / "source" / "opentargets2609"


class OpenTargets(Asset):
    """The Open Targets Platform 26.09 target-disease evidence tables.

    The release is published as Parquet, one directory per dataset. This asset
    is the reading the project consumes: the association table restricted to its
    per-datatype rows, the nested target-protein identifiers published as a link
    table, and the disease labels. ``OPENTARGETS_RELEASE`` in :mod:`release` pins
    the source files, each table's row count and the reader's assumptions.
    """

    release = OPENTARGETS_RELEASE

    options = AssetOptions(
        name="opentargets2609",
        website="https://platform.opentargets.org/downloads",
        version="26.09",
        profile=AssetProfile(
            subject="target-disease associations and the evidence behind them",
            coverage="the complete platform release, all diseases and targets",
            authority=AssetAuthority.REFERENCE,
            basis="the platform's own integrated dataset, not a query result",
        ),
        layout=AssetLayout(
            kind="directory",
            locator=str(SOURCE_ROOT),
            format="parquet",
            selector="{table}.parquet",
            members={
                "ot_association": "association.parquet",
                "ot_target_protein": "target_protein.parquet",
                "ot_disease": "disease.parquet",
            },
            properties={"reader": "opentargets"},
        ),
        governance=AssetGovernance(
            license=AssetLicense("CC0-1.0", url="https://platform.opentargets.org/downloads", attribution="Open Targets Platform, EMBL-EBI and GSK"),
            owner="pharos-kg data",
            metadata={
                "attribution": "Open Targets Platform, EMBL-EBI and GSK",
                "release": "26.09",
                "dataset": "association_by_datatype_direct",
            },
        ),
        meaning=Meaning(
            purpose=Purpose(
                "Give every target-disease edge a second, independent statement of "
                "what kind of evidence supports it, so that a reader can tell a "
                "genetic association from a literature co-mention without leaving "
                "the graph.",
                limitations=(
                    Limitation(
                        "Open Targets integrates upstream sources whose individual "
                        "licences still apply to the rows they contributed."
                    ),
                    Limitation(
                        "Only the per-datatype rows of the association table are "
                        "read; the release's overall score, time series and novelty "
                        "columns are not part of this reading."
                    ),
                    Limitation(
                        "The nested target identifier column is published as a link "
                        "table by the project adapter; the release itself stores one "
                        "row per target."
                    ),
                    Limitation(
                        "Identifiers are read as CURIEs: the release writes "
                        "MONDO_0005148 and the reading stores MONDO:0005148. No other "
                        "identifier is rewritten."
                    ),
                ),
            ),
            claims=(
                Claim("One source relation reads one table, one row per table row."),
                Claim("No source relation selects, renames, joins or aggregates."),
                Claim("The release is read at the version the manifest records."),
            ),
        ),
    )
