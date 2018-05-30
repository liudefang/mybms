from django.shortcuts import render,HttpResponse,redirect,reverse
from django.utils.decorators import method_decorator
from django.core import serializers
from django.views import View
import json
import datetime
import hashlib
import logging
from functools import wraps

from book import models
from book import myforms
from utils.mypage import MyPaginator

logger = logging.getLogger(__name__)
# 生成一个名为collect的实例
collect_logger = logging.getLogger('collect')

# 判断用户有没有登录得装饰器
def check_login(func):
    @wraps(func)
    def inner(request,*args,**kwargs):
        # 拿到当前访问网址
        url = request.get_full_path()
        if request.session.get('user'):
            return func(request,*args,**kwargs)
        else:
            return redirect('/login/?next={}'.format(url))

    return inner


# 登录
# def login(request):
#     login_form = myforms.LoginForm()
#     return render(request,'login.html',{'login_form':login_form})


# 注册
# def register(request):
#     register_form = myforms.LoginForm()
#     return render(request,'register.html',{'register_form':register_form})


# CBV 登录视图
class LoginView(View):

    def get(self,request):
        login_form = myforms.LoginForm()
        return render(request, 'login.html', {'login_form': login_form})

    def post(self,request):
        login_form = myforms.LoginForm(request.POST)
        if login_form.is_valid():
            username = login_form.cleaned_data.get('username')
            password = login_form.cleaned_data.get('password')
            # 把用户名当作盐 用户名只能唯一
            password = hashlib.md5(password.encode('utf-8') + username.encode('utf-8')).hexdigest()

            if models.UserInfo.objects.filter(name=username,pwd=password):
                # 设置session
                request.session['user'] = username
                # request.session.set_expiry(1800) # 设置session得失效时间

                # 登录成功 写log
                logger.info('用户：'+username+' 登录成功')

                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)   # 跳转到之前访问得页面
                else:
                    return redirect(reverse('book:book_list'))

            else:
                # 登录失败，写log
                logger.error('用户：'+username+' 登录时，用户名或密码错误')

                return render(request, 'login.html', {'login_form': login_form,'error_msg':'用户名或密码错误'})
        else:
            return render(request, 'login.html', {'login_form': login_form})


# CBV 注册视图
class RegisterView(View):

    # @method_decorator(check_login)  给cbv 加装饰器 逻辑上不应该加在这里，但可以验证装饰器加成功了
    def dispatch(self, request, *args, **kwargs):
        return super(RegisterView, self).dispatch(request,*args,**kwargs)

    def get(self,request):
        register_form = myforms.LoginForm()
        return render(request,'register.html',{'register_form':register_form})

    def post(self,request):
        register_form = myforms.LoginForm(request.POST)
        if register_form.is_valid():
            username = register_form.cleaned_data.get('username')
            password = register_form.cleaned_data.get('password')
            r_password = request.POST.get('r_password')
            if r_password == password:
                # 后台也需要判断用户名是否已存在，
                if not models.UserInfo.objects.filter(name=username):
                    # 把用户名当作盐 用户名只能唯一
                    password = hashlib.md5(password.encode('utf-8')+username.encode('utf-8')).hexdigest()
                    models.UserInfo.objects.create(name=username,pwd=password)

                    # 注册成功之后，设置session登录状态
                    request.session['user'] = username

                    # 注册成功 写入log  并收集特定信息的日志
                    collect_logger.info('用户：'+username+' 注册')

                    return redirect(reverse('book:book_list'))
            else:
                return render(request,'register.html',{'register_form':register_form,'error_msg':'确认密码不符合'})

        return render(request,'register.html',{'register_form':register_form})


# 查看用户是否已经存在
def exist_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        user_obj = models.UserInfo.objects.filter(name=username).first()
        if user_obj:
            reg = {'status':1,'msg':'用户已存在'}
        else:
            reg = {'status':0,'msg':'用户不存在'}

        return HttpResponse(json.dumps(reg))


# 注销
def logout(request):
    request.session.delete()
    return redirect(reverse('book:login'))


