from django import forms
from .models import Todo


class TodoForm(forms.ModelForm):
    class Meta:
        model = Todo
        fields = ["title", "start_date", "end_date"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "start_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "end_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
        }
