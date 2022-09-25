#!/usr/bin/env python3
import argparse
import requests
import configparser
import logging
from netaddr import *
from argparse import RawTextHelpFormatter

parser = argparse.ArgumentParser(description="NordVPN API parser\n"
                                             "The config file must begin with a section named [default]\n"
                                             "The [default] section must contain the api_url, subnet and new_prefix"
                                 , formatter_class=RawTextHelpFormatter)

parser.add_argument("-c", "--config", default="config", help="config file")
parser.add_argument("-l", "--log_level", dest="logLevel", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                    default="DEBUG", help="set the logging level")

parser.add_argument("-o", "--output", dest='output', default="output.log", type=str,
                    help="set logging output file")

args = parser.parse_args()

if args.logLevel:
    logging.basicConfig(level=getattr(logging, args.logLevel),
                        filename=args.output,
                        filemode="a",
                        format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
                        datefmt="%H:%M:%S")

api_url = ''
subnet = ''
new_prefix = ''


def parse_file():
    global api_url
    global subnet
    global new_prefix
    file = args.config
    logging.debug(f"Loading Configuration: {file}")
    config = configparser.ConfigParser()
    config.read(file)
    api_url = config['default']['api_url']
    subnet = config['default']['subnet']
    logging.debug(f"Loaded subnet: {subnet}")
    new_prefix = config['default']['new_prefix']
    return api_url, subnet, new_prefix


def get_subnets(ip):
    addr = IPNetwork(ip)
    subnets = list(addr.subnet(int(new_prefix)))
    logging.debug(f"Generating new prefix size: {new_prefix}")
    logging.info(f"Generated subnets: {subnets}")
    return subnets


def get_ips(url):
    response = requests.get(api_url).json()
    logging.debug(f"Pulling info from {api_url}")
    ips = []
    count = 0
    logging.debug(f"Loaded {len(response)} servers from API")
    while count < len(response):
        ips.append({'host': response[count]['hostname'], 'ip': response[count]['ips'][0]['ip']['ip']})
        count += 1
    return ips


def better_func(ip_address, cidr):
    if IPAddress(ip_address) in IPNetwor(cidr):
        print("match")
    else:
        print("miss")


def search(_subnets, _hosts):
    matching_hosts = []
    not_matching_hosts = []
    subnet_host_mapping = {}

    for _host in _hosts:
        for _subnet in _subnets:
            if IPAddress(_host['ip']) in IPNetwork(str(_subnet)):
                matching_hosts.append(_host)
                if str(_subnet) not in subnet_host_mapping.keys():
                    subnet_host_mapping[str(_subnet)] = []
                subnet_host_mapping[str(_subnet)].append(_host['host'])
                logging.debug(f"Hosts: {_host['ip']}, Subnet: {_subnet}, Status: Match")
            else:
                logging.debug(f"Hosts: {_host['ip']}, Subnet: {_subnet}, Status: Miss")

    for _host in _hosts:
        if _host not in matching_hosts:
            not_matching_hosts.append(_host['host'])

    for _subnet, list_of_hosts in subnet_host_mapping.items():
        logging.info(f"Subnet: {_subnet} Hosts: {list_of_hosts}")
        print(f"Subnet: {_subnet} Hosts: {list_of_hosts}\n")

    print(f"hosts with no subnet match {not_matching_hosts}")
    logging.info(f"hosts with no subnet match {not_matching_hosts}")


def main():
    parse_file()
    print(f"api_url={api_url}\nsubnet={subnet}\nnew_prefix={new_prefix}\n")
    returned_hosts_list = get_ips(api_url)
    print(f"loaded {len(returned_hosts_list)} online servers from the API\n")
    returned_subnets = get_subnets(subnet)
    search(returned_subnets, returned_hosts_list)


if __name__ == '__main__':
    main()
