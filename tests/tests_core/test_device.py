from src.core.device import get_device_uid


class TestGetDeviceUID:
    """Tests for the get_device_uid function."""

    def test_get_device_uid_returns_string(self):
        """Verify that the function returns a string."""
        # GIVEN: The default mock is in place
        # (No specific setup needed)

        # WHEN: Calling get_device_uid
        result = get_device_uid()

        # THEN: The result should be a string
        assert isinstance(result, str)

    def test_get_device_uid_returns_hex_string(self):
        """Verify that the function returns a valid hexadecimal string."""
        # GIVEN: The default mock is in place
        # (No specific setup needed)

        # WHEN: Calling get_device_uid
        result = get_device_uid()

        # THEN: All characters should be valid hexadecimal characters
        assert all(c in "0123456789abcdef" for c in result.lower())

    def test_get_device_uid_with_default_mock(self):
        """Verify the result with the default mock."""
        # GIVEN: The default mock returns b'\xe6cX\x98c\\7/'
        # (Mock configured in tests/mocks/machine.py)

        # WHEN: Calling get_device_uid
        result = get_device_uid()

        # THEN: The result should be the hexadecimal representation "e6635898635c372f"
        assert result == "e6635898635c372f"

    def test_get_device_uid_consistent_output(self):
        """Verify that the function always returns the same result for the same UID."""
        # GIVEN: The default mock is in place
        # (No specific setup needed)

        # WHEN: Calling get_device_uid twice
        result1 = get_device_uid()
        result2 = get_device_uid()

        # THEN: Both results should be identical
        assert result1 == result2

    def test_get_device_uid_with_different_ids(self, mocker):
        """Verify that different UIDs give different results."""
        # GIVEN: Mocks configured for unique_id and hexlify
        mock_unique_id = mocker.patch("src.core.device.unique_id")
        mock_hexlify = mocker.patch("src.core.device.hexlify")

        # WHEN: Calling get_device_uid with a first UID
        mock_unique_id.return_value = b'\x01\x02\x03\x04\x05\x06\x07\x08'
        mock_hexlify.return_value = b'0102030405060708'
        result1 = get_device_uid()

        # THEN: The result should match the first UID
        assert result1 == "0102030405060708"

        # WHEN: Calling get_device_uid with a different second UID
        mock_unique_id.return_value = b'\xff\xfe\xfd\xfc\xfb\xfa\xf9\xf8'
        mock_hexlify.return_value = b'fffefdfcfbfaf9f8'
        result2 = get_device_uid()

        # THEN: The result should match the second UID and be different from the first
        assert result2 == "fffefdfcfbfaf9f8"
        assert result1 != result2

    def test_get_device_uid_calls_functions_correctly(self, mocker):
        """Verify that machine.unique_id and hexlify functions are called correctly."""
        # GIVEN: Mocks configured for unique_id and hexlify
        mock_unique_id = mocker.patch("src.core.device.unique_id")
        mock_hexlify = mocker.patch("src.core.device.hexlify")
        mock_unique_id.return_value = b'\xaa\xbb\xcc\xdd'
        mock_hexlify.return_value = b'aabbccdd'

        # WHEN: Calling get_device_uid
        result = get_device_uid()

        # THEN: unique_id should be called once
        mock_unique_id.assert_called_once()

        # THEN: hexlify should be called once with the result of unique_id
        mock_hexlify.assert_called_once_with(b'\xaa\xbb\xcc\xdd')

        # THEN: The result should be the decoded hexadecimal string
        assert result == "aabbccdd"

    def test_get_device_uid_no_uppercase(self):
        """Verify that the UID does not contain uppercase letters."""
        # GIVEN: The default mock is in place
        # (No specific setup needed)

        # WHEN: Calling get_device_uid
        result = get_device_uid()

        # THEN: The result should be all lowercase
        assert result == result.lower()
