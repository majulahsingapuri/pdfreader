import zlib

from decimal import Decimal

null = None
Boolean = bool
Integer = int
Real = Decimal
Array = list
Dictionary = dict


class String(str):
    """ Literal string. Just to tell apart of the other types """


class Name(str):
    """ Name type: /SomeName """


class HexString(String):
    """ Hexadecimal string: <AF20FA> """


class Stream(object):
    """ binary stream: dictionary and binary data
        common keys:
        Length - integer (required)
        Filter - name or array
        DecodeParams - dict or array
        F - file specification
        FFilter -

    """

    def __init__(self, info_dict, binary_stream):
        assert isinstance(info_dict, Dictionary)
        assert isinstance(binary_stream, bytes)

        if "Length" not in info_dict:
            raise KeyError("Missing stream length")

        if info_dict["Length"] != len(binary_stream):
            raise ValueError("Inconsistend stream")

        self.dictionary = info_dict
        self.stream = binary_stream

    def __getitem__(self, item):
        return self.dictionary.__getitem__(item)

    def get(self, item, default=None):
        return self.dictionary.get(item, default)

    def __len__(self):
        return len(self.stream)

    def __repr__(self):
        data = self.stream
        if len(data) > 25:
            data = (self.stream[:25] + b' ...')
        return "<Stream:len={},data={}>".format(self.dictionary["Length"], repr(data))

    @property
    def filtered(self):
        filters = self.get('Filter')
        if not filters:
            return self.stream

        if isinstance(filters, Array):
            farr = filters
        elif isinstance(filters, Name):
            farr = Array()
            farr.append(filters)
        else:
            raise TypeError("Incorrect filter type: {}".format(filters))

        data = self.stream
        for f in farr:
            method = getattr(self, "filter_{}".format(f))
            if method is None:
                raise ValueError("Unknown filter {}".format(f))
            data = method(data)
        return data

    def _remove_predictors(self, data):
        """ Remove LZW/Flate predictors
        1 - No prediction
        2 - TIFF predictor 2
        10 - PNG None
        11 - PNG Sub
        12 - PNG Up
        13 - PNG Average
        14 - PNG Paeth
        15 - PNG Optimum
        """
        params = self.get('DecodeParms') or dict()
        predictor = params.get('Predictor', 1)
        if predictor == 1:
            res = data
        elif predictor == 2:
            raise ValueError("TIFF prediction not implemented")
        elif 10 <= predictor <= 15:
            row_size = params["Columns"] + 1
            res = b''
            for i in range(0, len(data), row_size):
                if data[0] + 10 != predictor:
                    raise ValueError("Unexpected predictor {}".format(data[0]))
                res += data[i+1:i+row_size] # skip leading predictor byte
        else:
            raise ValueError("Unknown predictor type {}".format(predictor))
        return res

    def filter_FlateDecode(self, data):
        data = zlib.decompress(data)
        data = self._remove_predictors(data)
        return data

    def __eq__(self, other):
        return self.dictionary == other.dictionary and self.stream == other.stream


class Comment(str):
    """ % Some PDF Comment """


class IndirectReference(object):
    def __init__(self, number, generation):
        """ 10 0 R """
        assert isinstance(number, int)
        assert isinstance(generation, int) and generation >= 0

        self.num = number
        self.gen = generation

    def __repr__(self):
        return "<IndirectReference:n={self.num},g={self.gen}>".format(self=self)

    def __eq__(self, other):
        return self.num == other.num and self.gen == other.gen


class IndirectObject(object):
    """ 10 0 obj
        ....
        endobj
    """
    def __init__(self, number, generation, value):
        assert isinstance(number, int)
        assert isinstance(generation, int) and generation >= 0
        assert isinstance(value,
                          (type(null), Boolean, Integer, Real, Array, Dictionary, String, Name, HexString, Stream,
                           IndirectReference))
        self.num = number
        self.gen = generation
        self.val = value

    @property
    def id(self):
        return self.num, self.gen

    def __repr__(self):
        return "<IndirectObject:n={self.num},g={self.gen},v={val}>".format(self=self, val=repr(self.val))

    def __eq__(self, other):
        return self.num == other.num and self.gen == other.gen


PDF_TYPES = (type(null), IndirectReference, IndirectObject, Comment, Stream, Dictionary, Integer, Real, Boolean, Array,
             String, HexString, Name)

ATOMIC_TYPES = (Integer, Real, Boolean, String, HexString, Name, type(null))