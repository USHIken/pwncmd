# -*- coding: utf-8 -*-
# vim:fenc=utf-8

import argparse
import glob
import os
import subprocess
import sys
import yaml

GTFOBINS_PATH = "../GTFOBins/_gtfobins/"
GTFOFUNCTIONS_PATH = "../GTFOBins/_data/"

class Color:
    BLACK     = '\033[30m'
    RED       = '\033[31m'
    GREEN     = '\033[32m'
    YELLOW    = '\033[33m'
    BLUE      = '\033[34m'
    PURPLE    = '\033[35m'
    CYAN      = '\033[36m'
    WHITE     = '\033[37m'
    END       = '\033[0m'
    BOLD      = '\033[1m'
    UNDERLINE = '\033[4m'
    INVISIBLE = '\033[08m'
    REVERCE   = '\033[07m'

class PwnCmd:
    def __init__(self, name):
        self.name = name
        self.desc = self._get_yamldata()
    
    def __str__(self):
        return "<Command: {}, Path: {}>".format(self.name, self.path)

    def _get_yamldata(self):
        """
            return yamldata:dict
            yamldata = {
                "functions": [{
                    function_name": [{
                        "description": "description_body",
                        "code": "code_body"
                    }],...
                }]
            }
        """
        with open(GTFOBINS_PATH+self.name+".md") as f:
            data = "\n".join(f.read().split("\n")[1:-2])
        return yaml.load(data, Loader=yaml.SafeLoader)
        
    def _get_cmd_lsal(self):
        """
            return (permission:str, owner:str, group:str)
        """
        get_cmd = ["ls", "-al", self.path]
        ret = subprocess.check_output(get_cmd).decode()[:-1].split(" ")
        return (ret[0], ret[3], ret[5])

    def set_cmd_attr(self, cmd):
        try:
            self.path = subprocess.check_output(["which", cmd]).decode()[:-1]
            self.exist = True
            #self.ls_al = self._get_cmd_lsal()
            #self.perm = self.ls_al[0]
            #self.owner = self.ls_al[1]
            #self.group = self.ls_al[2]
        except subprocess.CalledProcessError: # コマンドが存在しなかったとき
            self.exist = False

def _get_gtfobins_cmdnames():
    cmd_filenames = glob.glob(GTFOBINS_PATH+"*")
    cmd_basenames = [os.path.basename(fn) for fn in cmd_filenames]
    cmd_names = [os.path.splitext(fn)[0] for fn in cmd_basenames]
    return sorted(cmd_names)

def _get_gtfobins_functions():
    with open(GTFOFUNCTIONS_PATH+"functions.yml") as f:
        data = yaml.load(f.read(), Loader=yaml.SafeLoader)
    return sorted(list(data.keys()))

def _make_cmd_list(cmds=None, funcs=None):
    sys.stdout.write("\033[2K\033[G[NOTE] making command list...")
    sys.stdout.flush()

    if cmds:
        cmd_names = cmds
    else:
        cmd_names = _get_gtfobins_cmdnames()

    pwncmd_list = [PwnCmd(cmd_name) for cmd_name in cmd_names]

    if funcs:
        pwncmd_find = []
        for cmd in pwncmd_list:
            cmd_funcs = list(cmd.desc["functions"].keys())
            if all(map(cmd_funcs.__contains__, funcs)):
                pwncmd_find.append(cmd)
        pwncmd_list = pwncmd_find

    cmd_len = len(cmd_names)
    cnt = 0
    tmp = []
    for cmd in pwncmd_list:
        perc = cnt/cmd_len * 100
        sys.stdout.write("\033[2K\033[G[NOTE] making command list...{:.3}%".format(perc))
        sys.stdout.flush()
        cmd.set_cmd_attr(cmd.name)
        if cmd.exist: tmp.append(cmd)
        cnt += 1
    pwncmd_list = tmp
    sys.stdout.write("\033[2K\033[G")
    sys.stdout.flush()
    return pwncmd_list

