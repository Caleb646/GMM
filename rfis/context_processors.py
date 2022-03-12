from django.conf import settings


def get_domain_url(request):
    return {"DOMAIN_URL": settings.DOMAIN_URL}
