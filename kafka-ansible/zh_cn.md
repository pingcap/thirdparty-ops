# Ansible playbooks for Kafka and Zookeeper

## 概述
Ansible 是一款自动化运维工具。它可以用来配置系统，部署软件，或者编排高级的 IT 任务，例如滚动更新。

Kafka-Ansible 是基于 Ansible playbook 功能编写的集群部署工具。你可以通过 Kafka-Ansible 配置文件来设置集群拓扑。使用 Kafka-Ansible 可以快速部署一个新的 Kafka 集群或扩容集群。

#### 默认版本
|名字|版本|
|:---:|:---:|
|Kafka|2.12-1.0.0|
|Zookeeper|3.4.11|

> 以上信息可以查看 `kafka-ansible/roles/download/templates/kafka_packages.yml.j2` 文件。

## 需求
#### 推荐配置

|名字|数量|内存|CPU|硬盘|
|:---:|:---:|:---:|:---:|:---:|
|Kafka|3+|32G+|16+|1TB SAS/SSD * 2|
|Zookeeper|3+|8G+|4+|300G SAS/SSD|

> Kafka：推荐使用多块数据盘，可获取更好的吞吐。

#### 在中控机器上安装 Ansible 及其依赖

请按以下方式在 CentOS 7 系统的中控机上安装 Ansible。 通过 epel 源安装， 会自动安装 Ansible 相关依赖(如 Jinja2==2.7.2 MarkupSafe==0.11)，安装完成后，可通过 ansible --version 查看版本。

> 请务必确认是 Ansible 2.4 及以上版本，否则会有兼容问题。

  ```bash
  # yum install epel-release
  # yum install ansible curl
  # ansible --version
    ansible 2.4.2.0
  ```

其他系统可参考 [官方手册](http://docs.ansible.com/ansible/intro_installation.html)安装 Ansible。

## 部署
#### 下载 Kafka-Ansible 到中控机
使用以下命令下载 Kafka-Ansible。

```
git clone https://github.com/pingcap/thirdparty-ops.git
cd kafka-ansible
```

#### 编排 Kafka 集群
编辑 `kafka-ansible/inventory.ini` 文件。假设你有 6 台服务器，每台服务器有两块磁盘用于保存数据。

```
[zookeeper_servers]
zk1 ansible_host=172.17.8.204  deploy_dir=/home/tidb/zk_deploy  myid=1
zk2 ansible_host=172.17.8.205  deploy_dir=/home/tidb/zk_deploy  myid=2
zk3 ansible_host=172.17.8.206  deploy_dir=/home/tidb/zk_deploy  myid=3

[kafka_servers]
kafka1 ansible_host=172.17.8.201 deploy_dir=/home/tidb/kafka_deploy data_dirs=/data1/kafka_data,/data2/kafka_data kafka_port=9092  id=1
kafka2 ansible_host=172.17.8.202 deploy_dir=/home/tidb/kafka_deploy data_dirs=/data1/kafka_data,/data2/kafka_data kafka_port=9092  id=2
kafka3 ansible_host=172.17.8.203 deploy_dir=/home/tidb/kafka_deploy data_dirs=/data1/kafka_data,/data2/kafka_data kafka_port=9092  id=3
```

- Zookeeper 变量:

| 变量 | 描述 |
| ---- | ------- |
| deploy_dir | zookeeper 部署目录 |
| myid | [zookeeper myid]((http://zookeeper.apache.org/doc/current/zookeeperAdmin.html#sc_configuration)), 唯一，范围为 1-255 |

- Kafka 变量:

| Variable | Description |
| ---- | ------- |
| deploy_dir | Kafka 部署目录 |
| id | broker id, 每个 broker 需设置为一个唯一的整数值 |
| kafka_port | Kafka 端口 |
| data_dirs | Kakfa 数据目录。如果未设置，其值为 `$deploy_dir/datalog`。如果你有多块磁盘和数据目录或希望自定义该目录，可以设置逗号隔开的一个或多个目录。 |

#### 部署  Kafka 集群
- 连接外网下载 Kafka 和 zookeeper 安装包到中控机 

> 依赖包可查看  `kafka-ansible/roles/packages/packagesfiles` 文件。

```
ansible-playbook -i inventory.ini local_prepare.yml
```

- 初始化系统环境，修改内核参数

```
ansible-playbook -i inventory.ini bootstrap.yml
```

- 安装依赖包，部署 zookeeper 和 kafka

```
ansible-playbook -i inventory.ini deploy.yml
```

- 启动 zookeeper 和 kafka 服务

```
ansible-playbook -i inventory.ini start.yml
```

#### 测试 Kafka 集群
进行 `kafka-ansible` 文件夹, 执行以下命令：
- 启动 consumer
```
tools/kafka-console-consumer -brokers="172.17.8.201:9092,172.17.8.202:9092,172.17.8.203:9092" -topic=test
```
- 启动 producer
```
tools/kafka-console-producer -brokers="172.17.8.201:9092,172.17.8.202:9092,172.17.8.203:9092" -topic=test -value=world -key=hello
```

## 常见任务
- 关闭 kafka 和 zookeeper 服务
``` 
ansible-playbook -i inventory.ini stop.yml
```
> playbook 会先关闭 kafka 服务, 然后关闭 zookeeper。

- 人工启动/关闭 zookeeper/kafka 服务
```
cd $deploy_dir/scripts && ./run_zookeeper.sh start|status|stop
cd $deploy_dir/scripts && ./run_kafka.sh start|stop
```

## 扩容 zookeeper/kafka 服务
添加主机及进程信息到 `inventory.ini` 文件, 然后执行以下命令：
```
ansible-playbook -i inventory.ini prepare.yml --diff
ansible-playbook -i inventory.ini deploy.yml --diff
ansible-playbook -i inventory.ini start.yml --diff
```

## 部署目录结构
#### Zookeeper
```
zk_deploy/
├── backup
├── data
│   ├── myid
│   ├── version-2
│   └── zookeeper_server.pid
├── datalog
│   └── version-2
├── log
│   └── zookeeper.out
├── package
│   └── zookeeper-3.4.11
├── scripts
│   └── run_zookeeper.sh
└── zk -> /home/tidb/zk_deploy/package/zookeeper-3.4.11
```

#### Kafka
```
kafka_deploy/
├── backup
├── datalog
│   ├── cleaner-offset-checkpoint
│   ├── __consumer_offsets-2
│   ├── log-start-offset-checkpoint
│   ├── meta.properties
│   ├── recovery-point-offset-checkpoint
│   ├── replication-offset-checkpoint
│   └── test-1.
├── kafka -> /home/tidb/kafka_deploy1/package/kafka_2.12-1.0.0
├── log
│   ├── controller.log
│   ├── kafka-authorizer.log
│   ├── kafka-request.log
│   ├── kafkaServer-gc.log.0.current
│   ├── kafkaServer.out
│   ├── log-cleaner.log
│   ├── server.log
│   └── state-change.log
├── package
│   └── kafka_2.12-1.0.0
└── scripts
    └── run_kafka.sh
```
