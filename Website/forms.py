from django import forms
from .models import ContactMessage, RoofEstimate


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'message']


class QuoteRequestForm(forms.ModelForm):
    class Meta:
        model = RoofEstimate
        fields = ['customer_full_name', 'customer_phone', 'customer_email', 'project_location', 'project_county', 'customer_notes']
        widgets = {
            'customer_full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full name',
            }),
            'customer_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+2547XXXXXXXX',
            }),
            'customer_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'you@example.com',
            }),
            'project_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Project location',
            }),
            'project_county': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'County',
            }),
            'customer_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Additional notes or special requirements',
            }),
        }
