from ..constants import WHITESPACES
from ..types.content import InlineImage
from ..types.native import Token
from .base import BasicTypesParser


class InlineImageParser(BasicTypesParser):
    """ BI/EI section parser

    >>> content = b'BI/D [1 0]/IM true /W 1800 /H 3113 /BPC 1 /F /CCITTFaxDecode /DecodeParms << /K -1 /Columns 1800 /Rows 3113 /BlackIs1 true >> ID <SOME-BINARY-CONTENT> EI'
    >>> img = InlineImageParser(None, content).inline_image()
    >>> img.dictionary['W']
    1800
    >>> img.dictionary['D']
    [1, 0]
    >>> img.data
    b'<SOME-BINARY-CONTENT>'

    """
    def __init__(self, context, *args, **kwargs):
        self.context = context
        # ToDo: we should take into account current graphics state
        super(InlineImageParser, self).__init__(*args, **kwargs)

    def _get_parser(self):
        method = super(InlineImageParser, self)._get_parser()
        if method is None:
            # assume token
            method = self.token
        return method

    def entities(self):
        res = dict()
        self.maybe_spaces_or_comments()
        while self.current != b'I': # all entities come before ID, then - binary data comes
            key = self.name()
            self.maybe_spaces_or_comments()
            val = self.object()
            if isinstance(val, Token):
                self.on_parser_error("Unexpected token: {}".format(val))
            res[key] = val
            self.maybe_spaces_or_comments()
        self.next()
        if self.next() != b'D':
            self.on_parser_error("ID expected ")
        return res

    def inline_image(self):
        token = self.object()
        if token != 'BI':
            self.on_parser_error("Unexpected token")
        entities = self.entities()
        if not self.is_whitespace:
            self.on_parser_error("Whitespace expected")
        self.next()
        # read until whitespace + ID
        data = b''
        while True:
            data += self.next()
            if data.endswith(b'EI') and data[-3:-2] in WHITESPACES:
                data = data[:-3]
                break

        res = InlineImage(entities, data)
        return res


if __name__ == "__main__":
    import doctest
    doctest.testmod()