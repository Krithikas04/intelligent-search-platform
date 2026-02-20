"""
Tests for config defaults — especially the dynamic data_dir path.
"""
import os
from pathlib import Path


def test_default_data_dir_is_derived_from_file():
    """data_dir default must be derived from __file__ (portable), not a literal string."""
    from backend import config as cfg
    from backend.config import _DEFAULT_DATA_DIR

    # Must end with 'searchAgent'
    assert Path(_DEFAULT_DATA_DIR).name == "searchAgent"

    # The default must equal what Path(__file__).parent.parent / "searchAgent" resolves to,
    # confirming it's computed dynamically rather than a literal hardcoded string.
    expected = str(Path(cfg.__file__).parent.parent / "searchAgent")
    assert _DEFAULT_DATA_DIR == expected, (
        f"data_dir default ({_DEFAULT_DATA_DIR!r}) is not derived from __file__"
    )


def test_default_data_dir_resolves_correctly():
    """The default data_dir should point to <project_root>/searchAgent."""
    from backend.config import _DEFAULT_DATA_DIR
    # The path should be an absolute path (resolved by Path)
    assert os.path.isabs(_DEFAULT_DATA_DIR), "data_dir default should be an absolute path"


def test_default_model_is_claude():
    """Default model must be claude-sonnet-4-6, not gpt-4o-mini."""
    from backend.config import Settings
    # Instantiate with minimal required fields
    import os
    os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test")
    os.environ.setdefault("OPENAI_API_KEY", "sk-test")
    os.environ.setdefault("PINECONE_API_KEY", "pcsk-test")
    os.environ.setdefault("JWT_SECRET_KEY", "test-secret-32-bytes-long-xxxxxxx")
    # Read from Settings class default directly
    assert Settings.model_fields["model"].default == "claude-sonnet-4-6"
