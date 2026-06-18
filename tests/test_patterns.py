from mergeradar.utils.patterns import build_keyword_map, normalized_parts, top_level_component


def test_normalized_parts_splits_posix_path() -> None:
    assert normalized_parts("app/auth/service.py") == ("app", "auth", "service.py")


def test_normalized_parts_normalizes_backslashes() -> None:
    assert normalized_parts("app\\auth\\service.py") == ("app", "auth", "service.py")


def test_normalized_parts_lowercases() -> None:
    assert normalized_parts("App/Auth/Service.py") == ("app", "auth", "service.py")


def test_normalized_parts_empty_string() -> None:
    assert normalized_parts("") == tuple()


def test_top_level_component_returns_first_part() -> None:
    assert top_level_component("app/auth/service.py") == "app"


def test_top_level_component_returns_none_for_empty() -> None:
    assert top_level_component("") is None


def test_top_level_component_single_component() -> None:
    assert top_level_component("Dockerfile") == "dockerfile"


def test_build_keyword_map_returns_defaults() -> None:
    kw = build_keyword_map()
    assert "auth" in kw
    assert "api" in kw
    assert "jwt" in kw["auth"]
    assert "route" in kw["api"]


def test_build_keyword_map_merges_overrides() -> None:
    kw = build_keyword_map({"auth": ["sso", "casbin"]})
    assert "jwt" in kw["auth"]
    assert "sso" in kw["auth"]
    assert "casbin" in kw["auth"]


def test_build_keyword_map_overrides_lowercased() -> None:
    kw = build_keyword_map({"auth": ["SSO"]})
    assert "sso" in kw["auth"]


def test_build_keyword_map_ignores_unknown_category() -> None:
    kw = build_keyword_map({"nonexistent": ["foo"]})
    assert "foo" not in kw.get("nonexistent", set())


def test_build_keyword_map_defaults_are_lowercased() -> None:
    kw = build_keyword_map()
    for keywords in kw.values():
        for keyword in keywords:
            assert keyword == keyword.lower(), f"keyword {keyword!r} is not lowercased"
