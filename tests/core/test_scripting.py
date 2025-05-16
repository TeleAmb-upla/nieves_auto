from unittest import mock
from email_validator import EmailNotValidError
from more_itertools import side_effect
import pytest
from datetime import datetime

# from unittest.mock import MagicMock, patch
from core.exporting import ExportManager
from snow_ipa.core.scripting import (
    ScriptManager,
    init_script_config,
    error_message,
)
from snow_ipa.services.messaging import EmailService
from snow_ipa.utils import dates


class TestScriptManager:
    @pytest.fixture
    def default_config(self):
        return {
            "service_credentials_file": "path/to/credentials.json",
            "export_to": "toAssetAndDrive",
            "gee_assets_path": "path/to/gee/assets",
            "google_drive_path": "path/to/drive",
            "regions_asset_path": "path/to/regions",
            "months_list": ["2023-01-01", "2023-02-01"],
            "enable_email": True,
            "smtp_server": "smtp.example.com",
            "smtp_port": 587,
            "smtp_username": "user@example.com",
            "smtp_password": "password",
            "from_address": "from@example.com",
            "to_address": "to@example.com",
        }

    @pytest.fixture
    def script_manager(self, default_config):
        return ScriptManager(default_config)

    def test_update_config(self, script_manager):
        new_config = {"export_to": "toDrive"}
        updated_config = script_manager.update_config(new_config)
        assert updated_config["export_to"] == "toDrive"

    def test_update_config_with_none(self, script_manager):
        updated_config = script_manager.update_config()
        assert updated_config == script_manager.config

    def test_fill_from_files(self, script_manager, mocker):
        mock_open = mocker.patch(
            "snow_ipa.core.scripting.open", mocker.mock_open(read_data="file_content")
        )
        script_manager.config["some"] = None
        script_manager.config["some_file"] = "path/to/file"
        script_manager.fill_from_files()
        assert script_manager.config["some"] == "file_content"
        mock_open.assert_called_once_with("path/to/file", "r")

    def test_check_required_valid(self, script_manager):
        assert script_manager.check_required() is True

    def test_check_required_missing_credentials(self, script_manager):
        script_manager.config["service_credentials_file"] = None
        with pytest.raises(ValueError, match="Service credentials file is required."):
            script_manager.check_required()

    def test_check_required_missing_gee_path(self, script_manager):
        script_manager.config["export_to"] = "toAsset"
        script_manager.config["gee_assets_path"] = None
        with pytest.raises(
            ValueError,
            match="Assets path is required if export_to is set to 'toAsset' or 'toAssetAndDrive'.",
        ):
            script_manager.check_required()

    def test_check_required_missing_drive_path(self, script_manager):
        script_manager.config["export_to"] = "toDrive"
        script_manager.config["google_drive_path"] = None
        with pytest.raises(
            ValueError,
            match="Drive path is required if export_to is set to 'toDrive' or 'toAssetAndDrive'.",
        ):
            script_manager.check_required()

    def test_check_required_missing_regions_path(self, script_manager):
        script_manager.config["regions_asset_path"] = None
        with pytest.raises(ValueError, match="Regions asset path is required."):
            script_manager.check_required()

    def test_check_required_invalid_months_list(self, script_manager):
        script_manager.config["months_list"] = ["invalid_date"]
        with pytest.raises(
            ValueError, match="One or more dates provided in months_list are not valid"
        ):
            script_manager.check_required()

    def test_check_email_required_valid(self, script_manager):
        script_manager.check_email_required()

    @pytest.mark.parametrize(
        "key", ["smtp_server", "smtp_port", "from_address", "to_address"]
    )
    def test_check_email_required_missing_key(self, script_manager, key):
        script_manager.config[key] = None
        with pytest.raises(ValueError):
            script_manager.check_email_required()

    def test_check_email_required_invalid_from_email(self, script_manager):
        script_manager.config["from_address"] = "invalid_email"
        with pytest.raises(EmailNotValidError):
            script_manager.check_email_required()

    def test_check_email_required_invalid_to_email(self, script_manager):
        script_manager.config["to_address"] = "invalid_email"
        with pytest.raises(EmailNotValidError):
            script_manager.check_email_required()

    def test_run_complete_config_no_email_valid(self, script_manager, mocker):
        # TODO: Verify if script manager status is still needed
        script_manager.config["enable_email"] = False
        mocker.patch.object(script_manager, "check_required", return_value=None)
        mocker.patch.object(script_manager, "check_email_required")
        script_manager.run_complete_config()  # Raise no Exception

        assert script_manager.status == "OK"

    def test_run_complete_config_no_email_error(self, script_manager, mocker):
        script_manager.config["enable_email"] = False
        mocker.patch.object(
            script_manager, "check_required", side_effect=ValueError("Test error")
        )
        with pytest.raises(ValueError, match="Test error"):
            script_manager.run_complete_config()

    def test_run_complete_config_email_valid(self, script_manager, mocker, caplog):
        script_manager.config["enable_email"] = True
        mocker.patch.object(script_manager, "fill_from_files")
        mocker.patch.object(script_manager, "check_email_required")
        mocker.patch.object(script_manager, "check_required")

        mock_email_service = mocker.patch(
            "snow_ipa.core.scripting.EmailService", return_value=mock.MagicMock()
        )

        with caplog.at_level("DEBUG"):
            script_manager.run_complete_config()
        # print("caplog_text: ", caplog.text)

        assert "Email messaging enabled" in caplog.text
        mock_email_service.assert_called_once()

    def test_run_complete_config_email_fail(self, script_manager, mocker, caplog):
        script_manager.config["enable_email"] = True
        mocker.patch.object(script_manager, "fill_from_files")
        mocker.patch.object(script_manager, "check_email_required")
        mocker.patch.object(
            script_manager, "check_required", side_effect=ValueError("Test error")
        )

        mock_email_service = mocker.patch(
            "snow_ipa.core.scripting.EmailService", return_value=mock.MagicMock()
        )

        with caplog.at_level("DEBUG"):
            with pytest.raises(ValueError, match="Test error"):
                script_manager.run_complete_config()

        assert "Email messaging enabled" in caplog.text
        mock_email_service.assert_called_once()

    def test_run_complete_config_email_config_fail(
        self, script_manager, mocker, caplog
    ):
        script_manager.config["enable_email"] = True
        mocker.patch.object(script_manager, "fill_from_files")
        mocker.patch.object(
            script_manager, "check_email_required", side_effect=ValueError("Test error")
        )
        mocker.patch.object(script_manager, "check_required")

        mock_email_service = mocker.patch(
            "snow_ipa.core.scripting.EmailService", return_value=mock.MagicMock()
        )

        with caplog.at_level("DEBUG"):
            with pytest.raises(ValueError, match="Test error"):
                script_manager.run_complete_config()

        assert "Configuration failed" in caplog.text
        mock_email_service.assert_not_called()

    def test_print_config(self, script_manager):
        masked_config = script_manager.print_config(keys_to_mask=["regions_asset_path"])

        assert "'smtp_password': '********'" in masked_config
        assert "'regions_asset_path': '********'" in masked_config
        assert "'service_credentials_file': 'path/to/credentials.json'" in masked_config


