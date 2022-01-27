
import imp
from sys import stderr, stdout
from bs4 import BeautifulSoup, element
from urllib.parse import unquote


def emit(x=''):
    if not x:
        return

    if hasattr(x, 'getText'):
        return emit(x.getText())

    x = ' '.join(
        w.strip()
        for w in x.split('\n')
        if w
    )
    x = unquote(x)

    stdout.write(f'"{x.strip()}",')


def tostring(x):
    if x is None:
        return ''

    return x if isinstance(x, str) else x.getText()


def soundings():
    with open('website/collections/soundings/index.htm') as fd:
        bs = BeautifulSoup(fd)

    for node in bs.select('.headerlarge, a'):
        emit(node)
        if node.name == 'a':
            emit(node.attrs.get('href'))

            nextel = node.next_sibling
            authors = ''
            while nextel and not (isinstance(nextel, element.Tag) and nextel.name == 'a'):
                authors = authors + tostring(nextel)
                nextel = nextel.next_sibling

            emit(authors.replace(' and ', ', '))

        print()


def ourhistory():
    with open('website/collections/shs/index.htm') as fd:
        bs = BeautifulSoup(fd)

    for node in bs.select('.headerlarge, a'):
        emit(node)
        if node.name == 'a':
            emit(node.attrs.get('href'))

            nextel = node.next_sibling
            authors = ''
            while nextel and not (isinstance(nextel, element.Tag) and nextel.name == 'a'):
                authors = authors + tostring(nextel)
                nextel = nextel.next_sibling

            emit(authors.replace(' and ', ', '))

        print()


ourhistory()
