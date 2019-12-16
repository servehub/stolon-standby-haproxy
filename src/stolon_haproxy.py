import json
import os
import sys
import time
from subprocess import check_output, run

import yaml
from jinja2 import Template


def read_config(config_file):
    input_file = open(config_file, 'rb')
    return yaml.load(input_file.read())


def check_env_variables():
    need_env = ['STOLONCTL_CLUSTER_NAME', 'STOLONCTL_STORE_BACKEND', 'STOLONCTL_STORE_ENDPOINTS']
    for ne in need_env:
        if ne not in os.environ:
            sys.stderr.write("Please set {} environment variable".format(ne))
            sys.exit(1)


# get_stolon_servers accepts a JSON from stolonctl utility and returns list of servers available to connect
def get_stolon_servers(stolon_json, fallback_to_master=False):
    server_list = []
    master_address = None

    # Adding support for newer version stolon clusterdata format
    if 'DBs' in stolon_json:
        key = 'DBs'
    else:
        key = 'dbs'

    # get standby's
    for db in stolon_json[key]:
        database = stolon_json[key][db]
        if 'healthy' in database['status'] and 'listenAddress' in database['status']:
            if database['status']['healthy']:
                if database['spec']['role'] == 'standby':
                    server_list.append(database['status']['listenAddress'] + ':' + database['status']['port'])
                else:
                    master_address = database['status']['listenAddress'] + ':' + database['status']['port']

    if server_list == [] and fallback_to_master and master_address:
        server_list.append(master_address)

    return server_list


if __name__ == '__main__':
    print("Starting...")

    if len(sys.argv) != 2:
        print("Usage: %s <yaml config>" % sys.argv[0])
        sys.exit(-1)

    # read config
    config = read_config(sys.argv[1])
    check_env_variables()

    haproxy_template = open('./stolon_haproxy.j2', 'r')
    template = Template(haproxy_template.read())
    haproxy_template.close()

    time.sleep(3)  # await while haproxy started

    while True:
        output = check_output("stolonctl clusterdata read", shell=True)

        try:
            stolon_json = json.loads(output)
        except Exception as e:
            print("Error output from stolonctl: %s" % output)
            time.sleep(config['timeout'])
            continue

        standby_list = get_stolon_servers(stolon_json, config['fallback_to_master'])

        # if np servers to route - skip this iteration and print the error
        if not standby_list:
            print("No available backends!")
            continue

        new_render = template.render(servers=standby_list, frontend_port=config['postgres_haproxy_port'])

        haproxy_config = open(config['postgres_haproxy_config'], 'r')

        if haproxy_config.read() != new_render:
            print("Config changed!")
            haproxy_config.close()
            haproxy_config = open(config['postgres_haproxy_config'], 'w')
            haproxy_config.write(new_render)
            run(config['haproxy_reload_command'], shell=True, check=True)

        haproxy_config.close()
        haproxy_template.close()

        time.sleep(config['timeout'])
