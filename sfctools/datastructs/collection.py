__version__ = "0.3"
__author__ = "Thomas Baldauf"
__email__ = "thomas.baldauf@dlr.de"
__license__ = "MIT"
__birthdate__ = '15.11.2021'
__status__ = 'prod' # options are: dev, test, prod


from collections import defaultdict, deque
from functools import partial
import numpy as np
from enum import Enum

class CollectionType(Enum):
    SINGLE = 0
    LIST = 1
    DEQUE = 2


class Collection:
    """
    A 'collection' is a special data structure: it is a dict of items.

    kind 'single' looks like
    {tag: value,
    tag2: value,
    tag3: value,
    ...}

    inserting a new value will result in overwrite.

    kind 'list' looks like
    {tag: [value,value,value,..],
    tag2: [value,value,...],
    tag3: [...],
    ...}

    if maxlen is not infinity then insertion will result in a deque append, otherwise list append.

    possible operations are:

    - insert()  inserts a new item
    - remove()   removes an item
    - get_count() gets the number of items stored under a tag
    - get_last() gets the last inserted item of a tag

    """

    def __init__(self, kind="single", maxlen=np.inf):
        """
        :param kind: 'single' or 'list'
        :param maxlen: maximum allowed length. only has an effect if kind is 'list'

        constructor for Collection.
        """

        self.last_tag = None
        self.kind = None
        self._data = None

        """
        assign kind of data format, 
        assign actual data initially
        """

        assert kind == "single" or kind == "list"

        if kind == "list" and maxlen == np.inf:  # a list with infinite length
            self.kind = CollectionType.LIST
            self._data = defaultdict(list)

        elif kind == "list" and maxlen < np.inf:  # a 'list with limited length' (deque)
            self.kind = CollectionType.DEQUE
            self._data = defaultdict(partial(deque, maxlen=maxlen))

        elif kind == "single":  # a single entry
            self.kind = CollectionType.SINGLE
            self._data = {}

        else:
            raise TypeError("Invalid kind of collection. Allowed are 'single' or 'list'")

    def items(self):
        return self._data.items()

    def keys(self):
        return self._data.keys()

    def insert(self, t, new_data, verbose=False):
        """
        insert new data at tag t.

        :param t: the tag (e.g. time) for the data
        :param new_data:  the new data
        :param verbose: verbose flag
        """
        if verbose: print("insert", t, new_data,self.kind)

        if self.kind == CollectionType.SINGLE:
            # if t in self._data:
            #    raise KeyError("Key %s already written" % t)
            # else:
            self._data[t] = new_data

        elif self.kind == CollectionType.LIST or self.kind == CollectionType.DEQUE:
            self._data[t].append(new_data)  # defaultdict will take care of missing keys

        self.last_tag = t

    def remove(self, t, entry):
        """
        remove an entry from a tag t
        :param t:  tag
        :param entry:  entry to be removed
        """

        if t in self._data:
            # self._data.pop(t, None) <- this actually removes all entries
            self._data[t].remove(entry)

            if len(self._data[t]) == 0: # if this was the last item <- pop out the tag completely
                self._data.pop(t,None)

        else:
            raise KeyError("Cannot remove item: Tag %s was not found" % t)  # we do not want to use defaultdict here

    def get_count(self, t):
        """
        Get the number of existing entries for this count
        :param t:
        :return:
        """

        count = 0
        if t in self._data:
            count = len(self._data[t])

        return count

    def get_last(self):
        """
        get the last tag and data. If there was None, return None

        :return: t, data or None
        """

        if self.last_tag is None:
            return None
        else:
            return self.last_tag, self._data[self.last_tag]

    def values(self):
        """
        like in a dict, return all value entries
        """

        all_vals = []

        for key,val in self._data.items():
            if isinstance(val,dict) or isinstance(val,defaultdict):
                all_vals.append(val.values())
            else:
                all_vals.append(val)

        return all_vals

    def get_entries(self):
        return self._data

    def __getitem__(self,key):
        """
        element search in Collection by key

        :param key: key to search for
        :returns: value, stored value
        """

        return self._data[key]


    def __str__(self):
        return str(self._data)