import os
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import connection
from core.models import Profile, Category, Course, CourseContent, Quiz, Question, Enrollment, CertificateRequest, Review, PaymentMethod

class Command(BaseCommand):
    help = 'حذف قاعدة البيانات القديمة وإنشاء بيانات اختبار سورية (25 صف لكل جدول)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-delete',
            action='store_true',
            help='عدم حذف البيانات الموجودة'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('⚠️  بدء عملية تعبئة قاعدة البيانات...'))
        
        # حذف البيانات القديمة ما لم يتم تحديد --no-delete
        if not options['no_delete']:
            self.delete_old_data()
        
        # إنشاء البيانات الجديدة
        self.create_categories()
        self.create_users()
        self.create_courses()
        self.create_course_content()
        self.create_quizzes()
        self.create_questions()
        self.create_enrollments()
        self.create_certificate_requests()
        self.create_reviews()
        self.create_payment_methods()
        
        self.stdout.write(self.style.SUCCESS('✅ تم تعبئة قاعدة البيانات بنجاح!'))
        self.print_summary()

    def delete_old_data(self):
        """حذف جميع البيانات الموجودة"""
        self.stdout.write(self.style.WARNING('🗑️  جاري حذف البيانات القديمة...'))
        
        # حذف بالترتيب العكسي للعلاقات
        Question.objects.all().delete()
        Quiz.objects.all().delete()
        CourseContent.objects.all().delete()
        Enrollment.objects.all().delete()
        CertificateRequest.objects.all().delete()
        Review.objects.all().delete()
        Course.objects.all().delete()
        Category.objects.all().delete()
        PaymentMethod.objects.all().delete()
        Profile.objects.all().delete()
        User.objects.all().delete()
        
        # إعادة تعيين AutoField
        self.reset_sequences()
        
        self.stdout.write(self.style.SUCCESS('✓ تم حذف البيانات القديمة'))

    def reset_sequences(self):
        """إعادة تعيين العدادات التلقائية"""
        tables = [
            'auth_user', 'core_profile', 'core_category', 'core_course',
            'core_coursecontent', 'core_quiz', 'core_question',
            'core_enrollment', 'core_certificaterequest', 'core_review',
            'core_paymentmethod'
        ]
        
        with connection.cursor() as cursor:
            for table in tables:
                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")

    # ==================== بيانات سورية ====================
    
    SYRIAN_FIRST_NAMES = [
        'أحمد', 'محمد', 'محمود', 'خالد', 'عمر', 'يوسف', 'إبراهيم', 'حسن', 'حسين', 'علي',
        'فاطمة', 'عائشة', 'زينب', 'مريم', 'نور', 'هدى', 'سارة', 'ليلى', 'رنا', 'دينا',
        'بشار', 'طه', 'ياسر', 'سامر', 'ماهر', 'رانيا', 'غادة', 'سميرة', 'أماني', 'هالة'
    ]
    
    SYRIAN_LAST_NAMES = [
        'الأسد', 'الحريري', 'الحلبي', 'الدمشقي', 'الحمصي', 'اللاذقاني', 'الطرطوسي',
        'الحماوي', 'الدرعاني', 'السويدي', 'الكردي', 'العلوي', 'السني', 'المسيحي',
        'الأكراد', 'التركمان', 'الشركس', 'الأرمن', 'الروم', 'العرب',
        'القوتلي', 'العظم', 'العظمة', 'الجابري', 'القيمي', 'المقداد', 'الزعبي',
        'الشهابي', 'الآغا', 'باشا', 'بيك', 'أفندي', 'خوجة', 'صباغ', 'كاتب'
    ]
    
    SYRIAN_CITIES = [
        'دمشق', 'حلب', 'حمص', 'اللاذقية', 'طرطوس', 'حماة', 'درعا', 'السويداء',
        'القنيطرة', 'إدلب', 'الرقة', 'دير الزور', 'الحسكة', 'طرطوس', 'بانياس',
        'جبلة', 'صافيتا', 'تدمر', 'دوما', 'زبداني', 'يبرود', 'النبيك', 'قطنا',
        'الكسوة', 'التل', 'حرستا', 'عربين', 'جرمانا', 'المعضمية', 'داريا'
    ]
    
    COURSE_TITLES = [
        'مقدمة في البرمجة بلغة Python',
        'تطوير الويب باستخدام Django',
        'تصميم الجرافيك بالفوتوشوب',
        'التسويق الرقمي ووسائل التواصل',
        'إدارة المشاريع الاحترافية PMP',
        'تعلم اللغة الإنجليزية للمستويات المتقدمة',
        'محاسبة وإدارة مالية للمبتدئين',
        'تطوير تطبيقات الموبايل بـ Flutter',
        'الذكاء الاصطناعي وتعلم الآلة',
        'أمن المعلومات والسيبراني',
        'تصميم قواعد البيانات SQL',
        'تطوير الواجهات الأمامية React',
        'التجارة الإلكترونية من الألف للياء',
        'إدارة الموارد البشرية HR',
        'تصميم الشعارات والهوية البصرية',
        'تحرير الفيديو ببرنامج Premiere',
        'الكتابة الإبداعية والمحتوى',
        'تحليل البيانات بـ Excel و Power BI',
        'أساسيات الشبكات Network+',
        'لغة الجسد والتواصل الفعال',
        'ريادة الأعمال وإنشاء المشاريع',
        'التصوير الفوتوغرافي الاحترافي',
        'تطوير الألعاب بـ Unity',
        'بلوك تشين والعملات الرقمية',
        'إدارة الوقت والإنتاجية الشخصية'
    ]
    
    COURSE_DESCRIPTIONS = [
        'تعلم أساسيات البرمجة من الصفر حتى الاحتراف مع تطبيقات عملية',
        'دورة شاملة لتطوير مواقع الويب باستخدام إطار عمل جانغو',
        'أتقن تصميم الجرافيك باستخدام أدوبي فوتوشوب خطوة بخطوة',
        'استراتيجيات التسويق الرقمي الناجحة لزيادة مبيعاتك',
        'شهادة إدارة المشاريع الاحترافية مع نماذج تطبيقية',
        'حسّن مهاراتك في اللغة الإنجليزية للتواصل والعمل',
        'أساسيات المحاسبة والإدارة المالية للشركات الناشئة',
        'بناء تطبيقات الموبايل للنظامين Android و iOS',
        'مقدمة في الذكاء الاصطناعي وخوارزميات تعلم الآلة',
        'حماية الأنظمة والشبكات من الاختراقات الإلكترونية',
        'تصميم وإدارة قواعد البيانات العلائقية بفعالية',
        'بناء واجهات مستخدم تفاعلية وحديثة بـ React',
        'إنشاء متجر إلكتروني ناجح وإدارة المبيعات أونلاين',
        'إدارة فريق العمل والموارد البشرية باحترافية',
        'تصميم شعارات احترافية وهوية بصرية متكاملة',
        'تحرير المونتاج والفيديو بشكل سينمائي احترافي',
        'فن الكتابة الإبداعية وإنشاء محتوى جذاب',
        'تحليل البيانات وعرضها بطرق احترافية',
        'فهم أساسيات الشبكات والاتصالات الحديثة',
        'تطوير مهارات التواصل ولغة الجسد',
        'خطوات إنشاء مشروع ريادي ناجح من الفكرة للتنفيذ',
        'تقنيات التصوير الفوتوغرافي الاحترافي',
        'برمجة وتصميم الألعاب ثلاثية الأبعاد',
        'فهم تقنية البلوك تشين والعملات المشفرة',
        'زيادة إنتاجيتك وإدارة وقتك بفعالية'
    ]

    # ==================== إنشاء البيانات ====================

    def create_categories(self):
        """إنشاء 25 تصنيف"""
        self.stdout.write('📁 جاري إنشاء التصنيفات...')
        
        categories_data = [
            ('برمجة وتطوير', 'دورات في البرمجة وتطوير البرمجيات'),
            ('تصميم جرافيك', 'تصميم الجرافيك والهوية البصرية'),
            ('تسويق', 'التسويق الرقمي والإلكتروني'),
            ('إدارة أعمال', 'إدارة المشاريع والشركات'),
            ('لغات', 'تعلم اللغات الأجنبية'),
            ('محاسبة ومالية', 'المحاسبة والإدارة المالية'),
            ('تقنية معلومات', 'تقنية المعلومات والشبكات'),
            ('تطوير ذات', 'تطوير المهارات الشخصية'),
            ('تصوير وفيديو', 'التصوير الفوتوغرافي والمونتاج'),
            ('تجارة إلكترونية', 'التجارة الإلكترونية والمبيعات'),
            ('ذكاء اصطناعي', 'الذكاء الاصطناعي وتعلم الآلة'),
            ('أمن سيبراني', 'أمن المعلومات والحماية'),
            ('قواعد بيانات', 'إدارة وتصميم قواعد البيانات'),
            ('تطبيقات موبايل', 'تطوير تطبيقات الهواتف'),
            ('ريادة أعمال', 'إنشاء وإدارة المشاريع الريادية'),
            ('كتابة ومحتوى', 'الكتابة الإبداعية وصناعة المحتوى'),
            ('تحليل بيانات', 'تحليل البيانات والإحصاء'),
            ('شبكات', 'الشبكات والاتصالات'),
            ('تعليم', 'طرق التدريس والتعليم'),
            ('صحة', 'الصحة واللياقة البدنية'),
            ('فن', 'الفنون والرسم'),
            ('موسيقى', 'العزف والموسيقى'),
            ('طبخ', 'الطبخ والحلويات'),
            ('أزياء', 'التصميم والأزياء'),
            ('سياحة', 'السياحة والسفر')
        ]
        
        for name, desc in categories_data:
            Category.objects.create(name=name, description=desc)
        
        self.stdout.write(self.style.SUCCESS(f'✓ تم إنشاء {Category.objects.count()} تصنيف'))

    def create_users(self):
        """إنشاء 25 مستخدم (مدير، معلمين، طلاب)"""
        self.stdout.write('👥 جاري إنشاء المستخدمين...')
        
        # إنشاء مدير نظام
        admin = User.objects.create_user(
            username='admin',
            email='admin@lms.sy',
            password='admin123',
            first_name='مدير',
            last_name='النظام'
        )
        Profile.objects.filter(user=admin).update(role='admin', phone='+963911000000')
        
        # إنشاء 8 معلمين
        teachers = []
        for i in range(8):
            first_name = random.choice(self.SYRIAN_FIRST_NAMES[:20])
            last_name = random.choice(self.SYRIAN_LAST_NAMES)
            username = f'teacher{i+1}'
            
            teacher = User.objects.create_user(
                username=username,
                email=f'{username}@lms.sy',
                password='teacher123',
                first_name=first_name,
                last_name=last_name
            )
            Profile.objects.filter(user=teacher).update(
                role='teacher',
                phone=f'+9639{random.randint(10000000, 99999999)}',
                bio=f'معلم خبير في مجاله مع {random.randint(3, 15)} سنوات خبرة'
            )
            teachers.append(teacher)
        
        # إنشاء 16 طالب
        students = []
        for i in range(16):
            first_name = random.choice(self.SYRIAN_FIRST_NAMES[20:])
            last_name = random.choice(self.SYRIAN_LAST_NAMES)
            username = f'student{i+1}'
            
            student = User.objects.create_user(
                username=username,
                email=f'{username}@lms.sy',
                password='student123',
                first_name=first_name,
                last_name=last_name
            )
            Profile.objects.filter(user=student).update(
                role='student',
                phone=f'+9639{random.randint(10000000, 99999999)}',
                bio=f'طالب متحمس للتعلم من {random.choice(self.SYRIAN_CITIES)}'
            )
            students.append(student)
        
        self.stdout.write(self.style.SUCCESS(f'✓ تم إنشاء {User.objects.count()} مستخدم'))
        return teachers, students

    def create_courses(self):
        """إنشاء 25 كورس"""
        self.stdout.write('📚 جاري إنشاء الكورسات...')
        
        teachers = list(User.objects.filter(profile__role='teacher'))
        categories = list(Category.objects.all())
        
        courses = []
        for i in range(25):
            course = Course.objects.create(
                title=self.COURSE_TITLES[i],
                description=self.COURSE_DESCRIPTIONS[i],
                teacher=random.choice(teachers),
                category=random.choice(categories),
                price=round(random.uniform(10, 200), 2),
                status=random.choice(['draft', 'published', 'published', 'published', 'archived']),
                created_at=datetime.now() - timedelta(days=random.randint(1, 365))
            )
            courses.append(course)
        
        self.stdout.write(self.style.SUCCESS(f'✓ تم إنشاء {Course.objects.count()} كورس'))
        return courses

    def create_course_content(self):
        """إنشاء محتوى للكورسات (حوالي 25 عنصر)"""
        self.stdout.write('📝 جاري إنشاء محتوى الكورسات...')
        
        courses = list(Course.objects.all())
        content_types = ['video', 'text', 'file']
        
        content_count = 0
        for course in courses:
            num_contents = random.randint(1, 5)
            for j in range(num_contents):
                CourseContent.objects.create(
                    course=course,
                    title=f'درس {j+1}: {random.choice(["مقدمة", "أساسيات", "تطبيقات", "أمثلة", "اختبار"]) }',
                    content_type=random.choice(content_types),
                    link_or_file=f'https://example.com/content/{content_count}',
                    order=j+1
                )
                content_count += 1
                if content_count >= 25:
                    break
            if content_count >= 25:
                break
        
        self.stdout.write(self.style.SUCCESS(f'✓ تم إنشاء {CourseContent.objects.count()} عنصر محتوى'))

    def create_quizzes(self):
        """إنشاء 25 اختبار"""
        self.stdout.write('📋 جاري إنشاء الاختبارات...')
        
        courses = list(Course.objects.all())
        
        for i in range(25):
            Quiz.objects.create(
                course=random.choice(courses),
                title=f'اختبار {i+1}: {random.choice(["الدرس الأول", "الوحدة الأولى", "التقييم النهائي", "اختبار منتصف المادة", "اختبار عملي"])}',
                status=random.choice(['draft', 'active', 'active', 'active', 'closed'])
            )
        
        self.stdout.write(self.style.SUCCESS(f'✓ تم إنشاء {Quiz.objects.count()} اختبار'))

    def create_questions(self):
        """إنشاء 25 سؤال للاختبارات"""
        self.stdout.write('❓ جاري إنشاء أسئلة الاختبارات...')
        
        quizzes = list(Quiz.objects.all())
        
        questions_data = [
            ('ما هي لغة البرمجة المستخدمة في Django؟', 'Python'),
            ('ماذا يعني HTML؟', 'HyperText Markup Language'),
            ('ما هو العنصر الأساسي في CSS؟', 'Selector'),
            ('كم عدد أركان الإسلام؟', '5'),
            ('ما هي عاصمة سوريا؟', 'دمشق'),
            ('ما هو أكبر كوكب في المجموعة الشمسية؟', 'المشتري'),
            ('ما هي لغة queries في قواعد البيانات؟', 'SQL'),
            ('ماذا يعني API؟', 'Application Programming Interface'),
            ('ما هو بروتوكول نقل النصوص التشعبية؟', 'HTTP'),
            ('ما هي شركة تطوير React؟', 'Facebook'),
            ('ما معنى OOP؟', 'Object Oriented Programming'),
            ('ما هي لغة styling للويب؟', 'CSS'),
            ('ما هو نظام التحكم بالنسخ الأشهر؟', 'Git'),
            ('ماذا يعني JSON؟', 'JavaScript Object Notation'),
            ('ما هي منصة التعلم الأشهر؟', 'Coursera'),
            ('ما معنى SaaS؟', 'Software as a Service'),
            ('ما هي لغة Flutter؟', 'Dart'),
            ('ماذا يعني UI؟', 'User Interface'),
            ('ما معنى UX؟', 'User Experience'),
            ('ما هي قاعدة البيانات العلائقية الأشهر؟', 'MySQL'),
            ('ماذا يعني CDN؟', 'Content Delivery Network'),
            ('ما هي لغة الـ Backend الأشهر؟', 'Python'),
            ('ماذا يعني MVC؟', 'Model View Controller'),
            ('ما معنى REST؟', 'Representational State Transfer'),
            ('ما هي تقنية الحاويات الأشهر؟', 'Docker')
        ]
        
        for i in range(25):
            Question.objects.create(
                quiz=random.choice(quizzes),
                text=questions_data[i][0],
                correct_answer=questions_data[i][1]
            )
        
        self.stdout.write(self.style.SUCCESS(f'✓ تم إنشاء {Question.objects.count()} سؤال'))

    def create_enrollments(self):
        """إنشاء 25 طلب تسجيل"""
        self.stdout.write('📝 جاري إنشاء طلبات التسجيل...')
        
        students = list(User.objects.filter(profile__role='student'))
        courses = list(Course.objects.all())
        
        for i in range(25):
            Enrollment.objects.create(
                student=random.choice(students),
                course=random.choice(courses),
                status=random.choice(['pending', 'approved', 'approved', 'approved', 'rejected']),
                enrolled_at=datetime.now() - timedelta(days=random.randint(1, 180))
            )
        
        self.stdout.write(self.style.SUCCESS(f'✓ تم إنشاء {Enrollment.objects.count()} طلب تسجيل'))

    def create_certificate_requests(self):
        """إنشاء 25 طلب شهادة"""
        self.stdout.write('🎓 جاري إنشاء طلبات الشهادات...')
        
        students = list(User.objects.filter(profile__role='student'))
        courses = list(Course.objects.all())
        
        for i in range(25):
            CertificateRequest.objects.create(
                student=random.choice(students),
                course=random.choice(courses),
                status=random.choice(['pending', 'issued', 'issued', 'issued', 'rejected']),
                request_date=datetime.now() - timedelta(days=random.randint(1, 90))
            )
        
        self.stdout.write(self.style.SUCCESS(f'✓ تم إنشاء {CertificateRequest.objects.count()} طلب شهادة'))

    def create_reviews(self):
        """إنشاء 25 تقييم"""
        self.stdout.write('⭐ جاري إنشاء التقييمات...')
        
        students = list(User.objects.filter(profile__role='student'))
        courses = list(Course.objects.all())
        
        review_comments = [
            'كورس ممتاز جداً، استفدت كثيراً',
            'شرح واضح ومفهوم، أنصح به',
            'محتوى رائع ولكن يحتاج لتحديث',
            'أفضل كورس تعلمته حتى الآن',
            'المعلم ممتاز والشرح مبسط',
            'كورس مفيد جداً للمبتدئين',
            'جودة الفيديو عالية والشرح ممتاز',
            'أنصح الجميع بهذا الكورس',
            'تجربة تعليمية رائعة',
            'محتوى غني ومفيد',
            'الشرح مفصل وواضح',
            'كورس يستحق الوقت والجهد',
            'تعلمت الكثير من هذا الكورس',
            'ممتاز جداً، شكراً للمعلم',
            'كورس احترافي ومفيد',
            'أنصح به بشدة',
            'تجربة رائعة في التعلم',
            'محتوى متميز وشامل',
            'الشرح سهل ومبسط',
            'كورس رائع جداً',
            'استفدت كثيراً من الكورس',
            'جودة عالية ومحتوى ممتاز',
            'كورس مفيد وعملي',
            'أنصح به لكل المهتمين',
            'تجربة تعليمية مميزة'
        ]
        
        for i in range(25):
            Review.objects.create(
                student=random.choice(students),
                course=random.choice(courses),
                rating=random.randint(3, 5),
                comment=random.choice(review_comments),
                created_at=datetime.now() - timedelta(days=random.randint(1, 120))
            )
        
        self.stdout.write(self.style.SUCCESS(f'✓ تم إنشاء {Review.objects.count()} تقييم'))

    def create_payment_methods(self):
        """إنشاء 25 طريقة دفع"""
        self.stdout.write('💳 جاري إنشاء طرق الدفع...')
        
        payment_methods = [
            ('بطاقة ائتمان Visa', True),
            ('بطاقة ائتمان MasterCard', True),
            ('PayPal', True),
            ('تحويل بنكي', True),
            ('الدفع عند الاستلام', True),
            ('بطاقة مدى', True),
            ('Apple Pay', True),
            ('Google Pay', True),
            ('STC Pay', True),
            ('فوري', True),
            ('بطاقة ميزة', True),
            ('تحويل عبر الصراف', False),
            ('Western Union', False),
            ('MoneyGram', False),
            ('Bitcoin', False),
            ('Ethereum', False),
            ('USDT', False),
            ('بطاقة هدايا', True),
            ('دفع نقدي', True),
            ('تقسيط', True),
            ('تابي', True),
            ('تمارا', True),
            ('كاشير', True),
            ('ماستر كارد', True),
            ('فيزا إلكترونية', True)
        ]
        
        for name, is_active in payment_methods:
            PaymentMethod.objects.create(name=name, is_active=is_active)
        
        self.stdout.write(self.style.SUCCESS(f'✓ تم إنشاء {PaymentMethod.objects.count()} طريقة دفع'))

    def print_summary(self):
        """طباعة ملخص البيانات"""
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('📊 ملخص البيانات المضافة:'))
        self.stdout.write(self.style.SUCCESS('='*50))
        
        data = [
            ('المستخدمين', User.objects.count()),
            ('الملفات الشخصية', Profile.objects.count()),
            ('التصنيفات', Category.objects.count()),
            ('الكورسات', Course.objects.count()),
            ('محتوى الكورسات', CourseContent.objects.count()),
            ('الاختبارات', Quiz.objects.count()),
            ('الأسئلة', Question.objects.count()),
            ('طلبات التسجيل', Enrollment.objects.count()),
            ('طلبات الشهادات', CertificateRequest.objects.count()),
            ('التقييمات', Review.objects.count()),
            ('طرق الدفع', PaymentMethod.objects.count()),
        ]
        
        for name, count in data:
            self.stdout.write(self.style.SUCCESS(f'  {name}: {count}'))
        
        self.stdout.write(self.style.SUCCESS('='*50))
        
        # معلومات الدخول
        self.stdout.write(self.style.WARNING('\n🔑 بيانات الدخول للتجربة:'))
        self.stdout.write(self.style.WARNING('  المدير: admin / admin123'))
        self.stdout.write(self.style.WARNING('  المعلم: teacher1 / teacher123'))
        self.stdout.write(self.style.WARNING('  الطالب: student1 / student123'))
        self.stdout.write(self.style.WARNING('='*50 + '\n'))