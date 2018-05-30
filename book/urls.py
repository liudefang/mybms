from django.urls import path,re_path

from book import views

urlpatterns = [
    # path('login/',views.login, name = 'login'),                 # FBV
    path('login/',views.LoginView.as_view(), name = 'login'),   # CBV
    # path('register/',views.register, name = 'register'),
    path('register/',views.RegisterView.as_view(), name = 'register'),
    path('exist_user/',views.exist_user),
    path('logout/',views.logout),

    path('book_list/',views.book_list, name = 'book_list'),
    # re_path(r'^book_list/(\d+)/(publisher)',views.book_list),
    re_path(r'^book_list/(?P<id>\d+)/(?P<type>publisher)',views.book_list),  # 有名分组
    # re_path(r'^book_list/(\d+)/(author)',views.book_list),
    re_path(r'^book_list/(?P<id>\d+)/(?P<type>author)',views.book_list),     # 有名分组

    path('del_book/',views.del_book, name = 'del_book'),
    re_path(r'^del_book/(\d+)/(publisher)',views.del_book),
    re_path(r'^del_book/(\d+)/(author)',views.del_book),

    path('add_book/',views.add_book,name='add_book'),
    re_path(r'^add_book/(\d+)/(publisher)',views.add_book),
    re_path(r'^add_book/(\d+)/(author)',views.add_book),

    re_path(r'^update_book/(?P<id>\d+)/(?P<type_id>\d+)/(?P<type>publisher)',views.update_book),
    re_path(r'^update_book/(?P<id>\d+)/(?P<type_id>\d+)/(?P<type>author)',views.update_book),
    re_path(r'^update_book/(?P<id>\d+)',views.update_book),
    # 这个得放到下面 否则会截走 上面两个 因为第一个也是正则

    path('publisher_list/',views.publisher_list, name = 'publisher_list'),
    path('del_publisher/',views.del_publisher, name = 'del_publisher'),
    path('add_publisher/',views.add_publisher, name = 'add_publisher'),
    re_path(r'^update_publisher/(\d+)',views.update_publisher),

    path('author_list/',views.author_list, name = 'author_list'),
    path('del_author/',views.del_author, name = 'del_author'),
    path('add_author/',views.add_author, name = 'add_author'),
    re_path(r'^update_author/(\d+)',views.update_author),

]
