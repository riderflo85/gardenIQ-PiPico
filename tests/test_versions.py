import sys

from src.__version__ import get_micropython_version


class TestGetMicropythonVersion:
    """Test suite for get_micropython_version function."""

    def test_get_micropython_version_standard_format(self, monkeypatch):
        """
        GIVEN a standard MicroPython version string in sys.version
        WHEN get_micropython_version is called
        THEN it should return the version without the 'v' prefix
        """
        # GIVEN
        mock_version = "3.4.0; MicroPython v1.25.0 on 2025-04-15"
        monkeypatch.setattr(sys, "version", mock_version)

        # WHEN
        result = get_micropython_version()

        # THEN
        assert result == "1.25.0"

    def test_get_micropython_version_different_version(self, monkeypatch):
        """
        GIVEN a different MicroPython version string
        WHEN get_micropython_version is called
        THEN it should correctly extract and return the version
        """
        # GIVEN
        mock_version = "3.4.0; MicroPython v1.20.5 on 2024-01-10"
        monkeypatch.setattr(sys, "version", mock_version)

        # WHEN
        result = get_micropython_version()

        # THEN
        assert result == "1.20.5"

    def test_get_micropython_version_major_version_change(self, monkeypatch):
        """
        GIVEN a MicroPython version string with a major version change
        WHEN get_micropython_version is called
        THEN it should correctly extract and return the version
        """
        # GIVEN
        mock_version = "3.5.0; MicroPython v2.0.0 on 2026-01-01"
        monkeypatch.setattr(sys, "version", mock_version)

        # WHEN
        result = get_micropython_version()

        # THEN
        assert result == "2.0.0"

    def test_get_micropython_version_with_patch_number(self, monkeypatch):
        """
        GIVEN a MicroPython version string with patch number
        WHEN get_micropython_version is called
        THEN it should correctly extract the full version including patch
        """
        # GIVEN
        mock_version = "3.4.0; MicroPython v1.19.1 on 2023-12-15"
        monkeypatch.setattr(sys, "version", mock_version)

        # WHEN
        result = get_micropython_version()

        # THEN
        assert result == "1.19.1"

    def test_get_micropython_version_removes_v_prefix(self, monkeypatch):
        """
        GIVEN a MicroPython version string with 'v' prefix
        WHEN get_micropython_version is called
        THEN it should return the version without the 'v' prefix
        """
        # GIVEN
        mock_version = "3.4.0; MicroPython v1.23.0 on 2025-06-01"
        monkeypatch.setattr(sys, "version", mock_version)

        # WHEN
        result = get_micropython_version()

        # THEN
        assert not result.startswith("v")
        assert result == "1.23.0"
