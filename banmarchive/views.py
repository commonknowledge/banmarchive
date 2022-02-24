from django.http.response import HttpResponseRedirect


def handler404(request, exception=None):
    return HttpResponseRedirect('/')
