# -*- coding=utf-8 -*-
#!/usr/bin/python
####################################################
## Copyright (2022, ) Gemini.Chen
## Author: gemini_chen@163.com
## Date  : 2022/07/22
#####################################################


# log style
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[43;31m"
WGBC = "\033[47;30m"
ENDC = "\033[0m"


def _banner(content):
    banner = content
    bar = len(banner)*"="
    blank = len(banner)*" "

    print("  ."+bar+".")
    print("  |"+blank+"|")
    print("  |"+banner+"|")
    print("  |"+blank+"|")
    print("  '"+bar+"'")


def _banner_index(content):
    banner = content
    bar = len(banner) * "-"
    blank = len(banner) * " "

    print("  ."+bar+".")
    print("  |"+blank+"|")
    print("  |"+banner+"|")
    print("  |"+blank+"|")
    print("  '"+bar+"'")


def _log_success(content):
    message= content
    print(GREEN + message + ENDC)
    print("\033[0m")


def _log_error(content):
    message = content
    print(RED + message + ENDC)
    print("\033[0m")


def _log_warn(content):
    message = content
    print(YELLOW + message + ENDC)
    print("\033[0m")


def _log_info(content):
    message = content
    print(WGBC + message + ENDC)
    print("\033[0m")


def _log_adv(title, content):
    message = content
    _banner_index(title)
    print("Suggestion: "+GREEN + message + ENDC)
    print("\033[0m")


def _log_verify(target, content):
    message = content
    print("[ "+ GREEN + target + ENDC +" ] Status is : "+GREEN + message + ENDC)
    print("\033[0m")
