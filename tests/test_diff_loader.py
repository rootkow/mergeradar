from pathlib import Path

import pytest

from mergeradar.git.diff_loader import (
    DiffLoaderError,
    _build_spec,
    _merge_name_status_and_numstat,
    load_changed_files_from_diff_file,
)


def test_head_requires_base() -> None:
    with pytest.raises(DiffLoaderError, match="--head requires --base"):
        _build_spec(base=None, head="feature")


def test_rename_keeps_numstat_churn() -> None:
    changed_files = _merge_name_status_and_numstat(
        b"R050\0app/old.py\0app/new.py\0",
        b"5\t2\t\0app/old.py\0app/new.py\0",
    )

    assert len(changed_files) == 1
    assert changed_files[0].path == "app/new.py"
    assert changed_files[0].old_path == "app/old.py"
    assert changed_files[0].status == "R"
    assert changed_files[0].additions == 5
    assert changed_files[0].deletions == 2


def test_nul_delimited_git_output_preserves_unusual_filename_characters() -> None:
    path = "src/caf\N{LATIN SMALL LETTER E WITH ACUTE}\tmodule\nname.py"
    encoded_path = path.encode()

    changed_files = _merge_name_status_and_numstat(
        b"M\0" + encoded_path + b"\0",
        b"3\t1\t" + encoded_path + b"\0",
    )

    assert changed_files[0].path == path
    assert changed_files[0].additions == 3
    assert changed_files[0].deletions == 1


@pytest.mark.parametrize(
    ("metadata", "expected_status"),
    [
        ("new file mode 100644", "A"),
        ("deleted file mode 100644", "D"),
    ],
)
def test_saved_diff_detects_file_status(
    tmp_path: Path, metadata: str, expected_status: str
) -> None:
    diff_file = tmp_path / "change.diff"
    diff_file.write_text(
        "\n".join(
            [
                "diff --git a/app/file.py b/app/file.py",
                metadata,
                "--- a/app/file.py",
                "+++ b/app/file.py",
                "@@ -1 +1 @@",
                "-old",
                "+new",
            ]
        ),
        encoding="utf-8",
    )

    changed_files = load_changed_files_from_diff_file(diff_file)

    assert changed_files[0].status == expected_status
