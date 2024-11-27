import os
import sys
import logging

import pytest
from unittest import mock

from snow_ipa.utilities.scripting import (
    init_config,
    csv_to_list,
    check_required,
    read_file_to_var,
    print_config,
    terminate_error,
    get_email_template,
    DEFAULT_CONFIG,
)


class TestInitConfig:
    @pytest.fixture(autouse=True)
    def setup_method(self, monkeypatch):
        self.default_config = DEFAULT_CONFIG.copy()

    def test_init_config_with_defaults(self):
        config = init_config(self.default_config)
        assert config == self.default_config

    @mock.patch.dict(os.environ, {"SNOW_SERVICE_USER": "test_user"})
    def test_init_config_with_env_vars(self):
        config = init_config(self.default_config)
        assert config["SERVICE_USER"] == "test_user"

    def test_init_config_with_cmd_args(self):
        cmd_args = {"service_user": "cmd_user"}
        config = init_config(self.default_config, cmd_args)
        assert config["SERVICE_USER"] == "cmd_user"

    def test_init_config_with_list_values(self):
        config = self.default_config.copy()
        config["SAMPLE_LIST"] = "item1, item2, item3"
        config = init_config(config)
        assert config["SAMPLE_LIST"] == ["item1", "item2", "item3"]

    def test_init_config_with_list_values_error(self, monkeypatch):
        # Mock the csv_to_list function to raise an exception
        mock_csv_to_list = mock.MagicMock(side_effect=Exception("Test exception"))
        monkeypatch.setattr(
            "snow_ipa.utilities.scripting.csv_to_list", mock_csv_to_list
        )

        # Mock the logging.error function
        mock_logging_error = mock.MagicMock()
        monkeypatch.setattr(logging, "error", mock_logging_error)

        # Define a config with a key ending with _LIST
        config = self.default_config.copy()
        config["SAMPLE_LIST"] = "item1, item2, item3"

        # Run the init_config function and expect an exception
        with pytest.raises(Exception, match="Test exception"):
            init_config(config)

        # Assertions
        mock_csv_to_list.assert_called_once_with("item1, item2, item3")
        mock_logging_error.assert_called_once_with(
            "Error parsing SAMPLE_LIST: Test exception"
        )


def test_csv_to_list():
    csv_string = "item1, item2, item3"
    expected_list = ["item1", "item2", "item3"]
    assert csv_to_list(csv_string) == expected_list


