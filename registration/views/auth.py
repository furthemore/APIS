import functools

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect

from registration.models import Firebase


class TerminalRequest(HttpRequest):
    terminal: Firebase | None
    terminal_authed: bool


class RequiredTerminalRequest(TerminalRequest):
    terminal: Firebase


def get_bearer_token(request) -> str | None:
    header = request.headers.get("authorization", "") or ""
    if header.startswith("Bearer "):
        token = header.removeprefix("Bearer ").strip()
        return token or None
    return None


def resolve_terminal_from_request(request) -> Firebase | None:
    terminal_id = request.headers.get("X-Terminal-Id")

    if not terminal_id:
        return None

    try:
        return Firebase.objects.get(id=int(terminal_id))
    except (ValueError, TypeError, Firebase.DoesNotExist):
        return None


def no_terminal_response() -> JsonResponse:
    return JsonResponse(
        {"success": False, "reason": "No terminal associated with request"},
        status=400,
    )


def _authorize(
    session_permissions: tuple[str, ...],
    require_terminal: bool,
    trust_any_terminal: bool,
):
    def decorator(view):
        @csrf_exempt
        @functools.wraps(view)
        def wrapper(request, *args, **kwargs):
            token = get_bearer_token(request)
            if token is not None:
                try:
                    terminal = Firebase.objects.get(token=token)
                except Firebase.DoesNotExist:
                    return JsonResponse(
                        {"success": False, "reason": "Unknown token"}, status=401
                    )
                if not terminal.web_access and not trust_any_terminal:
                    return JsonResponse(
                        {"success": False, "reason": "Terminal not permitted"},
                        status=403,
                    )
                request.terminal = terminal
                request.terminal_authed = True
                return view(request, *args, **kwargs)

            user = getattr(request, "user", None)
            if not (
                user and user.is_authenticated and user.is_active and user.is_staff
            ):
                return JsonResponse(
                    {"success": False, "reason": "Authentication required"}, status=401
                )

            for permission in session_permissions:
                if not user.has_perm(permission):
                    return JsonResponse(
                        {"success": False, "reason": "Permission denied"}, status=403
                    )

            request.terminal = resolve_terminal_from_request(request)
            request.terminal_authed = False

            if require_terminal and request.terminal is None:
                return no_terminal_response()

            return csrf_protect(view)(request, *args, **kwargs)

        return wrapper

    return decorator


def staff_or_terminal_required(
    session_permissions: tuple[str, ...] = (), *, require_terminal: bool = False
):
    return _authorize(session_permissions, require_terminal, trust_any_terminal=False)


def device_token_required(*, require_terminal: bool = False):
    return _authorize((), require_terminal, trust_any_terminal=True)
