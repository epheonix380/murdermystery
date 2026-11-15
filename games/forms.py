from django import forms
from django.utils import timezone


class NewGameForm(forms.Form):
    party_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    player_count = forms.TypedChoiceField(coerce=int, label="Number of players")

    def __init__(self, case, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["player_count"].choices = [(n, n) for n in range(case.min_players, case.max_players + 1)]

    def clean_party_date(self):
        date = self.cleaned_data["party_date"]
        if date < timezone.localdate():
            raise forms.ValidationError("The party date can't be in the past.")
        return date
