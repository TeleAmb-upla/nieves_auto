import pathlib
import logging

def check_docker_secret(var:str)->str:
    '''
    Checks if file exists in a given path or in docker secrets path. 
    Returns None if file is not found or the file path if it is found. 

    Args:
        var: path and name of the file to read.

    Returns:
        Returns the path to use to read var value or None if file doesn't exist
    '''
    docker_secrets_path = "/var/run/secrets"
    var_path=pathlib.Path(var)
    docker_var_path = pathlib.Path(docker_secrets_path,var)   

    if len(var_path.parts) > 1 and var_path.exists():
            return var_path.as_posix()

    elif docker_var_path.exists():
            return docker_var_path.as_posix()
    else:
        logging.warning(f"file not found {var}")
        return None