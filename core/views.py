from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.db.models import Count, Avg, Sum, Q
from django.http import HttpResponse, HttpResponseForbidden
from django.core.paginator import Paginator
from .models import *
from .forms import *
from django.contrib.auth.models import User
import csv
import arabic_reshaper
import datetime
from bidi.algorithm import get_display
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

ITEMS_PER_PAGE = 10

# --- Helper Functions ---
def is_admin(user):
    return user.is_authenticated and hasattr(user, 'profile') and user.profile.role == 'admin'

def is_teacher(user):
    return user.is_authenticated and hasattr(user, 'profile') and user.profile.role == 'teacher'

def is_student(user):
    return user.is_authenticated and hasattr(user, 'profile') and user.profile.role == 'student'

# ==================== Landing & Authentication ====================

def landing_page(request):
    courses = Course.objects.filter(status='published').annotate(avg_rating=Avg('review__rating'))[:6]
    categories = Category.objects.all()
    return render(request, 'landing.html', {'courses': courses, 'categories': categories})

def register(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        role = request.POST.get('role', 'student')  
        certificate = request.FILES.get('certificate')
        specialization_id = request.POST.get('specialization')

        if not username or not password or not email:
            messages.error(request, 'يرجى ملء كافة الحقول الأساسية المطلوبة.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'اسم المستخدم هذا موجود بالفعل، يرجى اختيار اسم آخر.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'البريد الإلكتروني مدخل ومسجل مسبقاً في النظام.')
        elif len(password) < 8:
            messages.error(request, 'كلمة المرور ضعيفة! يجب أن تحتوي على 8 أحرف أو أرقام على الأقل.')
        elif role == 'teacher' and not specialization_id:
            messages.error(request, 'يجب عليك اختيار تخصصك العلمي أولاً.')
        elif role == 'teacher':
            try:
                specialization = Category.objects.get(pk=specialization_id)
            except Category.DoesNotExist:
                messages.error(request, 'التصنيف المحدد غير صالح.')
            else:
                user = User.objects.create_user(username=username, password=password, email=email)
                user.is_active = False
                user.save()
                profile, created = Profile.objects.get_or_create(user=user)
                profile.role = role
                profile.certificate = certificate
                profile.is_approved = False
                profile.specialization = specialization
                profile.save()
                messages.info(request, 'تم تسجيل حسابك كمعلم بنجاح! يرجى الانتظار حتى تقوم إدارة النظام بمراجعة وتدقيق شهادتك المرفقة لتفعيل الحساب.')
                return redirect('login')
        else:
            user = User.objects.create_user(username=username, password=password, email=email)
            user.is_active = True
            user.save()
            profile, created = Profile.objects.get_or_create(user=user)
            profile.role = role
            profile.certificate = certificate
            profile.is_approved = True
            profile.save()
            messages.success(request, 'تهانينا! تم إنشاء حسابك كطالب بنجاح ومتاح لك تسجيل الدخول الفوري وتصفح الكورسات الآن.')
            return redirect('login')
    
    return render(request, 'accounts/register.html', {'categories': categories})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            if user.profile.role == 'teacher' and not user.profile.is_approved:
                messages.warning(request, 'عذراً، حسابك بانتظار موافقة مدير النظام.')
                return redirect('login')
            
            login(request, user)
            messages.success(request, f'مرحباً بك {user.username}')
            
            if user.profile.role == 'admin':
                return redirect('admin_dashboard')
            elif user.profile.role == 'teacher':
                return redirect('teacher_dashboard')
            elif user.profile.role == 'student':
                return redirect('student_dashboard')
            else:
                return redirect('landing_page')
        messages.error(request, 'بيانات الدخول غير صحيحة')
    return render(request, 'accounts/login.html')

@login_required
@user_passes_test(is_student)
def student_dashboard(request):
    enrollments_count = Enrollment.objects.filter(student=request.user, status='approved').count()
    pending_enrollments = Enrollment.objects.filter(student=request.user, status='pending').count()
    quiz_results_count = QuizResult.objects.filter(student=request.user).count()
    certificates_count = CertificateRequest.objects.filter(student=request.user, status='issued').count()
    
    context = {
        'enrollments_count': enrollments_count,
        'pending_enrollments': pending_enrollments,
        'quiz_results_count': quiz_results_count,
        'certificates_count': certificates_count,
    }
    return render(request, 'student/dashboard.html', context)

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'تم تسجيل الخروج بنجاح')
    return redirect('landing_page')

@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserForm(request.POST, instance=request.user)
        p_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'تم تحديث الملف الشخصي بنجاح')
            return redirect('profile')
    else:
        u_form = UserForm(instance=request.user)
        p_form = ProfileForm(instance=request.user.profile)
    return render(request, 'accounts/profile.html', {'u_form': u_form, 'p_form': p_form})

# ==================== Teacher Views ====================

