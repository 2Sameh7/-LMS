from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile, Course, Enrollment

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """إنشاء ملف تعريف تلقائي عند إنشاء مستخدم جديد"""
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """حفظ ملف التعريف عند حفظ المستخدم"""
    if hasattr(instance, 'profile'):
        instance.profile.save()

@receiver(post_save, sender=Enrollment)
def enrollment_notification(sender, instance, created, **kwargs):
    """إرسال إشعار عند تسجيل جديد"""
    if created and instance.status == 'pending':
        # يمكن إضافة كود لإرسال إشعار للمعلم هنا
        pass

@receiver(post_delete, sender=Course)
def course_deleted(sender, instance, **kwargs):
    """تنظيف البيانات المرتبطة عند حذف كورس"""
    # يمكن إضافة كود لتنظيف البيانات المرتبطة هنا
    pass