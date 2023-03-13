# libraries
from datetime import datetime, date
import pytz



# Constants. Used as Defaults in case no alternative is provided.
UTC_TZ=pytz.timezone('UTC')

def format_ee_timestamp(dt, tz=UTC_TZ):
    '''
    Formats a date retreived from GEE using a given timezon. 
    Default timezone is UTC
    '''
    return datetime.fromtimestamp(dt['value']/1000, tz)

def print_ee_timestamp(dt, tz=UTC_TZ):
    '''
    Prints a date retreived from gee using a given Timezone. 
    Default timezone is UTC
    '''
    print(format_ee_timestamp(dt, tz))