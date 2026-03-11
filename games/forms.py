# games/forms.py
from django import forms
from django.contrib.auth.models import User
from .models import Partida, Comentari, PerfilJugador, Club

class PartidaForm(forms.ModelForm):
    class Meta:
        model = Partida
        fields = ['pgn_text', 'visibilitat']
        widgets = {
            'pgn_text': forms.Textarea(attrs={'rows': 10, 'cols': 80, 'placeholder': 'Enganxa aquí el PGN complet...'}),
        }
        labels = {
            'pgn_text': 'PGN de la partida',
            'visibilitat': 'Qui pot veure-la?'
        }

class ComentariForm(forms.ModelForm):
    class Meta:
        model = Comentari
        fields = ['text', 'jugada_num']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Escriu el teu comentari o variant aquí...'}),
            'jugada_num': forms.NumberInput(attrs={'placeholder': 'Ex: 14 (opcional)'})
        }
        labels = {
            'text': 'Comentari',
            'jugada_num': 'Jugada nº'
        }


class ImportPGNForm(forms.Form):
    pgn_file = forms.FileField(label="Fitxer PGN")
    visibilitat = forms.ChoiceField(
        label="Visibilitat per defecte",
        choices=Partida.OPCIONS_VISIBILITAT,
        initial=Partida.CLUB
    )

class RegistreForm(forms.ModelForm):
    username = forms.CharField(label="Nom d'usuari")
    password = forms.CharField(widget=forms.PasswordInput, label="Contrasenya")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Repeteix contrasenya")
    
    class Meta:
        model = PerfilJugador
        fields = ['nom_complet', 'club', 'fcat_id']
    
    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError("Les contrasenyes no coincideixen.")
        return cd['password2']

    def save(self, commit=True):
        # Crear l'User
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password']
        )
        # Crear el Perfil
        perfil = super().save(commit=False)
        perfil.usuari = user
        if commit:
            perfil.save()
        return perfil