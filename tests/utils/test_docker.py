import pytest
import pathlib
from unittest import mock
from snow_ipa.utils.dockers import check_docker_secret, DOCKER_SECRET_LINUX_PATH


class TestCheckDockerSecret:
    @mock.patch("pathlib.Path.exists")
    def test_file_exists_in_given_path(self, mock_exists):
        mock_exists.side_effect = lambda: True
        var = "/path/to/file"
        assert check_docker_secret(var) == var

    @mock.patch("pathlib.Path.exists")
    def test_file_exists_in_docker_secrets_path(self, mock_exists):
        mock_exists.side_effect = [False, True]
        var = "file"
        expected_path = pathlib.Path(DOCKER_SECRET_LINUX_PATH, var).as_posix()
        assert check_docker_secret(var) == expected_path

    @mock.patch("pathlib.Path.exists")
    def test_file_not_found(self, mock_exists):
        mock_exists.return_value = False
        var = "nonexistent_file"
        with pytest.raises(FileNotFoundError, match=f"file not found: {var}"):
            check_docker_secret(var)
