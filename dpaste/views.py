from django.shortcuts import (
    render_to_response,
    get_object_or_404,
    get_list_or_404,
)
from django.template.context import RequestContext
from django.http import (
    HttpResponseRedirect,
    HttpResponseBadRequest,
    HttpResponse,
    HttpResponseForbidden,
)
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from dpaste.forms import SnippetForm
from dpaste.models import Snippet
from dpaste.highlight import pygmentize, guess_code_lexer
from django.core.urlresolvers import reverse
from django.utils import simplejson
import difflib


def snippet_details(request, snippet_id,
                    template_name='dpaste/snippet_details.html', is_raw=False):

    snippet = get_object_or_404(Snippet, secret_id=snippet_id)

    tree = snippet.get_root()
    tree = tree.get_descendants(include_self=True)

    new_snippet_initial = {
        'title' : snippet.title,
        'sha1' : snippet.sha1,
        'content': snippet.content,
        'lexer': snippet.lexer,
    }

    if request.method == "POST":
        snippet_form = SnippetForm(data=request.POST, request=request,
                                   initial=new_snippet_initial)
        if snippet_form.is_valid():
            request, new_snippet = snippet_form.save(parent=snippet)
            return HttpResponseRedirect(new_snippet.get_absolute_url())
    else:
        snippet_form = SnippetForm(initial=new_snippet_initial,
                                   request=request)

    template_context = {
        'snippet_form': snippet_form,
        'snippet': snippet,
        'lines': range(snippet.get_linecount()),
        'tree': tree,
    }

    response = render_to_response(
        template_name,
        template_context,
        RequestContext(request)
    )

    if is_raw:
        response['Content-Type'] = 'text/plain'
        return response
    else:
        return response


def snippet_delete(request, snippet_id):
    snippet = get_object_or_404(Snippet, secret_id=snippet_id)
    try:
        snippet_list = request.session['snippet_list']
    except KeyError:
        return HttpResponseForbidden(
            'You have no recent snippet list, cookie error?')
    if not snippet.pk in snippet_list:
        return HttpResponseForbidden('That\'s not your snippet, sucka!')
    snippet.delete()
    return HttpResponseRedirect(reverse('snippet_new'))


def snippet_merge(request, snippet_id):
    snippet = get_object_or_404(Snippet, secret_id=snippet_id)
    snippet.gitmerge()
    snippet.get_root().get_descendants(include_self=True).delete()
    return HttpResponseRedirect(reverse('snippet_userlist'))


def snippet_userlist(request, template_name='dpaste/snippet_list.html'):

    try:
        snippet_list = Snippet.objects.raw(
        'SELECT snip.* FROM dpaste_snippet AS snip \
            LEFT OUTER JOIN (SELECT title, max(mptt_level) as max_level FROM dpaste_snippet GROUP BY title) \
                             AS msnip ON snip.mptt_level = msnip.max_level AND snip.title = msnip.title \
                             WHERE msnip.max_level IS NOT NULL \
                             ORDER BY title')
    except ValueError:
        snippet_list = None

    template_context = {
        'snippets_max': getattr(settings, 'MAX_SNIPPETS_PER_USER', 31),
        'snippet_list': snippet_list,
    }

    return render_to_response(
        template_name,
        template_context,
        RequestContext(request)
    )


def snippet_diff(request, template_name='dpaste/snippet_diff.html'):

    a = request.GET.get("a")
    b = request.GET.get("b")

    if a is not None and a.isdigit() and b is not None and b.isdigit():
        try:
            fileA = Snippet.objects.get(pk=int(a))
            fileB = Snippet.objects.get(pk=int(b))
        except ObjectDoesNotExist:
            return HttpResponseBadRequest(u'Selected file(s) does not exist.')
    else:
        return HttpResponseBadRequest(u'You must select two snippets.')

    if fileA.content != fileB.content:
        d = difflib.unified_diff(
            fileA.content.splitlines(),
            fileB.content.splitlines(),
            'Original',
            'Current',
            lineterm=''
        )
        difftext = '\n'.join(d)
        difftext = pygmentize(difftext, 'diff')
    else:
        difftext = _(u'No changes were made between this two files.')

    template_context = {
        'difftext': difftext,
        'fileA': fileA,
        'fileB': fileB,
    }

    return render_to_response(
        template_name,
        template_context,
        RequestContext(request)
    )
