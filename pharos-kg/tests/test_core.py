"""Contract tests for the declarations and the compile step.

These run without the downloaded data: they assert the semantic model, the
standards annotations and the planner wiring. Data-dependent tests live in
``test_build.py``.
"""

from __future__ import annotations

from tests.support import blueprint_revision, compile_pharos, create_pharos_blueprint


def _ids(values: object) -> set[str]:
    result: set[str] = set()
    for annotation in values or []:  # type: ignore[union-attr]
        result.add(str(getattr(annotation, "id", "")))
    return result


def test_blueprint_shape() -> None:
    blueprint = create_pharos_blueprint()
    assert blueprint.graph_declaration is not None
    assert blueprint.graph_declaration.name == "pharos_kinase"
    # Nine node kinds and twelve edge kinds produce records; the two annotation
    # categories are abstract and produce none.
    assert len([
        node for node in blueprint.graph.nodes
        if not getattr(node, "abstract", False)
    ]) == 9
    assert len([
        edge for edge in blueprint.graph.edges
        if not getattr(edge, "abstract", False)
    ]) == 12
    # Two assets: the pinned Pharos 3.19 dump and the pinned Open Targets
    # 26.09 evidence release.
    assert len(blueprint.data.source_relations) == 22
    assert len(blueprint.assets.assets) == 3
    # associated_with (kinase_target, kinase_target_protein, kinase_protein,
    # target_disease_contribution, target_disease_pair, disease_label), the
    # interaction chain (kinase_interaction, kinase_interaction_pair,
    # protein_interaction_pair, experimental_interaction_pair,
    # predicted_interaction_pair), the ligand chain (kinase_activity,
    # ligand_target_pair, ligand_label) and the context chains
    # (kinase_phenotype, protein_phenotype_pair, phenotype_label;
    # kinase_pathway, protein_pathway_pair, pathway_label;
    # kinase_expression, protein_anatomy_pair, anatomical_label).
    assert len(blueprint.data.derived_relations) == 44
    assert len(blueprint.bindings) == 21
    assert blueprint_revision(blueprint)


def test_every_declaration_has_meaning() -> None:
    blueprint = create_pharos_blueprint()
    declarations = [
        blueprint.graph_declaration,
        *blueprint.graph.nodes,
        *blueprint.graph.edges,
        *blueprint.assets.assets,
        *blueprint.bindings,
        *(prop for node in blueprint.graph.nodes for prop in node.properties),
        *(prop for edge in blueprint.graph.edges for prop in edge.properties),
    ]
    missing = [
        getattr(value, "name", getattr(value, "debug_name", "?"))
        for value in declarations
        if getattr(value, "meaning", None) is None
    ]
    assert missing == []


def test_nodes_and_edges_carry_biolink_annotations() -> None:
    blueprint = create_pharos_blueprint()
    for node in blueprint.graph.nodes:
        if getattr(node, "abstract", False):
            continue
        assert "class" in _ids(getattr(node, "annotations", [])), node.name
    for edge in blueprint.graph.edges:
        if getattr(edge, "abstract", False):
            continue
        assert "predicate" in _ids(getattr(edge, "annotations", [])), edge.name


def test_relations_name_the_asset() -> None:
    blueprint = create_pharos_blueprint()
    names = {asset.name for asset in blueprint.assets.assets}
    for relation in blueprint.data.source_relations:
        symbol = relation.asset.symbol
        assert symbol.key.segments
        assert symbol.key.segments[0] in names


def test_compile_has_binding_and_source_steps() -> None:
    plan = compile_pharos()
    assert plan.steps
    assert plan.connections
    names = {step.name for step in plan.steps}
    assert any(name.startswith("source.") for name in names)
    assert any(name.startswith("binding.") for name in names)


def test_revision_is_stable() -> None:
    first = blueprint_revision(create_pharos_blueprint())
    second = blueprint_revision(create_pharos_blueprint())
    assert first == second
    assert len(first) == 16


def test_every_node_declares_its_identity_namespaces() -> None:
    blueprint = create_pharos_blueprint()
    for node in blueprint.graph.nodes:
        if getattr(node, "abstract", False):
            continue
        prefixes = [
            annotation.arguments.get("values")
            for annotation in node.annotations
            if annotation.namespace == "pharos" and annotation.id == "key_prefix"
        ]
        assert prefixes and prefixes[0], node.name


def test_design_guard_accepts_the_project_blueprint() -> None:
    from pharos_kg.modules.design_guard import design_problems

    assert design_problems(create_pharos_blueprint()) == []


def test_design_guard_refuses_a_prefixless_record_and_a_dangling_edge() -> None:
    from types import SimpleNamespace

    from pharos_kg.modules.design_guard import design_problems

    node = SimpleNamespace(
        name="protein",
        annotations=[],
    )
    endpoint = SimpleNamespace(key=SimpleNamespace(segments=("protein",)))
    edge = SimpleNamespace(
        name="binds",
        annotations=[],
        source=endpoint,
        target=SimpleNamespace(key=SimpleNamespace(segments=("ligand",))),
    )
    blueprint = SimpleNamespace(
        graph=SimpleNamespace(nodes=[node], edges=[edge]),
        bindings=[SimpleNamespace(name="protein"), SimpleNamespace(name="binds")],
    )
    problems = design_problems(blueprint)
    assert any("identity prefix" in item for item in problems)
    assert any("Biolink class" in item for item in problems)
    assert any("Biolink predicate" in item for item in problems)
    assert any("undeclared node 'ligand'" in item for item in problems)


def test_record_guard_predicate_names_the_declared_namespaces() -> None:
    import duckdb

    from pharos_kg.modules.design_guard import identity_predicate

    con = duckdb.connect()
    con.execute("CREATE TABLE records (build_key VARCHAR)")
    con.execute("INSERT INTO records VALUES ('PHAROS:P1'), ('PROTEIN:P2'), (NULL)")
    predicate = identity_predicate("node", ("PHAROS:",))
    invalid = con.execute(
        f"SELECT count(*) FROM records WHERE {predicate}"
    ).fetchone()[0]
    assert invalid == 2