def _conv_color(string, color):
    return color+string+Color.END

def _print_desc(cmd, func):
    func_desc = cmd.desc["functions"][func] # except: KeyError
    print("{}:".format(_conv_color(func, Color.BOLD)))
    for desc in func_desc:
        try:
            print("  [description] {}".format(desc["description"]))
        except:
            pass
        print("  [code]")
        for code in desc["code"].split("\n"):
            print("  {}".format(_conv_color(code, Color.GREEN)))

def pwncmd_update(args): # GTFOBinsのupdate
    #print(subprocess.check_output("cd", "../GTFOBins/", ";", "git", "pull"))
    pass
    
def pwncmd_list(args):
    pwncmd_list = _make_cmd_list(args.command)
    max_width = max(len(cmd.path) for cmd in pwncmd_list)+4
    for cmd in pwncmd_list:
        funcs = sorted(cmd.desc["functions"].keys())
        print("{:{}}\t{}".format(
            _conv_color(cmd.path, Color.RED),
            max_width,
            ", ".join(funcs)
        ))

def pwncmd_desc(args):
    pwncmd_desc = _make_cmd_list(cmds=args.command)
    #max_width = max(len(_conv_color(cmd.path, Color.RED)) for cmd in pwncmd_desc)

    print("pwnable command description.\n---")
    for cmd in pwncmd_desc:
        print("{}:".format(_conv_color(cmd.path, Color.RED)))
        if args.function:
            for func in args.function:
                try:
                    _print_desc(cmd, func)
                except KeyError:
                    pass
            print("---")
        else:
            funcs = cmd.desc["functions"].keys()
            for func in funcs:
                _print_desc(cmd, func)
            print("---")

def pwncmd_find(args):
    pwncmd_find = _make_cmd_list(funcs=args.function)
    max_width = max(len(_conv_color(cmd.path, Color.RED)) for cmd in pwncmd_find)

    for cmd in pwncmd_find:
        funcs = sorted(cmd.desc["functions"].keys())
        print("{:{}}\t{}".format(
            _conv_color(cmd.path, Color.RED),
            max_width,
            ", ".join(funcs)
        ))

def pwncmd_argparse():
    desc = """
        This command find Unix commands that can be exploited by attacker in your computer.
    """
    help = {
        "list": "show all or specified commands list that available on your computer, see `list -h`.",
        "desc": "show description of specified command[s], see `desc -h`.",
        "find": "find command[s] by specified function[s], see `find -h`.",
        "update": "update commands information.",
        "command": "specify command[s].",
        "function": "specify function[s]."
    }
    funcs = _get_gtfobins_functions()
    parser = argparse.ArgumentParser(
        description=desc,
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers()
    
    parser_list = subparsers.add_parser("list", help=help["list"])
    parser_list.add_argument("-c", dest="command", nargs="+", help=help["command"])
    parser_list.set_defaults(handler=pwncmd_list)

    parser_desc = subparsers.add_parser("desc", help=help["desc"])
    parser_desc.add_argument("-c", dest="command", nargs="+", help=help["command"])
    parser_desc.add_argument("-f", dest="function", nargs="*", choices=funcs, help=help["function"])
    parser_desc.set_defaults(handler=pwncmd_desc)

    parser_find = subparsers.add_parser("find", help=help["find"])
    parser_find.add_argument("-f", dest="function", nargs="*", choices=funcs, help=help["function"])
    parser_find.set_defaults(handler=pwncmd_find)

    parser_update = subparsers.add_parser("update", help=help["update"])
    parser_update.set_defaults(handler=pwncmd_update)
    return parser

if __name__ == "__main__":
    parser = pwncmd_argparse()
    args = parser.parse_args()
    if hasattr(args, 'handler'):
        args.handler(args)
    else:
        parser.print_help()
