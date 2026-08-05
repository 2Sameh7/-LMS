# 🎓 نظام إدارة التعلم LMS

منصة تعليمية متكاملة مبنية باستخدام Django و Bootstrap 5

## ✨ المميزات

### 👨‍🏫 للمعلمين
- ✅ إنشاء وإدارة الكورسات
- ✅ إضافة المحتوى (فيديو، نص، ملفات)
- ✅ إنشاء الاختبارات والأسئلة
- ✅ متابعة الطلاب واعتماد التسجيلات
- ✅ إدارة طلبات الشهادات
- ✅ عرض إحصائيات الأداء

### 👨‍💼 لمديري النظام
- ✅ إدارة حسابات المستخدمين (تفعيل/حظر/حذف)
- ✅ إدارة التصنيفات
- ✅ إدارة طرق الدفع
- ✅ عرض التقارير والإحصائيات الشاملة
- ✅ تصدير البيانات

## 🚀 التثبيت والتشغيل

### المتطلبات
- Python 3.10+
- pip

### الخطوات

```bash
# 1. استنساخ المشروع
git clone <repository-url>
cd lms_project

# 2. إنشاء بيئة افتراضية
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. تثبيت المكتبات
pip install -r requirements.txt

# 4. إنشاء قاعدة البيانات
python manage.py makemigrations
python manage.py migrate

# 5. تشغيل السيرفر
python manage.py runserver

# 6. فتح المتصفح
http://127.0.0.1:8000/