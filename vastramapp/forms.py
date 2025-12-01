# forms.py - Updated
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Product, ContactQuery

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, required=True, 
                            widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}))
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a username'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}))
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactQuery
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your full name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your email address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your phone number'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject of your message'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Your message...', 'rows': 5}),
        }