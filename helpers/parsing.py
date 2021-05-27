import re


def parse(parser, stream):
    tok = parser(stream)
    if tok:
        res, stream = tok
        if len(stream) != 0:
            raise Exception(
                f'Failed with {len(stream)} unparsed items from {trimmed(stream[0]).strip()}')

        return res
    else:
        raise Exception('Parse Error')


def trimmed(el):
    s = el if isinstance(el, str) else el.get_text()
    return re.sub('\\s+', ' ', s)


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
        return res, stream


def element(selector=None):
    def parser(stream):
        if len(stream) == 0:
            return

        head = stream[0]

        if isinstance(head, str):
            return

        matches = head.find_all(selector)
        if len(matches) == 0:
            return

        match = matches[len(matches) - 1]

        return trimmed(match), deep_pop_to(stream, match)

    return parser


def any_of(*parsers):
    def parser(stream):
        for p in parsers:
            tok = p(stream)
            if tok:
                return tok

    return parser


def multiple(parser):
    def parse(stream):
        stream = list(stream)
        res = []

        while len(stream) != 0:
            tok = parser(stream)
            if tok:
                val, stream = tok
                res.append(val)
            else:
                break

        return res, stream

    return parse


def sequence(*seq):
    def parser(stream):
        res = []

        for s in seq:
            tok = s(stream)
            if tok is None:
                return

            val, stream = tok
            res.append(val)

        return res, stream

    return parser


def mapped(inner, fn):
    def parser(stream):
        tok = inner(stream)
        if tok:
            res, stream = tok
            return fn(*res), stream

    return parser


def filtered(inner, fn):
    def parser(stream):
        tok = inner(stream)
        if tok:
            res, stream = tok
            if fn(res):
                return tok

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


def count_up_to(match, stream):
    i = 0
    for x in stream:
        if x == match:
            return i
        i += 1


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
    length = 1 if isinstance(match, str) else len(list(match.descendants))

    return pop_front(stream, offset + length + 1)
