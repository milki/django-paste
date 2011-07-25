import datetime
import difflib
import random
import mptt
import re
from django.db import models
from django.db.models import permalink
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_init, pre_save, post_delete
from django.dispatch import receiver

from dpaste.highlight import pygmentize

from dpaste.settings import *

from dulwich.repo import Repo
from dulwich.object_store import tree_lookup_path
from dulwich.objects import Blob, Commit
import time

t = 'abcdefghijkmnopqrstuvwwxyzABCDEFGHIJKLOMNOPQRSTUVWXYZ1234567890'
repo = Repo(GITREPO)

def generate_secret_id(length=4):
    return ''.join([random.choice(t) for i in range(length)])

class Snippet(models.Model):
    secret_id = models.CharField(_(u'Secret ID'), max_length=4, blank=True)
    branch = models.CharField(_(u'branch'), max_length=120, blank=False)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')
    sha1 = models.CharField(_(u'sha1'), max_length=40, null=True, blank=False, unique=True)

    class Meta:
        ordering = ('-branch',)

    def get_linecount(self):
        return len(self.content.splitlines())

    def content_splitted(self):
        return self.content_highlighted.splitlines()

    def raw_content_splitted(self):
        return self.content.splitlines()

    def short_sha1(self):
        return self.sha1[:8]

    def formatted_time(self):
        return time.strftime("%Y.%m.%d %H:%M:%S", time.localtime(self.time))

    @staticmethod
    def get_title(branch):
         return re.sub(r".*/","#",branch)

    @staticmethod
    def get_author(branch,sha1=None):
        if sha1:
            return repo.get_object(sha1).author
        return repo[branch].author

    @staticmethod
    def get_content(branch,sha1=None):
        if sha1:
            bcommit = repo.get_object(sha1)
        else:
            bcommit = repo[branch]
        file = tree_lookup_path(repo.get_object,bcommit.tree,Snippet.get_title(branch))
        return repo.get_object(file[1]).data.decode('UTF-8')

    @staticmethod
    def get_sha1(branch):
        return repo[branch].id

    @staticmethod
    def get_time(sha1):
        return repo.get_object(sha1).commit_time

    def is_merged(self):
        try:
            bcommit = repo['refs/heads/master']
            file = tree_lookup_path(repo.get_object,bcommit.tree,self.title)
            merged = True
        except KeyError:
            merged = False
        return merged

    def merge(self):
        filename = self.title.encode('UTF-8')
        bcommit = repo[self.branch]
        btree = repo.get_object(bcommit.tree)

        mcommit = repo['refs/heads/master']
        mtree = repo.get_object(mcommit.tree)

        author = COMMITTER
        message = MERGE_MESSAGE % (self.title[1:])
        
        mtree[filename] = btree[filename]

        commit = Commit()
        commit.tree = mtree.id
        commit.parents = [mcommit.id,bcommit.id]
        commit.author = commit.committer = author
        commit.commit_time = commit.author_time = int(time.time())
        commit.commit_timezone = commit.author_timezone = time.timezone
        commit.encoding = 'UTF-8'
        commit.message = message
        
        repo.object_store.add_object(mtree)
        repo.object_store.add_object(commit)
        
        repo['refs/heads/master'] = commit.id

    @permalink
    def get_absolute_url(self):
        return ('snippet_details', (self.secret_id,))

    def __unicode__(self):
        return '%s' % self.secret_id

mptt.register(Snippet, order_insertion_by=['branch'])

@receiver(post_delete,sender=Snippet)
def remove_branch(sender, instance, **kwargs):
    try:
        del repo[instance.branch]
    except:
        pass

@receiver(post_init,sender=Snippet)
def init_meta(sender,instance,**kwargs):
    if instance.branch:
        instance.title = Snippet.get_title(instance.branch)
        instance.merged = instance.is_merged()

        if not instance.sha1:
            instance.author = Snippet.get_author(instance.branch)
            instance.content = Snippet.get_content(instance.branch)
            instance.sha1 = instance.get_sha1(instance.branch)
        else:
            instance.author = Snippet.get_author(instance.branch,instance.sha1)
            instance.content = Snippet.get_content(instance.branch,instance.sha1)

        instance.time = instance.get_time(instance.sha1)
        instance.content_highlighted = pygmentize(instance.content, 'irc')

@receiver(pre_save,sender=Snippet)
def gitsync(sender,instance,raw,using,**kwargs):
    commit = kwargs.get("commit",True)
    gitcommit = kwargs.pop("gitcommit",True)

    if not commit or not gitcommit:
        return

    # Git sync
    filename = Snippet.get_title(instance.branch).encode('UTF-8')
    bcommit = repo[instance.branch]
    tree = repo.get_object(bcommit.tree)

    blob = Blob.from_string(instance.content.encode('UTF-8'))
    tree[filename] = (tree[filename][0],blob.id)

    author = "milki <milki@cibo.ircmylife.com>"
    message = "Editted via dpaste"

    commit = Commit()
    commit.tree = tree.id
    commit.parents = [bcommit.id]
    commit.author = commit.committer = author
    commit.commit_time = commit.author_time = int(time.time())
    commit.commit_timezone = commit.author_timezone = time.timezone
    commit.encoding = 'UTF-8'
    commit.message = message

    repo.object_store.add_object(blob)
    repo.object_store.add_object(tree)
    repo.object_store.add_object(commit)

    repo.refs[instance.branch] = commit.id

    # Db sync
    if not instance.pk:
        instance.secret_id = generate_secret_id()

    instance.sha1 = commit.id
