from math import log
import smtplib
from email.message import EmailMessage
import logging
from typing import Optional
import re
from typing import List
from email_validator import validate_email, EmailNotValidError


class EmailSender:
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

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        smtp_username: str,
        smtp_password: str,
        from_address: str,
        to_address: List[str],
    ) -> None:
        """
        Initializes the EmailSender class.

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
        self.from_address = from_address
        self.to_address = to_address
        if not self.test_connection():
            raise Exception("Failed to create EmailSender class: Connection failed.")

    def _connect(self) -> None:
        """
        Connects to the SMTP server.
        """
        try:
            self.smtp_connection = smtplib.SMTP(self.smtp_server, self.smtp_port)
            self.smtp_connection.starttls()
            self.smtp_connection.login(self.smtp_username, self.smtp_password)
        except Exception as e:
            print(f"Error connecting to SMTP server: {e}")
            self.smtp_connection = None

    def test_connection(self) -> bool:
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
                return False
            status = self.smtp_connection.noop()[0]
        except:
            status = -1
        finally:
            self._close_connection()
        return True if status == 250 else False

    def send_email(self, subject: str, body: str) -> None:
        """
        Sends an email with the given subject and body.

        Parameters:
        -----------
        subject : str
            The subject of the email.
        body : str
            The body of the email.
        """
        try:
            self._connect()
            message = EmailMessage()
            message["From"] = self.from_address
            message["To"] = self.to_address
            message["Subject"] = subject
            message.set_content(body)
            if self.smtp_connection is not None:
                self.smtp_connection.send_message(message)
        except Exception as e:
            logging.error(f"Error sending email: {e}")
        finally:
            self._close_connection()

    def _close_connection(self) -> None:
        """
        Closes the connection to the SMTP server.
        """
        if self.smtp_connection is None:
            return

        if hasattr(self, "smtp_connection") and self.smtp_connection:
            if self.smtp_connection.sock and not self.smtp_connection.sock._closed:  # type: ignore
                self.smtp_connection.quit()

    def __del__(self) -> None:
        """
        Closes the connection to the SMTP server when the object is deleted.
        """
        self._close_connection()


def init_email_service(config) -> Optional[EmailSender]:
    """
    Initializes an instance of EmailSender if email messaging is enabled in the configuration.

    Args:
        config (Config): A configuration object containing the variables for email messaging.

    Returns:
        An instance of EmailSender if email messaging is enabled, otherwise None.
    """
    logging.debug("---Initializing email messaging")

    enable_email = str(config.get("ENABLE_EMAIL", "")).lower() in ["true", "yes", "1"]

    if not enable_email:
        logging.debug("Email messaging disabled")
        return None

    try:
        if config.get("SMTP_USERNAME_FILE"):
            with open(config["SMTP_USERNAME_FILE"], "r") as f:
                config["SMTP_USERNAME"] = f.read().strip()

        if config.get("SMTP_PASSWORD_FILE"):
            with open(config["SMTP_PASSWORD_FILE"], "r") as f:
                config["SMTP_PASSWORD"] = f.read().strip()

        # if smtp_username or smtp_password are empty, then raise an error
        if not config["SMTP_USERNAME"]:
            raise ValueError("Invalid SMTP USERNAME")
        if not config["SMTP_PASSWORD"]:
            raise ValueError("Invalid SMTP PASSWORD")

        try:
            from_address = validate_email(config["FROM_ADDRESS"])
        except Exception as e:
            raise ValueError(f"Invalid FROM_ADDRESS: {repr(e)}")

        to_address = parse_emails(config["TO_ADDRESS"])

        if not to_address:
            raise ValueError("Invalid TO_ADDRESS")

        email_sender = EmailSender(
            smtp_server=config["SMTP_SERVER"],
            smtp_port=config["SMTP_PORT"],
            smtp_username=config["SMTP_USERNAME"],
            smtp_password=config["SMTP_PASSWORD"],
            from_address=from_address.email,
            to_address=to_address,
        )

        logging.debug("Email messaging enabled")
        return email_sender

    except FileNotFoundError as e:
        logging.warning(
            f"Initializing email service failed: SMTP username or password file not found -> {e}"
        )
    except ValueError as e:
        logging.warning(f"Initializing email service failed: {e}")
    except Exception as e:
        logging.warning(f"Initializing email service failed: {e}")

    return None


def build_email_message(message, start_time, end_time):
    """
    Build an email message to send to the user.
    """
    text = f"""\
    Start time: {start_time}
    End time: {end_time}

    {message}
    """
    html = f"""\
    <html>
        <body>
            <p>Start time: {start_time}<br>
             End time: {end_time}</p>
            <p>{message}</p>
        </body>
    </html>
    """
    return text, html


def send_email(server: EmailSender, message, start_time, end_time):
    """
    Send an email to the user.
    """
    subject = "Snow Automation Script"
    text, html = build_email_message(message, start_time, end_time)
    server.send_email(
        subject=subject,
        body=text,
    )
    return


def parse_emails(emails_str: str) -> List[str]:
    """
    Parse a string of comma or semicolon separated email addresses into a list of email addresses.
    """
    emails = re.split(r"[,;]\s*", emails_str)
    valid_emails = []
    for email in emails:
        try:
            # Validate the email using email-validator package
            valid = validate_email(email)
            # Append the email to the list of valid emails
            valid_emails.append(valid.email)
        except EmailNotValidError:
            # If the email is not valid, skip it
            pass
    return valid_emails


def main():
    pass


if __name__ == "__main__":
    main()
