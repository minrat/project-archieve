# -*- coding=utf-8 -*-
#!/usr/bin/python
####################################################
## Copyright (2022, ) Gemini.Chen
## Author: gemini_chen@163.com
## Date  : 2022/08/16
#####################################################

from Logs import _log_error
import requests
import os, sys, json
import configparser
import urllib3

urllib3.disable_warnings()


class Quota:
    def __init__(self):
        current_direct = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        config_out = configparser.ConfigParser()
        config_out.read(current_direct + '/conf/base.cfg', encoding="utf-8")
        # cluster ip
        self.cluster_ip = config_out.get("System", "self_service_ip").strip()
        # tenant name
        self.tenant_name = config_out.get("Tenant", "tenant_username").strip()
        # manager name
        self.login_username = config_out.get("Manager", "manager_username").strip()
        # manager password
        login_password = config_out.get("Manager", "manager_password").strip()
        # manager password encrypt
        login_password_out = os.popen("java -jar " + current_direct + "/lib/util.jar " + str(login_password),
                                      'r').readlines()
        self.login_password = login_password_out[0].strip()

    # Get The User Login Token
    def get_token(self):
        login_url = "https://" + self.cluster_ip + ":60006/api/sms/v1/users/login"
        login_json = {"account": self.login_username, "password": self.login_password, "isManager": True}
        login_content = requests.post(login_url, json=login_json, verify=False)
        login_out = json.loads(login_content.content)

        if not login_out.get('success'):
            _log_error("!!! Admin_Name or Admin_Password is invalid, Please Double Confirm !!!")
            sys.exit(0)
        if login_out.get('data').get('token').strip() != "":
            return login_out.get('data').get('token')
        else:
            # return "Invalid"
            _log_error("Get Access Token From Server: FAIL")
            sys.exit(0)

    def get_tenant_info_from_server(self):
        tenant_list_out = {}
        token = self.get_token()
        target_url = "https://" + self.cluster_ip + ":60006/api/sms/v1/tenants?params=[]"
        headers = {"token": token}
        content = requests.get(target_url, headers=headers, verify=False)
        tenant_out_data = json.loads(content.content)
        tenant_list = tenant_out_data.get('data').get('rows')
        for tenant_index in range(len(tenant_list)):
            tenant_list_out[tenant_list[tenant_index].get('account')] = tenant_list[tenant_index].get('id')
        return tenant_list_out.get(self.tenant_name)

    def get_tenant_vm_quota(self):
        quota_out = {}
        token = self.get_token()
        id = self.get_tenant_info_from_server()
        target_url = "https://" + self.cluster_ip +":60006/api/cos/v1/tenants/"+str(id)+"/quotas/metas"
        headers = {"token": token}
        content = requests.get(target_url, headers=headers, verify=False)
        tenant_quota_data = json.loads(content.content)

        if tenant_quota_data.get('success'):
            quota_data_detail = tenant_quota_data.get('data')
            for quota_index in range(len(quota_data_detail)):
                code = quota_data_detail[quota_index].get('code')
                quota_out[str(code)] = \
                    int(quota_data_detail[quota_index].get('quota')) - int(quota_data_detail[quota_index].get('minQuota'))
        else:
            _log_error("[ Tenant Quota ] API Request Meet Unexpected Error, Please Retry Again")
            # api error ,exit
            sys.exit(0)
        return quota_out

    # services list under tenant
    def get_tenant_service_quota(self):
        tenant_service_out = {}
        token = self.get_token()
        id = self.get_tenant_info_from_server()
        target_url = "https://" + self.cluster_ip + ":60006/api/cos/v1/services/tenants/"+str(id)+"/able?event=toAssignTenant&quotaAble=true"
        headers = {"token": token}
        content = requests.get(target_url, headers=headers, verify=False)
        tenant_service_data = json.loads(content.content)

        if tenant_service_data.get('success'):
            quota_service_detail = tenant_service_data.get('data')
            for quota_index in range(len(quota_service_detail)):
                service_code = quota_service_detail[quota_index].get('code')
                min_quota = quota_service_detail[quota_index].get('minQuota')
                set_quota = quota_service_detail[quota_index].get('quota')
                if service_code is not None and min_quota is not None and set_quota is not None:
                    tenant_service_out[str(service_code)] = int(set_quota) - int(min_quota)
        else:
            _log_error("[ Tenant Service ] API Request Meet Unexpected Error, Please Retry Again")
            # api error, exit
            sys.exit(0)
        return tenant_service_out


if __name__ == '__main__':
    # quota = Quota()
    pass