# 书列表 3中情况 从book_list下来的书  从publisher_list 下来的书 从author_list下来的书
# @check_login
def book_list(request,id = 0, type = 'src'):
    books = None
    if type == 'publisher':
        books = models.Book.objects.filter(publisher_id=id).values('id','title','price','publish_date','publisher__name').order_by('-id')
    elif type == 'author':
        books = models.Book.objects.filter(authors__id=id).values('id','title','price','publish_date','publisher__name').order_by('-id')
    else:
        books = models.Book.objects.all().values('id', 'title', 'price', 'publish_date', 'publisher__name').order_by('-id')

    current_page_num = request.GET.get('page', 1)
    page_obj = MyPaginator(books,current_page_num)

    current_path ={'path':request.path}
    ret_dic = page_obj.show_page  # 页码返回的是字典
    ret_dic.update(current_path)  # 两个字典拼接

    # return render(request,'book_list.html',page_obj.show_page)
    return render(request,'book_list.html',ret_dic)


# 删除一本书 3中情况 从book_list下来的书  从publisher_list 下来的书 从author_list下来的书
def del_book(request, id = 0, type = 'src'):
    delete_id = request.POST.get('delete_id')
    if type == 'author':   # 清除绑定关系
        author_id = id
        author_obj = models.Author.objects.filter(id = author_id).first()
        try:
            author_obj.books.remove(delete_id)
            reg = {'status': 1, 'msg': '删除成功'}
        except Exception as e:
            reg = {'status':0,'msg':'删除失败'}

    else:  # 其他情况都删除书 book_list  publishe_list下来的书
        try:
            models.Book.objects.filter(id=delete_id).delete()
            reg = {'status':1,'msg':'删除成功'}
        except Exception as e:
            reg = {'status':0,'msg':'删除失败'}

    return HttpResponse(json.dumps(reg))


# 增加书
def add_book(request,id = 0, type = 'src'):
    current_publisher_id = 0
    current_author_id = 0
    if type == 'publisher':
        current_publisher_id = int(id)
    elif type == 'author':
        current_author_id = int(id)

    book_form = myforms.BookForm()

    if request.method == 'POST':
        if current_publisher_id:
            # 前端设置select disbaled  不能传到后台了,因此需要需要这样做
            publisher_id = current_publisher_id
        else:
            publisher_id = int(request.POST.get('publisher'))

        if request.POST.get('publish_date') != '':
            publish_date = request.POST.get('publish_date')
        else:
            publish_date = datetime.datetime.now()

        book_form = myforms.BookForm(request.POST)

        if book_form.is_valid():
            book_obj = models.Book.objects.create(
                title =  book_form.cleaned_data.get('title'),
                price = book_form.cleaned_data.get('price'),
                publish_date = publish_date,
                publisher_id = publisher_id,
            )
            if current_author_id:
                book_obj.authors.add(current_author_id)  # 绑定多对多关系

            # return redirect(reverse('book:book_list')) #  因为有3种情况，分别跳到自己对应的页面下
            return redirect(request.path.replace('add_book','book_list'))

    publisher = models.Publisher.objects.all().values('id', 'name').order_by('-id')
    return render(request,'add_book.html',{'book_form':book_form,
                                            'publisher':publisher,
                                            "current_publisher_id":current_publisher_id})


# 修改书
def update_book(request,id,type_id = 0, type = 'src'):
    book = models.Book.objects.filter(id=id).first()
    book_form = myforms.BookForm()
    book_form.initial = {'title':book.title,'price':book.price}

    if request.method == 'POST':
        if request.POST.get('publish_date') != '':
            publish_date = request.POST.get('publish_date')
        else:
            publish_date = datetime.datetime.now()

        book_form = myforms.BookForm(request.POST)

        if book_form.is_valid():
            models.Book.objects.filter(id=id).update(
                title=book_form.cleaned_data.get('title'),
                price=book_form.cleaned_data.get('price'),
                publish_date=publish_date,
                publisher_id=request.POST.get('publisher'),
            )

            # 有3种情况，分别跳到自己对应的页面下
            if type == 'publisher':
                new_url = reverse('book:book_list')+type_id+'/'+type
            elif type == 'author':
                new_url = reverse('book:book_list')+type_id+'/'+type
            else:
                new_url = reverse('book:book_list')

            return redirect(new_url)

    publisher = models.Publisher.objects.all().values('id', 'name').order_by('-id')
    return render(request,'update_book.html',{'book_form':book_form,
                                              'publisher':publisher,
                                              'current_publisher_id':book.publisher_id,
                                              'publish_date':book.publish_date})


