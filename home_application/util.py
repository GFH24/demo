from common.log import logger
from blueking.component.shortcuts import get_client_by_user
from home_application.models import Logs
import time
import base64
import pdb


def get_job_instance_id(client, biz_id, ip, command):
    """
    创建快速执行脚本作业
    """
    script_content = base64.b64encode(command)
    kwargs = {
        'bk_biz_id': biz_id,
        'script_content': script_content,
        "script_timeout": 1000,
        "account": "root",
        "script_type": 1,
        "ip_list": [
            {
                "bk_cloud_id": 0,
                "ip": ip
            }
        ],
    }
    resp = client.job.fast_execute_script(**kwargs)

    if resp.get('result'):
        job_instance_id = resp.get('data').get('job_instance_id')
    else:
        job_instance_id = -1
    return resp.get('result'), job_instance_id


def get_job_result(client, biz_id, job_instance_id, ip):
    """
    获取资源利用率数据
    """
    kwargs = {
        'bk_biz_id': biz_id,
        'job_instance_id': job_instance_id,
    }
    is_finish = False
    result_data = []
    while True:
        resp = client.job.get_job_instance_log(**kwargs)
        if resp.get('result'):
            data = resp.get('data')
            logs = ''
            if data[0].get('is_finished'):
                is_finish = True
                logs = data[0]['step_results'][0].get('ip_logs')[0].get('log_content')
                print logs
                break

    result_data.append({
        'ip': ip,
        'data': logs,
    })

    return is_finish, result_data


# 调用配置平台API获取主机信息
def get_hosts(client, biz_id, ip_list):
    # 封装传入接口的参数
    kwargs = {
        "page": {"start": 0, "limit": 5, "sort": "bk_host_id"},
        "ip": {
            "flag": "bk_host_innerip|bk_host_outerip",
            "exact": 1,
            "data": ip_list
        },
        "condition": [
            {
                "bk_obj_id": "host",
                "fields": ["bk_os_name", "bk_host_innerip", "bk_cloud_id"],
                "condition": []
            },
            {"bk_obj_id": "module", "fields": ["bk_module_name"], "condition": []},
            {"bk_obj_id": "set", "fields": ["bk_set_name"], "condition": []},
            {
                "bk_obj_id": "biz",
                "fields": [
                    "default",
                    "bk_biz_id",
                    "bk_biz_name",
                ],
                "condition": [
                    {
                        "field": "bk_biz_id",
                        "operator": "$eq",
                        "value": biz_id  # 设置成业务ID
                    }
                ]
            }
        ]
    }
    # 调用API接口
    resp = client.cc.search_host(**kwargs)

    host_list = []
    i = 0
    if resp.get('result'):
        data = resp.get('data', {}).get('info', {})
        for _d in data:
            ip = _d.get('host', {}).get('bk_host_innerip')
            set_name = _d.get('set', {})[0].get('bk_set_name')
            module_name = _d.get('module', {})[0].get('bk_module_name')
            cloud_name = _d.get('host', {}).get('bk_cloud_id')[0].get('bk_inst_name')
            os_type = _d.get('host', {}).get('bk_os_name')

            # 封装返回的参数
            host = {
                "id": 1,  # 主机ID
                "ip": ip,  # 主机IP
                "os_type": os_type  # 主机操作类型系统
            }
            i = i + 1
            host_list.append(host)

    return host_list
