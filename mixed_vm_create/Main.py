# -*- coding=utf-8 -*-
#!/usr/bin/python
####################################################
## Copyright (2022, ) Gemini.Chen
## Author: gemini_chen@163.com
## Date  : 2022/07/22
#####################################################
import sys

from bin.Logs import _log_info, _log_success, _log_error,_banner,_log_warn
import os, platform


def install_soft(soft_path, soft_name):
    file_list = os.listdir(soft_path+soft_name)
    soft_cmd = ""
    for index_soft in range(len(file_list)):
        soft_cmd = soft_cmd+soft_path+soft_name+"/"+file_list[index_soft]+" "
    install_soft_status = os.system('python -m pip install ' + soft_cmd)
    if install_soft_status == 0:
        _log_success("Install Module [ "+soft_name+" ] : success")
        return True
    else:
        _log_error("Install Module [ "+soft_name+" ] : failed")
        return False


def init_env():
    current_direct = os.path.dirname(os.path.realpath(__file__))
    init_flag_pip = True
    init_flag_requests = True
    init_flag_tqdm = True
    init_flag_configparser = True
    init_flag_openpyxl = True
    init_flag_jdk = True

    _log_info("Prepare Python Related Env For Next Stages...")
    # pip
    try:
        import pip
    except:
        # install pip
        linux_cmd_setup_tools = "cd " + current_direct + "/lib/pip/setuptools-44.0.0 && python setup.py install"
        linux_cmd_pip = "cd " + current_direct + "/lib/pip/pip-20.2 && python setup.py install"
        install_01 = os.system(linux_cmd_setup_tools)
        install_02 = os.system(linux_cmd_pip)
        if install_01 == 0 and install_02 == 0:
            _log_success("Checking config module : success")
        else:
            _log_error("Checking config module: failed")
            init_flag_pip = False
    # requests
    try:
        import requests
    except:
        # install requests
        install = install_soft("./lib/", "requests")
        if install:
            _log_success("Checking requests module : success")
        else:
            _log_error("Checking requests module: failed")
            init_flag_requests = False

    # tqdm
    try:
        import tqdm
    except:
        # install tqdm
        install_tqdm = install_soft("./lib/", "tqdm")
        if install_tqdm:
            _log_success("Checking tqdm module : success")
        else:
            _log_error("Checking tqdm module : failed")
            init_flag_tqdm = False

    # config
    try:
        import configparser
    except:
        # install config
        install_config = os.system('python -m pip install lib/configparser-3.7.3-py2.py3-none-any.whl')
        if install_config == 0:
            _log_success("Checking config module : success")
        else:
            _log_error("Checking config module: failed")
            init_flag_configparser = False

    # python excel
    try:
        from openpyxl import load_workbook
    except:
        # install openpyxl
        install = install_soft("./lib/", "openpyxl")
        if install:
            _log_success("Checking openpyxl module : success")
        else:
            _log_error("Checking openpyxl module : failed")
            init_flag_openpyxl = False

    # java
    java_installed_status = os.system("java -version")
    if java_installed_status == 0:
        _log_success("Java Installed : success ")
    else:
        _log_warn("Java Not Installed, Please Install ")
        if platform.system().lower() == "windows":
            cmd = "lib/java/jdk-8u333-windows-x64.exe /s ADDLOCAL='ToolsFeature,SourceFeature,PublickjreFeature' /INSTALLDIR=C:\\java\\jdk-1.8 /INSTALLDIRPUBJRE=C:\\java\\jre-1.8"
            java_status = os.system(cmd)
            if java_status == 0:
                _log_success("[Windows] JDK Install : PASS")
            else:
                _log_error("[Windows] Java Install : FAILED")
                init_flag_jdk = False
        elif platform.system().lower() == "linux":
            java_status = os.system("rpm -ivh lib/java/jdk-8u333-linux-x64.rpm")
            if java_status == 0:
                _log_success("[Linux] JDK Install : PASS")
            else:
                _log_error("[Linux] Java Install : FAILED")
                init_flag_jdk = False

    if init_flag_pip and init_flag_requests and init_flag_tqdm \
            and init_flag_configparser and init_flag_openpyxl and init_flag_jdk:
        return True
    else:
        return False


def init_template(filename):
    init_flag = False
    if os.path.exists(filename):
        file_readable = os.access(filename, os.R_OK)
        if file_readable and os.path.splitext(filename)[1] == '.xlsx':
            _log_success("[Verify] : VM Template File OK For Use")
            init_flag = True
    else:
        _log_error("[Verify] : VM Template File Not Valid, Please Double Confirm")
    return init_flag


if __name__ == '__main__':
    filename = "Auto_VM_Template.xlsx"

    # env prepare
    _banner("Prepare For The Create VMs Task")
    stag_init = init_env()
    stage_template = init_template(filename)

    if stag_init and stage_template:
        from bin.VM_Template import VM_Object
        vm = VM_Object(filename)
        vm.run()
    else:
        _log_error("Prepare Stage Meet Error.")