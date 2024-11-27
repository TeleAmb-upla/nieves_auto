import pytest
from argparse import ArgumentParser
from snow_ipa.utilities.command_line import set_argument_parser


class TestSetArgumentParser:
    @pytest.fixture
    def parser(self):
        return set_argument_parser()

    def test_parser_creation(self, parser):
        assert isinstance(parser, ArgumentParser)

    def test_service_user_argument(self, parser):
        args = parser.parse_args(["-u", "test_user"])
        assert args.user == "test_user"

    def test_service_credentials_argument(self, parser):
        args = parser.parse_args(["-c", "credentials.json"])
        assert args.service_credentials_file == "credentials.json"

    def test_assets_path_argument(self, parser):
        args = parser.parse_args(["-s", "path/to/assets"])
        assert args.assets_path == "path/to/assets"

    def test_drive_path_argument(self, parser):
        args = parser.parse_args(["-d", "path/to/drive"])
        assert args.drive_path == "path/to/drive"

    def test_regions_asset_path_argument(self, parser):
        args = parser.parse_args(["-r", "path/to/regions"])
        assert args.regions_asset_path == "path/to/regions"

    def test_export_to_argument(self, parser):
        args = parser.parse_args(["-e", "toDrive"])
        assert args.export_to == "toDrive"

    def test_months_list_argument(self, parser):
        args = parser.parse_args(["--months-to-export", "2022-11-01,2022-10-01"])
        assert args.months_list == "2022-11-01,2022-10-01"

    def test_log_level_argument(self, parser):
        args = parser.parse_args(["-l", "DEBUG"])
        assert args.log_level == "DEBUG"

    def test_enable_email_argument(self, parser):
        args = parser.parse_args(["--enable-email"])
        assert args.enable_email is True

    def test_smtp_server_argument(self, parser):
        args = parser.parse_args(["--smtp-server", "smtp.server.com"])
        assert args.smtp_server == "smtp.server.com"

    def test_smtp_port_argument(self, parser):
        args = parser.parse_args(["--smtp-port", "587"])
        assert args.smtp_port == "587"

    def test_smtp_username_argument(self, parser):
        args = parser.parse_args(["--smtp-user", "user"])
        assert args.smtp_username == "user"

    def test_smtp_password_argument(self, parser):
        args = parser.parse_args(["--smtp-password", "password"])
        assert args.smtp_password == "password"

    def test_smtp_username_file_argument(self, parser):
        args = parser.parse_args(["--smtp-user-file", "user_file"])
        assert args.smtp_username_file == "user_file"

    def test_smtp_password_file_argument(self, parser):
        args = parser.parse_args(["--smtp-password-file", "password_file"])
        assert args.smtp_password_file == "password_file"

    def test_from_address_argument(self, parser):
        args = parser.parse_args(["--from-address", "from@example.com"])
        assert args.from_address == "from@example.com"

    def test_to_address_argument(self, parser):
        args = parser.parse_args(["--to-address", "to@example.com"])
        assert args.to_address == "to@example.com"
