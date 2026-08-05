// ===== تهيئة المشروع =====
document.addEventListener('DOMContentLoaded', function() {
    initializeTooltips();
    initializeModals();
    initializeForms();
    initializeNotifications();
});

// ===== Tooltips =====
function initializeTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// ===== Modals =====
function initializeModals() {
    // إغلاق النوافذ المنبثقة تلقائياً بعد النجاح
    document.querySelectorAll('.modal').forEach(function(modal) {
        modal.addEventListener('hidden.bs.modal', function() {
            // تنظيف النماذج
            var form = modal.querySelector('form');
            if (form) form.reset();
        });
    });
}

// ===== Forms =====
function initializeForms() {
    // تأكيد حذف العناصر
    document.querySelectorAll('.delete-confirm').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            if (!confirm('هل أنت متأكد من الحذف؟ لا يمكن التراجع عن هذا الإجراء.')) {
                e.preventDefault();
            }
        });
    });
    
    // معاينة الصور قبل الرفع
    var imageInput = document.querySelector('#id_image');
    if (imageInput) {
        imageInput.addEventListener('change', function(e) {
            var file = e.target.files[0];
            if (file) {
                var reader = new FileReader();
                reader.onload = function(e) {
                    var preview = document.querySelector('.image-preview');
                    if (preview) {
                        preview.src = e.target.result;
                        preview.style.display = 'block';
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    }
    
    // التحقق من صحة النماذج
    document.querySelectorAll('form').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            var submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="loading"></span> جاري الحفظ...';
            }
        });
    });
}

// ===== Notifications =====
function initializeNotifications() {
    // إخفاء التنبيهات تلقائياً بعد 5 ثواني
    document.querySelectorAll('.alert').forEach(function(alert) {
        setTimeout(function() {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

// ===== Print Function =====
function printReport() {
    window.print();
}

// ===== Export Function =====
function exportData(type) {
    var url = '/admin-panel/export/' + type + '/';
    window.location.href = url;
}