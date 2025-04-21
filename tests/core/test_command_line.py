from ast import arg
import pytest
from argparse import ArgumentParser
from snow_ipa.core.command_line import set_argument_parser, parse_list_arg


class TestSetArgumentParser:
    @pytest.fixture
    def parser(self):
        return set_argument_parser()

    @pytest.fixture
    def mock_env_vars(self, monkeypatch):
        monkeypatch.setenv("SNOW_USER", "env_user")
        monkeypatch.setenv("SNOW_SERVICE_CREDENTIALS_FILE", "env_credentials.json")
        monkeypatch.setenv("SNOW_GEE_ASSETS_PATH", "env/path/to/gee/assets")
        monkeypatch.setenv("SNOW_GOOGLE_DRIVE_PATH", "env/path/to/google/drive")
        monkeypatch.setenv("SNOW_REGIONS_ASSET_PATH", "env/path/to/regions")
        monkeypatch.setenv("SNOW_EXPORT_TO", "toAssetAndDrive")
        monkeypatch.setenv("SNOW_MONTHS_LIST", "2022-11-01,2022-10-01")
        monkeypatch.setenv("SNOW_LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("SNOW_LOG_FILE", "env_logfile.log")
        monkeypatch.setenv("SNOW_ENABLE_EMAIL", "true")
        monkeypatch.setenv("SNOW_SMTP_SERVER", "env.smtp.example.com")
        monkeypatch.setenv("SNOW_SMTP_PORT", "3000")
        monkeypatch.setenv("SNOW_SMTP_USER", "env_smtp_user")
        monkeypatch.setenv("SNOW_SMTP_PASSWORD", "env_smtp_password")
        monkeypatch.setenv("SNOW_SMTP_USER_FILE", "env_smtp_user_file")
        monkeypatch.setenv("SNOW_SMTP_PASSWORD_FILE", "env_smtp_password_file")
        monkeypatch.setenv("SNOW_FROM_ADDRESS", "env.from@example.com")
        monkeypatch.setenv("SNOW_TO_ADDRESS", "env.to@example.com, env.to2@example.com")

    @pytest.fixture
    def parser_with_env(self, mock_env_vars):
        parser = set_argument_parser()
        return parser

    def test_parser_creation(self, parser):
        assert isinstance(parser, ArgumentParser)

    def test_default_values_no_env(self, parser):
        args = parser.parse_args([])
        assert args.user is None
        assert args.service_credentials_file is None
        assert args.gee_assets_path is None
        assert args.google_drive_path is None
        assert args.regions_asset_path is None
        assert args.export_to == "toAsset"
        assert args.months_list is None
        assert args.log_level == "INFO"
        assert args.enable_email is False
        assert args.smtp_server is None
        assert args.smtp_port is None
        assert args.smtp_username is None
        assert args.smtp_password is None
        assert args.smtp_username_file is None
        assert args.smtp_password_file is None
        assert args.from_address is None
        assert args.to_address is None

    def test_user_argument(self, parser):
        args = parser.parse_args(["-u", "test_user"])
        assert args.user == "test_user"

    def test_user_argument_with_env(self, parser_with_env):
        args = parser_with_env.parse_args([])
        assert args.user == "env_user"

    def test_service_credentials_argument(self, parser):
        args = parser.parse_args(["-c", "credentials.json"])
        assert args.service_credentials_file == "credentials.json"

    def test_service_credentials_argument_with_env(self, parser_with_env):
        args = parser_with_env.parse_args([])
        assert args.service_credentials_file == "env_credentials.json"

    def test_gee_assets_path_argument(self, parser):
        args = parser.parse_args(["-s", "path/to/gee/assets"])
        assert args.gee_assets_path == "path/to/gee/assets"

    def test_gee_assets_path_argument_with_env(self, parser_with_env):
        args = parser_with_env.parse_args([])
        assert args.gee_assets_path == "env/path/to/gee/assets"

    def test_google_drive_path_argument(self, parser):
        args = parser.parse_args(["-d", "path/to/google/drive"])
        assert args.google_drive_path == "path/to/google/drive"

    def test_google_drive_path_argument_with_env(self, parser_with_env):
        args = parser_with_env.parse_args([])
        assert args.google_drive_path == "env/path/to/google/drive"

    def test_regions_asset_path_argument(self, parser):
        args = parser.parse_args(["-r", "path/to/regions"])
        assert args.regions_asset_path == "path/to/regions"

    def test_regions_asset_path_argument_with_env(self, parser_with_env):
        args = parser_with_env.parse_args([])
        assert args.regions_asset_path == "env/path/to/regions"

    def test_export_to_choices(self, parser):
        args = parser.parse_args(["-e", "toAsset"])
        assert args.export_to == "toAsset"
        args = parser.parse_args(["-e", "toDrive"])
        assert args.export_to == "toDrive"
        args = parser.parse_args(["-e", "toAssetAndDrive"])
        assert args.export_to == "toAssetAndDrive"

    def test_invalid_export_to_argument(self, parser):
        with pytest.raises(SystemExit):
            parser.parse_args(["-e", "invalidOption"])

    def test_export_to_argument_with_env(self, parser_with_env):
        args = parser_with_env.parse_args([])
        assert args.export_to == "toAssetAndDrive"

    def test_invalid_export_to_argument_with_env(self, monkeypatch):
        monkeypatch.setenv("SNOW_EXPORT_TO", "invalidOption")
        with pytest.raises(SystemExit):
            parser = set_argument_parser()

    def test_months_list_argument_single_value(self, parser):
        args = parser.parse_args(["--months-to-export", "2022-11-01"])
        assert args.months_list == ["2022-11-01"]

    def test_months_list_argument_list(self, parser):
        args = parser.parse_args(["--months-to-export", "2022-11-01,2022-10-01"])
        assert args.months_list == ["2022-11-01", "2022-10-01"]

    def test_months_list_argument_with_env(self, parser_with_env):
        args = parser_with_env.parse_args([])
        assert args.months_list == ["2022-11-01", "2022-10-01"]

    def test_log_level_argument(self, parser):
        args = parser.parse_args(["-l", "DEBUG"])
        assert args.log_level == "DEBUG"

    def test_log_level_choices(self, parser):
        args = parser.parse_args(["-l", "DEBUG"])
        assert args.log_level == "DEBUG"
        args = parser.parse_args(["-l", "INFO"])
        assert args.log_level == "INFO"
        args = parser.parse_args(["-l", "WARNING"])
        assert args.log_level == "WARNING"
        args = parser.parse_args(["-l", "ERROR"])
        assert args.log_level == "ERROR"

    def test_invalid_log_level_argument(self, parser):
        with pytest.raises(SystemExit):
            parser.parse_args(["-l", "INVALID"])

    def test_log_level_argument_with_env(self, parser_with_env):
        args = parser_with_env.parse_args([])
        assert args.log_level == "DEBUG"

    def test_invalid_log_level_argument_with_env(self, monkeypatch):
        monkeypatch.setenv("SNOW_LOG_LEVEL", "INVALID")
        with pytest.raises(SystemExit):
            parser = set_argument_parser()

    def test_log_file_argument(self, parser):
        args = parser.parse_args(["--log-file", "logfile.log"])
        assert args.log_file == "logfile.log"

    def test_log_file_argument_with_env(self, parser_with_env):
        args = parser_with_env.parse_args([])
        assert args.log_file == "env_logfile.log"

    def test_enable_email_argument(self, parser):
        args = parser.parse_args(["--enable-email"])
        assert args.enable_email is True

    # def test_enable_email_argument_with_env(self, parser_with_env):
    #     args = parser_with_env.parse_args([])
    #     assert args.enable_email is True

    @pytest.mark.parametrize(
        "env_value, expected",
        [
            ("true", True),
            ("True", True),
            ("1", True),
            ("yes", True),
            ("non_bool", False),
        ],
    )
    def test_enable_email_with_env(self, monkeypatch, env_value, expected):
        monkeypatch.setenv("SNOW_ENABLE_EMAIL", env_value)
        parser = set_argument_parser()
        args = parser.parse_args([])
        assert args.enable_email is expected

    def test_smtp_server_argument(self, parser):
        args = parser.parse_args(["--smtp-server", "smtp.server.com"])
        assert args.smtp_server == "smtp.server.com"

    def test_smtp_server_argument_with_env(self, parser_with_env):
        args = parser_with_env.parse_args([])
        assert args.smtp_server == "env.smtp.example.com"

    def test_smtp_port_argument(self, parser):
        args = parser.parse_args(["--smtp-port", "587"])
        assert args.smtp_port == 587

    def test_invalid_smtp_port_argument(self, parser):
        with pytest.raises(SystemExit):
            parser.parse_args(["--smtp-port", "invalid_port"])

    def test_smtp_port_argument_with_env(self, parser_with_env):
        args = parser_with_env.parse_args([])
        assert args.smtp_port == 3000

    def test_invalid_smtp_port_argument_with_env(self, monkeypatch):
        monkeypatch.setenv("SNOW_SMTP_PORT", "invalid_port")
        parser = set_argument_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_smtp_username_argument(self, parser):
        args = parser.parse_args(["--smtp-user", "user"])
        assert args.smtp_username == "user"

    def test_smtp_username_argument_with_env(self, parser_with_env):
        args = parser_with_env.parse_args([])
        assert args.smtp_username == "env_smtp_user"

    def test_smtp_password_argument(self, parser):
        args = parser.parse_args(["--smtp-password", "password"])
        assert args.smtp_password == "password"

    def test_smtp_password_argument_with_env(self, parser_with_env):
        args = parser_with_env.parse_args([])
        assert args.smtp_password == "env_smtp_password"

    def test_smtp_username_file_argument(self, parser):
        args = parser.parse_args(["--smtp-user-file", "user_file"])
        assert args.smtp_username_file == "user_file"

    def test_smtp_username_file_argument_with_env(self, parser_with_env):
        args = parser_with_env.parse_args([])
        assert args.smtp_username_file == "env_smtp_user_file"

    def test_smtp_password_file_argument(self, parser):
        args = parser.parse_args(["--smtp-password-file", "password_file"])
        assert args.smtp_password_file == "password_file"

    def test_smtp_password_file_argument_with_env(self, parser_with_env):
        args = parser_with_env.parse_args([])
        assert args.smtp_password_file == "env_smtp_password_file"

    def test_from_address_argument(self, parser):
        args = parser.parse_args(["--from-address", "from@example.com"])
        assert args.from_address == "from@example.com"

    def test_from_address_argument_with_env(self, parser_with_env):
        args = parser_with_env.parse_args([])
        assert args.from_address == "env.from@example.com"

    def test_to_address_argument_single_value(self, parser):
        args = parser.parse_args(["--to-address", "to@example.com"])
        assert args.to_address == ["to@example.com"]

    def test_to_address_argument_list(self, parser):
        args = parser.parse_args(
            ["--to-address", "email1@example.com,email2@example.com"]
        )
        assert args.to_address == ["email1@example.com", "email2@example.com"]

    def test_to_address_argument_with_env(self, parser_with_env):
        args = parser_with_env.parse_args([])
        assert args.to_address == ["env.to@example.com", "env.to2@example.com"]


class TestParseListArg:
    def test_parse_list_arg_single_value(self):
        result = parse_list_arg("value1")
        assert result == ["value1"]

    def test_parse_list_arg_multiple_values(self):
        result = parse_list_arg("value1, value2, value3")
        assert result == ["value1", "value2", "value3"]

    def test_parse_list_arg_with_extra_spaces(self):
        result = parse_list_arg("  value1  ,  value2 ,value3  ")
        assert result == ["value1", "value2", "value3"]

    def test_parse_list_arg_empty_string(self):
        result = parse_list_arg("")
        assert result == [""]

    def test_parse_list_arg_with_special_characters(self):
        result = parse_list_arg("value1, value@2, value#3")
        assert result == ["value1", "value@2", "value#3"]

    def test_parse_list_arg_with_numbers(self):
        result = parse_list_arg("123, 456, 789")
        assert result == ["123", "456", "789"]
