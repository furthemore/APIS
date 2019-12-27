from django import forms

from .models import Panel


class PanelForm(forms.ModelForm):
    def __init__(self, event, *args, **kwargs):
        super(PanelForm, self).__init__(*args, **kwargs)
        self.fields["event"].queryset = self.fields["event"].queryset.filter(
            pk=event.pk
        )
        self.fields["room"].queryset = self.fields["room"].queryset.filter(event=event)
        self.fields["panelist"].queryset = self.fields["panelist"].queryset.filter(
            event=event
        )

    class Meta:
        model = Panel
        fields = "__all__"
