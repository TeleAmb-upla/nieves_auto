import pytest
from snow_ipa.utils.templates.templates import get_template
from snow_ipa.utils import templates
from importlib import resources


class TestGetTemplate:
    """Test the get_template function."""

    @pytest.fixture
    def mock_joinpath(self, mocker):
        return mocker.MagicMock(
            side_effect=lambda filename: f"/path/to/templates/{filename}"
        )

    @pytest.fixture
    def mock_resources_files(self, mocker, mock_joinpath):
        """Mock the resources.files function."""
        mock_files = mocker.patch(
            "snow_ipa.utils.templates.templates.resources.files",
            return_value=mocker.MagicMock(),
        )

        mock_files.return_value.joinpath = mock_joinpath
        return mock_files

    def test_get_template_file_exists(
        self, mocker, mock_resources_files, mock_joinpath
    ):
        # Mock the open function
        mock_open = mocker.mock_open(read_data="Template content")
        mocker.patch("snow_ipa.utils.templates.templates.open", mock_open)

        # Call the function
        result = get_template("existing_template.txt", "Default content")
        print("mock_joinpath: ", mock_joinpath.call_args_list)
        print("mock_open: ", mock_open.call_args_list)

        # Assertions
        assert result == "Template content"
        mock_joinpath.assert_called_once_with("existing_template.txt")
        mock_open.assert_called_once_with("/path/to/templates/existing_template.txt")

    def test_get_template_file_empty(
        self, mocker, mock_resources_files, mock_joinpath, caplog
    ):
        # Mock the file to simulate its existence but empty content
        mock_open = mocker.mock_open(read_data="")
        mocker.patch("snow_ipa.utils.templates.templates.open", mock_open)

        result = get_template("empty_template.txt", "Default content")

        assert result == "Default content"
        assert "Template file is empty" in caplog.text
        assert "WARNING" == caplog.records[0].levelname
        mock_joinpath.assert_called_once_with("empty_template.txt")
        mock_open.assert_called_once_with("/path/to/templates/empty_template.txt")

    def test_get_template_file_not_found(
        self, mocker, mock_resources_files, mock_joinpath, caplog
    ):
        # Simulate a FileNotFoundError
        mock_open = mocker.patch(
            "snow_ipa.utils.templates.templates.open", side_effect=FileNotFoundError
        )

        result = get_template("missing_template.txt", "Default content")

        assert result == "Default content"
        assert "file not found" in caplog.text
        assert "ERROR" == caplog.records[0].levelname
        # # mock_logger.error.assert_called_once_with(
        #     "Template file not found: missing_template.txt"
        # )
        mock_joinpath.assert_called_once_with("missing_template.txt")
        mock_open.assert_called_once_with("/path/to/templates/missing_template.txt")

    def test_get_template_unexpected_error(
        self, mocker, mock_resources_files, mock_joinpath, caplog
    ):
        # Simulate an unexpected error
        mock_open = mocker.patch(
            "snow_ipa.utils.templates.templates.open",
            side_effect=Exception("Unexpected error"),
        )

        result = get_template("error_template.txt", "Default content")

        assert result == "Default content"
        assert "An unexpected error occurred" in caplog.text
        assert "ERROR" == caplog.records[0].levelname
        mock_joinpath.assert_called_once_with("error_template.txt")
        mock_open.assert_called_once_with("/path/to/templates/error_template.txt")
