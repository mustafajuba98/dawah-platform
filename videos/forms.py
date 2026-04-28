from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from videos.models import MosqueLesson
from videos.models import TodoItem


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


class MosqueLessonForm(forms.ModelForm):
    class Meta:
        model = MosqueLesson
        fields = ("mosque_name", "title", "lesson_time", "manual_time_text", "is_weekly", "weekday", "one_time_date", "is_active")
        widgets = {
            "lesson_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "one_time_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }
        labels = {
            "mosque_name": "اسم المسجد",
            "title": "عنوان الدرس",
            "lesson_time": "وقت الدرس (بالساعة)",
            "manual_time_text": "وقت يدوي (اختياري)",
            "is_weekly": "درس أسبوعي ثابت",
            "weekday": "اليوم الأسبوعي",
            "one_time_date": "تاريخ الدرس الفردي",
            "is_active": "نشط",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == "is_weekly" or name == "is_active":
                field.widget.attrs["class"] = "form-check-input"
            elif name not in ("lesson_time", "one_time_date"):
                field.widget.attrs["class"] = "form-control"


class TodoItemForm(forms.ModelForm):
    class Meta:
        model = TodoItem
        fields = ("title", "notes", "due_at")
        widgets = {
            "due_at": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
        }
        labels = {
            "title": "عنوان المهمة",
            "notes": "ملاحظات (اختياري)",
            "due_at": "موعد مستهدف (اختياري)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != "due_at":
                field.widget.attrs["class"] = "form-control"
