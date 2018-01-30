# Ansible playbooks for Kafka and Zookeeper

## Overview
Ansible is an IT automation tool. It can configure systems, deploy software, and orchestrate more advanced IT tasks such as continuous deployments or zero downtime rolling updates.

Kafka-Ansible is a Kafka cluster deployment tool based on Ansible playbook. You can use the Kafka-Ansible configuration file to set up the cluster topology. Kafka-Ansible enables you to quickly deploy a new Kafka cluster or scale a Kafka cluster.

#### Default Version
|Name|Version|
|:---:|:---:|
|Kafka|2.12-1.0.0|
|Zookeeper|3.4.11|

> Above information in `roles/download/templates/kafka_packages.yml.j2` file.

## Requirements
#### Recommended Hardware
|Name|Cluster Size|Memory|CPU|Disk|
|:---:|:---:|:---:|:---:|:---:|
|Kafka|3+|16G|8+|2+ 1TB|
|Zookeeper|3+|8G|4+|2+ 300G|

#### Install Ansible in the Control Machine

Install Ansible 2.3 or later to your platform:

- PPA source on Ubuntu:

    ```
    sudo add-apt-repository ppa:ansible/ansible
    sudo apt-get update
    sudo apt-get install ansible
    ```

- EPEL source on CentOS:

    ```
    yum install epel-release
    yum update
    yum install ansible
    ```

You can use the `ansible --version` command to see the version information.

For more information, see [Ansible Documentation](http://docs.ansible.com/ansible/intro_installation.html).

## Deploy
#### Download Kafka-Ansible to the Control Machine
Use the following command to download Kafka-Ansible. The `kafka-ansible` directory contains all files you need to get started with Kafka-Ansible.
```
git clone https://github.com/pingcap/thirdparty-ops.git
cd kafka-ansible
```

#### Orchestrate the Kafka cluster
Edit `kafka-ansible/inventory.ini` file. Assume you have 6 servers, and each kafka server have two disks to keep data. We recommend using multiple drives to get good throughput. 
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

- Zookeeper variables:

| Variable | Description |
| ---- | ------- |
| deploy_dir | zookeeper deployment directory |
| myid | [zookeeper myid]((http://zookeeper.apache.org/doc/current/zookeeperAdmin.html#sc_configuration)), it must be unique and range 1-255 |

- Kafka variables:

| Variable | Description |
| ---- | ------- |
| deploy_dir | Kafka deployment directory |
| id | id of the broker, it must be set to a unique integer for each broker |
| kafka_port | Kafka port |
| data_dirs | Kakfa's data directory. If not set, the value is `$deploy_dir/datalog`. If you have multiple drives and data directories or want to customize, set a comma-separated list of one or more directories. |

#### Deploy the Kafka cluster
- Connect to the network and download Kafka and zookeeper binary to the Control Machine, initialize remote host's system environment and modify kernel parameters, install dependent packages.
> Dependent packages: `roles/packages/packagesfiles`
```
ansible-playbook -i inventory.ini prepare.yml
```

- Deploy zookeeper and kafka 
```
ansible-playbook -i inventory.ini deploy.yml
```

- Start zookeeper and kafka
```
ansible-playbook -i inventory.ini start.yml
```

#### Test the Kafka cluster
cd `kafka-ansible` directory, and run following commands:
- Start consumer
```
tools/kafka-console-consumer -brokers="172.17.8.201:9092,172.17.8.202:9092,172.17.8.203:9092" -topic=test
```
- Start producer
```
tools/kafka-console-producer -brokers="172.17.8.201:9092,172.17.8.202:9092,172.17.8.203:9092" -topic=test -value=world -key=hello
```

## Common Tasks
- Stop kafka and zookeeper
``` 
ansible-playbook -i inventory.ini stop.yml
```
> The playbook will stop kafka first, then stop zookeeper.

- Manual start/stop zookeeper/kafka
```
cd $deploy_dir/scripts && ./run_zookeeper.sh start|status|stop
cd $deploy_dir/scripts && ./run_kafka.sh start|stop
```

## Scale zookeeper/kafka
Add host and process information to `inventory.ini` file, then run following commands.
```
ansible-playbook -i inventory.ini prepare.yml --diff
ansible-playbook -i inventory.ini deploy.yml --diff
ansible-playbook -i inventory.ini start.yml --diff
```

## Deployment directory structure
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
│   └── test-1
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
