from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Post, Comment, Profile


class PostForm(forms.ModelForm):
    tag_names = forms.CharField(required=False, help_text='Separate tags with commas.', widget=forms.TextInput(attrs={'placeholder': 'python, django, web development'}))

    class Meta:
        model = Post
        fields = ['title', 'content', 'category', 'category_ref', 'cover_image', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Enter a clear, engaging title'}),
            'content': forms.Textarea(attrs={'placeholder': 'Write your article here...', 'rows': 12}),
            'category': forms.TextInput(attrs={'placeholder': 'e.g. Technology'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['tag_names'].initial = ', '.join(self.instance.tags.values_list('name', flat=True))
        self.fields['category_ref'].required = False




class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        if commit:
            user.save()
        return user


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['body']
        widgets = {'body': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Share your thoughts...'})}


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'avatar', 'website', 'location']
