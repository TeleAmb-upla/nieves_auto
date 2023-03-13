import sys
import os
import logging
from . import logs

def set_script_config_var (var:str, arg_value:str=None, default=None, 
                           required:bool=False, parse:str=None):
    '''
    Sets a global variable from a given argument, an Environmental Variable or using a default value.
    
    Args:
        var: Name of the variable to set
        arg_value: explicit value to set in the variable. If not set the value will be taken from an Environment Variable or a pre set default value
        default: Default value to use in case no explicit value or Environment Variable is found.
        required: Indicates if the value is required and can't be None, otherwise error out. 
        parse: Indicates if the value needs to be parsed in a given form. Currently only parses to list.

    Returns:
        Returns a string or a list.
    '''
    # Check the required variable exists in globals otherwise Exit
    # try: 
    #     assert var in globals()
    # except:
    #     logging.print_log(f"{var}: Unknown variable", "ERROR")
    #     sys.exit(0)
    
    # Set var value
    using_default_msg=""
    try:
        if arg_value:
            value = arg_value
        else:
            value =  os.environ[var]
    except KeyError as e:
        value = default
        using_default_msg= "(default value)"

    # Parse values 
    if value and parse:
        try: 
            if parse == 'List':
                value = [item.strip() for item in value.split(",")]
        except:
            logs.print_log(f"Could not parse value as: {parse}", "ERROR")

    # Error out if var is required but value is None
    if required==True and value==None:
        logs.print_log(f"{var} is required but no value was set", 'ERROR')
        sys.exit(0)
    
    logging.debug(f"{var}: {value} {using_default_msg}")
    return value
