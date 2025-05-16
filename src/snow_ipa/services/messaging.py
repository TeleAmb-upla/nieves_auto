import smtplib
from email.message import EmailMessage
import logging
import re
from datetime import datetime
import arrow
from email_validator import validate_email, EmailNotValidError

# from snow_ipa.utils.templates import templates
from snow_ipa.core.exporting import ExportManager
from snow_ipa.core.configs import ERROR_EMAIL_TEMPLATE, SUCCESS_EMAIL_TEMPLATE
from jinja2 import Template, Environment, PackageLoader, select_autoescape


logger = logging.getLogger(__name__)

template_env = Environment(
    loader=PackageLoader(package_name="snow_ipa.utils", package_path="templates"),
    autoescape=select_autoescape(),
)


class EmailService:
    """
    A class for sending emails using SMTP.

    Attributes:
    -----------
    smtp_server : str
        The SMTP server to use for sending emails.
    smtp_port : int
        The port number to use for the SMTP server.
    smtp_username : str
        The username to use for authenticating with the SMTP server.
    smtp_password : str
        The password to use for authenticating with the SMTP server.
    from_address : str
        The email address to use as the sender.
    to_address : List[str]
        The email address to use as the recipient.

    Methods:
    --------
    test_connection() -> bool
        Tests the connection to the SMTP server.
    send_email(subject: str, body: str) -> None
        Sends an email with the given subject and body.
    """

    smtp_connection: smtplib.SMTP | None = None

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        smtp_username: str,
        smtp_password: str,
    ) -> None:
        """
        Initializes the EmailService class.

        Parameters:
        -----------
        smtp_server : str
            The SMTP server to use for sending emails.
        smtp_port : int
            The port number to use for the SMTP server.
        smtp_username : str
            The username to use for authenticating with the SMTP server.
        smtp_password : str
            The password to use for authenticating with the SMTP server.
        from_address : str
            The email address to use as the sender.
        to_address : str
            The email address to use as the recipient.
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.test_connection()

    def _connect(self) -> None:
        """
        Connects to the SMTP server.
        """
        # NOTE: _connect will not raise an Exception in case server is down.
        # Automated image processing should still run.
        try:
            self.smtp_connection = smtplib.SMTP(self.smtp_server, self.smtp_port)
            self.smtp_connection.starttls()
            self.smtp_connection.login(self.smtp_username, self.smtp_password)
        except Exception as e:
            # Catching all errors, no specific action being taken for SMTP errors
            e_message = f"Error connecting to SMTP server: {e}"
            logger.error(e_message)
            self.smtp_connection = None
            # raise Exception(e_message)

    def test_connection(self) -> None:
        """
        Tests the connection to the SMTP server.

        Returns:
        --------
        bool
            True if the connection is successful, False otherwise.
        """
        try:
            self._connect()
            if self.smtp_connection is None:
                raise Exception("SMTP connection failed. Check logs for specific error")
            response_code, _ = self.smtp_connection.noop()
            if response_code == 250:
                logger.debug(
                    f"SMTP connection test successful with response code: {response_code}"
                )
            else:
                raise Exception(
                    f"SMTP connection test failed with response code: {response_code}"
                )
            self._close_connection()
        except Exception as e:
            logger.exception(e)
            raise e

    def send_email(
        self, subject: str, body: str, from_address: str, to_address: str | list[str]
    ) -> None:
        """
        Sends an email with the given subject and body.

        Parameters:
        -----------
        subject : str
            The subject of the email.
        body : str
            The body of the email.
        """
        self._connect()

        if self.smtp_connection is None:
            logger.error("SMTP connection could not be established. Email not sent.")
            return

        if isinstance(to_address, str):
            to_address = [to_address]

        for _address in to_address:
            try:
                message = EmailMessage()
                message["From"] = from_address
                message["To"] = _address
                message["Subject"] = subject
                message.set_content(body)
                if self.smtp_connection is not None:
                    self.smtp_connection.send_message(message)
            except Exception as e:
                logger.error(f"Error sending email [{_address}]: {e}")

        # Close the connection
        self._close_connection()

    def _close_connection(self) -> None:
        """
        Closes the connection to the SMTP server.
        """
        if self.smtp_connection is None:
            return

        try:
            # Quit and set connection to none
            self.smtp_connection.quit()
            self.smtp_connection = None
        except Exception as e:
            logger.error(f"Error closing SMTP connection: {e}")
            self.smtp_connection = None

    def __del__(self) -> None:
        """
        Closes the connection to the SMTP server when the object is deleted.
        """
        self._close_connection()


def parse_emails(emails: str | list) -> list[str]:
    """
    Parse a string emails separated by commas or semicolon into a list of email addresses.

    validates if the emails are valid. Omits invalid emails from the result list.

    Args:
        emails_str (str): A string of email addresses separated by comma or semicolon

    Returns:
        List[str]: A list of valid email


    """
    if isinstance(emails, str):
        # Split the string into a list of emails using regex to handle various delimiters
        emails = re.split(r"[;,]", emails.strip())

    valid_emails = []
    for email in emails:
        try:
            valid = validate_email(email, check_deliverability=False)
            valid_emails.append(valid.normalized)
        except EmailNotValidError:
            logger.warning(f"Invalid email address will be skipped: {email}")
    return valid_emails


def send_error_message(
    script_start_time: datetime,
    exception: Exception,
    email_service: EmailService,
    from_address: str,
    to_address: str | list[str],
) -> str | None:

    start_time = arrow.get(script_start_time)
    end_time = arrow.get(datetime.now())
    runtime = start_time.humanize(end_time, only_distance=True)

    try:
        template = template_env.get_template(ERROR_EMAIL_TEMPLATE)
        message = template.render(
            {
                "status": "Error",
                "error_message": str(exception),
                "start_time": start_time.format("YYYY-MM-DD HH:mm:ss (dddd)"),
                "execution_time": runtime,
            }
        )

    except Exception as e:
        logger.error(f"Error reading or rendering email template: {e}")
        message = f"Error Message: {str(exception)}"

    subject = "Snow IPA Export Report: Failed"
    email_service.send_email(
        subject=subject, body=message, from_address=from_address, to_address=to_address
    )

    return message


def send_report_message(
    export_manager: ExportManager,
    script_start_time: datetime,
    email_service: EmailService,
    from_address: str,
    to_address: str | list[str],
):

    image_prefix = export_manager.image_prefix

    # Runtime Info
    start_time = arrow.get(script_start_time)
    end_time = arrow.get(datetime.now())
    runtime = start_time.humanize(end_time, only_distance=True)

    # MODIS Status
    modis_status = (
        f"Collection: {export_manager.modis_status['collection']}\n"
        + f"Total Images: {export_manager.modis_status['total_images']}\n"
        + f"Last Image: {export_manager.modis_status['last_image']}\n"
        + f"Last Complete Month: {export_manager.modis_status['last_complete_month']}"
    )
    # General Export Plan
    general_plan = export_manager.export_plan["final_plan"]

    if general_plan is None:
        general_plan = [f"- {image_prefix}_{m[:7]}" for m in general_plan]
        general_plan = "\n".join(general_plan)
    else:
        general_plan = "- No new images to export"

    # General Export Plan Exceptions
    general_exceptions = export_manager.export_plan["excluded"]
    if len(general_exceptions.keys()) > 0:
        general_exceptions = [
            f"- {image_prefix}_{key[:7]}: {value}"
            for key, value in general_exceptions.items()
        ]
        general_exceptions = "\n".join(general_exceptions)
    else:
        general_exceptions = ""

    general_plan = (
        f"Images to export:\n{general_plan}\n\nImages Excluded:\n{general_exceptions}"
    )

    # GEE export plan
    gee_path = (
        export_manager.gee_assets_path if export_manager.export_to_gee else "Disabled"
    )
    gee_export_plan = [
        f"{task.image}: {task.status} {task.error if task.error else ''}"
        for task in export_manager.export_tasks.export_tasks
        if task.target == "gee"
    ]
    if len(gee_export_plan) > 0:
        gee_export_plan = [f"- {task}" for task in gee_export_plan]
        gee_export_plan = "\n".join(gee_export_plan)
        gee_export_plan = f"Results:\n{gee_export_plan}"
        gee_results_summary = export_manager.export_tasks.pretty_export_summary(
            filter="gee"
        )
    else:
        gee_export_plan = "- No new images to export"
        gee_results_summary = ""

    # GDRIVE export plan
    gdrive_path = (
        export_manager.gdrive_assets_path
        if export_manager.export_to_gdrive
        else "Disabled"
    )
    gdrive_export_plan = [
        f"{task.image}: {task.status} {task.error if task.error else ''}"
        for task in export_manager.export_tasks.export_tasks
        if task.target == "gdrive"
    ]
    if len(gdrive_export_plan) > 0:
        gdrive_export_plan = [f"- {task}" for task in gdrive_export_plan]
        gdrive_export_plan = "\n".join(gdrive_export_plan)
        gdrive_export_plan = f"Results:\n{gdrive_export_plan}"
        gdrive_results_summary = export_manager.export_tasks.pretty_export_summary(
            filter="gdrive"
        )
    else:
        gdrive_export_plan = "- No new images to export"
        gdrive_results_summary = ""

    # Status
    exports = [
        str(img)
        for img in export_manager.export_tasks.export_tasks
        if img.status != "ALREADY_EXISTS"
    ]
    complete_exports = [
        str(img)
        for img in export_manager.export_tasks.export_tasks
        if img.status == "COMPLETED"
    ]

    if complete_exports:
        status = f"Completed - {len(complete_exports)} images exported"
    elif exports:
        status = f"Completed - with errors"
    else:
        status = "Completed - No new images to export"

    try:
        template = template_env.get_template(SUCCESS_EMAIL_TEMPLATE)
        message = template.render(
            {
                "status": status,
                "start_time": start_time.format("YYYY-MM-DD HH:mm:ss (dddd)"),
                "execution_time": runtime,
                "results_summary": export_manager.export_tasks.pretty_export_summary(),
                "general_plan": general_plan,
                "gee_path": gee_path,
                "gee_results_summary": gee_results_summary,
                "gee_export_plan": gee_export_plan,
                "gdrive_path": gdrive_path,
                "gdrive_results_summary": gdrive_results_summary,
                "gdrive_export_plan": gdrive_export_plan,
                "modis_status": modis_status,
            }
        )
    except Exception as e:
        print(str(e))
        logger.error(f"Error reading or rendering email template: {str(e)}")

    subject = f"Snow IPA Export Report: {status}"
    email_service.send_email(
        subject=subject, body=message, from_address=from_address, to_address=to_address
    )

    return message