@login_required
@user_passes_test(is_teacher)
def teacher_dashboard(request):
    courses = Course.objects.filter(teacher=request.user)
    total_students = Enrollment.objects.filter(course__teacher=request.user, status='approved').count()
    total_quizzes = Quiz.objects.filter(course__teacher=request.user).count()
    pending_requests = Enrollment.objects.filter(course__teacher=request.user, status='pending').count()
    
    context = {
        'courses': courses,
        'total_students': total_students,
        'total_quizzes': total_quizzes,
        'pending_requests': pending_requests,
        'courses_count': courses.count()
    }
    return render(request, 'teacher/dashboard.html', context)

@login_required
@user_passes_test(is_teacher)
def teacher_courses(request):
    if not request.user.profile.specialization:
        messages.error(request, 'يجب تحديد تخصصك أولاً من صفحة الملف الشخصي قبل إنشاء كورسات.')
        return redirect('teacher_dashboard')

    courses = Course.objects.filter(teacher=request.user).annotate(
        students_count=Count('enrollment', filter=Q(enrollment__status='approved')),
        avg_rating=Avg('review__rating')
    )
    
    search = request.GET.get('search')
    if search:
        courses = courses.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )
    
    status_filter = request.GET.get('status')
    if status_filter:
        courses = courses.filter(status=status_filter)
    
    sort = request.GET.get('sort', 'newest')
    if sort == 'oldest':
        courses = courses.order_by('created_at')
    elif sort == 'students':
        courses = courses.order_by('-students_count')
    elif sort == 'rating':
        courses = courses.order_by('-avg_rating')
    elif sort == 'price':
        courses = courses.order_by('-price')
    else:
        courses = courses.order_by('-created_at')
    
    paginator = Paginator(courses, ITEMS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    if request.method == 'POST':
        form = CourseForm(user=request.user, data=request.POST)
        if form.is_valid():
            category = form.cleaned_data['category']
            if category.pk != request.user.profile.specialization.pk:
                messages.error(request, 'لا يمكنك إنشاء كورس إلا في تخصصك المسجل.')
                return redirect('teacher_courses')
            course = form.save(commit=False)
            course.teacher = request.user
            course.save()
            messages.success(request, 'تم إضافة الكورس بنجاح')
            return redirect('teacher_courses')
    else:
        form = CourseForm(user=request.user)
    
    return render(request, 'teacher/courses.html', {
        'courses': page_obj,
        'page_obj': page_obj,
        'form': form,
        'search': search,
        'selected_status': status_filter,
        'selected_sort': sort,
    })

@login_required
@user_passes_test(is_teacher)
def edit_course(request, pk):
    course = get_object_or_404(Course, pk=pk, teacher=request.user)
    if request.method == 'POST':
        form = CourseForm(user=request.user, data=request.POST, instance=course)
        if form.is_valid():
            category = form.cleaned_data['category']
            if category.pk != request.user.profile.specialization.pk:
                messages.error(request, 'لا يمكنك تغيير التصنيف إلى تخصص غير تخصصك.')
                return redirect('edit_course', pk=pk)
            form.save()
            messages.success(request, 'تم تحديث الكورس بنجاح')
            return redirect('teacher_courses')
    else:
        form = CourseForm(user=request.user, instance=course)
    return render(request, 'teacher/course_form.html', {'form': form, 'course': course})

@login_required
@user_passes_test(is_teacher)
def delete_course(request, pk):
    course = get_object_or_404(Course, pk=pk, teacher=request.user)
    course_title = course.title
    course.delete()
    messages.success(request, f'تم حذف الكورس "{course_title}" بنجاح')
    return redirect('teacher_courses')

@login_required
@user_passes_test(is_teacher)
def manage_content(request, course_id):
    course = get_object_or_404(Course, pk=course_id, teacher=request.user)
    contents = CourseContent.objects.filter(course=course).order_by('order')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content_type = request.POST.get('content_type')
        link_or_file = request.POST.get('link_or_file')
        file_upload = request.FILES.get('file_upload')
        order = request.POST.get('order', 1)
        
        if title:
            CourseContent.objects.create(
                course=course,
                title=title,
                content_type=content_type,
                link_or_file=link_or_file,
                file_upload=file_upload,
                order=order
            )
            messages.success(request, 'تم إضافة المحتوى التعليمي بنجاح.')
            return redirect('manage_content', course_id=course.id)
        else:
            messages.error(request, 'عذراً، يرجى كتابة عنوان المحتوى التعليمي أولاً.')
            
    return render(request, 'teacher/content.html', {'course': course, 'contents': contents, 'form': ContentForm()})

@login_required
@user_passes_test(is_teacher)
def edit_content(request, pk):
    content = get_object_or_404(CourseContent, id=pk)
    
    if content.course.teacher != request.user:
        return HttpResponseForbidden("لا تملك صلاحية تعديل هذا المحتوى")
    
    if request.method == 'POST':
        form = ContentForm(request.POST, request.FILES, instance=content)
        if form.is_valid():
            form.save()
            return redirect('manage_content', course_id=content.course.id)
    else:
        form = ContentForm(instance=content)
    
    return render(request, 'teacher/edit_content.html', {
        'form': form,
        'content': content
    })

@login_required
@user_passes_test(is_teacher)
def delete_content(request, pk):
    content = get_object_or_404(CourseContent, pk=pk, course__teacher=request.user)
    course_id = content.course.id
    content.delete()
    messages.success(request, 'تم حذف المحتوى بنجاح')
    return redirect('manage_content', course_id=course_id)

@login_required
@user_passes_test(is_teacher)
def manage_quizzes(request, course_id):
    course = get_object_or_404(Course, pk=course_id, teacher=request.user)
    quizzes = Quiz.objects.filter(course=course).annotate(questions_count=Count('questions'))
    
    if request.method == 'POST':
        title = request.POST.get('title')
        status = request.POST.get('status', 'draft')
        
        if title:
            Quiz.objects.create(
                course=course,
                title=title, 
                status=status
            )
            messages.success(request, 'تم إضافة الاختبار بنجاح وبانتظار صياغة الأسئلة.')
            return redirect('manage_quizzes', course_id=course.id)
        else:
            messages.error(request, 'عذراً، يرجى تحديد عنوان للاختبار الجديد.')
            
    return render(request, 'teacher/quizzes.html', {'course': course, 'quizzes': quizzes, 'form': QuizForm()})

@login_required
@user_passes_test(is_teacher)
def delete_quiz(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, course__teacher=request.user)
    course_id = quiz.course.id
    quiz.delete()
    messages.success(request, 'تم حذف الاختبار بنجاح')
    return redirect('manage_quizzes', course_id=course_id)

@login_required
@user_passes_test(is_teacher)
def manage_questions(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id, course__teacher=request.user)
    questions = Question.objects.filter(quiz=quiz)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            text = request.POST.get('text')
            correct_answer = request.POST.get('correct_answer')
            
            if text and correct_answer:
                Question.objects.create(
                    quiz=quiz, 
                    text=text, 
                    correct_answer=correct_answer
                )
                messages.success(request, 'تم إضافة السؤال بنجاح إلى بنك أسئلة الاختبار.')
                return redirect('manage_questions', quiz_id=quiz.id)
            else:
                messages.error(request, 'يرجى كتابة نص السؤال وتحديد الإجابة الصحيحة الدقيقة.')

        elif action == 'edit':
            question_id = request.POST.get('question_id')
            text = request.POST.get('text')
            correct_answer = request.POST.get('correct_answer')
            
            question_obj = get_object_or_404(Question, pk=question_id, quiz=quiz)
            if text and correct_answer:
                question_obj.text = text
                question_obj.correct_answer = correct_answer
                question_obj.save()
                messages.success(request, 'تم تعديل السؤال بنجاح.')
            else:
                messages.error(request, 'فشل التعديل، يرجى ملء كافة الحقول.')
            return redirect('manage_questions', quiz_id=quiz.id)
                
        elif action == 'delete':
            question_id = request.POST.get('question_id')
            question = get_object_or_404(Question, pk=question_id, quiz=quiz)
            question.delete()
            messages.success(request, 'تم حذف السؤال بنجاح.')
            return redirect('manage_questions', quiz_id=quiz.id)
            
    return render(request, 'teacher/questions.html', {'quiz': quiz, 'questions': questions, 'form': QuestionForm()})

@login_required
@user_passes_test(is_teacher)
def view_results(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id, course__teacher=request.user)
    return render(request, 'teacher/results.html', {'quiz': quiz})

@login_required
@user_passes_test(is_teacher)
def teacher_students(request):
    enrollments = Enrollment.objects.filter(course__teacher=request.user).select_related('student', 'course')
    
    search = request.GET.get('search')
    if search:
        enrollments = enrollments.filter(
            Q(student__username__icontains=search) |
            Q(course__title__icontains=search)
        )
    
    status_filter = request.GET.get('status')
    if status_filter:
        enrollments = enrollments.filter(status=status_filter)
    
    course_filter = request.GET.get('course')
    if course_filter:
        enrollments = enrollments.filter(course_id=course_filter)
    
    sort = request.GET.get('sort', 'newest')
    if sort == 'oldest':
        enrollments = enrollments.order_by('enrolled_at')
    elif sort == 'student':
        enrollments = enrollments.order_by('student__username')
    else:
        enrollments = enrollments.order_by('-enrolled_at')
    
    teacher_courses = Course.objects.filter(teacher=request.user)
    
    paginator = Paginator(enrollments, ITEMS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'teacher/students.html', {
        'enrollments': page_obj,
        'page_obj': page_obj,
        'teacher_courses': teacher_courses,
        'search': search,
        'selected_status': status_filter,
        'selected_course': course_filter,
        'selected_sort': sort,
    })

@login_required
@user_passes_test(is_teacher)
def update_enrollment(request, pk, status):
    enrollment = get_object_or_404(Enrollment, pk=pk, course__teacher=request.user)
    enrollment.status = status
    enrollment.save()
    messages.success(request, f'تم {status} طلب التسجيل بنجاح')
    return redirect('teacher_students')

@login_required
@user_passes_test(is_teacher)
def teacher_certificates(request):
    requests = CertificateRequest.objects.filter(course__teacher=request.user).select_related('student', 'course')
    
    search = request.GET.get('search')
    if search:
        requests = requests.filter(
            Q(student__username__icontains=search) |
            Q(course__title__icontains=search)
        )
    
    status_filter = request.GET.get('status')
    if status_filter:
        requests = requests.filter(status=status_filter)
    
    sort = request.GET.get('sort', 'newest')
    if sort == 'oldest':
        requests = requests.order_by('request_date')
    elif sort == 'student':
        requests = requests.order_by('student__username')
    else:
        requests = requests.order_by('-request_date')
    
    paginator = Paginator(requests, ITEMS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'teacher/certificates.html', {
        'requests': page_obj,
        'page_obj': page_obj,
        'search': search,
        'selected_status': status_filter,
        'selected_sort': sort,
    })

@login_required
@user_passes_test(is_teacher)
def update_certificate(request, pk, status):
    cert_req = get_object_or_404(CertificateRequest, pk=pk, course__teacher=request.user)
    cert_req.status = status
    cert_req.save()
    messages.success(request, f'تم {status} طلب الشهادة بنجاح')
    return redirect('teacher_certificates')

@login_required
@user_passes_test(is_teacher)
def teacher_performance(request):
    courses = Course.objects.filter(teacher=request.user)
    
    courses_count = courses.count()
    published_count = courses.filter(status='published').count()
    
    total_students = Enrollment.objects.filter(course__in=courses, status='approved').count()
    
    from django.db.models import Avg
    avg_rating = Review.objects.filter(course__in=courses).aggregate(Avg('rating'))['rating__avg'] or 0

    return render(request, 'teacher/performance.html', {
        'courses': courses,
        'courses_count': courses_count,
        'published_count': published_count,
        'total_students': total_students,
        'avg_rating': avg_rating,
    })

# ==================== Admin Views ====================

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    users_count = User.objects.count()
    teachers_count = User.objects.filter(profile__role='teacher').count()
    students_count = User.objects.filter(profile__role='student').count()
    courses_count = Course.objects.count()
    published_courses = Course.objects.filter(status='published').count()
    total_revenue = Course.objects.filter(status='published').aggregate(total=Sum('price'))['total'] or 0
    total_enrollments = Enrollment.objects.filter(status='approved').count()
    
    recent_courses = Course.objects.all().order_by('-created_at')[:5]
    recent_users = User.objects.all().order_by('-date_joined')[:5]
    
    context = {
        'users_count': users_count,
        'teachers_count': teachers_count,
        'students_count': students_count,
        'courses_count': courses_count,
        'published_courses': published_courses,
        'total_revenue': total_revenue,
        'total_enrollments': total_enrollments,
        'recent_courses': recent_courses,
        'recent_users': recent_users,
    }
    return render(request, 'admin_panel/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_users(request):
    users = User.objects.all().select_related('profile').order_by('-date_joined')
    
    search = request.GET.get('search')
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    role_filter = request.GET.get('role')
    if role_filter:
        users = users.filter(profile__role=role_filter)
    
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    elif status_filter == 'pending':
        users = users.filter(profile__role='teacher', profile__is_approved=False)
    
    sort = request.GET.get('sort', 'newest')
    if sort == 'oldest':
        users = users.order_by('date_joined')
    elif sort == 'username':
        users = users.order_by('username')
    elif sort == 'email':
        users = users.order_by('email')
    else:
        users = users.order_by('-date_joined')
    
    paginator = Paginator(users, ITEMS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        user = get_object_or_404(User, pk=user_id)
        
        if action == 'approve_teacher':
            user.profile.is_approved = True
            user.profile.save()
            user.is_active = True
            user.save()
            messages.success(request, f'تم تفعيل حساب المعلم {user.username}')
        elif action == 'ban':
            user.is_active = False
            user.save()
            messages.warning(request, f'تم حظر حساب {user.username}')
        elif action == 'unban':
            user.is_active = True
            user.save()
            messages.success(request, f'تم إلغاء حظر حساب {user.username}')
        elif action == 'delete':
            username = user.username
            user.delete()
            messages.success(request, f'تم حذف حساب {username}')
            return redirect('admin_users')
        
        current_params = request.GET.urlencode()
        return redirect(f"{request.path}?{current_params}" if current_params else request.path)
    
    return render(request, 'admin_panel/users.html', {
        'users': page_obj,
        'page_obj': page_obj,
        'search': search,
        'selected_role': role_filter,
        'selected_status': status_filter,
        'selected_sort': sort,
    })

def approve_user(request, pk):
    if not request.user.is_superuser:
        return redirect('landing_page')
    
    profile = get_object_or_404(Profile, pk=pk)
    profile.is_approved = True
    profile.save()
    
    profile.user.is_active = True
    profile.user.save()
    
    messages.success(request, f'تم تفعيل حساب المعلم {profile.user.username} بنجاح.')
    return redirect('admin_users')

@login_required
@user_passes_test(is_admin)
def admin_categories(request):
    categories = Category.objects.all().annotate(courses_count=Count('course'))
    
    search = request.GET.get('search')
    if search:
        categories = categories.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    
    sort = request.GET.get('sort', 'name')
    if sort == 'name':
        categories = categories.order_by('name')
    elif sort == 'courses':
        categories = categories.order_by('-courses_count')
    elif sort == 'newest':
        categories = categories.order_by('-id')
    else:
        categories = categories.order_by('name')
    
    paginator = Paginator(categories, ITEMS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        category_id = request.POST.get('category_id')
        
        if action == 'add':
            name = request.POST.get('name')
            description = request.POST.get('description')
            if name:
                Category.objects.create(name=name, description=description)
                messages.success(request, 'تم إضافة التصنيف بنجاح')
        
        elif action == 'edit':
            category = get_object_or_404(Category, pk=category_id)
            category.name = request.POST.get('name')
            category.description = request.POST.get('description')
            category.save()
            messages.success(request, 'تم تحديث التصنيف بنجاح')
            
        elif action == 'delete':
            category = get_object_or_404(Category, pk=category_id)
            category.delete()
            messages.success(request, 'تم حذف التصنيف بنجاح')
        
        return redirect('admin_categories')

    return render(request, 'admin_panel/categories.html', {
        'categories': page_obj,
        'page_obj': page_obj,
        'search': search,
        'selected_sort': sort,
    })

@login_required
@user_passes_test(is_admin)
def admin_payments(request):
    methods = PaymentMethod.objects.all()
    
    search = request.GET.get('search')
    if search:
        methods = methods.filter(name__icontains=search)
    
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        methods = methods.filter(is_active=True)
    elif status_filter == 'inactive':
        methods = methods.filter(is_active=False)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        method_id = request.POST.get('method_id')
        
        if action == 'add':
            name = request.POST.get('name')
            if name:
                PaymentMethod.objects.create(name=name, is_active=True)
                messages.success(request, 'تم إضافة طريقة الدفع بنجاح')
        
        elif action == 'toggle':
            method = get_object_or_404(PaymentMethod, pk=method_id)
            method.is_active = not method.is_active
            method.save()
            messages.success(request, 'تم تحديث حالة طريقة الدفع')
            
        elif action == 'delete':
            method = get_object_or_404(PaymentMethod, pk=method_id)
            method.delete()
            messages.success(request, 'تم حذف طريقة الدفع')
        
        elif action == 'edit':
            method = get_object_or_404(PaymentMethod, pk=method_id)
            name = request.POST.get('name')
            if name:
                method.name = name
                method.save()
                messages.success(request, 'تم تعديل طريقة الدفع بنجاح')
        
        return redirect('admin_payments')

    return render(request, 'admin_panel/payments.html', {
        'methods': methods,
        'search': search,
        'selected_status': status_filter,
    })

@login_required
@user_passes_test(is_admin)
def admin_reports(request):
    courses = Course.objects.annotate(
        avg_rating=Avg('review__rating'),
        students_count=Count('enrollment', filter=Q(enrollment__status='approved')),
        reviews_count=Count('review')
    ).order_by('-created_at')
    
    search = request.GET.get('search')
    if search:
        courses = courses.filter(
            Q(title__icontains=search) |
            Q(teacher__username__icontains=search) |
            Q(category__name__icontains=search)
        )
    
    status_filter = request.GET.get('status')
    if status_filter:
        courses = courses.filter(status=status_filter)
    
    category_filter = request.GET.get('category')
    if category_filter:
        courses = courses.filter(category_id=category_filter)
    
    sort = request.GET.get('sort', 'newest')
    if sort == 'oldest':
        courses = courses.order_by('created_at')
    elif sort == 'rating':
        courses = courses.order_by('-avg_rating')
    elif sort == 'students':
        courses = courses.order_by('-students_count')
    elif sort == 'price_high':
        courses = courses.order_by('-price')
    elif sort == 'price_low':
        courses = courses.order_by('price')
    else:
        courses = courses.order_by('-created_at')
    
    total_courses = courses.count()
    published_courses = courses.filter(status='published').count()
    avg_rating_all = courses.aggregate(avg=Avg('avg_rating'))['avg'] or 0
    total_students = Enrollment.objects.filter(status='approved').count()
    total_revenue = Course.objects.filter(status='published').aggregate(total=Sum('price'))['total'] or 0
    
    categories = Category.objects.all()
    
    paginator = Paginator(courses, ITEMS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'courses': page_obj,
        'page_obj': page_obj,
        'total_courses': total_courses,
        'published_courses': published_courses,
        'avg_rating_all': avg_rating_all,
        'total_students': total_students,
        'total_revenue': total_revenue,
        'categories': categories,
        'search': search,
        'selected_status': status_filter,
        'selected_category': category_filter,
        'selected_sort': sort,
    }
    return render(request, 'admin_panel/reports.html', context)

@login_required
@user_passes_test(is_admin)
def admin_settings(request):
    settings_obj, created = SystemSettings.objects.get_or_create(id=1)

    if request.method == 'POST':
        settings_obj.platform_name = request.POST.get('platform_name')
        settings_obj.support_email = request.POST.get('support_email')
        settings_obj.enable_registration = 'enable_registration' in request.POST
        settings_obj.enable_certificates = 'enable_certificates' in request.POST
        
        settings_obj.save()
        messages.success(request, 'تم حفظ إعدادات النظام بنجاح')
        return redirect('admin_settings')

    return render(request, 'admin_panel/settings.html', {'settings': settings_obj})

@login_required
@user_passes_test(is_admin)
def export_report(request, report_type):
    """تصدير التقارير بصيغ مختلفة"""
    
    courses = Course.objects.annotate(
        avg_rating=Avg('review__rating'),
        students_count=Count('enrollment', filter=Q(enrollment__status='approved'))
    ).order_by('-created_at')
    
    if report_type == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="courses_report.csv"'
        response.write('\ufeff'.encode('utf8'))  # BOM for Excel UTF-8
        
        writer = csv.writer(response)
        writer.writerow(['الكورس', 'المعلم', 'التصنيف', 'السعر', 'الطلاب', 'التقييم', 'الحالة'])
        
        for course in courses:
            writer.writerow([
                course.title,
                course.teacher.username,
                course.category.name if course.category else '-',
                course.price,
                course.students_count or 0,
                f"{course.avg_rating:.1f}" if course.avg_rating else '-',
                course.get_status_display()
            ])
        
        return response
    
    elif report_type == 'excel':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="courses_report.csv"'
        response.write('\ufeff'.encode('utf8'))  # BOM for Excel UTF-8
        
        writer = csv.writer(response, delimiter=';')
        writer.writerow(['الكورس', 'المعلم', 'التصنيف', 'السعر', 'الطلاب', 'التقييم', 'الحالة'])
        
        for course in courses:
            writer.writerow([
                course.title,
                course.teacher.username,
                course.category.name if course.category else '-',
                course.price,
                course.students_count or 0,
                f"{course.avg_rating:.1f}" if course.avg_rating else '-',
                course.get_status_display()
            ])
        
        return response
    
    elif report_type == 'pdf':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="courses_report.pdf"'
        
        try:
            pdfmetrics.registerFont(TTFont('ArabicFont', 'static/fonts/Amiri-Regular.ttf'))
            font_name = 'ArabicFont'
        except:
            font_name = 'Helvetica' 

        p = canvas.Canvas(response, pagesize=letter)
        width, height = letter

       
        def format_arabic(text):
            if not text: 
                return "-"
            reshaped_text = arabic_reshaper.reshape(str(text)) 
            bidi_text = get_display(reshaped_text) 
            return bidi_text

        p.setFont(font_name, 16)
        title = format_arabic("تقرير الكورسات - LMS Platform")
        p.drawRightString(width - 1*inch, height - 1*inch, title)

        p.setFont(font_name, 10)
        y_position = height - 2*inch
        
        headers = ["الحالة", "السعر", "المعلم", "الكورس"]
        x_positions = [1*inch, 2.5*inch, 4*inch, 5.5*inch]
        
        for i, header in enumerate(headers):
            p.drawRightString(x_positions[i], y_position, format_arabic(header))

        y_position -= 0.3*inch
        p.line(0.5*inch, y_position, width - 0.5*inch, y_position)

        p.setFont(font_name, 9)
        for course in courses:
            y_position -= 0.25*inch
            if y_position < 1*inch:
                p.showPage()
                y_position = height - 1*inch
                p.setFont(font_name, 9)

            p.drawRightString(1*inch, y_position, format_arabic(course.get_status_display()))
            p.drawRightString(2.5*inch, y_position, format_arabic(course.price))
            p.drawRightString(4*inch, y_position, format_arabic(course.teacher.username))
            p.drawRightString(5.5*inch, y_position, format_arabic(course.title))

        p.showPage()
        p.save()
        return response
    
    else:
        return HttpResponse('صيغة غير مدعومة', status=400)

# ==================== Course Views (Public) ====================

def course_list(request):
    courses = Course.objects.filter(status='published').annotate(
        avg_rating=Avg('review__rating'),
        students_count=Count('enrollment', filter=Q(enrollment__status='approved'))
    )
    
    search = request.GET.get('search')
    if search:
        courses = courses.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search) | 
            Q(teacher__username__icontains=search) |
            Q(category__name__icontains=search)
        )
    
    category_id = request.GET.get('category')
    if category_id:
        courses = courses.filter(category_id=category_id)
    
    teacher = request.GET.get('teacher')
    if teacher:
        courses = courses.filter(teacher__username=teacher)
    
    price_min = request.GET.get('price_min')
    if price_min:
        courses = courses.filter(price__gte=price_min)
    
    price_max = request.GET.get('price_max')
    if price_max:
        courses = courses.filter(price__lte=price_max)
    
    free_only = request.GET.get('free')
    if free_only:
        courses = courses.filter(price=0)
    
    sort = request.GET.get('sort', 'newest')
    if sort == 'oldest':
        courses = courses.order_by('created_at')
    elif sort == 'price_low':
        courses = courses.order_by('price')
    elif sort == 'price_high':
        courses = courses.order_by('-price')
    elif sort == 'rating':
        courses = courses.order_by('-avg_rating')
    elif sort == 'students':
        courses = courses.order_by('-students_count')
    else:
        courses = courses.order_by('-created_at')
    
    categories = Category.objects.all()
    teachers = User.objects.filter(profile__role='teacher', profile__is_approved=True).distinct()
    
    paginator = Paginator(courses, ITEMS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'courses/list.html', {
        'courses': page_obj,
        'page_obj': page_obj,
        'categories': categories,
        'teachers': teachers,
        'selected_category': category_id,
        'search': search,
        'selected_teacher': teacher,
        'selected_sort': sort,
        'price_min': price_min,
        'price_max': price_max,
        'free_only': free_only,
    })

def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk, status='published')
    contents = CourseContent.objects.filter(course=course).order_by('order')
    reviews = Review.objects.filter(course=course).select_related('student')
    avg_rating = course.review_set.aggregate(avg=Avg('rating'))['avg'] or 0
    approved_enrollments_count = course.enrollment_set.filter(status='approved').count()
    
    is_enrolled = False
    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(student=request.user, course=course, status='approved').exists()
    
    return render(request, 'courses/detail.html', {
        'course': course,
        'approved_count': approved_enrollments_count,
        'contents': contents,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'is_enrolled': is_enrolled
    })

@login_required
@user_passes_test(is_admin)
def manage_user_status(request, user_id):
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)
        action = request.POST.get('action')
        
        if action == 'approve':
            profile = target_user.profile
            profile.is_approved = True
            profile.save()
            
            target_user.is_active = True
            target_user.save()
            
            messages.success(request, f'تم تفعيل حساب المعلم {target_user.username} بنجاح.')
            
        elif action == 'reject':
            username = target_user.username
            target_user.delete()
            messages.warning(request, f'تم رفض وحذف حساب {username}.')
            
    return redirect('admin_users')

