from django import forms
from .models import Rating


class RatingForm(forms.ModelForm):
    """Form for students to rate and review a course."""

    class Meta:
        model = Rating
        fields = ('score', 'comment')
        widgets = {
            'score': forms.RadioSelect(
                choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)],
                attrs={'class': 'star-rating-input'},
            ),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Share your experience (optional)...',
                'rows': 3,
                'aria-label': 'Review Comment',
            }),
        }
