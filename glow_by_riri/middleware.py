from django.http import HttpResponsePermanentRedirect


class RemoveWWWMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0]
        if host.startswith('www.'):
            return HttpResponsePermanentRedirect(
                'https://' + host[4:] + request.get_full_path()
            )
        return self.get_response(request)
