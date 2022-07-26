__author__ = "Thomas Baldauf"
__version__ = "Pre-release (michelada)"
__email__ = "thomas.baldauf@dlr.de"
__license__ = "MIT"
__version__ = "0.3"

import numpy as np
from collections import deque

class ShiftLogger(deque):
    """
    shifting logger register data structure.
    (Same as shift register in electronics.)

    [ a , b , c , d , e ] < f
      ^

    inserting a new value f will cause a to be dropped and all values shifted

    [ b , c , d , e, f ] < ...
      ^

    possible operations are:

    - insert() inserts a new value to the logger
    """

    def __init__(self, length=10):
        """"
        Constructor of the shift register,
        :param length: length of the register memory
        """
        super().__init__(maxlen=length)

    def predict(self, method="mean", dt=1):
        """
        predict dt time steps ahead
        :param method: prediction method to use

        * 'mean' is just the mean value
        * 'trend' uses the trend between first and last value

        :param dt:  number of time steps to predict ahead

        :return: the predicted value for t(0) + dt
        """

        if method == "mean":
            return np.mean(self)

        elif method == "trend":
            return self[-1] + (self[-1] - self[0]) / len(self) * dt

        raise NotImplementedError("Cannot find the prediction method %s" % method)
