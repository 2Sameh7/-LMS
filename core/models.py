from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[('admin', 'مدير النظام'), ('teacher', 'معلم'), ('student', 'طالب')], default='student')
    phone = models.CharField(max_length=15, blank=True)
    bio = models.TextField(blank=True)
    image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    certificate = models.ImageField(upload_to='certificates/', null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    specialization = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='التخصص')

    def __str__(self):
        return self.user.username

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Course(models.Model):
    STATUS_CHOICES = [('draft', 'مسودة'), ('published', 'منشور'), ('archived', 'مؤرشف')]
    title = models.CharField(max_length=200)
    description = models.TextField()
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'profile__role': 'teacher'})
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class CourseContent(models.Model):
    course = models.ForeignKey(Course, related_name='contents', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=20, choices=[('video', 'فيديو'), ('file', 'ملف')])
    link_or_file = models.URLField(blank=True)
    file_upload = models.FileField(upload_to='course_files/', null=True, blank=True)
    order = models.IntegerField(default=0)

class Quiz(models.Model):
    STATUS_CHOICES = [('draft', 'مسودة'), ('active', 'نشط'), ('closed', 'مغلق')]
    course = models.ForeignKey(Course, related_name='quizzes', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    text = models.TextField()
    correct_answer = models.CharField(max_length=200) 

class Enrollment(models.Model):
    STATUS_CHOICES = [('pending', 'قيد المراجعة'), ('approved', 'مقبول'), ('rejected', 'مرفوض')]
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'profile__role': 'student'})
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    enrolled_at = models.DateTimeField(auto_now_add=True)

class CertificateRequest(models.Model):
    STATUS_CHOICES = [('pending', 'قيد المراجعة'), ('issued', 'تم الإصدار'), ('rejected', 'مرفوض')]
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    request_date = models.DateTimeField(auto_now_add=True)

class Review(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class PaymentMethod(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)


class SystemSettings(models.Model):
    platform_name = models.CharField(max_length=255, default="LMS Platform")
    support_email = models.EmailField(default="support@lms.com")
    enable_registration = models.BooleanField(default=True)
    enable_certificates = models.BooleanField(default=True)

    class Meta:
        verbose_name = "إعدادات النظام"

class QuizResult(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_results')
    quiz = models.ForeignKey('Quiz', on_delete=models.CASCADE, related_name='results')
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    passed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.username} - {self.quiz.title} - {self.percentage}%"