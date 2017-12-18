## Deploy Zookeeper/Kafka with Ansible
**This repo deploy Zookeeper/Kafka with Ansible**

Default Version

|Name|Version| 
|:---:|:---:|
|Zookeeper|3.4.11|
|Kafka|2.12-1.0.0|

recommend hardware
||Cluster Size|Memory|CPU|Disk|
|:---:|:---:|:---:|:---:|:---:|
|Zookeeper|3+|16G|8+|2+ 1TB|
|Kafka|3+|8G|4+|2+ 300G|

Above information in repo file `roles/download/templates/kafka_packages.yml.j2`

Do it
------
1. First of all
2. Modify inventory.ini file
3. Prepare 
4. Deploy zookeeper/kafka
5. Start zookeeper/kafka
6. Stop  kafka/zookeeper
7. Manual start/stop zookeeper/kafka
8. Test
9. Expansion zookeeper/kafka


### First of all
- Install ansible
	- deb `apt-get install ansible -y`
	- rpm `yum install ansible -y`
- Clone repo
	- `git clone https://github.com/jomenxiao/kafka-ansible.git`
- Change directoy
	- `cd kafka-ansible`

### Modify inventory.ini file
- Zookeeper informations
	- `myid` is unique integer,range 1-255; documents:[zookeeper office website](http://zookeeper.apache.org/doc/current/zookeeperAdmin.html#sc_configuration)
	- `deploy_dir` deployment directory
	- one line mean one process
	- example: `zk_1 ansible_host=172.17.8.201  deploy_dir=/home/tidb/zk_deploy myid=1`

- Kafka informations
	- `kafka_port` for client connect 
	- `id` is the kafka's broker id. It must be set to a unique integer for each broker.
	- one line mean one process
	- kakfa's default data log directory is `$deploy_dir/datalog`
	- more than one disk to stroge kafka's data; please setting `data_drs`
	- example: `kafka1 ansible_host=172.17.8.201 deploy_dir=/home/tidb/kafka_deploy1 data_drs=/home/tidb/kafka_deploy1,/tmp/kafka1 kafka_port=9091  id=1`
	
### Prepare 
- Localhost create some deployment directory
- Localhost create ansible's facts 
- Localhost download zookeeper/kafka file
- Remote host create deployment directory 
- Remote host modify kernel params
- Remote host install necessary packages
	- setting in repo directory `roles/packages/packagesfiles`
	- example: java package

`ansible-playbook -i inventory.ini prepare.yml`

### Deploy zookeeper/kafka
- Copy zookeeper/kafka deployment packages to remote host
- Modify zookeeper/kafka's configure file 
- Generate zookeeper/kafka start/stop scripts

`ansible-playbook -i inventory.ini deploy.yml`

### Start zookeeper/kafka
- First start zookeeper
- Start kafka
 
`ansible-playbook -i inventory.ini start.yml`

### Stop kafka/zookeeper
- Firest stop kafka
- Stop zookeeper
 
`ansible-playbook -i inventory.ini stop.yml`

### Manual start/stop zookeeper/kafka
- Zookeeper
	- `cd $deploy_dir/scripts && ./run_zookeeper.sh start|status|stop"`
- Kafka
	- `cd $deploy_dir/scripts && ./run_kafka.sh start|stop"`
	
### Test
- Ansible `tools` directory
	- Start consumer
	`tools/kafka-console-consumer -brokers="172.17.8.201:9091,172.17.8.201:9092,172.17.8.202:9091,172.17.8.202:9092,172.17.8.203:9091,172.17.8.203:9092" -topic=test`
	- Start producer
		`tools/kafka-console-producer -brokers="172.17.8.201:9091,172.17.8.201:9092,172.17.8.202:9091,172.17.8.202:9092,172.17.8.203:9091,172.17.8.203:9092" -topic=test -value=world -key=hello`
		
### Scale zookeeper/kafka
- Add host/process informations to inventory.ini file
- `ansible-playbook -i inventory.ini prepare.yml --diff`
- `ansible-playbook -i inventory.ini deploy.yml --diff`
- `ansible-playbook -i inventory.ini start.yml --diff`

Deploy directory structure
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

Attentions
------
- **Restart kafka need 6 seconds interval**
