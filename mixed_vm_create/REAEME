# PLEASE READ THIS USAGE BEFORE START YOUR WORK 

`This Tool Only Tested on :` <font color='red'> [ CMP-V5.5 ]</font>

## step-01: update the target VMs

`!!! Auto_VM_Template.xlsx !!!`

<font color='red'>PLEASE DO NOT RE-NAME THIS FILE</font>

`[OpenStack]`
````    
update your information
````

`[VMware]`
````
update your information
````


## step-02: update the configure file 
`conf/base.cfg`
````
update the content using right information
````
`[System]`
````    
# System information
self_service_ip=<system_ip>
````

`[Manager]`
````
# Manager information
manager_username=<manager_name>
manager_password=<manager_password>
````

`[Tenant]`
````
# Tenant information
tenant_username=<tenant_name>
tenant_password=<tenant_password>
````

`[VM_Type]`
````
# openstack or vmware or openstack,vmware
vm_types=openstack
# if not setting password from external file(excel), use the following as the default
vm_init_password=123456
````

## step-03: Trigger the Task
```
python Main.py
```
