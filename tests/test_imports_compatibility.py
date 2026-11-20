"""
Tests import compatibility across new modular packages and legacy entrypoints.
"""

def test_modular_imports():
    import src.common.types as common_types
    import src.vision.stage1_preprocessing as stage1
    import src.vision.stage2a_vlm as stage2a
    import src.vision.pipeline as pipeline_mod

    assert hasattr(common_types, "BoundingBox")
    assert hasattr(stage1, "preprocess_image")
    assert hasattr(stage2a, "infer_elements")
    assert hasattr(pipeline_mod, "run_pipeline")


def test_legacy_shim_imports():
    import src.types as legacy_types
    import src.stage1_preprocessing as legacy_stage1
    import src.stage2a_vlm as legacy_stage2a
    import src.pipeline as legacy_pipeline

    assert hasattr(legacy_types, "BoundingBox")
    assert hasattr(legacy_stage1, "preprocess_image")
    assert hasattr(legacy_stage2a, "infer_elements")
    assert hasattr(legacy_pipeline, "run_pipeline")


def test_root_cli_import():
    import run_pipeline as root_cli
    assert hasattr(root_cli, "run_pipeline")
