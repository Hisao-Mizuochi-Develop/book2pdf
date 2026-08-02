# tests/test_capture_profiles.py

from core.capture_profiles import (
    CaptureProfile, get_profile, get_all_profile_keys, BUILTIN_PROFILES
)


def test_capture_profile_to_dict_roundtrip():
    p = CaptureProfile(name="Test", page_wait=1.0)
    d = p.to_dict()
    p2 = CaptureProfile.from_dict(d)
    assert p2.name == "Test"
    assert p2.page_wait == 1.0


def test_get_builtin_profile():
    p = get_profile("kindle")
    assert p.name == "Kindle for PC"


def test_get_custom_profile():
    config = {
        "capture": {
            "profiles": {
                "custom1": {"name": "Custom", "page_wait": 2.0}
            }
        }
    }
    p = get_profile("custom1", config)
    assert p.name == "Custom"
    assert p.page_wait == 2.0


def test_get_all_profile_keys():
    config = {
        "capture": {
            "profiles": {"custom1": {}, "custom2": {}}
        }
    }
    keys = get_all_profile_keys(config)
    assert "kindle" in keys
    assert "custom1" in keys
    assert "custom2" in keys