class TestCheckRequired:
    def setup_method(self):
        self.valid_config = DEFAULT_CONFIG.copy()
        self.valid_config.update(
            {
                "SERVICE_CREDENTIALS_FILE": "path/to/credentials",
                "EXPORT_TO": "toAsset",
                "ASSETS_PATH": "path/to/assets",
                "DRIVE_PATH": "path/to/drive",
                "REGIONS_ASSET_PATH": "path/to/regions",
                "ENABLE_EMAIL": True,
                "SMTP_SERVER": "smtp.server.com",
                "SMTP_PORT": 587,
                "FROM_ADDRESS": "from@example.com",
                "TO_ADDRESS": "to@example.com",
                "SMTP_USERNAME": "username",
                "SMTP_PASSWORD": "password",
            }
        )

    def test_check_required_with_valid_config(self):
        assert check_required(self.valid_config) is True

    def test_check_required_missing_service_credentials(self):
        invalid_config = self.valid_config.copy()
        invalid_config["SERVICE_CREDENTIALS_FILE"] = None
        with pytest.raises(Exception, match="Service credentials file is required."):
            check_required(invalid_config)

    def test_check_required_missing_assets_path(self):
        invalid_config = self.valid_config.copy()
        invalid_config["ASSETS_PATH"] = None
        invalid_config["EXPORT_TO"] = "toAsset"
        with pytest.raises(Exception, match="Assets path is required."):
            check_required(invalid_config)

    def test_check_required_missing_drive_path(self):
        invalid_config = self.valid_config.copy()
        invalid_config["DRIVE_PATH"] = None
        invalid_config["EXPORT_TO"] = "toDrive"
        with pytest.raises(Exception, match="Drive path is required."):
            check_required(invalid_config)

    def test_check_required_missing_regions_asset_path(self):
        invalid_config = self.valid_config.copy()
        invalid_config["REGIONS_ASSET_PATH"] = None
        with pytest.raises(Exception, match="Regions asset path is required."):
            check_required(invalid_config)

    def test_check_required_missing_smtp_server(self):
        invalid_config = self.valid_config.copy()
        invalid_config["SMTP_SERVER"] = None
        with pytest.raises(Exception, match="SMTP server is required."):
            check_required(invalid_config)

    def test_check_required_missing_smtp_port(self):
        invalid_config = self.valid_config.copy()
        invalid_config["SMTP_PORT"] = None
        with pytest.raises(Exception, match="SMTP port is required."):
            check_required(invalid_config)

    def test_check_required_missing_from_address(self):
        invalid_config = self.valid_config.copy()
        invalid_config["FROM_ADDRESS"] = None
        with pytest.raises(Exception, match="From address is required."):
            check_required(invalid_config)

    def test_check_required_missing_to_address(self):
        invalid_config = self.valid_config.copy()
        invalid_config["TO_ADDRESS"] = None
        with pytest.raises(Exception, match="To address is required."):
            check_required(invalid_config)

    def test_check_required_missing_smtp_username(self):
        invalid_config = self.valid_config.copy()
        invalid_config["SMTP_USERNAME"] = None
        invalid_config["SMTP_USERNAME_FILE"] = None
        with pytest.raises(Exception, match="SMTP username is required."):
            check_required(invalid_config)

    def test_check_required_missing_smtp_password(self):
        invalid_config = self.valid_config.copy()
        invalid_config["SMTP_PASSWORD"] = None
        invalid_config["SMTP_PASSWORD_FILE"] = None
        with pytest.raises(Exception, match="SMTP password is required."):
            check_required(invalid_config)


def test_read_file_to_var():
    with mock.patch("builtins.open", mock.mock_open(read_data="file content")):
        assert read_file_to_var("dummy_path") == "file content"


def test_print_config():
    config = {"key1": "value1", "SMTP_PASSWORD": "secret"}
    expected_output = "{'SMTP_PASSWORD': '********',\n 'key1': 'value1'}"
    assert print_config(config) == expected_output


class TestGetEmailTemplate:
    def test_get_email_template_found(self, monkeypatch):
        # Mock the open function to simulate reading the email template
        mock_file_content = "This is a test email template."
        mock_open_function = mock.mock_open(read_data=mock_file_content)
        monkeypatch.setattr("builtins.open", mock_open_function)

        # Run the get_email_template function
        template = get_email_template(
            "./templates/error_email_template", "Default template"
        )

        # Assertions
        assert template == mock_file_content
        mock_open_function.assert_called_once_with("./templates/error_email_template")

    def test_get_email_template_not_found(self, monkeypatch):
        # Mock the open function to raise a FileNotFoundError
        mock_open_function = mock.mock_open()
        mock_open_function.side_effect = FileNotFoundError
        monkeypatch.setattr("builtins.open", mock_open_function)

        # Run the get_email_template function
        template = get_email_template(
            "./templates/error_email_template", "Default template"
        )

        # Assertions
        assert template == "Default template"
        mock_open_function.assert_called_once_with("./templates/error_email_template")


# @mock.patch("snow_ipa.utilities.scripting.sys.exit")
# @mock.patch("snow_ipa.utilities.scripting.print_log")
# @mock.patch("snow_ipa.utilities.scripting.logging.error")
# @mock.patch("snow_ipa.utilities.scripting.logging.info")
# def test_terminate_error(mock_info, mock_error, mock_print_log, mock_exit):
#     email_service = mock.MagicMock()
#     terminate_error(
#         "Test error",
#         "2023-01-01 00:00:00",
#         Exception("Test exception"),
#         email_service,
#     )
#     mock_error.assert_called_once()
#     mock_print_log.assert_called_once_with("Test error", "ERROR")
#     mock_info.assert_called_once_with("------ EXITING SCRIPT ------")
#     mock_exit.assert_called_once()


