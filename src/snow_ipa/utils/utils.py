import os


def csv_to_list(csv_string: str) -> list:
    """
    Converts a comma-separated string to a list of strings.

    Args:
        csv_string: A string of comma-separated values.

    Returns:
        A list of strings.
    """
    csv_list = [item.strip(" \"'") for item in csv_string.split(",")]
    return list(filter(None, csv_list))


def env_to_dict(env_prefix: str) -> dict:
    """
    Convert environment variables with a specific prefix to a dictionary.

    Args:
        env_prefix (str): The prefix for the environment variables.

    Returns:
        dict: A dictionary containing the environment variables with the specified prefix.
    """
    env_dict = {}
    for key, value in os.environ.items():
        if key.startswith(env_prefix):
            env_key = key[len(env_prefix) + 1 :]
            env_dict[env_key] = value.strip(" \"'") if value else None
    return env_dict


def keys_to_lower(d: dict) -> dict:
    """
    Convert all keys in a dictionary to lowercase.

    Args:
        d (dict): The original dictionary.

    Returns:
        dict: A new dictionary with all keys converted to lowercase.
    """
    return {k.lower(): v for k, v in d.items()}


def replace_values_in_dict(d: dict, replacements: dict) -> dict:
    """
    Replace values in a dictionary based on a mapping dictionary.

    Args:
        d (dict): The original dictionary.
        replacements (dict): A dictionary containing the replacements.

    Returns:
        dict: The updated dictionary with replaced values.
    """
    target_dict = d.copy()
    for key in target_dict:
        replacement_value = replacements.get(key, None)
        if replacement_value:
            target_dict[key] = replacement_value
            continue

    return target_dict
