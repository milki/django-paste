import datetime
import sys
from optparse import make_option
from django.core.management.base import CommandError, LabelCommand
from dpaste.models import Snippet

from dulwich.repo import Repo
from dulwich.object_store import tree_lookup_path
from dulwich.objects import Blob

class Command(LabelCommand):
    option_list = LabelCommand.option_list + (
        make_option('--dry-run', '-d', action='store_true', dest='dry_run', 
            help='Don\'t do anything.'),
    )
    help = "Import snippets"

    def extract_log(x): return re.sub(r".*/","#",x)

    def handle(self, *args, **options):
        repo = Repo('/home/milki/git/ircmylife-logs.git')
        allbranches = list(repo.refs.keys())
        allbranches.sort()
        branches = allbranches[1:-1]

        new_snippets = []
        for branch_ref in branches:
            try:
                new_snippets.append( Snippet(branch="%s" % (branch_ref)) )
            except UnicodeError:
                sys.stdout.write(u"Failed to create - %s\n" % (branch_ref))
                pass
        sys.stdout.write(u"%s snippets created:\n" % len(new_snippets))
        for c in new_snippets:
            sys.stdout.write(u"%s - %s\n" % (c.branch,c.title))
        if options.get('dry_run'):
            sys.stdout.write(u'Dry run - Doing nothing! *crossingfingers*\n')
        else:
            [ snippet.save(gitcommit=False) for snippet in new_snippets ]
