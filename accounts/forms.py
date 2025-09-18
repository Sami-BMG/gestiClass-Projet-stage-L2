from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User, Group
from .models import User , Question


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'profil', 'phone')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'profil', 'phone', 'birth_date', 'photo')

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone',  'birth_date', 'photo')
        

class AssignRoleForm(forms.Form):
    role = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label="Sélectionner un rôle",
        empty_label="--- Choisir un rôle ---",
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'})
    )

class RoleForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'permissions']
        widgets = {
            'permissions': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'})
        }
        labels = {
            'name': 'Nom du rôle',
            'permissions': 'Permissions'}  
        

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['category', 'question', 'email']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'question': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': 'Posez votre question ici...'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'votre@email.com'
            }),
        }
        labels = {
            'category': 'Catégorie',
            'question': 'Votre question',
            'email': 'Email',
        }
        
        
        