@login_required
def enroll_in_course(request, course_id):
    system_settings = SystemSettings.objects.first()
    if system_settings and not system_settings.enable_registration:
        messages.error(request, "التسجيل في الكورسات مغلق حالياً من قبل إدارة النظام.")
        return redirect('course_detail', pk=course_id)
        
    course = get_object_or_404(Course, id=course_id)
    enrollment, created = Enrollment.objects.get_or_create(
        student=request.user,
        course=course,
        defaults={'status': 'pending'}
    )
    if created:
        messages.success(request, "تم تقديم طلب التسجيل بنجاح، وهو قيد المراجعة من قبل معلم الكورس.")
    else:
        messages.info(request, f"لديك طلب تسجيل سابق لهذا الكورس وحالته: {enrollment.get_status_display()}")
    return redirect('course_detail', pk=course_id)

@login_required
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all()
    
    is_approved = Enrollment.objects.filter(student=request.user, course=quiz.course, status='approved').exists()
    if not is_approved:
        return HttpResponseForbidden("غير مسموح لك بدخول الاختبار إلا بعد قبول طلب تسجيلك في الكورس.")
        
    if request.method == 'POST':
        score = 0
        total_questions = questions.count()
        
        if total_questions == 0:
            messages.warning(request, "هذا الاختبار لا يحتوي على أسئلة بعد.")
            return redirect('course_detail', pk=quiz.course.id)
            
        for question in questions:
            selected_option = request.POST.get(f'question_{question.id}')
            if selected_option == question.correct_answer:
                score += 1
                
        percentage = (score / total_questions) * 100
        passed = percentage >= 60.0  
        
        QuizResult.objects.create(
            student=request.user,
            quiz=quiz,
            score=score,
            total_questions=total_questions,
            percentage=percentage,
            passed=passed
        )
        
        return render(request, 'courses/quiz_result.html', {
            'quiz': quiz,
            'score': score,
            'total': total_questions,
            'percentage': percentage,
            'passed': passed
        })
        
    return render(request, 'courses/take_quiz.html', {'quiz': quiz, 'questions': questions})

