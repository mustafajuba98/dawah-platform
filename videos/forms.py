from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="البريد الإلكتروني")

    username = forms.CharField(label="اسم المستخدم")
    password1 = forms.CharField(label="كلمة المرور", widget=forms.PasswordInput)
    password2 = forms.CharField(label="تأكيد كلمة المرور", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].help_text = "حروف وأرقام فقط، بدون مسافات."
        self.fields["password1"].help_text = "8 أحرف على الأقل، مع حروف كبيرة وصغيرة وأرقام."
        self.fields["password2"].help_text = "أعد إدخال نفس كلمة المرور للتأكيد."
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("هذا البريد مستخدم بالفعل.")
        return email
