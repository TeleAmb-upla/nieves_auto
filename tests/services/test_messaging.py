from io import DEFAULT_BUFFER_SIZE
from smtplib import SMTP, SMTPAuthenticationError, SMTPException
from unittest import mock
from unittest.mock import DEFAULT
import pytest
import logging
from datetime import datetime
from snow_ipa.services.messaging import EmailService, parse_emails, send_error_message
from snow_ipa.core.configs import ERROR_EMAIL_TEMPLATE, SUCCESS_EMAIL_TEMPLATE


# parse_email uses use email_validator package to validate emails.
# email_validator checks for certain invalid email formats and domain (e.g @example.com returns invalid)
# use @validemail.com to avoid issues in testing
class TestParseEmails:
    def test_valid_emails_comma_separated(self):

        emails_str = "test1@validemail.com,test2@validemail.com"
        expected = ["test1@validemail.com", "test2@validemail.com"]
        assert parse_emails(emails_str) == expected

    def test_valid_emails_semicolon_separated(self):
        emails_str = "test1@validemail.com;test2@validemail.com"
        expected = ["test1@validemail.com", "test2@validemail.com"]
        assert parse_emails(emails_str) == expected

    def test_mixed_valid_and_invalid_emails(self):
        emails_str = "test1@validemail.com,invalid-email;test2@validemail.com"
        expected = ["test1@validemail.com", "test2@validemail.com"]
        assert parse_emails(emails_str) == expected

    def test_all_invalid_emails(self):
        emails_str = "invalid-email1,invalid-email2"
        expected = []
        assert parse_emails(emails_str) == expected


class TestEmailService:
    """
    This class contains tests to verify the initialization and functionality of the EmailSender class.
    It includes tests for successful initialization, sending emails, and handling errors.
    """

    @pytest.fixture
    def mock_smtp(self, mocker):
        """
        Fixture to set up the EmailService instance for testing.
        """
        mock_smtp_instance = mocker.MagicMock()
        return mocker.patch(
            "snow_ipa.services.messaging.smtplib.SMTP", return_value=mock_smtp_instance
        )

    def test_init_success(self, mocker):
        """
        Test that the EmailSender initializes correctly with valid SMTP settings.
        """
        mocked_test_connection = mocker.patch.object(
            EmailService, "test_connection", return_value=None
        )

        email_sender = EmailService(
            smtp_server="smtp.example.com",
            smtp_port=587,
            smtp_username="user",
            smtp_password="pass",
            from_address="from@example.com",
            to_address=["to@example.com"],
        )

        print(f"Mocked Test_connection called: {mocked_test_connection.call_count}")

        assert email_sender.smtp_server == "smtp.example.com"
        assert email_sender.smtp_port == 587
        assert email_sender.smtp_username == "user"
        assert email_sender.smtp_password == "pass"
        assert email_sender.from_address == "from@example.com"
        assert email_sender.to_address == ["to@example.com"]
        mocked_test_connection.assert_called_once()

    def test_connect(self, mocker, mock_smtp, caplog):
        mock_smtp.return_value.noop.return_value = (250, b"OK")
        with caplog.at_level("INFO"):
            email_sender = EmailService(
                smtp_server="smtp.example.com",
                smtp_port=587,
                smtp_username="user",
                smtp_password="pass",
                from_address="from@example.com",
                to_address=["to@example.com"],
            )

        print(f"Mocked calls : " f"{mock_smtp.mock_calls}")

        assert "connection test successful" in caplog.text
        assert email_sender.smtp_connection is None
        mock_smtp.assert_called_once_with("smtp.example.com", 587)

    def test_connect_fail_noop(self, mocker, mock_smtp, caplog):
        # mock_smtp_instance = mock_smtp.return_value
        # mock_smtp_instance.noop.return_value = (250, b"OK")
        mock_smtp.return_value.noop.return_value = (300, b"OK")
        with pytest.raises(Exception) as excinfo:
            with caplog.at_level("INFO"):
                email_sender = EmailService(
                    smtp_server="smtp.example.com",
                    smtp_port=587,
                    smtp_username="user",
                    smtp_password="pass",
                    from_address="from@example.com",
                    to_address=["to@example.com"],
                )

        print(f"Mocked calls : " f"{mock_smtp.mock_calls}")

        assert "connection test failed" in caplog.text
        assert "response code: 300" in caplog.text
        mock_smtp.assert_called_once_with("smtp.example.com", 587)

    def test_connect_fail_with_exception(self, mocker, mock_smtp, caplog):
        mock_smtp.return_value.login.side_effect = SMTPAuthenticationError(
            535, "Authentication failed"
        )
        with pytest.raises(Exception) as excinfo:
            with caplog.at_level("INFO"):
                email_sender = EmailService(
                    smtp_server="smtp.example.com",
                    smtp_port=587,
                    smtp_username="user",
                    smtp_password="pass",
                    from_address="from@example.com",
                    to_address=["to@example.com"],
                )

        print(f"Mocked calls : " f"{mock_smtp.mock_calls}")

        assert "Authentication failed" in caplog.text
        mock_smtp.assert_called_once_with("smtp.example.com", 587)

    def test_connect_fail_closing(self, mocker, mock_smtp, caplog):
        mock_smtp.return_value.noop.return_value = (250, b"OK")
        mock_smtp.return_value.quit.side_effect = Exception(
            "Failed to close connection"
        )

        with caplog.at_level("INFO"):
            email_sender = EmailService(
                smtp_server="smtp.example.com",
                smtp_port=587,
                smtp_username="user",
                smtp_password="pass",
                from_address="from@example.com",
                to_address=["to@example.com"],
            )

        print(f"Mocked calls : " f"{mock_smtp.mock_calls}")

        assert "Error closing SMTP connection" in caplog.text
        assert "Failed to close connection" in caplog.text
        assert email_sender.smtp_connection is None
        mock_smtp.assert_called_once_with("smtp.example.com", 587)

    @pytest.mark.parametrize(
        "emails, calls",
        [
            (["valid@example.com", "valid2@example.com"], 2),
            (["another.valid@example.com"], 1),
            ("string.email@example.com", 1),
        ],
    )
    def test_send_email_success(self, mocker, mock_smtp, emails, calls):
        # mock_smtp_instance = MagicMock()
        mock_smtp.return_value.noop.return_value = (250, b"OK")

        email_sender = EmailService(
            smtp_server="smtp.example.com",
            smtp_port=587,
            smtp_username="user",
            smtp_password="pass",
            from_address="from@example.com",
            to_address=emails,
        )

        email_sender.send_email(
            subject="Test Subject",
            body="Test Body",
            from_address="from@example.com",
            to_address=emails,
        )
        assert mock_smtp.return_value.send_message.call_count == calls

    def test_send_email_fail(self, mocker, mock_smtp, caplog):
        # mock_smtp_instance = MagicMock()
        mock_smtp.return_value.noop.return_value = (250, b"OK")
        mock_smtp.return_value.send_message.side_effect = Exception("SMTP error")

        email_sender = EmailService(
            smtp_server="smtp.example.com",
            smtp_port=587,
            smtp_username="user",
            smtp_password="pass",
            from_address="from@example.com",
            to_address=["to@example.com"],
        )

        with caplog.at_level("INFO"):
            email_sender.send_email(
                subject="Test Subject",
                body="Test Body",
                from_address="from@example.com",
                to_address=["to@example.com"],
            )

        assert "Error sending email [to@example.com]: SMTP error" in caplog.text
        assert mock_smtp.return_value.send_message.call_count == 1

    def test_send_email_no_connection(self, mocker, mock_smtp, caplog):
        mocked_methods = mocker.patch.multiple(
            EmailService,
            test_connection=mocker.DEFAULT,
            _connect=mocker.DEFAULT,
        )
        mocked_methods["test_connection"].return_value = None
        mocked_methods["_connect"].return_value = None

        email_sender = EmailService(
            smtp_server="smtp.example.com",
            smtp_port=587,
            smtp_username="user",
            smtp_password="pass",
            from_address="from@example.com",
            to_address=["to@example.com"],
        )

        with caplog.at_level(logging.DEBUG):
            email_sender.send_email(
                subject="Test Subject",
                body="Test Body",
                from_address="from@example.com",
                to_address=["to@example.com"],
            )

        print(caplog.records)
        assert (
            "SMTP connection could not be established. Email not sent." in caplog.text
        )
        assert mocked_methods["test_connection"].call_count == 1
        assert mocked_methods["_connect"].call_count == 1


