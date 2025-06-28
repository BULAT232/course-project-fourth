# from django.http import HttpResponseForbidden
# from django.shortcuts import redirect
# from django.urls import reverse

# class RoleAccessMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         response = self.get_response(request)
#         return response

#     def process_view(self, request, view_func, view_args, view_kwargs):
#         # Пропускаем публичные страницы
#         public_paths = [
#             reverse('main:login'),  # ИСПРАВЛЕНО
#             reverse('main:register'),  # ИСПРАВЛЕНО
#             reverse('main:home')  # ИСПРАВЛЕНО
#         ]
        
#         if request.path in public_paths:
#             return None
            
#         # Проверка аутентификации
#         if not request.user.is_authenticated:
#             return redirect('main:login')  # ИСПРАВЛЕНО
            
#         # Проверка ролей для защищенных страниц
#         admin_paths = ['/admin/', '/manage/']
#         if any(request.path.startswith(path) for path in admin_paths):
#             if not (request.user.role == 'admin' or request.user.is_superuser):
#                 return HttpResponseForbidden("Доступ запрещен")
                
#         return None