# 出版社列表
# @check_login
def publisher_list(request):
    publishers = models.Publisher.objects.all().order_by('-id')
    current_page_num = request.GET.get('page',1)
    page_obj = MyPaginator(publishers,current_page_num)

    return render(request,'publisher_list.html',page_obj.show_page)


# 删除一个出版社
def del_publisher(request):
    delete_id = request.POST.get('delete_id')
    try:
        models.Publisher.objects.filter(id=delete_id).delete()
        reg = {'status':1,'msg':'删除成功'}
    except Exception as e:
        reg = {'status':0,'msg':'删除失败'}

    return HttpResponse(json.dumps(reg))


# 增加出版社
def add_publisher(request):
    publisher_form = myforms.PublisherForm()
    if request.method == 'POST':
        publisher_form = myforms.PublisherForm(request.POST)
        if publisher_form.is_valid():
            models.Publisher.objects.create(**publisher_form.cleaned_data)
            return redirect(reverse('book:publisher_list'))

    return render(request,'add_publisher.html',{'publisher_form':publisher_form})


# 修改出版社
def update_publisher(request,id):
    publisher = models.Publisher.objects.filter(id=id).first()
    publisher_form = myforms.PublisherForm()
    publisher_form.initial = {'name': publisher.name}  # 对forms组件初始化

    if request.method == 'POST':
        publisher_form = myforms.PublisherForm(request.POST)
        if publisher_form.is_valid():
            models.Publisher.objects.filter(id=id).update(**publisher_form.cleaned_data)
            return redirect(reverse('book:publisher_list'))

    return render(request, 'update_publisher.html', {'publisher_form': publisher_form})


# 作者列表
# @check_login
def author_list(request):
    authors = models.Author.objects.all().values('id','detail_id','name','detail__age','detail__addr').order_by('-id')
    current_page_num = request.GET.get('page')
    page_obj = MyPaginator(authors,current_page_num)

    return render(request,'author_list.html',page_obj.show_page)


# 删除一个作者
def del_author(request):
    delete_id = request.POST.get('delete_id')
    try:
        # 删Author关联的不会被删掉
        # models.Author.objects.filter(id=delete_id).delete()

        # 删AuthorDetail关联的才会被删掉
        models.AuthorDetail.objects.filter(id=delete_id).delete()
        reg = {'status':1,'msg':'删除成功'}
    except Exception as e:
        reg = {'status':0,'msg':'删除失败'}

    return HttpResponse(json.dumps(reg))


# 增加作者
def add_author(request):
    author_form = myforms.AuthorForm()
    if request.method == 'POST':
        author_form = myforms.AuthorForm(request.POST)
        if author_form.is_valid():
            name = author_form.cleaned_data.get('name')
            age = author_form.cleaned_data.get('age')
            addr = author_form.cleaned_data.get('addr')

            authordetail = models.AuthorDetail.objects.create(age=age,addr=addr)
            models.Author.objects.create(name=name,detail=authordetail)

            return redirect(reverse('book:author_list'))

    return render(request,'add_author.html',{'author_form':author_form})


# 修改作者
def update_author(request,id):
    author = models.Author.objects.filter(id=id).values('name','detail__age','detail__addr').first()
    author_form = myforms.AuthorForm()
    author_form.initial = {'name':author.get('name'),'age':author.get('detail__age'),'addr':author.get('detail__addr')}

    if request.method == 'POST':
        author_form = myforms.AuthorForm(request.POST)
        if author_form.is_valid():
            name = author_form.cleaned_data.get('name')
            age = author_form.cleaned_data.get('age')
            addr = author_form.cleaned_data.get('addr')

            models.Author.objects.filter(id=id).update(name=name)
            models.AuthorDetail.objects.filter(author__id=id).update(age=age,addr=addr)

            return redirect(reverse('book:author_list'))

    return render(request,'update_author.html',{'author_form':author_form})
