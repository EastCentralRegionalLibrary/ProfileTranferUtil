import os
import sys
import pytest

# Add root project directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from remove_motw import has_zone_identifier_ads, remove_mark_of_the_web_from_shortcuts


@pytest.fixture
def create_shortcut_with_ads(tmp_path):
    """
    Creates a dummy .url file with a Zone.Identifier ADS in a temporary directory.
    Returns the path to the file.
    """
    shortcut = tmp_path / "test_shortcut.url"
    shortcut.write_text("[InternetShortcut]\nURL=https://example.com")

    # Simulate Mark of the Web by writing to the ADS
    ads_path = str(shortcut) + ":Zone.Identifier"
    with open(ads_path, "w") as ads:
        ads.write("[ZoneTransfer]\nZoneId=3")

    return shortcut


def test_has_zone_identifier_ads_true(create_shortcut_with_ads):
    """
    Test that has_zone_identifier_ads returns True when ADS is present.
    """
    shortcut = create_shortcut_with_ads
    assert has_zone_identifier_ads(str(shortcut)) is True


def test_has_zone_identifier_ads_false(tmp_path):
    """
    Test that has_zone_identifier_ads returns False when ADS is absent.
    """
    shortcut = tmp_path / "clean_shortcut.url"
    shortcut.write_text("[InternetShortcut]\nURL=https://example.com")
    assert has_zone_identifier_ads(str(shortcut)) is False


def test_remove_mark_of_the_web_from_shortcuts(tmp_path):
    """
    Test that remove_mark_of_the_web_from_shortcuts removes the ADS from .url files.
    """
    # Create a fake user profile with a Desktop folder
    user_profile = tmp_path / "User"
    desktop = user_profile / "Desktop"
    desktop.mkdir(parents=True)

    # Create a shortcut with ADS
    shortcut = desktop / "test.url"
    shortcut.write_text("[InternetShortcut]\nURL=https://example.com")
    with open(str(shortcut) + ":Zone.Identifier", "w") as ads:
        ads.write("[ZoneTransfer]\nZoneId=3")

    # Ensure ADS exists before removal
    assert has_zone_identifier_ads(str(shortcut)) is True

    # Run the removal function
    remove_mark_of_the_web_from_shortcuts(str(user_profile))

    # Check that ADS is gone
    assert has_zone_identifier_ads(str(shortcut)) is False
