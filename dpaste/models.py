import difflib
import random
import mptt
from django.conf import settings
from django.db import models
from django.db.models import permalink
from django.utils.translation import ugettext_lazy as _
from dpaste.highlight import LEXER_DEFAULT

content_model = getattr(settings, 'DPASTE_SNIPPET_CONTENT_MODEL', 'database')

if content_model is 'database':
    from dpaste.content_models.database import DBSnippet as ContentModel
else:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured("Invalid DPASTE_SNIPPET_CONTENT_MODEL. \
No such Snippet content model {0}".format(content_model))

t = 'abcdefghijkmnopqrstuvwwxyzABCDEFGHIJKLOMNOPQRSTUVWXYZ1234567890'


def generate_secret_id(length=8):
    return ''.join([random.choice(t) for i in range(length)])


class Snippet(ContentModel):
    secret_id = models.CharField(_(u'Secret ID'), max_length=8, blank=True)
    expires = models.DateTimeField(_(u'Expires'), blank=True, help_text='asdf')
    lexer = models.CharField(_(u'Lexer'), max_length=30, default=LEXER_DEFAULT)

    def get_linecount(self):
        return len(self.content.splitlines())

    def content_splitted(self):
        return self.content_highlighted.splitlines()

    def raw_content_splitted(self):
        return self.content.splitlines()

    def save(self, *args, **kwargs):
        if not self.pk:
            self.secret_id = generate_secret_id()
        super(Snippet, self).save(*args, **kwargs)

    @permalink
    def get_absolute_url(self):
        return ('snippet_details', (self.secret_id,))

    def __unicode__(self):
        return '%s' % self.secret_id
