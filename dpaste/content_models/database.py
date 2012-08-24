import datetime
from mptt.models import MPTTModel, TreeForeignKey

from django.db import models
from django.utils.translation import ugettext_lazy as _
from dpaste.highlight import pygmentize


class DBSnippet(MPTTModel):
    parent = TreeForeignKey('self', null=True, blank=True,
                            related_name='children')
    title = models.CharField(_(u'Title'), max_length=120, blank=True)
    author = models.CharField(_(u'Author'), max_length=30, blank=True)
    published = models.DateTimeField(_(u'Published'), blank=True)
    content = models.TextField(_(u'Content'), )
    content_highlighted = models.TextField(_(u'Highlighted Content'),
                                           blank=True)

    class Meta:
        ordering = ('-published',)
        abstract = True

    class MPTTMeta:
        level_attr = 'mptt_level'
        order_insertion_by = ['title']

    def save(self, *args, **kwargs):
        if not self.pk:
            self.published = datetime.datetime.now()
        self.content_highlighted = pygmentize(self.content, self.lexer)
        super(DBSnippet, self).save(*args, **kwargs)
