<img src="https://notes.sjtu.edu.cn/uploads/upload_e3dda98fba9de52fbd91bfa56c83fbda.png" 
     width="400" 
     height="200" 
     style="object-fit: contain;">


# 上海交大超算队同学在昇腾910B上成功部署DeepSeek满血版模型！附完整部署文档！

## 写在前面

开学第一周，上海交大超算队5位同学在网络信息中心教师和华为工程师的指导下，成功在昇腾910B服务器上部署了DeepSeek满血版模型，整理出一份完整的部署文档~~避坑指南~~。

文档以DeepSeek-V3-int8为例介绍部署流程，R1的部署流程与其类似，仅需在模型权重获取以及服务配置上做相应修改。

变量说明：
- $SERVER_IP: 当前服务器IP
- $OTHER_SERVER_IP：另一台服务器IP
- $NETMASK: 子网掩码
- $IPi:第i个NPU设置的IP
- $GATEWAY_IP: 网关IP 


## 0.基础环境

- 2 * 昇腾Atlas 800T A2 
- openEuler 22.03 TLS
> 单台服务器的NPU最大显存容量为8 * 64 =512 GB，所以需要两台服务器才可以将模型int8权重全部加载。


## 1.获取权重
MODELERS社区提供DeepSeek全系列权重，包括V3的int8量化版本、R1的int8量化版本等，大家可以按需下载到`/data`目录下，详见[DeepSeek模型权重下载](https://modelers.cn/updates/zh/modelers/20250213-deepseek权重下载/)



## 2.添加用户组

``` bash
groupadd HwHiAiUser
useradd -g HwHiAiUser -d /home/HwHiAiUser -m HwHiAiUser -s /bin/bash
```
> 昇腾的驱动安装依赖于这个特殊的用户，需要我们手动创建这个用户，否则驱动的安装会出现错误。
## 3.安装驱动
``` bash
./Ascend-hdk-910b-npu-driver_24.1.0_linux-aarch64.run --full --install-for-all
./Ascend-hdk-910b-npu-firmware_7.5.0.3.220.run --full
```

> 测试安装命令
> npu-smi info # 查看npu使用

## 4.安装docker

可以使用远程安装or离线安装
### 1）离线安装
``` bash
tar -xvzf docker-26.1.4.tgz
chmod 755 -R docker
cp docker/* /usr/bin
chmod 750 docker.service 
cp docker.service /etc/systemd/system/
systemctl daemon-reload
systemctl start docker
# 设置docker服务开机自启动
systemctl enable docker
```
### 2）在线安装
```bash
dnf install net-tools -y
yum makecache
yum install -y make dkms gcc kernel-devel-$(uname -r) docker
systemctl start docker 
```

### 3）载入docker镜像

```bash
docker load -i mindie-2.0.t3.1.tar
```

## 5.NPU网络设置
### 1）配置NPU IP

``` bash
hccn_tool -i 0 -ip -s address $IP0 netmask $NETMASK
hccn_tool -i 1 -ip -s address $IP1 netmask $NETMASK
hccn_tool -i 2 -ip -s address $IP2 netmask $NETMASK
hccn_tool -i 3 -ip -s address $IP3 netmask $NETMASK
hccn_tool -i 4 -ip -s address $IP4 netmask $NETMASK
hccn_tool -i 5 -ip -s address $IP5 netmask $NETMASK
hccn_tool -i 6 -ip -s address $IP6 netmask $NETMASK
hccn_tool -i 7 -ip -s address $IP7 netmask $NETMASK
```
> 查看IP
> hccn_tool -i <id> -ip -g

### 2）配置网关与侦测IP
```bash
hccn_tool -i 0 -gateway -s gateway $GATEWAY_IP
hccn_tool -i 1 -gateway -s gateway $GATEWAY_IP
hccn_tool -i 2 -gateway -s gateway $GATEWAY_IP
hccn_tool -i 3 -gateway -s gateway $GATEWAY_IP
hccn_tool -i 4 -gateway -s gateway $GATEWAY_IP
hccn_tool -i 5 -gateway -s gateway $GATEWAY_IP
hccn_tool -i 6 -gateway -s gateway $GATEWAY_IP
hccn_tool -i 7 -gateway -s gateway $GATEWAY_IP
```

``` bash
hccn_tool -i 0 -netdetect -s address $GATEWAY_IP
hccn_tool -i 1 -netdetect -s address $GATEWAY_IP
hccn_tool -i 2 -netdetect -s address $GATEWAY_IP
hccn_tool -i 3 -netdetect -s address $GATEWAY_IP
hccn_tool -i 4 -netdetect -s address $GATEWAY_IP
hccn_tool -i 5 -netdetect -s address $GATEWAY_IP
hccn_tool -i 6 -netdetect -s address $GATEWAY_IP
hccn_tool -i 7 -netdetect -s address $GATEWAY_IP
```
### 3）检测脚本
``` bash
# 检查物理链接
for i in {0..7}; do hccn_tool -i $i -lldp -g | grep Ifname; done
# 检查链接情况
for i in {0..7}; do hccn_tool -i $i -link -g ; done
# 检查网络健康情况
for i in {0..7}; do hccn_tool -i $i -net_health -g ; done
# 查看侦测ip的配置是否正确
for i in {0..7}; do hccn_tool -i $i -netdetect -g ; done
# 查看网关是否配置正确
for i in {0..7}; do hccn_tool -i $i -gateway -g ; done
# 检查NPU底层tls校验行为一致性，建议全0
for i in {0..7}; do hccn_tool -i $i -tls -g ; done | grep switch
# NPU底层tls校验行为置0操作
for i in {0..7}; do hccn_tool -i $i -tls -s enable 0;done
```
正常情况下上面的每一条命令都会显示8个NPU的相关信息，如果出现DOWN，或者少输出的情况，则需要去检查服务器网络的物理连接。
> 事实上所有的关于NPU的网络配置都会被/etc/hccn.conf中，我们可以通过输出这个文件来获取所有的NPU网络配置信息。

## 6.多机配置
我们需要使用两台昇腾服务器进行部署，其中一台作为主节点，另一台作为从节点，仅有主节点可以接收请求，并将两台服务器的计算结果返回。所以我们需要在两台服务器上完成NPU网络配置信息的交换，并指定主节点。步骤中使用到的两个脚本我们放在了本文末尾。

### 1）通信文件生成
这一步将单个节点以及其NPU的网络配置导出为json文件

``` bash
python3 hccl_tools.py --device_num "[0,8)" --server_ip="$SERVER_IP"
```
### 2）拼接json
将两台服务器的网络配置文件进行合并
``` bash
python3 merge_hccl.py hccl_1.json hccl_2.json
```

### 3）添加container IP
```json
"version": "1.0",
    "server_count": "1",
    "server_list": [
        {
            "server_id": "$SERVER_IP",
+            "container_ip":"$SERVER_IP",
            ...
        },
        {
            "server_id": "$OTHER_SERVER_IP",
+            "container_ip":"$OTHER_SERVER_IP",
            ...
        },
        ]
```

将权重文件和修改后的网络配置json复制到/data目录
修改配置文件json的权限为640
```bash
chmod 640 /data/<yourjson> 
```
### 4）关闭宿主机防火墙

``` bash
systemctl stop firewalld
systemctl disable firewalld
```

## 7. 启动DeepSeek服务
### 1）docker 启动
```bash
docker run -itd --privileged  --name=deepseek-v3-int8 --net=host \
   --shm-size 500g \
   --device=/dev/davinci0 \
   --device=/dev/davinci1 \
   --device=/dev/davinci2 \
   --device=/dev/davinci3 \
   --device=/dev/davinci4 \
   --device=/dev/davinci5 \
   --device=/dev/davinci6 \
   --device=/dev/davinci7 \
   --device=/dev/davinci_manager \
   --device=/dev/hisi_hdc \
   --device=/dev/devmm_svm \
   -v /usr/local/Ascend/driver:/usr/local/Ascend/driver \
   -v /usr/local/Ascend/firmware:/usr/local/Ascend/firmware \
   -v /usr/local/sbin/npu-smi:/usr/local/sbin/npu-smi \
   -v /usr/local/sbin:/usr/local/sbin \
   -v /etc/hccn.conf:/etc/hccn.conf \
   -v /data/:/data/ \
   swr.cn-south-1.myhuaweicloud.com/ascendhub/mindie:2.0.T3.1-800I-A2-py311-openeuler24.03-lts \
   bash
```

进入docker的bash进行后续的工作
```bash
docker exec -it <docker_id> /bin/bash
```

### 2）进入应用目录配置文件
```bash
cd /usr/local/Ascend/mindie/latest/mindie-service/conf
vim config.json
```
按照下述提示修改json文件
``` json5
{
  ...
  "ServerConfig": {
    "ipAddress": "$SERVER_IP", // TODO: change this to main node host ip
    "managementIpAddress": "TODO_MANAGEMENT_IP_ADDRESS", // TODO: change this to main node host ip
    ...
    "httpsEnabled": false, // NOTE: change to false
    ...
    "interCommTLSEnabled": false, // NOTE: change to false
    ...
  },
  "BackendConfig": {
    ...
    "multiNodesInferEnabled" : true, // NOTE: change to true
    "interNodeTLSEnabled" : false, // NOTE: change to false
    "npuDeviceIds": [
      [
        0,
        1,
        2,
        3,
        4,
        5,
        6,
        7
      ]
    ], // NOTE: change to actual device IDs
    ...
    "ModelDeployConfig": {
      "maxSeqLen": 32768, // NOTE: change this 32k
      "maxInputTokenLen": 16384, // NOTE: change this to 16k
      ...
      "ModelConfig": [
        {
          ...
          "modelName": "DeepSeek-V3-int8", // NOTE: change this to V3 or R1
          "modelWeightPath": "/data/DeepSeek-V3-w8a8", // NOTE: change this to model weight path
          "worldSize": 8, // NOTE: change this to device numbers
          ...
        }
      ]
    },
    "ScheduleConfig": {
      ...
      "maxPrefillBatchSize": 10, // NOTE: change this to 10
      "maxPrefillTokens": 32768, // WARN: config this same with BackendConfig.ModelDeployConfig.maxSeqLen
      ...
      "maxIterTimes": 16384, // NOTE: change this to 16k
      ...
    }
  }
}
```




### 3）启动服务

设置环境变量
```bash
export MIES_CONTAINER_IP=<host ip>
export RANKTABLEFILE=/data/hccl_2s_16p.json
export MINDIE_LOG_TO_STDOUT=0
export MINDIE_LLM_LOG_TO_STDOUT=0
export PYTORCH_NPU_ALLOC_CONF=expandable_segments:True
export ATB_WORKSPACE_MEM_ALLOC_ALG_TYPE=3
export ATB_WORKSPACE_MEM_ALLOC_GLOBAL=1
export OMP_NUM_THREADS=1

export HCCL_DETERMINISTIC=false
export HCCL_OP_EXPANSION_MODE="AIV"
export MIES_SERVICE_MONITOR_MODE=1
export NPU_MEMORY_FRACTION=0.99
```
在主节点和从节点上启动
```bash
cd /usr/local/Ascend/mindie/latest/mindie-service/bin
nohup ./mindieservice_daemon > mindie-log 2>&1 &
```

## 部署过程中踩过的坑和建议


### 1）系统安装时，在分区界面卡死
**建议**：应该是OpenEuler的软件bug，我们在自动添加分区-删除home分区后触发了这个问题，后来选择了手动添加分区规避了这个问题。

### 2）出现网络相关的报错
**建议**：检查服务器的防火墙设置，以及config.json中有关TLS和https相关的选项是否设置正确，最后可以检查hccl_2s_16p.json文件是否有拼写错误。

### 3）启动服务后，出现leakage等报错信息

**建议**：这个估计与服务启动时的预运行相关，我们尝试了将调低NPU_MEMORY_FRACTION，但是这样并不能解决问题，最后是通过将maxSeqLen，maxInputTokenLen调低之后解决了这个问题。如果出现了类似的错误也可以考虑将这两个值继续调低。

## 关于上海交大超算队更多信息见官网
SJTU HPC交流群 422403907
![](https://notes.sjtu.edu.cn/uploads/upload_b2f88f09c1a8ac33091b04aa4eaca2e2.jpg)

## 服务测试

### 1）请求测试
```shell=
curl --location 'http://<main_server_ip>:1025/v1/chat/completions?Content-Type=application%2Fjson' \
--header 'Content-Type: application/json' \
--header 'Accept: application/json' \
--data '{
    "model": "DeepSeek-R1-int8",
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": "<think>/n请介绍上海交通大学"
        }
    ],
    "stream": false
}'
```

### 2）性能测试
基于MindIE Benchmark，参考文档[MindIE Benchmark](https://www.hiascend.com/document/detail/zh/mindie/100/mindieservice/servicedev/mindie_service0150.html)

```shell=
pip show mindiebenchmark
pip show mindieclient

chmod 640 /usr/local/lib/python3.11/site-packages/mindiebenchmark/config/config.json
chmod 640 /usr/local/lib/python3.11/site-packages/mindiebenchmark/config/synthetic_config.json
chmod 640 /usr/local/lib/python3.11/site-packages/mindieclient/python/config/config.json

source /usr/local/Ascend/ascend-toolkit/set_env.sh     # CANN
source /usr/local/Ascend/nnal/atb/set_env.sh           # ATB
source /usr/local/Ascend/llm_model/set_env.sh          # ATB Models
source /usr/local/Ascend/mindie/set_env.sh             # MindIE

benchmark --DatasetType "synthetic" --ModelName DeepSeek-V3-int8 --ModelPath "/data/DeepSeek-V3-w8a8/" --TestType vllm_client --Http http://<main_server_ip>:1025 --ManagementHttp http://<main_server_ip>:1026 --Concurrency 80 --MaxOutputLen 2048 --TaskKind stream --Tokenizer True --SyntheticConfigPath /usr/local/lib/python3.11/site-packages/mindiebenchmark/config/synthetic_config.json
```
**synthetic_config.json示例**
这里直接控制了输入输出长度，可以通过Method来更改这个输入输出的分布
```json
{
    "Input": {
        "Method": "uniform",
        "Params": {"MinValue": 1848, "MaxValue": 2244}
    },
    "Output": {
        "Method": "gaussian",
        "Params": {"Mean": 2048, "Var": 204.8, "MinValue": 1848, "MaxValue": 2244}
    },
    "RequestCount": 128
}
```


## 附录

### A. hccl_tools.py

```python=
# Copyright 2020 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""generate hccl config file script"""
import os
import sys
import json
import socket
from argparse import ArgumentParser
from typing import Dict, Any


def parse_args():
    """
    parse args .

    Args:

    Returns:
        args.

    Examples:
        >>> parse_args()
    """
    parser = ArgumentParser(description="mindspore distributed training launch "
                                        "helper utility that will generate hccl"
                                        " config file")
    parser.add_argument("--device_num", type=str, default="[0,8)",
                        help="The number of the Ascend accelerators used. please note that the Ascend accelerators"
                             "used must be continuous, such [0,4) means using four chips "
                             "0，1，2，3; [0,1) means using chip 0; In the most Ascend system, "
                             "the first four chips belong to one group, and the last four chips belong to another one."
                             "Only full chips are allowed to cross-group such as [0,8), other cross-group such as [3,6)"
                             "are prohibited.")
    parser.add_argument("--visible_devices", type=str, default="0,1,2,3,4,5,6,7",
                        help="The visible devices according to the software system. "
                             "Usually used in the virtual system or docker container "
                             "that makes the device_id dismatch logic_id. --device_num uses logic_id. "
                             "For example \"4,5,6,7\" means the system has 4 logic chips "
                             "which are actually the last 4 chips in hardware "
                             "while `--device_num` could only be set to \"[0, 4)\" instead of \"[4, 8)\"")
    parser.add_argument("--server_ip", type=str, default="",
                        help="Set the server_ip manually, to avoid errors in auto detection.")
    args = parser.parse_args()
    return args


def get_host_ip():
    """
    get host ip
    """
    ip = None

    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
    except EOFError:
        pass

    return ip


def main():
    print("start", __file__)
    args = parse_args()

    # visible_devices
    visible_devices = args.visible_devices.split(',')
    print('visible_devices:{}'.format(visible_devices))

    # server_id
    ip = get_host_ip()
    if args.server_ip:
        server_id = args.server_ip
    elif ip:
        server_id = ip
    else:
        raise ValueError("please input server ip!")
    print('server_id:{}'.format(server_id))

    # device_num
    first_num = int(args.device_num[1])
    last_num = int(args.device_num[3])
    if first_num < 0 or last_num > 8:
        raise ValueError("device num {} must be in range [0,8] !".format(args.device_num))
    if first_num > last_num:
        raise ValueError("First num {} of device num {} must less than last num {} !".format(first_num, args.device_num,
                                                                                             last_num))
    if first_num < 4 < last_num:
        if first_num == 0 and last_num == 8:
            pass
        else:
            raise ValueError("device num {} must be in the same group of [0,4] or [4,8] !".format(args.device_num))

    device_num_list = list(range(first_num, last_num))
    print("device_num_list:", device_num_list)

    assert len(visible_devices) >= len(device_num_list)

    # construct hccn_table
    device_ips: Dict[Any, Any] = {}
    try:
        for device_id in device_num_list:
            ret = os.popen("hccn_tool -i %d -ip -g" % device_id).readlines()
            device_ips[str(device_id)] = ret[0].split(":")[1].replace('\n', '')
    except IndexError:
        print("Failed to call hccn_tool, try to read /etc/hccn.conf instead")
        try:
            with open('/etc/hccn.conf', 'r') as fin:
                for hccn_item in fin.readlines():
                    if hccn_item.strip().startswith('address_'):
                        device_id, device_ip = hccn_item.split('=')
                        device_id = device_id.split('_')[1]
                        device_ips[device_id] = device_ip.strip()
        except OSError:
            print("Failed to read /etc/hccn.conf")
            raise SystemError("Failed to find information for hccl")

    hccn_table = {'version': '1.0',
                  'server_count': '1',
                  'server_list': []}
    device_list = []
    rank_id = 0
    for instance_id in device_num_list:
        device_id = visible_devices[instance_id]
        device_ip = device_ips[device_id]
        device = {'device_id': device_id,
                  'device_ip': device_ip,
                  'rank_id': str(rank_id)}
        print('rank_id:{}, device_id:{}, device_ip:{}'.format(rank_id, device_id, device_ip))
        rank_id += 1
        device_list.append(device)
    hccn_table['server_list'].append({
        'server_id': server_id,
        'container_ip': server_id,
        'device': device_list,
        'host_nic_ip': 'reserve'
    })
    hccn_table['status'] = 'completed'

    # save hccn_table to file
    table_path = os.getcwd()
    table_fn = os.path.join(table_path,
                            'hccl_{}p_{}_{}.json'.format(len(device_num_list), "".join(map(str, device_num_list)),
                                                         server_id))
    with open(table_fn, 'w') as table_fp:
        json.dump(hccn_table, table_fp, indent=4)
    sys.stdout.flush()
    print("Completed: hccl file was save in :", table_fn)


if __name__ == "__main__":
    main()
```

### B. merge_hccl.py
```python
# Copyright 2021 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""generate hccl config file script"""
import os
import sys
import json
from argparse import ArgumentParser


def parse_args():
    """
    parse args .

    Args:

    Returns:
        args.

    Examples:
        >>> parse_args()
    """
    parser = ArgumentParser(description="Merge several hccl config json files"
                                        "of single server into one config file of the whole cluster")
    parser.add_argument("file_list", type=str, nargs="+", help="Hccl file lists")
    arg = parser.parse_args()
    return arg

if __name__ == "__main__":
    args = parse_args()
    print(args.file_list)

    server_count = 0
    json_list = []

    for f_name in args.file_list:
        with open(f_name) as f:
            f_json = json.load(f)
            json_list.append(f_json)
            server_count += int(f_json['server_count'])

    hccl_table = {'version': '1.0',
                  'server_count': f'{server_count}',
                  'server_list': []}

    rank_id = 0
    for j in json_list:
        server_list = j['server_list']
        for server in server_list:
            for device in server['device']:
                device['rank_id'] = str(rank_id)
                rank_id += 1
        hccl_table['server_list'].extend(server_list)

    hccl_table['status'] = 'completed'

    table_path = os.getcwd()
    table_name = os.path.join(table_path,
                              'hccl_{}s_{}p.json'.format(server_count, rank_id))
    with open(table_name, 'w') as table_fp:
        json.dump(hccl_table, table_fp, indent=4)
    sys.stdout.flush()
    print("Completed: hccl file was save in :", table_name)