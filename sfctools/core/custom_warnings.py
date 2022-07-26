__version__ = "0.3"
__author__ = "Thomas Baldauf"
__email__ = "thomas.baldauf@dlr.de"
__license__ = "MIT"
__birthdate__ = '15.11.2021'
__status__ = 'prod' # options are: dev, test, prod

import os 

def warning_on_one_line(message, category, filename, lineno, file=None, line=None):
    """
    This defines the warning format of all sfctools warnings.
    """
    return '%s %s: %s [%s LINE %i]\n' % (":-( sfctools", category.__name__, message,os.path.basename(filename),lineno)

