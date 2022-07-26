__version__ = "0.3"
__author__ = "Thomas Baldauf"
__email__ = "thomas.baldauf@dlr.de"
__license__ = "MIT"
__birthdate__ = '15.11.2021'
__status__ = 'prod' # options are: dev, test, prod


from ..core.clock import Clock
import warnings


class Slot:
    """
    Slot is the receiver of an information stream
    """
    _instances = {}

    def __init__(self, name, asynchronous = False):
        """
        This is a slot.
        :param name: name of the slot
        :param asynchronous:
        """

        self.name = name
        self.data = {}
        self.asynchronous = asynchronous
        self.__class__._instances[self.name] = self

    def __repr__(self):
        return "[Oo. SLOT %s]" % self.name

    @classmethod
    def retrieve(cls, name):
        """
        find a certain slot by name 

        :param name: name of the slot
        :return: Slot
        """
        return cls._instances[name]

    def receive(self,signal,verbose=False):
        """
        slot receives a signal

        :param signal: a Signal instance who triggered this slot to receive
        :param verbose: enables verbose mode (default False)

        """
        assert signal.name == self.name, "Signal and slot of different name have been connected, which is not allowed."
        if verbose:
            print("Slot %s received %s" % (self,signal))
        self.data[Clock().get_time()] = signal.value()

    def check_up_to_date(self):
        """
        checks if the slot is up to date, i.e. if the data has been filled with a value
        in the current time step
        """

        if Clock().get_time() in self.data:
            return True
        else:
            return False

    def value(self):
        """
        get current value
        """

        vals = self.data.values()
        if len(vals) == 0:
            warnings.warn("Empty data in Slot %s. Returning zero" % self.name)
            return 0.0

        return list(vals)[-1]

    def rlch(self):
        """
        get relative change since last update

        """
        vals = self.data.values()

        if len(vals) < 2:
            return 0

        vals = list(vals)[-2:]

        dif = (vals[-1] - vals[-2]) / vals[-2]
        return dif



class Signal:
    """
    Signal is the emitter of an information stream
    """
    _instances = {}

    def __init__(self, name, asynchronous=False):
        """
        This is a basic signal.

        :param name: name of the signal
        :param asyncronous: check_up_to_date will return True always if this is set to True
        """

        self.name = name
        self.data = {}
        self.asynchronous = False
        self.__class__._instances[self.name] = self
        self.slots = []

    def __repr__(self):
        return "[.oO SIGNAL %s]" % self.name
    @classmethod
    def retrieve(cls, name):
        """
        find a certain signal by name

        :param name: name of the signal
        :return: Signal
        """
        return cls._instances[name]

    def connect_to(self, list_of_slots):
        """
        slots connected
        
        :param list_of_slots: a list of slots to connect to this signal
        """
        self.slots = list_of_slots
        return self

    def emit(self,verbose=False):
        """
        emit the signal to all connected slots
        
        :param verbose: enables verbose mode (default False)
        """

        for slot in self.slots:
            slot.receive(self, verbose=verbose)

    def check_up_to_date(self):
        """
        checks if the signal is up to date, i.e. if the signal has been filled with a value
        in the current time step
        """
        
        if Clock().get_time() in self.data:
            return True
        else:
            return False

    def update(self, value):
        """
        insert latest value

        :param: value
        """

        self.data[Clock().get_time()] = value
        return self

    def value(self):
        """
        get current value
        """

        vals = self.data.values()
        if len(vals) == 0:
            warnings.warn("Empty data in Signal %s. Returning zero" % self.name)
            return 0.0
        return list(vals)[-1]

    def rlch(self):
        """
        get relative change since last update
        """

        vals = self.data.values()

        if len(vals) < 2:
            return 0

        vals = list(vals)[-2:]

        dif = (vals[-1] - vals[-2]) / vals[-2]
        return dif


class SignalSlot:
    """
    A connection including a signal and slot
    """

    def __init__(self, name, asynchronous=False):
        """
        
        :param name: name of the signal-slot connection
        :param asynchronous: is the signal triggered in every simulation period?
        """

        self.signal = Signal(name, asynchronous)
        self.slot = Slot(name, asynchronous)
        self.signal.slots.append(self.slot)

    def trigger(self):
        """
        Trigger of this connection. Emits the signal to the slot.
        """

        self.signal.emit()

