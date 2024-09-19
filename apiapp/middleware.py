from threading import local
import logging

_user = local()

logger = logging.getLogger(__name__)

def get_current_user():
  return getattr(_user, 'current', None)

class CurrentUserMiddleware:
  def __init__(self, get_response):
    self.get_response = get_response
  
  def __call__(self, request):
    _user.current = getattr(request, 'user', None)
    logger.info(f"CurrentUserMiddleware: Current User - {_user.current}")  # 로그 출력

    response = self.get_response(request)
    return response