class TestTerminateError:
    @pytest.fixture(autouse=True)
    def setup_method(self, monkeypatch):
        self.err_message = "Test error message"
        self.script_start_time = "2023-01-01 00:00:00"
        self.email_service = mock.MagicMock()

        # Mock the sys.exit function
        self.mock_sys_exit = mock.MagicMock()
        monkeypatch.setattr(sys, "exit", self.mock_sys_exit)

        # Mock the logging functions
        self.mock_logging_error = mock.MagicMock()
        self.mock_logging_info = mock.MagicMock()
        monkeypatch.setattr(logging, "error", self.mock_logging_error)
        monkeypatch.setattr(logging, "info", self.mock_logging_info)

        # Mock the print_log function
        self.mock_print_log = mock.MagicMock()
        monkeypatch.setattr(
            "snow_ipa.utilities.scripting.print_log", self.mock_print_log
        )

    def test_terminate_error_with_email_template_found(self, monkeypatch):
        # Mock the open function to simulate reading the email template
        mock_file_content = "Error Message: [error_message]\nStart Time: [start_time]\nEnd Time: [end_time]"
        mock_open_function = mock.mock_open(read_data=mock_file_content)
        monkeypatch.setattr("builtins.open", mock_open_function)

        # Run the terminate_error function
        terminate_error(
            err_message=self.err_message,
            script_start_time=self.script_start_time,
            exception_traceback=None,
            email_service=self.email_service,
            exit_script=True,
        )

        # Assertions
        self.email_service.send_email.assert_called_once()
        mock_open_function.assert_called_once_with("./templates/error_email_template")
        self.mock_print_log.assert_called_once_with(self.err_message, "ERROR")
        self.mock_logging_info.assert_called_once_with("------ EXITING SCRIPT ------")
        self.mock_sys_exit.assert_called_once()

    def test_terminate_error_with_email_template_not_found(self, monkeypatch):
        # Mock the open function to raise a FileNotFoundError
        mock_open_function = mock.mock_open()
        mock_open_function.side_effect = FileNotFoundError
        monkeypatch.setattr("builtins.open", mock_open_function)

        # Run the terminate_error function
        terminate_error(
            err_message=self.err_message,
            script_start_time=self.script_start_time,
            exception_traceback=None,
            email_service=self.email_service,
            exit_script=True,
        )

        # Assertions
        self.email_service.send_email.assert_called_once()
        mock_open_function.assert_called_once_with("./templates/error_email_template")
        self.mock_print_log.assert_called_once_with(self.err_message, "ERROR")
        self.mock_logging_info.assert_called_once_with("------ EXITING SCRIPT ------")
        self.mock_sys_exit.assert_called_once()

    def test_terminate_error_with_exception_traceback(self):
        # Run the terminate_error function
        terminate_error(
            err_message=self.err_message,
            script_start_time=self.script_start_time,
            exception_traceback=Exception("Test exception"),
            email_service=self.email_service,
            exit_script=True,
        )

        # Assertions
        self.mock_logging_error.assert_called_once_with(
            str(Exception("Test exception"))
        )
        self.mock_print_log.assert_called_once_with(self.err_message, "ERROR")
        self.mock_logging_info.assert_called_once_with("------ EXITING SCRIPT ------")
        self.mock_sys_exit.assert_called_once()

    def test_terminate_error_without_email_service(self):
        # Run the terminate_error function
        terminate_error(
            err_message=self.err_message,
            script_start_time=self.script_start_time,
            exception_traceback=None,
            email_service=None,
            exit_script=True,
        )

        # Assertions
        self.mock_print_log.assert_called_once_with(self.err_message, "ERROR")
        self.mock_logging_info.assert_called_once_with("------ EXITING SCRIPT ------")
        self.mock_sys_exit.assert_called_once()

    def test_terminate_error_without_exit_script(self):
        # Run the terminate_error function
        terminate_error(
            err_message=self.err_message,
            script_start_time=self.script_start_time,
            exception_traceback=None,
            email_service=None,
            exit_script=False,
        )

        # Assertions
        self.mock_print_log.assert_called_once_with(self.err_message, "ERROR")
        self.mock_logging_info.assert_called_once_with("------ EXITING SCRIPT ------")
        self.mock_sys_exit.assert_not_called()
