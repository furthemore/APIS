from django.conf import settings

def square_environment(request):
    return {'SQUARE_ENVIRONMENT': settings.SQUARE_ENVIRONMENT}