class TestSendErrorMessage:
    """
    This class contains tests to verify the functionality of the send_error_message function.
    It includes tests for successful sending and handling errors.
    """

    def test_send_error_message_success(self, mocker):

        error_message = Exception("Test Error Message")
        start_time = datetime(2023, 1, 1, 12, 0, 0)
        test_from_address = "from@example.com"
        test_to_email = "test@example.com"

        mock_email_service = mocker.MagicMock()
        mock_email_service.send_email.return_value = None

        mock_end_time = mocker.patch(
            "snow_ipa.services.messaging.datetime", autospec=True
        )
        mock_end_time.now.return_value = datetime(2023, 1, 1, 12, 5, 0)

        send_error_message(
            script_start_time=start_time,
            exception=error_message,
            email_service=mock_email_service,
            from_address=test_from_address,
            to_address=test_to_email,
        )

        response_message = mock_email_service.send_email.call_args_list[0][1]
        print(response_message)

        assert mock_email_service.send_email.call_count == 1
        assert response_message["subject"] == "Snow IPA Export Report: Failed"
        assert "Status: Error" in response_message["body"]
        assert "Date: 2023-01-01 12:00:00" in response_message["body"]
        assert str(error_message) in response_message["body"]

    def test_send_error_message_backup_msg(self, mocker, caplog):

        error_message = Exception("Test Error Message")
        start_time = datetime(2023, 1, 1, 12, 0, 0)
        test_from_address = "from@example.com"
        test_to_email = "test@example.com"
        mock_email_service = mocker.MagicMock()
        mock_email_service.send_email.return_value = None

        mock_end_time = mocker.patch(
            "snow_ipa.services.messaging.datetime", autospec=True
        )
        mock_end_time.now.return_value = datetime(2023, 1, 1, 12, 5, 0)

        mock_template_environment = mocker.patch(
            "snow_ipa.services.messaging.template_env.get_template",
            autospec=True,
            side_effect=Exception("Template not found"),
        )

        with caplog.at_level(logging.DEBUG):
            send_error_message(
                script_start_time=start_time,
                exception=error_message,
                email_service=mock_email_service,
                from_address=test_from_address,
                to_address=test_to_email,
            )

        response_message = mock_email_service.send_email.call_args_list[0][1]
        print(response_message)
        mock_template_environment.assert_called_once()
        assert "Error reading or rendering email template" in caplog.text
        assert mock_email_service.send_email.call_count == 1
        assert response_message["subject"] == "Snow IPA Export Report: Failed"
        assert str(error_message) in response_message["body"]
