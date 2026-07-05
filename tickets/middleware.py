import zoneinfo
from urllib.parse import unquote

from django.utils import timezone


class TimezoneMiddleware:
    """Activa la zona horaria del navegador (guardada en la cookie django_timezone)
    para que todas las fechas se muestren localizadas, aunque se almacenen en UTC."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tzname = request.COOKIES.get('django_timezone')
        if tzname:
            tzname = unquote(tzname)
            try:
                timezone.activate(zoneinfo.ZoneInfo(tzname))
            except zoneinfo.ZoneInfoNotFoundError:
                timezone.deactivate()
        else:
            timezone.deactivate()

        return self.get_response(request)
