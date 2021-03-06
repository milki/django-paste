from pygments.lexers import get_all_lexers, get_lexer_by_name, guess_lexer
from pygments.styles import get_all_styles
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound
from pygments import highlight

LEXER_LIST_ALL = sorted([(i[1][0], i[0]) for i in get_all_lexers()])
LEXER_LIST = (
    ('bash', 'Bash'),
    ('c', 'C'),
    ('css', 'CSS'),
    ('diff', 'Diff'),
    ('django', 'Django/Jinja'),
    ('html', 'HTML'),
    ('irc', 'IRC logs'),
    ('js', 'JavaScript'),
    ('perl', 'Perl'),
    ('php', 'PHP'),
    ('pycon', 'Python console session'),
    ('pytb', 'Python Traceback'),
    ('python', 'Python'),
    ('python3', 'Python 3'),
    ('sql', 'SQL'),
    ('text', 'Text only'),
)
LEXER_DEFAULT = 'irc'


class NakedHtmlFormatter(HtmlFormatter):
    def wrap(self, source, outfile):
        return self._wrap_code(source)

    def _wrap_code(self, source):
        for i, t in source:
            yield i, t


def pygmentize(code_string, lexer_name='text'):
    return highlight(code_string,
                     get_lexer_by_name(lexer_name),
                     NakedHtmlFormatter())


def guess_code_lexer(code_string, default_lexer='unknown'):
    try:
        return guess_lexer(code_string).name
    except ClassNotFound:
        return default_lexer
