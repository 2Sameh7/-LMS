from .models import Category, Course, SystemSettings

def site_settings(request):
    """إضافة إعدادات الموقع لجميع القوالب"""
    return {
        'site_name': 'LMS Platform',
        'site_description': 'نظام إدارة التعلم المتكامل',
        'categories': Category.objects.all()[:10],
        'featured_courses': Course.objects.filter(status='published')[:4],
    }

def user_notifications(request):
    """إضافة إشعارات المستخدم"""
    if request.user.is_authenticated:
        from .models import Enrollment, CertificateRequest
        
        if hasattr(request.user, 'profile'):
            if request.user.profile.role == 'teacher':
                pending_enrollments = Enrollment.objects.filter(
                    course__teacher=request.user, 
                    status='pending'
                ).count()
                pending_certificates = CertificateRequest.objects.filter(
                    course__teacher=request.user, 
                    status='pending'
                ).count()
                
                return {
                    'pending_enrollments': pending_enrollments,
                    'pending_certificates': pending_certificates,
                }
    
    return {}

def system_settings(request):
    settings, created = SystemSettings.objects.get_or_create(id=1)
    return {
        'site_settings': settings
    }