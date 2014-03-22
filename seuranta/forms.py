from django import forms
from django.forms.models import inlineformset_factory

from .models import Competition, Competitor

class CompetitionForm(forms.ModelForm):
	class Meta:
		model = Competition

class CompetitorForm(forms.ModelForm):
	class Meta:
		model = Competitor

CompetitorFormSet = inlineformset_factory(Competition, Competitor)