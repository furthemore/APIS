from allauth.account.adapter import DefaultAccountAdapter

class RegistrationAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, _request):
        return False
