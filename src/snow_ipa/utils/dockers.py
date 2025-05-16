import pathlib
import logging

DOCKER_SECRET_LINUX_PATH = "/var/run/secrets"


def check_docker_secret(var: str) -> str:
    """
    Checks if file exists in a given path or in docker secrets path.
    Returns None if file is not found or the file path if it is found.

    Args:
        var: path and name of the file to read.

    Returns:
        Returns the path to use to read var value or None if file doesn't exist
    """

    # Search for file path provided

    var_path = pathlib.Path(var)
    if var_path.exists():
        return var_path.as_posix()

    # else, if only file name is provided, try to find the file in docker secrets
    if len(var_path.parts) == 1:
        docker_var_path = pathlib.Path(DOCKER_SECRET_LINUX_PATH, var)
        if docker_var_path.exists():
            return docker_var_path.as_posix()

    raise FileNotFoundError(f"file not found: {var}")
