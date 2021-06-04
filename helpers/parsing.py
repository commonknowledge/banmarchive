import re
import datetime


def parse(parser, stream):
    tok = parser(stream)
    if tok:
        res, stream = tok
        if len(stream) != 0:
            raise Exception(
                f'Failed with {len(stream)} unparsed items from {str(stream[0])}')

        return res
    else:
        raise Exception('Parse Error')


def any_of(*parsers):
    def parse_any_of(stream):
        for p in parsers:
            tok = p(stream)
            if tok:
                return tok

    return parse_any_of


def multiple(parser, term=None):
    def parse_multiple(stream):
        stream = list(stream)
        res = []

        while len(stream) != 0:
            if term:
                tok = term(stream)
                if tok:
                    break

            tok = parser(stream)
            if tok:
                val, stream = tok
                res.append(val)
            else:
                break

        return res, stream

    return parse_multiple


def delimited(parser, delim, term=None):
    def parse_delimited(stream):
        stream = list(stream)
        res = []
        first = True

        while len(stream) != 0:
            if not first:
                tok = delim(stream)
                if tok is None:
                    break

                _, stream = tok

            if term:
                tok = term(stream)
                if tok:
                    break

            first = False
            tok = parser(stream)
            if tok:
                val, stream = tok
                res.append(val)
            else:
                break

        return res, stream

    return parse_delimited


def sequence(*seq):
    def parse_sequence(stream):
        res = []

        for s in seq:
            tok = s(stream)
            if tok is None:
                return

            val, stream = tok
            res.append(val)

        return res, stream

    return parse_sequence


def mapped(inner, fn):
    def parse_mapped(stream):
        tok = inner(stream)
        if tok:
            res, stream = tok
            return fn(*res), stream

    return parse_mapped


def filtered(inner, fn):
    def parse_filtered(stream):
        tok = inner(stream)
        if tok:
            res, stream = tok
            if fn(res):
                return tok

    return parse_filtered


def trimmed(el):
    s = el if isinstance(el, str) else el.get_text()
    return re.sub('\\s+', ' ', s).strip()


def parse_text(stream):
    res = ''

    while len(stream) > 0:
        head = stream[0]
        if isinstance(head, str):
            res += trimmed(head).strip()

        elif head.name == 'br':
            res += '\n'

        elif head.name == 'font':
            pass

        else:
            break

        stream = pop_front(stream)

    if res.strip() != '':
        return res.strip(), stream


def as_text(inner):
    return mapped(sequence(inner), lambda x: trimmed(x))


parse_string = mapped(
    sequence(parse_text),
    lambda text: trimmed(text)
)


def element(selector=None, deep=True):
    def test(head):
        if isinstance(head, str):
            return False

        if isinstance(selector, str):
            return head.name == selector

        elif isinstance(selector, tuple):
            return next((x for x in selector if head.name == x), None) is not None

        elif callable(selector):
            return selector(head)

    def parser(stream):
        if len(stream) == 0:
            return

        head = stream[0]
        match = None

        if isinstance(head, str):
            return

        if deep:
            # Find the first, deepest match of the selector on the head element
            candidate = head.find(selector)
            while candidate is not None:
                match = candidate
                candidate = candidate.find(selector)

        if match is None:
            match = head if test(head) else None

        if match:
            return trimmed(match), deep_pop_to(stream, match)

    return parser


def parse_whitespace(stream):
    if len(stream) == 0:
        return

    head = stream[0]

    if isinstance(head, str):
        text = head
    else:
        text = head.get_text()

    if text.strip() == '':
        return None, deep_pop_front(stream)


def parse_link(stream: list):
    if len(stream) == 0:
        return

    head = stream[0]

    if isinstance(head, str):
        return

    a = head if head.name == 'a' else head.find('a')
    if a is None:
        return

    res = {
        'content': trimmed(a).strip(),
        'href': a.attrs.get('href', '#')
    }
    return res, deep_pop_to(stream, a)


def filter_stream(parser, stream):
    res = []

    while len(stream) != 0:
        tok = parser(stream)
        if tok is None:
            res.append(stream[0])
            stream = pop_front(stream)
        else:
            _, stream = tok

    return res


def optional(inner, default=None):
    def parser(stream):
        tok = inner(stream)
        if tok is None:
            return default, stream
        else:
            return tok

    return parser


parse_pdf_link = filtered(
    parse_link, lambda link: link.get('href', '').endswith('.pdf'))


parse_internal_link = filtered(
    parse_link, lambda link: not link.get('href', '').endswith('.pdf'))


def find_markers(string: str, opts):
    if not isinstance(string, str):
        string = string.get_text()

    string = string.lower()

    if callable(opts):
        return opts(string)

    if isinstance(opts, re.Pattern):
        match = opts.search(string)
        if match is None:
            return -1

        return match.start()

    for marker in opts:
        idx = string.find(marker.lower())
        if idx > -1:
            return idx

    return -1


def has_markers(string, opts):
    return find_markers(string, opts) != -1


def upto_markers(string, opts, fn=None):
    idx = find_markers(string, opts)

    if idx == -1:
        return

    cut = string[:idx]
    return fn(cut) if fn is not None else cut


def after_markers(string, opts, fn=None):
    idx = find_markers(string, opts)

    if idx == -1:
        return

    cut = string[idx:]
    return fn(cut) if fn is not None else cut


def count_up_to(match, stream):
    i = 0
    for x in stream:
        if x == match:
            return i
        i += 1


def has_class(el, cls):
    return cls in el.attrs.get('class', ())


def pop_front(coll: list, count=1):
    next = list(coll)
    for _ in range(0, count):
        next.pop(0)

    return next


def deep_pop_front(stream):
    head = stream[0]

    num_descendants = 0 if isinstance(
        head, str) else len(list(head.descendants))

    return pop_front(stream, num_descendants + 1)


def deep_pop_to(stream, match):
    offset = count_up_to(match, stream)
    length = 1 if isinstance(match, str) else len(
        list(x for x in match.descendants))

    if offset is None:
        return pop_front(stream)
    else:
        return pop_front(stream, offset + length + 1)


SEASONS_WINTER_START = (
    ('winter', 12),
    ('spring', 3),
    ('summer', 6),
    ('autumn', 9),
)
YEAR_LNG = re.compile('\\d\\d\\d\\d')
YEAR_SHRT = re.compile('\\d\\d')


def seasonal_date(datestr: str):
    year = None
    month = None

    yearmatch = re.findall(YEAR_LNG, datestr)
    if len(yearmatch) > 0:
        year = int(yearmatch[0])

    else:
        yearmatch = re.findall(YEAR_SHRT, datestr)
        if len(yearmatch) > 0:
            year = 1900 + int(yearmatch[0])

    for season, season_month in SEASONS_WINTER_START:
        if season in datestr.lower():
            month = season_month

    if year is not None and month is not None:
        return datetime.date(year, month, 1)
