import pytest
import logging
from pathlib import Path
from snow_ipa.utils.logs import (
    get_log_level,
    update_logging_config,
    init_logging_config,
    print_and_log,
)
from snow_ipa.core.configs import DEFAULT_LOGGING_CONFIG, LOGGER_NAME


# @pytest.fixture(scope="function", autouse=True)
# def reset_logging_config():
#     """Reset the logging configuration to its default state before each test."""
#     DEFAULT_LOGGING_CONFIG["loggers"][LOGGER_NAME]["level"] = "INFO"
#     DEFAULT_LOGGING_CONFIG["handlers"]["file"]["filename"] = "./snow.log"


# @pytest.fixture()
# def patch_default_logging_config(mocker):
#     """Patch the logger's default configuration to avoid file creation."""
#     return mocker.patch(
#         "snow_ipa.utils.logs.DEFAULT_LOGGING_CONFIG",
#         new=DEFAULT_LOGGING_CONFIG.copy(),
#     )


class TestGetLogLevel:
    @pytest.mark.parametrize(
        "log_level, expected",
        [
            ("DEBUG", 10),
            ("INFO", 20),
            ("WARNING", 30),
            ("ERROR", 40),
            ("INVALID", 20),
            ("", 20),
        ],
    )
    def test_get_log_level(self, log_level, expected):
        assert get_log_level(log_level) == expected


class TestUpdateLoggingConfig:
    def test_update_logging_config_with_valid_config(self, mocker):
        replacement_values = {"log_level": "DEBUG", "log_file": "test.log"}
        mock_replace_values = mocker.patch(
            "snow_ipa.utils.logs.replace_values_in_dict",
            return_value=replacement_values,
        )

        updated_config = update_logging_config(config=replacement_values)

        assert updated_config["loggers"][LOGGER_NAME]["level"] == "DEBUG"
        assert updated_config["handlers"]["file"]["filename"] == "test.log"
        mock_replace_values.assert_called_once()

    def test_update_logging_config_with_no_config(self, mocker):
        mock_replace_values = mocker.patch("snow_ipa.utils.logs.replace_values_in_dict")
        updated_config = update_logging_config()

        # assert updated_config["loggers"][LOGGER_NAME]["level"] == "INFO"
        assert updated_config["handlers"]["file"]["filename"] == "./snow.log"
        assert updated_config == DEFAULT_LOGGING_CONFIG
        mock_replace_values.assert_not_called()


class TestInitLoggingConfig:
    def test_init_logging_config(self):
        logger = init_logging_config()

        assert isinstance(logger, logging.Logger)
        assert logger.name == LOGGER_NAME
        assert logger.level == 20
        assert len(logger.handlers) == 2

    def test_init_logging_custom_config(self, mocker):
        replacement_values = {"log_level": "DEBUG", "log_file": "test.log"}
        mock_replace_values = mocker.patch(
            "snow_ipa.utils.logs.replace_values_in_dict",
            return_value=replacement_values,
        )
        logger = init_logging_config(config=replacement_values)
        logger_file = Path(logger.handlers[0].baseFilename)  # type: ignore
        target_logger_file = Path(replacement_values["log_file"])

        assert isinstance(logger, logging.Logger)
        assert logger.name == LOGGER_NAME
        assert logger.level == 10
        assert len(logger.handlers) == 2
        assert logger_file.name == target_logger_file.name


class TestPrintAndLog:
    @pytest.fixture(scope="function", autouse=True)
    def mock_print(self, mocker):
        return mocker.patch("snow_ipa.utils.logs.print")

    @pytest.mark.parametrize(
        "message, level, expected_level",
        [
            ("Test message", "INFO", "INFO"),
            ("Debug message", "DEBUG", "DEBUG"),
            ("Warning message", "WARNING", "WARNING"),
            ("Error message", "ERROR", "ERROR"),
        ],
    )
    def test_print_and_log(self, caplog, mock_print, message, level, expected_level):
        with caplog.at_level(get_log_level(level)):
            print_and_log(message, level)

            mock_print.assert_called_once_with(message)
            assert message in caplog.text
            assert caplog.records[-1].levelname == expected_level
