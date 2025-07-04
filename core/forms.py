from django import forms
from .models import Content, UserSettings, SocialAccount

class ContentForm(forms.ModelForm):
    platforms = forms.MultipleChoiceField(
        choices=SocialAccount.PLATFORM_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    
    class Meta:
        model = Content
        fields = ['original_text', 'media', 'platforms', 'scheduled_time', 'tone']
        widgets = {
            'scheduled_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'w-full p-3 border border-gray-300 rounded-lg'}
            ),
            'original_text': forms.Textarea(
                attrs={
                    'rows': 5, 
                    'class': 'w-full h-40 p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                    'placeholder': 'Paste your content here. Our AI will adapt it for each platform...'
                }
            ),
            'media': forms.FileInput(
                attrs={'class': 'hidden'}
            ),
        }

class SettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = ['timezone', 'tone_preference', 'email_notifications', 'push_notifications']
        widgets = {
            'timezone': forms.Select(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg'}),
            'tone_preference': forms.Select(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg'}),
            'email_notifications': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded'}),
            'push_notifications': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded'}),
        }