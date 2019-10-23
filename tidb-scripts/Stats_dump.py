#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json
import argparse
import pymysql
import subprocess
import os
import time
import tarfile
import shutil


def main():
    args = parse_args()
    if args.database is None and args.tables is None:
        info = parser_all_info()
    elif args.tables is None and args.database is not None:
        info = parser_database_info(args.database)
    elif args.database is None and args.tables is not None:
        info = parser_table_info(args.tables)
    else:
        print("Please enter the correct library or table name！")

    download_dir = time.strftime("%Y%m%d-%H%M%S", time.localtime()) + "-stats"
    dir_stats = os.path.join(download_dir, 'stats')
    if not os.path.isdir(download_dir):
        os.makedirs(download_dir)
    if not os.path.isdir(dir_stats):
        os.makedirs(dir_stats)

    file_name = os.path.join(download_dir, 'schema.sql')
    content = parser_version()
    comments = "TiDB Version"
    schema_file(content, comments, file_name)
    for database_name in info:
        content = get_databas_schema(database_name) + ";\nuse {};".format(
            database_name)
        comments = "Database {} schema".format(database_name)
        schema_file(content, comments, file_name)
        for table_name in info[database_name]:
            stats_name = os.path.join(
                dir_stats, "{}.{}.json".format(database_name, table_name))
            stats_name_tmp = os.path.join(
                'stats', "{}.{}.json".format(database_name, table_name))
            comments = "Table {} schema".format(table_name)
            content = get_table_schema(
                database_name,
                table_name) + ";\nLOAD STATS '{}';".format(stats_name_tmp)
            schema_file(content, comments, file_name)
            content = parser_stats(database_name, table_name)
            stats_file(content, stats_name)
    try:
        with tarfile.open("{}.tar.gz".format(download_dir), "w:gz") as tar:
            tar.add(download_dir, arcname=os.path.basename(download_dir))
        shutil.rmtree(download_dir)
        print(
            "Directory {} was compressed successfully, and directory {} was deleted~".format(
                download_dir, download_dir))
    except:
        print("Compression failure!")


def parser_stats(database_name, table_name):
    args = parse_args()
    httpAPI = "http://{}/stats/dump/{}/{}".format(args.tidb, database_name,
                                                  table_name)
    try:
        webContent = subprocess.check_output(["curl", "-sl", httpAPI])
        webContent = json.loads(webContent)
    except:
        print("Failed to obtain table {}.{} statistics".format(database_name,
                                                               table_name))

    return webContent


def stats_file(content, file_name):
    try:
        with open(file_name, 'a+') as f:
            json.dump(content, f)
        print(u"File {} written successfully~".format(file_name))
    except:
        print(u"Write {} error!".format(file_name))


def schema_file(content, comments, file_name):
    try:
        with open(file_name, 'a+') as f:
            f.write(u"-- {} \n".format(comments))
            f.write(u"{} \n\n".format(content))
        print(u"Write {} Successful~".format(comments))
    except:
        print("Write error: {}!".format(content))


def get_table_schema(database_name, table_name):
    content = mysql_execute("use {};".format(database_name),
                            "show create table {};".format(table_name))
    content = content[0]['Create Table']

    return content


def get_databas_schema(database_name):
    content = mysql_execute("show create database {}".format(database_name))
    content = content[0]['Create Database']

    return content


def parser_version():
    content = mysql_execute("select tidb_version()")
    content = content[0]["tidb_version()"]
    content = "/*\n" + content + "\n*/"

    return content


def parser_table_info(tables):
    info = {}
    for content in tables.split(','):
        database_name = content.split('.')[0]
        table_name = content.split('.')[1]
        table = list(info.get(database_name, ''))
        table.append(table_name)
        info[database_name] = table

    return info


def parser_database_info(database_name):
    info = {}
    for database_name in database_name.split(','):
        content = mysql_execute("use {};".format(database_name), "show tables;")
        tables = []
        for table in content:
            table_name = table["Tables_in_{}".format(database_name)]
            tables.append(table_name)
        info[database_name] = tables

    return info


def parser_all_info():
    info = {}
    content = mysql_execute('show databases;')
    for database in content:
        database_name = database["Database"]
        if database_name not in ["INFORMATION_SCHEMA", "PERFORMANCE_SCHEMA",
                                 "mysql", "default"]:
            content = mysql_execute("use {};".format(database_name),
                                    "show tables;")
            tables = []
            for table in content:
                table_name = table["Tables_in_{}".format(database_name)]
                tables.append(table_name)
            info[database_name] = tables
        else:
            print(
                "Backing up INFORMATION_SCHEMA,PERFORMANCE_SCHEMA,mysql,default libraries is not supported!")

    return info


def mysql_execute(*_sql):
    args = parse_args()
    host = args.mysql.split(':', 1)[0]
    port = int(args.mysql.split(':', 1)[1])
    try:
        connection = pymysql.connect(host=host,
                                     user=args.user,
                                     password=args.password,
                                     port=port,
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)
    except:
        print("Connect Database is failed~")

    try:
        with connection.cursor() as cursor:
            for sql in _sql:
                cursor.execute(sql)
            content = cursor.fetchall()
            connection.commit()
    except:
        print(
            "SQL {} execution failed~ \n Please check table or database exists or not!".format(
                _sql))

    finally:
        cursor.close()
        connection.close()

    return content


def parse_args():
    parser = argparse.ArgumentParser(
        description="Export statistics and table structures")
    parser.add_argument("-tu",
                        dest="tidb",
                        help="tidb status url, default: 127.0.0.1:10080",
                        default="127.0.0.1:10080")
    parser.add_argument(
        "-H",
        dest="mysql",
        help="Database address and port, default: 127.0.0.1:4000",
        default="127.0.0.1:4000")
    parser.add_argument("-u",
                        dest="user",
                        help="Database account, default: root",
                        default="root")
    parser.add_argument("-p",
                        dest="password",
                        help="Database password, default: null",
                        default="")
    parser.add_argument(
        "-d",
        dest="database",
        help="Database name, for example: test,test1, default: None",
        default=None)
    parser.add_argument(
        "-t",
        dest="tables",
        help=
        "Table name (database.table), for example: test.test,test.test2, default: None",
        default=None)
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    main()