class TestInitScriptConfig:

    def test_init_script_config(self, mocker):

        mock_args = mocker.MagicMock()
        mock_parser = mocker.patch("snow_ipa.core.scripting.set_argument_parser")
        mock_parser.return_value = mock_args
        mock_vars = mocker.patch(
            "snow_ipa.core.scripting.vars", return_value={"export_to": "toDrive"}
        )

        script_manager = init_script_config()
        assert script_manager.config["export_to"] == "toDrive"


class TestErrorMessage:

    def test_error_message_with_email_service(self, mocker, caplog):
        mock_send_error_message = mocker.patch(
            "snow_ipa.core.scripting.send_error_message"
        )
        # mock_email_service = mocker.MagicMock(spec=EmailService)
        script_manager = mocker.MagicMock(spec=ScriptManager)
        script_manager.start_time = datetime.today()
        script_manager.email_service = mocker.MagicMock(spec=EmailService)
        script_manager.config = {
            "from_address": "from@example.com",
            "to_address": "to@example.com",
        }

        with caplog.at_level("DEBUG"):
            error_message(Exception("Test error"), script_manager)

        print(mock_send_error_message.call_args_list)

        assert "Sending error message" in caplog.text
        mock_send_error_message.assert_called_once()

    def test_error_message_without_email_service(self, mocker):
        script_manager = mocker.MagicMock(spec=ScriptManager)
        script_manager.email_service = None

        # Should not raise an exception
        error_message(Exception("Test error"), script_manager)


class TestExportManager:
    @pytest.fixture
    def export_manager(self):
        return ExportManager(
            export_to_gee=True, export_to_gdrive=True, months_to_save=["2023-01"]
        )

    def test_init(self, export_manager):
        assert export_manager.export_to_gee is True
        assert export_manager.export_to_gdrive is True
        assert export_manager.months_to_save == ["2023-01"]

    def test_calc_months_to_save_with_months(self, export_manager):
        export_manager.calc_months_to_save()
        assert export_manager.months_to_save == ["2023-01"]

    def test_calc_months_to_save_without_months(self, export_manager):
        export_manager.months_to_save = []
        export_manager.modis_distinct_months = ["2023-02", "2023-01"]
        export_manager.calc_months_to_save()
        assert export_manager.months_to_save == ["2023-02"]

    def test_calc_months_to_save_no_modis_data(self, export_manager):
        export_manager.months_to_save = []
        export_manager.modis_distinct_months = []
        export_manager.calc_months_to_save()
        assert export_manager.months_to_save == []

    def test_final_assets_to_save(self, export_manager):
        export_manager.gee_assets_to_save = ["asset1", "asset2"]
        export_manager.gdrive_assets_to_save = ["asset2", "asset3"]
        final_assets = export_manager.final_assets_to_save
        assert final_assets == ["asset1", "asset2", "asset3"]
