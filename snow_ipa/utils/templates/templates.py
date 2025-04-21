from importlib import resources
import snow_ipa.utils.templates as templates
import logging

logger = logging.getLogger(__name__)

# def read_file_to_var(file_path: str) -> str:
#     """
#     Reads a file and returns its contents as a string.

#     Args:
#         file_path (str): The path to the file to read.

#     Returns:
#         str: The contents of the file.
#     """
#     with open(file_path, "r") as f:
#         file_contents = f.read()
#     return file_contents


def get_template(template: str, default_template: str) -> str:
    """
    Retrieves the content of a template file. If the file is not found, returns the default template.

    Args:
        template (str): The name of the template file.
        default_template (str): The default template content to return if the file is not found.

    Returns:
        str: The content of the template file or the default template.
    """

    try:
        template_path = resources.files(templates).joinpath(template).__str__()
        with open(template_path) as f:
            content = f.read()
        if not content.strip():
            logger.warning(f"Template file is empty: {template}")
        else:
            return content

    except FileNotFoundError:
        logger.error(f"Template file not found: {template}")

    except Exception as e:
        logger.exception(
            f"An unexpected error occurred while reading the template: {template}"
        )

    return default_template
