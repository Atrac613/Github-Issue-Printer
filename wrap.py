"""
Text wrap function (for japanese)
Copyright (c) 2008 Tadashi Matsumoto <ma2@city.plala.jp>

Usage:
    import wrap
    wrapped_text = wrap.wrap(unicode_text, cols)

License: PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2
"""

from StringIO import StringIO
from unicodedata import east_asian_width

def _chr_width(u):
    w = east_asian_width(u)
    if w in ('W', 'F'):
        return 2
    else:
        return 1

def _split(u, cols):
    width, i = 0, 0
    for c in u:
        width += _chr_width(c)
        if width <= cols:
            i += 1
            continue
        else:
            break
    return u[:i], u[i:]

def wrap(text, cols=72):
    lines = text.split(u'\n')
    lines = [x.strip() for x in lines]
    text = StringIO()
    c = u''
    for line in lines:
        if line:
            d = line[0]
        else:
            d = u''
        if not c:
            if d:
                text.write(line)
                text.write(u'\n')
                c = d
            continue
        if not d:
            if c == u'\n':
                text.write(u'\n')
            else:
                text.write(u'\n\n')
            c = u'\n'
            continue
        if not (ord(c) >= 256 and ord(d) >= 256):
            if c != u'\n':
                text.write(u' ')
        text.write(line)
        text.write(u'\n')
        c = d        
    text = text.getvalue()
    lines = text.split(u'\n')
    newlines = []
    for line in lines:
        if not line:
            newlines.append(u'')
            continue
        while line:
            line1, line2 = _split(line, cols)
            newlines.append(line1.rstrip())
            line = line2.lstrip()
    text = u'\n'.join(newlines)
    return text
