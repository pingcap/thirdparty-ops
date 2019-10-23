#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json
import argparse
import shlex
import subprocess


def main():
    args = parse_args()
    info = table_region_parser()
    _input = raw_input(
        'We will Split region: {}, y/n(default is yes): '.format(
            info[args.table])) or 'y'
    if _input == 'y':
        for _region_id in info[args.table]:
            Split_region(int(_region_id))
    else:
        print('exit')


def table_region_parser():
    args = parse_args()
    httpAPI = "http://{}/tables/{}/{}/regions".format(args.tidb, args.database,
                                                      args.table)

    webContent = subprocess.check_output(["curl", "-sl", httpAPI])
    region_info = json.loads(webContent)
    table_id = region_info['id']
    region_id = []
    index_region_id = []
    Info = {}
    print("Table {} Info:").format(args.table)
    for regions in region_info['record_regions']:
        region_id.append(str(regions["region_id"]))
        ip_info = store_info(regions['leader']['store_id'])
        print(
            "  Region id is {}, leader id is {}, Store id is {} and IP is {}").format(
                regions["region_id"], regions['leader']['id'],
                regions['leader']['store_id'], ip_info)
    Info[args.table] = region_id

    if region_info['indices'] is not None:
        print("\nTable {} Index info:").format(args.table)
        for index_info in region_info['indices']:
            print("Index {} info, id is {}:").format(index_info['name'],
                                                     index_info['id'])
            for index_region in index_info['regions']:
                index_region_id.append(str(index_region['region_id']))
                ip_info = store_info(index_region['leader']['store_id'])
                print(
                    '  Region id is {} and leader id is {}, Store id is {} and IP is {}').format(
                        index_region['region_id'],
                        index_region['leader']['id'],
                        index_region['leader']['store_id'], ip_info)
            Info[index_info['name']] = index_region_id
    return Info


def store_info(store_id):
    args = parse_args()
    _cmd = "../resources/bin/pd-ctl -u http://{} -d store {}".format(args.pd,
                                                                     store_id)
    _sc = subprocess.check_output(shlex.split(_cmd))
    _store_info = json.loads(_sc)
    info = _store_info["store"]["address"]
    return info


def Split_region(region_id):
    args = parse_args()
    _split_cmd = "../resources/bin/pd-ctl -u http://{} -d operator add split-region {} --policy=approximate".format(
        args.pd, region_id)
    try:
        _sc = subprocess.check_output(shlex.split(_split_cmd))
        print("Split Region {} Command executed {}").format(region_id, _sc)
    except:
        print("Split Region {} is faild").format(region_id)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Show the hot region details and splits")
    parser.add_argument("--th",
                        dest="tidb",
                        help="tidb status url, default: 127.0.0.1:10080",
                        default="127.0.0.1:10080")
    parser.add_argument("--ph",
                        dest="pd",
                        help="pd status url, default: 127.0.0.1:2379",
                        default="127.0.0.1:2379")
    parser.add_argument("database", help="database name")
    parser.add_argument("table", help="table name")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    main()
