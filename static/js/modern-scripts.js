document.addEventListener('DOMContentLoaded', function() {
    initSidebar();
    initTooltips();
    initModals();
    initAnimations();
    initNotifications();
    initForms();
});

function initSidebar() {
    var toggle = document.getElementById('sidebar-toggle');
    var sidebar = document.getElementById('sidebar-wrapper');
    if (!toggle || !sidebar) return;
    
    toggle.addEventListener('click', function() {
        sidebar.classList.toggle('show');
    });
    
    document.addEventListener('click', function(e) {
        if (sidebar.classList.contains('show') && !sidebar.contains(e.target) && e.target !== toggle) {
            sidebar.classList.remove('show');
        }
    });
}

function initTooltips() {
    var tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(function(el) {
        new bootstrap.Tooltip(el);
    });
}

function initModals() {
    var modals = document.querySelectorAll('.modal');
    modals.forEach(function(modal) {
        modal.addEventListener('show.bs.modal', function() {
            document.body.style.overflow = 'hidden';
        });
        modal.addEventListener('hidden.bs.modal', function() {
            document.body.style.overflow = '';
            var forms = modal.querySelectorAll('form');
            forms.forEach(function(f) { f.reset(); });
        });
    });
}

function initAnimations() {
    var observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.card, .stat-card, .feature-card, .course-card').forEach(function(el) {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        observer.observe(el);
    });

    document.querySelectorAll('.stat-value').forEach(function(el) {
        var target = parseInt(el.textContent);
        if (isNaN(target)) return;
        var current = 0;
        var step = Math.max(1, Math.floor(target / 30));
        var timer = setInterval(function() {
            current += step;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            el.textContent = current;
        }, 30);
    });
}

function initNotifications() {
    setTimeout(function() {
        document.querySelectorAll('.alert-dismissible').forEach(function(alert) {
            var bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        });
    }, 5000);
}

function initForms() {
    document.querySelectorAll('[data-confirm]').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            if (!confirm(this.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });

    document.querySelectorAll('form').forEach(function(form) {
        form.addEventListener('submit', function() {
            var submitBtn = this.querySelector('[type="submit"]');
            if (submitBtn && !submitBtn.dataset.reset) {
                submitBtn.disabled = true;
                submitBtn.dataset.originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin ml-1"></i> جاري المعالجة...';
                setTimeout(function() {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = submitBtn.dataset.originalText;
                }, 5000);
            }
        });
    });
}

function showLoading(el) {
    if (!el) return;
    el.dataset.originalText = el.innerHTML;
    el.disabled = true;
    el.innerHTML = '<i class="fas fa-spinner fa-spin ml-1"></i> جاري التحميل...';
}

function hideLoading(el, text) {
    if (!el) return;
    el.disabled = false;
    el.innerHTML = text || el.dataset.originalText || '';
}

function showToast(message, type) {
    type = type || 'info';
    var container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = 'position:fixed;top:1.5rem;left:50%;transform:translateX(-50%);z-index:9999;display:flex;flex-direction:column;gap:0.5rem;';
        document.body.appendChild(container);
    }
    var toast = document.createElement('div');
    toast.className = 'alert alert-' + type + ' alert-dismissible fade show shadow-sm';
    toast.style.cssText = 'margin:0;min-width:300px;text-align:center;font-weight:600;border-radius:var(--radius-lg);';
    toast.innerHTML = message + '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';
    container.appendChild(toast);
    setTimeout(function() {
        var bsAlert = bootstrap.Alert.getOrCreateInstance(toast);
        bsAlert.close();
    }, 3000);
}
