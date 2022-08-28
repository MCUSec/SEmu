#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import argparse
import datetime
import stat
import random
import struct
import configparser
from jinja2 import Environment, FileSystemLoader, StrictUndefined

testcase_length = 8;
DEFAULT_TEMPLATES_DIR = os.getcwd()
def read_config(cfg_f, nlpfilename, firmwarename, debug):
    global testcase_length
    if not os.path.isfile(cfg_f):
        sys.exit("Cannot find the specified configuration file: %s" % cfg_f)
    parser = configparser.SafeConfigParser()
    parser.read(cfg_f)

    # Prepare the target firmware lua configuration
    config = {
        'loglevel': "debug" if debug else "warn",
        'creation_time': str(datetime.datetime.now()),
        'firmware_name': firmwarename,
        'pwd': str(os.getcwd()),
        'klee_debug': "true",
        'nlp_file_name': nlpfilename,
    }

    # MEM
    config['rom'] = parser.get("MEM_Config","rom").split( )
    config['ram'] = parser.get("MEM_Config","ram").split( )
    config['vtor'] = int(parser.get("MEM_Config","vtor"), 16)


    # Invlid states detection
    config['bb_inv1'] = parser.getint("INV_Config","bb_inv1")
    config['bb_inv2'] = parser.getint("INV_Config","bb_inv2")
    config['kill_points'] = parser.get("INV_Config","kill_points").split()
    config['alive_points'] = parser.get("INV_Config","alive_points").split()

    # IRQ
    config['disable_irqs'] = parser.get("IRQ_Config","disable_irqs").split()
    config['disable_systick'] = parser.get("IRQ_Config","disable_systick")
    if config['disable_systick'] == "true":
        config['systick_begin_point'] = parser.get("IRQ_Config","systick_begin_point")

	# NLP Peripheral Model
    config['nlp_mmio_range'] = parser.get("NLP_Config","nlp_mmio_range").split( )
    config['fork_point'] = int(parser.get("NLP_Config","fork_point"), 16)

    return config


def _init_template_env(templates_dir=None):
    """
    Initialize the jinja2 templating environment using the templates in the
    given directory.
    """
    if not templates_dir:
        templates_dir = DEFAULT_TEMPLATES_DIR

    env = Environment(loader=FileSystemLoader(templates_dir),
                      autoescape=False, undefined=StrictUndefined)

    return env

def render_template(context, template, output_path, templates_dir=None,
                    executable=False):
    """
    Renders the ``template`` template with the given ``context``. The result is
    returned as a string and written to ``output_path`` (if specified).
    A directory containing the Jinja templates can optionally be specified.
    """
    env = _init_template_env(templates_dir)

    rendered_data = env.get_template(template).render(context)

    # Remove trailing spaces
    cleaned_lines = []
    for line in rendered_data.splitlines():
        cleaned_lines.append(line.rstrip())
    rendered_data = '\n'.join(cleaned_lines)

    if output_path:
        with open(output_path, 'w') as f:
            f.write(rendered_data)

        if executable:
            st = os.stat(output_path)
            os.chmod(output_path, st.st_mode | stat.S_IEXEC)

    return rendered_data

def main(argv):
    global testcase_length
    parser = argparse.ArgumentParser()
    parser.add_argument("firmware", type=str,
                            help="Configure the firmware name will run on SEmu")
    parser.add_argument("config", type=str, default="",
                            help="Configure the configuration file used for Knowledge Base extration. e.g., SEmu.cfg")
    parser.add_argument("--debug", action="store_true",
                            help="In debug mode, SEmu will output huge log, please ensure you have enough space (e.g., more than 100M)")	
    parser.add_argument("-rule", "--nlpfilename", type=str, default="",
                            help="Configure the C-A Rule filename used for SEmu")

    args = parser.parse_args()

    if args.config != "":
        args.config = os.path.abspath(args.config)
    else:
        sys.exit("Please set .cfg configuration file!")

    if args.nlpfilename == "":
        sys.exit("Please set .txt C-A rule filename!")

    if args.debug:
        print("SEmu will dignose %s with debug level log" % (args.firmware))
    else:
        print("SEmu will dignose %s with warning level log" % (args.firmware))

    config = read_config(args.config, args.nlpfilename, args.firmware, args.debug)
    render_template(config, "SEmu-config-template.lua", "SEmu-config.lua")

    launch = {
        'creation_time': str(datetime.datetime.now()),
        'qemu_arch':"arm",
        'memory':"2M",
        'firmware': args.firmware,
        'root_dir': os.environ['SEmuDIR'],
    }
    render_template(launch, "launch-SEmu-template.sh", "launch-SEmu.sh", executable=True)


if __name__ == "__main__":
    # sys.argv[1:]为要处理的参数列表，sys.argv[0]为脚本名，所以用sys.argv[1:]过滤掉脚本名
    main(sys.argv[1:])
