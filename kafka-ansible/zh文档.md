## ansible部署 Zookeeper/Kafka工具
**这个repo通过ansible来部署 Zookeeper/Kafka**

默认版本

|Name|Version| 
|:---:|:---:|
|Zookeeper|3.4.11|
|Kafka|2.12-1.0.0|

推荐配置
||数量|内存|CPU|硬盘|
|:---:|:---:|:---:|:---:|:---:|
|Zookeeper|3+|16G|8+|2+ 1TB|
|Kafka|3+|8G|4+|2+ 300G|

上述信息在repo的 `roles/download/templates/kafka_packages.yml.j2`file中

目录
------
1. 安装ansible和clone repo
2. 修改inventory.ini文件
3. 准备部署的工作
4. 分发和部署zookeeper/kafka
5. 启动zookeeper/kafka
6. 停止kafka/zookeeper
7. 手动启停zookeeper/kafka
8. 测试zookeeper/kafka功能是否正常
9. 扩容zookeeper/kafka


### 安装ansible和clone repo
- 安装ansible
	- deb `apt-get install ansible -y`
	- rpm `yum install ansible -y`
- Clone repo
	- `git clone https://github.com/jomenxiao/kafka-ansible.git`
- 进入repo目录
	- `cd kafka-ansible`

### 修改inventory.ini文件
- Zookeeper配置信息
	- `myid` Zookeeper唯一id，非重复；范围1-255; 说明文档:[zookeeper office website](http://zookeeper.apache.org/doc/current/zookeeperAdmin.html#sc_configuration)
	- `deploy_dir` 部署目录
	- 一行代表一个进程
	- example: `zk_1 ansible_host=172.17.8.201  deploy_dir=/home/tidb/zk_deploy myid=1`

- Kafka配置信息
	- `kafka_port` 用户连接端口
	- `id` kafka唯一id;非重复
	- 一行代表一个进程
	- kafka的默认存储目录为部署目录下`datalog`
	- 当kafka配置多个存储硬盘时，请配置data_drs；否则留空
	- example: `kafka1 ansible_host=172.17.8.201 deploy_dir=/home/tidb/kafka_deploy1 data_drs=/home/tidb/kafka_deploy1,/tmp/kafka1 kafka_port=9091  id=1`
	
### 准备部署的工作 
- 部署机创建部署目录
- 部署机创建facts
- 部署机下载zookeeper/kafka包
- 节点创建部署目录
- 节点修改系统参数
- 节点安装zookeeper/kafka需要的packages
	- 包名配置文件在repo的`roles/packages/packagesfiles`
	- example: java包

`ansible-playbook -i inventory.ini prepare.yml`

### 分发和部署zookeeper/kafka
- 分发zookeeper/kafka文件
- 修改zookeeper/kafka配置文件
- 生成启停脚本

`ansible-playbook -i inventory.ini deploy.yml`

### 启动zookeeper/kafka
- 首先启动zookeeper
- 启动kafka
 
`ansible-playbook -i inventory.ini start.yml`

### 停止kafka/zookeeper
- 首先停止kafka
- 停止zookeeper
 
`ansible-playbook -i inventory.ini stop.yml`

### 手动启停zookeeper/kafka
- Zookeeper
	- `cd $deploy_dir/scripts && ./run_zookeeper.sh start|status|stop"`
- Kafka
	- `cd $deploy_dir/scripts && ./run_kafka.sh start|stop"`
	
### 测试zookeeper/kafka功能是否正常
- `tools` 目录下有测试文件
	- 启动消费者
	`tools/kafka-console-consumer -brokers="172.17.8.201:9091,172.17.8.201:9092,172.17.8.202:9091,172.17.8.202:9092,172.17.8.203:9091,172.17.8.203:9092" -topic=test`
	- 启动生产者
		`tools/kafka-console-producer -brokers="172.17.8.201:9091,172.17.8.201:9092,172.17.8.202:9091,172.17.8.202:9092,172.17.8.203:9091,172.17.8.203:9092" -topic=test -value=world -key=hello`
		
### 扩容zookeeper/kafka
- 把新加机器和进程加到inventory.ini文件
- `ansible-playbook -i inventory.ini prepare.yml --diff`
- `ansible-playbook -i inventory.ini deploy.yml --diff`
- `ansible-playbook -i inventory.ini start.yml --diff`

节点部署完毕目录结构
------
### Zookeeper
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

### Kafka
```
kafka_deploy1/
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

注意事项
------
- **重启kafka时需要有6秒间隔，因为6秒内，zookeeper会认为是新加进程，导致kafka的id冲突**
