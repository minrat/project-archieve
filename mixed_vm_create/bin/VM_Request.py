# -*- coding=utf-8 -*-
#!/usr/bin/python
####################################################
## Copyright (2022, ) Gemini.Chen
## Author: gemini_chen@163.com
## Date  : 2022/07/22
#####################################################

'''
VM  Related Request To Self-Service, including: OpenStack , Vmware
'''

import os, requests, json
import sys
import time
import urlparse
import configparser
from Logs import _banner_index, _log_success, _log_error, _log_info, _log_adv, _log_verify
import urllib3

urllib3.disable_warnings()

reload(sys)
sys.setdefaultencoding("utf-8")


class VM_Request():
    def __init__(self):
        # template data for vm
        self.common_template_data = {}
        # vmware
        self.vmware_template_data = {}
        # openstack
        self.openstack_template_data = {}
        self.current_direct = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        # config related
        self.config = self.read_config_file()

        self.login_username = self.config.get("Tenant", "tenant_username").strip()

        login_password = self.config.get("Tenant", "tenant_password").strip()
        login_password_out = os.popen("java -jar "+self.current_direct+"/lib/util.jar " + str(login_password), 'r').readlines()

        self.login_password = login_password_out[0].strip()

        # cluster ip
        self.cluster_ip = self.config.get("System", "self_service_ip").strip()
        # token
        self.access_token = self.get_token()
        # # init password
        vm_default_password = self.config['VM_Type']['vm_init_password'].strip()
        self.vm_default_password = os.popen("java -jar "+self.current_direct+"/lib/util.jar "
                                            + str(vm_default_password)).read().strip()

    # Load The configuration file
    def read_config_file(self):
        # current_direct = os.path.dirname(os.path.abspath(__file__))
        current_direct = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        config_out = configparser.ConfigParser()
        config_out.read(current_direct+'/conf/base.cfg', encoding="utf-8")
        return config_out

    # Get the Real Url
    def get_real_url(self, url):
        try:
            import urllib.parse as parse
            out = parse.unquote(url, encoding="utf-8")
        except:
            import urllib2
            out = urlparse.unquote(url)
        _log_adv(url, out)
        return out

    # Get The User Login Token
    def get_token(self):
        login_url = "https://"+self.cluster_ip+":60008/api/sms/v1/tenants/login"
        login_json = {"account": self.login_username, "password": self.login_password}

        login_content = requests.post(login_url, json=login_json,  verify=False)
        login_out = json.loads(login_content.content)

        if not login_out.get('success'):
            _log_error("!!! Tenant_Name or Tenant_Password is invalid, Please Double Confirm !!!")
            sys.exit(0)

        # tenant id
        self.common_template_data['tenant_id'] = login_out.get('data').get('tenant').get('id')

        if login_out.get('data').get('token').strip() != "":
            return login_out.get('data').get('token')
        else:
            # return "Invalid"
            _log_error("Get Access Token From Server: FAILED")
            sys.exit(1)

    # get region
    def get_region(self):
        _log_info("Get Region From Server")
        token = self.access_token
        target_url = "https://" + self.cluster_ip + ":60008/api/sms/v1/dictionaries/children?value=REGION"
        headers = {"token": token}
        content = requests.get(target_url, headers=headers, verify=False)
        # region_out = json.loads(content.content).encode('unicode-escape').decode('string_escape').strip()
        region_out_data = json.loads(content.content)

        region_out = region_out_data.get('data')[0].get('value')
        # region setting
        self.common_template_data['region'] = region_out
        # self.openstack_template_data['region'] = region_out
        # self.vmware_template_data['region'] = region_out
        return region_out

    # Get Location Info
    def get_location(self):
        _log_info("Get Available Location From Zone : [ "+self.get_region()+" ]")
        token = self.access_token
        location_out = {}
        target_url = "https://" + self.cluster_ip + ":60008/api/sms/v1/dictionaries/children?value="+self.get_region()
        headers = {"token": token}
        content = requests.get(target_url, headers=headers, verify=False)
        location_out_data = json.loads(content.content)

        for index in range(0, len(location_out_data.get('data'))):
            location_name = location_out_data.get('data')[index].get('name')
            location_id = str(location_out_data.get('data')[index].get("value"))

            location_out[location_id] = location_name
        return location_out

    # get server type
    def get_available_server(self):
        _log_info("[Common] Get Available Service Provider From Server")
        token = self.access_token
        params = {"condition":"getServiceType","catalog":"server"}
        target_url = "https://" + self.cluster_ip + ":60008/api/cos/v1/cloud/services/condition?condition=" + str(
            params)
        headers = {"token": token}
        content = requests.get(target_url, headers=headers, verify=False)
        provider_list_data = json.loads(content.content)
        return provider_list_data.get('data')

    # here maybe need some enhancement later------(optional)----
    def prepare_for_resource(self):
        _log_info("Prepare For Get Resource")
        token = self.access_token
        target_url = "https://" + self.cluster_ip + ":60008/api/sms/v1/users?params=[]"

        headers = {"token": token}
        content = requests.get(target_url, headers=headers, verify=False)
        prepare_for_resource_out_data = json.loads(content.content)

        user_info_list = prepare_for_resource_out_data.get('data').get('rows')

        # print str(user_info_list).replace("\'", "\"").replace("u","")
        for user_index in range(len(user_info_list)):
            self.common_template_data['creator_id'] = user_info_list[user_index].get('id')
            self.common_template_data['mender_id'] = user_info_list[user_index].get('id')
            self.common_template_data['owner_id'] = user_info_list[user_index].get('id')

        return self.common_template_data

    # get target in [$available_zone]  [$vendor_type]
    def get_resource_related(self, available_zone, vendor_type):
        _log_info("Get Resource From Server [ "+available_zone+" ], Type is [ "+vendor_type+" ]")
        # update
        self.prepare_for_resource()
        resource_flag = False
        token = self.access_token
        resource_result_out = {}
        # Here need inject from outside
        real_region = self.get_region()

        # verify available zone
        location_list = self.get_location()
        # dict reverse
        # print zip(location_list.values(), location_list.keys())
        #
        # print [key for key, value in location_list.items() if value == "吴江"]
        # print "吴江".encode('unicode-escape')
        # if available_zone in self.get_location():
        real_available_zone = [key for key, value in location_list.items() if value == available_zone]

        real_available_zone = real_available_zone[0]

        real_vendor_type = str(vendor_type).upper()
        payload = {"condition":"getByAz","region":str(real_region),"az":real_available_zone,"vendorType":real_vendor_type}
        target_url = "https://" + self.cluster_ip + ":60008/api/ims/v1/pool/groups/condition?condition="+str(payload)

        headers = {"token": token}
        content = requests.get(target_url, headers=headers, verify=False)
        resource_out_data = json.loads(content.content)

        if resource_out_data.get("success"):
            for index in range(len(resource_out_data.get("data"))):
                # resource_out_data.append(str(resource_out_data.get('data')[index].get("value")))

                self.common_template_data['poolGroup_id'] = resource_out_data.get('data').get('id')
                self.common_template_data['vendor_id'] = resource_out_data.get('data').get('vendorId')
                self.common_template_data['vendorType'] = resource_out_data.get('data').get('vendorType')
                self.common_template_data['available_zone'] = real_available_zone

                # if real_vendor_type is "OPENSTACK":
                #     self.openstack_template_data['poolGroup_id'] = resource_out_data.get('data').get('id')
                #     self.openstack_template_data['vendor_id'] = resource_out_data.get('data').get('vendorId')
                #     self.openstack_template_data['vendorType'] = resource_out_data.get('data').get('vendorType')
                #     # self.openstack_template_data['creator_id'] = resource_out_data.get('data').get('creatorId')
                #     # self.openstack_template_data['mender_id'] = resource_out_data.get('data').get('menderId')
                #     self.openstack_template_data['available_zone'] = real_available_zone
                #
                # elif real_vendor_type is "VMWARE":
                #     self.vmware_template_data['poolGroup_id'] = resource_out_data.get('data').get('id')
                #     self.vmware_template_data['vendor_id'] = resource_out_data.get('data').get('vendorId')
                #     self.vmware_template_data['vendorType'] = resource_out_data.get('data').get('vendorType')
                #     self.vmware_template_data['available_zone'] = real_available_zone

                resource_result_out['common_detail'] = self.common_template_data
                # update the flag
                resource_flag = True
                resource_result_out['status'] = resource_flag
        else:
            _log_error("Zone: ["+available_zone+" ], Do not have [ " + real_vendor_type + " ]")
            sys.exit(0)
        return resource_result_out

    # Get Project List
    def get_project_list(self):
        _log_info("Get Project List")
        token = self.access_token
        project_out_data = {}
        target_url = "https://" + self.cluster_ip + ':60008/api/sms/v1/projects/condition?condition={"condition":"listApplyProjects","businessId":""}'
        headers = {"token": token}
        content = requests.get(target_url, headers=headers, verify=False)
        project_list_out = json.loads(content.content)

        for i in range(0, len(project_list_out.get('data'))):
            project_id = project_list_out.get('data')[i].get('id')
            project_name = project_list_out.get('data')[i].get('name')

            project_out_data[project_id] = str(project_name)

        return project_out_data

    # Get Network List
    def get_openstack_network(self):
        _log_info("Get Network List")
        token = self.access_token
        network_list_out = []
        # Here need inject from outside
        tenant_Id = self.common_template_data.get('tenant_id')
        vendor_Id = self.common_template_data.get('vendor_id')

        payload = {"condition":"networkAndSubnets","vendorId":vendor_Id,"tenantId":tenant_Id}
        target_url = "https://" + self.cluster_ip + ":60008/api/ims/v1/networks/condition?condition="+str(payload)
        headers = {"token": token}

        content = requests.get(target_url,  headers=headers, verify=False)
        network_out = json.loads(content.content)

        for i in range(0, len(network_out.get('data'))):
            network_out_detail = {}
            network_out_detail['network_id'] = str(network_out.get('data')[i].get('id'))
            network_out_detail['network_name'] = str(network_out.get('data')[i].get('name'))
            network_out_detail['subnet_name'] = str(network_out.get('data')[i].get('subnets')[0].get('name'))
            network_out_detail['tenantId'] = str(network_out.get('data')[i].get('tenantId'))
            network_out_detail['vendorId'] = str(network_out.get('data')[i].get('vendorId'))

            # network details
            tem_data = network_out.get('data')[i].get('subnets')

            tem_data_out = {}
            for i in tem_data[0].keys():
                if i == "ipPools":
                    tem_data_out[str(i)] = str(tem_data[0].get(i))
                else:
                    tem_data_out[str(i)] = str(tem_data[0].get(i))

            network_out_detail['subnet_detail'] = tem_data_out
            network_list_out.append(network_out_detail)
        return network_list_out

    # Get SecurityGroup List
    def get_security_group(self):
        _log_info("Get Security Group List")
        token = self.access_token
        security_group_out = []
        # Here need inject from outside
        tenant_Id = self.common_template_data.get('tenant_id')
        vendor_Id = self.common_template_data.get('vendor_id')

        payload = [{"param": {"vendorId": vendor_Id, "tenantId": tenant_Id},"sign": "EQ"}]
        target_url = "https://" + self.cluster_ip + ":60008/api/ims/v1/sgroups?params="+str(payload)

        headers = {"token": token}
        content = requests.get(target_url, headers=headers, verify=False)

        security_group_out_data = json.loads(content.content)
        for i in range(len(security_group_out_data.get('data').get('rows'))):
            security_group_out_detail = {}
            security_group_out_detail['name'] = security_group_out_data.get('data').get('rows')[i].get('name')
            security_group_out_detail['vendorId'] = security_group_out_data.get('data').get('rows')[i].get('vendorId')
            security_group_out_detail['id'] = security_group_out_data.get('data').get('rows')[i].get('id')
            security_group_out_detail['groupUuid'] = security_group_out_data.get('data').get('rows')[i].get('groupUuid')
            security_group_out.append(security_group_out_detail)
        return security_group_out

    # Get Image list
    def get_openstack_images(self):
        _log_info("Get Available Image List")
        token = self.access_token
        vm_image_detail = {}

        # here need enhancement
        vendor_Id = self.common_template_data.get('vendor_id')

        condition = {"condition": "listTenantImages", "vendorId": vendor_Id}

        target_url = "https://" + self.cluster_ip + ":60008/api/ims/v1/images/condition?condition="+str(condition)
        headers = {"token": token}
        content = requests.get(target_url, headers=headers, verify=False)
        vm_image_out_data = json.loads(content.content)

        for image_index in range(len(vm_image_out_data.get('data'))):
            image_version_id = {}
            image_type_name = str(vm_image_out_data.get('data').keys()[image_index])
            image_type_version_res = vm_image_out_data.get('data').get(image_type_name)
            image_type_version_list = vm_image_out_data.get('data').get(image_type_name).keys()

            for version_index in range(len(image_type_version_list)):
                image_version = image_type_version_list[version_index]
                image_id = image_type_version_res.get(image_version)[0].get('id')
                image_version_id[str(image_version)] = image_id

            # image name can not be updated
            vm_image_detail[image_type_name] = image_version_id
        return vm_image_detail

    # get openstack vm disk info
    def prepare_openstack_vm_disk(self):
        _log_info("[OpenStack] Get Disk For Target VM [1/2] - Prepare")
        token = self.access_token
        target_url = "https://" + self.cluster_ip + ":60008/api/cos/v1/cloud/services/openstack.standard.volume/categories"
        headers = {"token": token}
        content = requests.get(target_url, headers=headers, verify=False)
        prepare_disk_info_out = json.loads(content.content)

        return prepare_disk_info_out.get('data')[0].get('id')

    # Get Disk List
    def get_vm_disk(self):
        _log_info("Get Disk For Target VM [2/2] - DO")
        token = self.access_token
        disk_out = {}
        # categoryId : SAS
        category_Id = self.prepare_openstack_vm_disk()

        params = [{"param": {"categoryId": category_Id}, "sign": "EQ"}]
        target_url = "https://" + self.cluster_ip + ":60008/api/cos/v1/services/skus/condition?params="+str(params)
        headers = {"token": token}
        content = requests.get(target_url, headers=headers, verify=False)
        disk_info_out = json.loads(content.content)
        for i in range(0, len(disk_info_out.get('data'))):
            disk_detail_info = {}
            disk_detail_info['code'] = str(disk_info_out.get('data')[i].get('code'))
            # sku id
            disk_detail_info['sku_id'] = str(disk_info_out.get('data')[i].get('id'))

            vm_disk_capacity = json.loads(disk_info_out.get('data')[i].get('spec'))[0].get('specValue')
            disk_detail_info['capacity'] = str(vm_disk_capacity)
            disk_detail_info['catalogId'] = str(disk_info_out.get('data')[i].get('catalogId'))
            #
            disk_detail_info['categoryId'] = disk_info_out.get('data')[i].get('categoryId')
            disk_detail_info['serviceId'] = str(disk_info_out.get('data')[i].get('serviceId'))
            disk_detail_info['serviceCode'] = str(disk_info_out.get('data')[i].get('serviceCode'))
            # re-pack into dict
            disk_out[str(vm_disk_capacity)] = disk_detail_info
        return disk_out

    #
    def prepare_vm_template(self, vm_type):
        _log_info("Get Template For Target VM [1/2]-Prepare")
        token = self.access_token
        params = {"condition":"queryByCode","code":str(vm_type)}
        target_url = "https://" + self.cluster_ip + ":60008/api/cos/v1/cloud/services/condition?condition="+str(params)
        headers = {"token": token}
        content = requests.get(target_url, headers=headers, verify=False)
        prepare_vm_template_info_out = json.loads(content.content)
        return prepare_vm_template_info_out.get('data').get('id')

    # verify flavor
    def get_vm_template(self, vm_type):
        _log_info("Get Template For Target VM [2/2]")
        vm_provider = ""
        if str(vm_type).upper() == "OPENSTACK":
            vm_provider = "openstack.standard.server"
        if str(vm_type).upper() == "VMWARE":
            vm_provider = "vmware.standard.server"
        template_out = {}
        token = self.access_token
        #
        category_Id = self.prepare_vm_template(vm_provider)

        params = [{"param": {"categoryId": category_Id}, "sign": "EQ"}]
        target_url = "https://" + self.cluster_ip + ":60008/api/cos/v1/services/skus/condition?params="+str(params)
        headers = {"token": token}
        content = requests.get(target_url, headers=headers, verify=False)
        templats_out = json.loads(content.content)
        for i in range(len(templats_out.get('data'))):
            template_index_out = {}
            template_index_data_out = {}
            template_index_out['code'] = templats_out.get('data')[i].get('code')
            # sku id
            template_index_out['sku_id'] = templats_out.get('data')[i].get('id')
            # cpu & mem
            tmp_data = json.loads(templats_out.get('data')[i].get('spec'))

            vm_cpu = str(tmp_data[0].get('specValue'))
            vm_mem = str(tmp_data[1].get('specValue'))

            template_index_out['cpu'] = vm_cpu
            template_index_out['mem'] = vm_mem

            template_index_out['catalogId'] = str(templats_out.get('data')[i].get('catalogId'))
            template_index_out['categoryId'] = str(templats_out.get('data')[i].get('categoryId'))
            template_index_out['serviceId'] = str(templats_out.get('data')[i].get('serviceId'))

            template_index_out['serviceCode'] = str(templats_out.get('data')[i].get('serviceCode'))

            key = str(vm_cpu)+"c"+str(vm_mem)+"g"
            template_out[key] = template_index_out
        return template_out

    # get common related information
    def get_common_data_from_server(self):
        _log_info("Get Common Related Information From Target Server")
        # location
        self.get_location()
        # project
        self.get_project_list()

        self.prepare_for_resource()

        return self.common_template_data

    # create VMs
    def create_target_vms(self, vm_template_file):
        _banner_index("Create Vms from template file : ["+vm_template_file+" ]")
        token = self.access_token
        target_url = "https://" + self.cluster_ip + ":60008/api/cos/v1/resource/application"
        headers = {"token": token, "Content-Type": "application/json"}
        vm_create_out_info = {}
        # template load
        try:
            with open(vm_template_file, "r") as fp:
                # load from json file
                payload = json.load(fp)

                # create vm
                content = requests.post(target_url, data=json.dumps(payload), headers=headers, verify=False)
                vm_create_out = json.loads(content.content)
                vm_create_out_flag = vm_create_out.get('success')
                vm_create_out_message = vm_create_out.get('message')

                vm_create_out_info['status'] = vm_create_out_flag
                vm_create_out_info['message'] = vm_create_out_message
        except:
            _log_error("[Common-Generate Vms] Open File Meet Unexpected Error")

        return vm_create_out_info

    # get vmware related information
    def get_result_from_server(self, vendor_type, vms_list):
        _log_adv("Get VMs Result From Server :[ "+vendor_type+" ] ", "Waiting For A Moment....")
        # sleep 30s
        from tqdm import tqdm
        for i in tqdm(range(1, 101)):
            time.sleep(0.3)
        _log_info("Start Task Verifying")
        token = self.access_token
        vendor_type = str(vendor_type).upper()
        # get the vm names
        for vm_index in range(len(vms_list)):
            _log_info("VM ["+vms_list[vm_index]+"] Start Verifying ...")
            params = [{"param": {"name": str(vms_list[vm_index]).strip()}, "sign": "LK"},
                    {"param": {"vendorType": vendor_type, "isRecycle": 0}, "sign": "EQ"}]
            # all provider
            # params = [{"param":{"vendorType":vendor_type,"isRecycle":0},"sign":"EQ"}]
            target_url = "https://" + self.cluster_ip + ":60008/api/ims/v1/vms?params=" + str(params)
            headers = {"token": token}
            content = requests.get(target_url, headers=headers, verify=False)
            result_info_out = json.loads(content.content)
            count = int(result_info_out.get('data').get('total'))
            result_list = result_info_out.get('data').get('rows')
            for result_index in range(count):
                vm_name = result_list[result_index].get('name')
                vm_status = result_list[result_index].get('status')
                # update later
                _log_verify(vm_name, vm_status)

    # logout the system
    def log_out(self):
        _log_info("Logout From Server")
        token = self.access_token
        target_url = "https://" + self.cluster_ip + ":60008/api/sms/v1/tenants/logout"
        headers = {"token": token}
        content = requests.post(target_url, headers=headers, verify=False)
        logout = json.loads(content.content)
        if logout.get('success') is True:
            _log_success("Logout Success")
            return True
        else:
            _log_error("Logout Faild")
            return False

    # get vmware network card id (image + network-card)
    def get_vmware_related_from_template(self):
        vm_template_detail = []
        token = self.access_token

        # Here need inject from outside
        # vendor_id = self.vmware_template_data.get('vendor_id')
        vendor_id = 5

        params = {"condition":"listTenantImages","vendorId":vendor_id}
        target_url = "https://" + self.cluster_ip + ":60008/api/ims/v1/images/condition?condition=" + str(params)
        headers = {"token": token}
        content = requests.get(target_url, headers=headers, verify=False)
        result_info_data = json.loads(content.content)
        result_info_out = result_info_data.get('data')

        for os_index in result_info_out.keys():
            # os type
            os_type = os_index
            for version_index in result_info_out.get(os_index):
                vm_template_detail_tmp = {}
                # os type
                vm_template_detail_tmp['os_type'] = str(os_type)
                os_type_version = version_index
                # os version
                vm_template_detail_tmp['os_type_version'] = str(os_type_version)

                os_type_version_data = result_info_out.get(os_index).get(version_index)

                vm_template_detail_tmp['os_image_id'] = str(os_type_version_data[0].get('id'))

                os_type_version_card_id = os_type_version_data[0].get('networkCards')[0].get('id')
                # card id
                vm_template_detail_tmp['os_type_version_card_id'] = str(os_type_version_card_id)
                # re-pack
                vm_template_detail.append(vm_template_detail_tmp)
        return vm_template_detail

    # vmware ip verify
    def vmware_ip_verify(self, pool_id, ip):
        token = self.access_token
        condition = {"condition": "checkIp", "poolId": pool_id, "ips": [str(ip)]}
        target_url = "https://" + self.cluster_ip + ":60008/api/ims/v1/ips/condition?condition=" + str(condition)
        headers = {"token": token}
        content = requests.get(target_url, headers=headers, verify=False)
        result_info_out = json.loads(content.content)

        return result_info_out.get('success')

    # vmware network list
    def get_vmware_network(self):
        token = self.access_token
        network_result_out = []
        # Here need inject from outside
        real_region = self.get_region()
        # real_region = "BOCLOUD_REGION"
        params = {"condition":"getByAz","region":str(real_region),"az":"","vendorType":"VMWARE"}
        target_url = "https://" + self.cluster_ip + ":60008/api/ims/v1/pool/groups/condition?condition=" + str(params)
        headers = {"token": token}
        content = requests.get(target_url, headers=headers, verify=False)
        result_info_out = json.loads(content.content)

        network_result_tmp = result_info_out.get('data').get('networkRelations')

        for network_index in range(len(network_result_tmp)):
            ippool_data = {}
            ippool_tmp = {}

            ippool_tmp['id'] = network_result_tmp[network_index].get("ipPoolId")
            ippool_tmp['name'] = str(network_result_tmp[network_index].get("ipPoolName"))
            ippool_tmp['version'] = str(network_result_tmp[network_index].get("version"))

            portGroupName = network_result_tmp[network_index].get("portGroupName")
            ippool_data['portGroupName'] = str(portGroupName)
            ippool_data['portGroupId'] = network_result_tmp[network_index].get("portGroupId")
            ippool_data['poolGroupId'] = network_result_tmp[network_index].get("poolGroupId")
            ippool_data['pool_detail'] = ippool_tmp

            network_result_out.append(ippool_data)
        return network_result_out


if __name__ == '__main__':
    pass