@login_required
def request_certificate(request, course_id):
    system_settings = SystemSettings.objects.first()
    if system_settings and not system_settings.enable_certificates:
        messages.error(request, "إصدار الشهادات معطل حالياً من قبل إدارة النظام.")
        return redirect('course_detail', pk=course_id)
        
    course = get_object_or_404(Course, id=course_id)
    cert_request, created = CertificateRequest.objects.get_or_create(
        student=request.user,
        course=course,
        defaults={'status': 'pending'}
    )
    if created:
        messages.success(request, "تم إرسال طلب الشهادة بنجاح لمعلم الكورس للمراجعة.")
    else:
        messages.info(request, f"لديك طلب شهادة سابق وحالته الحالية هي: {cert_request.get_status_display()}")
    return redirect('course_detail', pk=course_id)

@login_required
def add_course_review(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.student = request.user
            review.course = course
            review.save()
            messages.success(request, "تم إضافة تقييمك بنجاح، شكراً لك!")
        else:
            messages.error(request, "فشل إضافة التقييم، يرجى التأكد من البيانات.")
    return redirect('course_detail', pk=course_id)


@login_required
def view_results(current_request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, course__teacher=current_request.user)
    enrollments = Enrollment.objects.filter(course=quiz.course, status='approved')
    return render(current_request, 'teacher/results.html', {'quiz': quiz, 'enrollments': enrollments})

@login_required
def student_enrollments_history(request):
    enrollments = Enrollment.objects.filter(student=request.user).select_related('course')
    
    search = request.GET.get('search')
    if search:
        enrollments = enrollments.filter(course__title__icontains=search)
    
    status_filter = request.GET.get('status')
    if status_filter:
        enrollments = enrollments.filter(status=status_filter)
    
    sort = request.GET.get('sort', 'newest')
    if sort == 'oldest':
        enrollments = enrollments.order_by('enrolled_at')
    elif sort == 'course':
        enrollments = enrollments.order_by('course__title')
    else:
        enrollments = enrollments.order_by('-enrolled_at')
    
    paginator = Paginator(enrollments, ITEMS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'student/enrollments_history.html', {
        'enrollments': page_obj,
        'page_obj': page_obj,
        'search': search,
        'selected_status': status_filter,
        'selected_sort': sort,
    })

@login_required
def student_scorecard(request):
    results = QuizResult.objects.filter(student=request.user).select_related('quiz__course')
    
    search = request.GET.get('search')
    if search:
        results = results.filter(
            Q(quiz__title__icontains=search) |
            Q(quiz__course__title__icontains=search)
        )
    
    status_filter = request.GET.get('status')
    if status_filter == 'passed':
        results = results.filter(passed=True)
    elif status_filter == 'failed':
        results = results.filter(passed=False)
    
    sort = request.GET.get('sort', 'newest')
    if sort == 'oldest':
        results = results.order_by('created_at')
    elif sort == 'score_high':
        results = results.order_by('-percentage')
    elif sort == 'score_low':
        results = results.order_by('percentage')
    else:
        results = results.order_by('-created_at')
    
    paginator = Paginator(results, ITEMS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'student/scorecard.html', {
        'results': page_obj,
        'page_obj': page_obj,
        'search': search,
        'selected_status': status_filter,
        'selected_sort': sort,
    })

@login_required
def student_certificates_history(request):
    requests = CertificateRequest.objects.filter(student=request.user).select_related('course')
    
    search = request.GET.get('search')
    if search:
        requests = requests.filter(course__title__icontains=search)
    
    status_filter = request.GET.get('status')
    if status_filter:
        requests = requests.filter(status=status_filter)
    
    sort = request.GET.get('sort', 'newest')
    if sort == 'oldest':
        requests = requests.order_by('request_date')
    elif sort == 'course':
        requests = requests.order_by('course__title')
    else:
        requests = requests.order_by('-request_date')
    
    paginator = Paginator(requests, ITEMS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'student/certificates_history.html', {
        'requests': page_obj,
        'page_obj': page_obj,
        'search': search,
        'selected_status': status_filter,
        'selected_sort': sort,
    })

@login_required
def download_certificate_pdf(request, cert_id):
    cert_req = get_object_or_404(CertificateRequest, id=cert_id, student=request.user, status='issued')
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificate_{cert_req.id}.pdf"'
    
    try:
        pdfmetrics.registerFont(TTFont('ArabicFont', 'static/fonts/Amiri-Regular.ttf'))
        font_name = 'ArabicFont'
    except:
        font_name = 'Helvetica'
        
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    
    def ar(text):
        if not text: return ""
        return get_display(arabic_reshaper.reshape(str(text)))
        
    p.setLineWidth(4)
    p.setStrokeColorRGB(0.1, 0.3, 0.6)
    p.rect(30, 30, width - 60, height - 60)
    
    p.setFont(font_name, 28)
    p.drawCentredString(width/2, height - 150, ar("شهادة إتمام وتفوق"))
    p.setFont(font_name, 16)
    p.drawCentredString(width/2, height - 220, ar("تشهد منصة التعليم الإلكتروني بأن الطالب:"))
    p.setFont(font_name, 22)
    p.drawCentredString(width/2, height - 280, ar(cert_req.student.username))
    p.setFont(font_name, 16)
    p.drawCentredString(width/2, height - 340, ar("قد أكمل بنجاح واجتاز كافة الاختبارات المقررة في كورس:"))
    p.setFont(font_name, 20)
    p.drawCentredString(width/2, height - 400, ar(cert_req.course.title))
    p.setFont(font_name, 12)
    p.drawCentredString(width/2, height - 500, ar(f"تحت إشراف المعلم: {cert_req.course.teacher.username}"))
    p.drawCentredString(width/2, height - 530, ar(f"تاريخ الإصدار: {datetime.date.today().strftime('%Y-%m-%d')}"))
    
    p.showPage()
    p.save()
    return response