#!/bin/python
# src location in 3rd nfs
source_location="/tmp/dev/src"

# target location in 3rd 
dest_location="/tmp/dev/target"

# real cluster ip
cluster_api="10.171.51.171"

# access token for k8s
access_token="eyJhbGciOiJSUzI1NiIsImtpZCI6ImVSSUpzN3pmOWxMeDZUVFZWb05mbjJQYVBMNzNPZUZTbmlhVEVzWFBpZW8ifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlLXN5c3RlbSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJtYW5hZ2VtZW50LWFkbWluLXRva2VuLXI0bjZnIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQubmFtZSI6Im1hbmFnZW1lbnQtYWRtaW4iLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC51aWQiOiI0MmQwNTg2MC0wYjNmLTQzN2QtOTZlZS05Mzk0YjQxMmM4ZDMiLCJzdWIiOiJzeXN0ZW06c2VydmljZWFjY291bnQ6a3ViZS1zeXN0ZW06bWFuYWdlbWVudC1hZG1pbiJ9.r6eGO83omHlKCODgGHi6XLDue2BsnKLxl7AEcou56PLSJGIir133XzG6hAtOymBhM23r9WxCv7cQ2OeNpmTVRS_Ij51PDRbzGan93xdNmE-19dTawSbQopKJXNIh7VVhHwidPbT9OpYfawVJnDjff9HXREHPNFEZ3Fqc7Ja7kIoCQTKJyURlk091byRMO_c4o_m8kl_E_voXWC5D3GYur4CaOScsKdkMFWiYSqHqchNP0ZGEFMj4wlSXHi7MKnxE_IwuiYllOL0cU6ddvjD4BSfLHn4hd440z53bXPzNym16Z7LR7-mKEildanco6QBY5DXPlRiBp_jhQPFypb38iQ"

import os, requests, json
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# 
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def set_pvc_with_nfs(access_token, source_location, dest_location):
    target_url = "https://"+cluster_api+":6443/api/v1/persistentvolumeclaims"
    headers = {'Authorization': 'Bearer ' + access_token}
    content = requests.get(target_url, headers=headers, verify=False)
    # 
    pvc_out = json.loads(content.content)
    value = pvc_out.get('items')
    #
    for index in range(0, len(value)):
        namespace = value[index].get('metadata').get('namespace')
        pvc_name = value[index].get('metadata').get('name')
        volumeName = value[index].get('spec').get('volumeName')
        #print("Namespace: "+namespace + " PvcName: "+ pvc_name + " volumeName: "+volumeName)
        # make up full link name
        link_name = namespace + "_" + pvc_name + "_" + volumeName
        # create related linked file [0/1]
        if not os.path.exists(dest_location):
            os.mkdir(dest_location)
        # [1/1] ln -s src des , directory tree is subname in full name
        nfs_files=os.listdir(source_location)
        for index in nfs_files:
		# check pvc match end storage
		if volumeName in index:
        		target_path=os.path.join(source_location, index)
    			if os.path.isdir(target_path):
        			cmd = "ln -s "+target_path  + " "+ dest_location + "/" + link_name
        			os.system(cmd)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", help="Kubernetes Access Token", required=True, type=str)
    parser.add_argument("--dest", help="Link File Target Location", required=True, type=str)
    args = parser.parse_args()
    if args.token and args.dest:
        print("Access Kubernetes [1/2]")
	set_pvc_with_nfs(access_token, source_location, dest_location)
        print("Create Link : PASS [2/2]")
    else:
        print('''usage: k8s_pvc.py [-h] [--token TOKEN]
    optional arguments:
        -h, --help     show this help message and exit
        --token TOKEN  Kubernetes Access Token
        --dest DEST Link File Target Location
''')
