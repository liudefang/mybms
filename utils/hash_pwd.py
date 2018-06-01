# -*- coding:utf-8 -*-
import hashlib


def salt_pwd(password,username):
    # 把用户名当作盐 用户名只能唯一
    return hashlib.md5(password.encode('utf-8') + username.encode('utf-8')).hexdigest()
