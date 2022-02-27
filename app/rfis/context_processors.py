from django.conf import settings

def get_domain_url(request):
    context = {
        "DOMAIN_URL": settings.DOMAIN_URL
    }
    return context