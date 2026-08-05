from django.urls import path
from . import views

urlpatterns = [
    # Landing & Auth
    path('', views.landing_page, name='landing_page'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    
    # Courses (Public)
    path('courses/', views.course_list, name='course_list'),
    path('courses/<int:pk>/', views.course_detail, name='course_detail'),
    
    # Teacher URLs
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/courses/', views.teacher_courses, name='teacher_courses'),
    path('teacher/course/<int:pk>/edit/', views.edit_course, name='edit_course'),
    path('teacher/course/<int:pk>/delete/', views.delete_course, name='delete_course'),
    path('teacher/course/<int:course_id>/content/', views.manage_content, name='manage_content'),
    path('teacher/content/<int:pk>/delete/', views.delete_content, name='delete_content'),
    path('teacher/course/<int:course_id>/quizzes/', views.manage_quizzes, name='manage_quizzes'),
    path('teacher/content/<int:pk>/edit/', views.edit_content, name='edit_content'),
    path('teacher/quiz/<int:pk>/delete/', views.delete_quiz, name='delete_quiz'),
    path('teacher/quiz/<int:quiz_id>/questions/', views.manage_questions, name='manage_questions'),
    path('teacher/quiz/<int:quiz_id>/results/', views.view_results, name='view_results'),
    path('teacher/students/', views.teacher_students, name='teacher_students'),
    path('teacher/enrollment/<int:pk>/<str:status>/', views.update_enrollment, name='update_enrollment'),
    path('teacher/certificates/', views.teacher_certificates, name='teacher_certificates'),
    path('teacher/certificate/<int:pk>/<str:status>/', views.update_certificate, name='update_certificate'),
    path('teacher/performance/', views.teacher_performance, name='teacher_performance'),
    
    # Admin URLs
    path('admin-panel/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/users/', views.admin_users, name='admin_users'),
    path('admin-panel/users/<int:pk>/approve/', views.approve_user, name='approve_user'),
    path('admin-panel/categories/', views.admin_categories, name='admin_categories'),
    path('admin-panel/payments/', views.admin_payments, name='admin_payments'),
    path('admin-panel/reports/', views.admin_reports, name='admin_reports'),
    path('admin-panel/settings/', views.admin_settings, name='admin_settings'),
    path('admin-panel/export/<str:report_type>/', views.export_report, name='export_report'),
    path('admin-panel/users/<int:user_id>/manage/', views.manage_user_status, name='manage_user_status'),

    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('course/<int:course_id>/enroll/', views.enroll_in_course, name='enroll_in_course'),
    path('student/enrollments/', views.student_enrollments_history, name='student_enrollments_history'),
    path('quiz/<int:quiz_id>/take/', views.take_quiz, name='take_quiz'),
    path('student/scorecard/', views.student_scorecard, name='student_scorecard'),
    path('course/<int:course_id>/request-certificate/', views.request_certificate, name='request_certificate'),
    path('student/certificates/', views.student_certificates_history, name='student_certificates_history'),
    path('certificate/<int:cert_id>/download/', views.download_certificate_pdf, name='download_certificate_pdf'),
    path('course/<int:course_id>/add-review/', views.add_course_review, name='add_course_review'),
]