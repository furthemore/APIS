from django.forms import ModelForm
from django.forms.widgets import TextInput

from .models import Firebase


class FirebaseForm(ModelForm):
    class Meta:
        model = Firebase
        fields = "__all__"
        widgets = {
            "foreground_color": TextInput(attrs={"type": "color"}),
            "background_color": TextInput(attrs={"type": "color"}),
        }
