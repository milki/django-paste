import datetime
import difflib
import random
import mptt
import re
from django.db import models
from django.db.models import permalink
from django.utils.translation import ugettext_lazy as _
from dpaste.highlight import LEXER_DEFAULT, pygmentize

from dpaste.settings import *

from dulwich.repo import Repo
from dulwich.object_store import tree_lookup_path
from dulwich.objects import Blob

t = 'abcdefghijkmnopqrstuvwwxyzABCDEFGHIJKLOMNOPQRSTUVWXYZ1234567890'
repo = Repo(GITREPO)

def generate_secret_id(length=4):
    return ''.join([random.choice(t) for i in range(length)])

class Snippet(models.Model):
    secret_id = models.CharField(_(u'Secret ID'), max_length=4, blank=True)
    branch = models.CharField(_(u'branch'), max_length=120, blank=True)
    lexer = models.CharField(_(u'Lexer'), max_length=30, default=LEXER_DEFAULT)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')

    def __init__(self, *args, **kwargs):
        super(Snippet, self).__init__(*args, **kwargs)

        if self.branch:
            self.title = Snippet.get_title(self.branch)
            self.author = Snippet.get_author(self.branch)
            self.content = Snippet.get_content(self.branch)
            self.content_highlighted = pygmentize(self.content, self.lexer)
            self.merged = self.is_merged()

    class Meta:
        ordering = ('-branch',)

    def get_linecount(self):
        return len(self.content.splitlines())

    def content_splitted(self):
        return self.content_highlighted.splitlines()

    def raw_content_splitted(self):
        return self.content.splitlines()

    @staticmethod
    def get_title(branch):
         return re.sub(r".*/","#",branch)

    @staticmethod
    def get_author(branch):
        return repo[branch].author

    @staticmethod
    def get_content(branch):
        bcommit = repo[branch]
        file = tree_lookup_path(repo.get_object,bcommit.tree,Snippet.get_title(branch))
        return repo.get_object(file[1]).data


    def is_merged(self):
        try:
            bcommit = repo['refs/heads/master']
            file = tree_lookup_path(repo.get_object,bcommit.tree,self.title)
            merged = True
        except KeyError:
            merged = False
        return merged

    def save(self, *args, **kwargs):
        if not self.pk:
            self.secret_id = generate_secret_id()
        super(Snippet, self).save(*args, **kwargs)

    @permalink
    def get_absolute_url(self):
        return ('snippet_details', (self.secret_id,))

    def __unicode__(self):
        return '%s' % self.secret_id

mptt.register(Snippet, order_insertion_by=['branch'])
