#!/usr/bin/env python
# coding:utf-8
# Build By LandGrey

import os
import re
import sys
import json
import time
import argparse
import traceback

try:
    reload(sys)
    sys.setdefaultencoding("utf-8")
except:
    pass


def get_files_path(directory, extensions):
    fpss = []
    temp = []
    for root_path, sub_dirs, file_names in os.walk(directory):
        temp.extend([os.path.abspath(os.path.join(root_path, _)) for _ in file_names])
    if extensions == "all":
        return temp
    for t in temp:
        for ext in extensions.split(","):
            if str(t).endswith("." + ext):
                fpss.append(t)
    return fpss


def load_rules(rule_path):
    rule_list = []
    try:
        with open(rule_path, 'r') as f:
            rules_dict = dict(json.loads(f.read(), encoding='utf-8'))
            for code, values in rules_dict.items():
                if code in languages:
                    for items in values:
                        rid = ""
                        rname = ""
                        rrule = []
                        for description, item in dict(items).items():
                            if description == "id":
                                rid = item
                            elif description == "name":
                                rname = item
                            elif description == "rulelist":
                                rrule = item
                        for rule in rrule:
                            op = ""
                            data = ""
                            for key, value in dict(rule).items():
                                if key == "type":
                                    op = value
                                elif key == "data":
                                    data = value
                            rule_list.append((rid, rname, op, data))
    except Exception as e:
        print(u"[-] Exception when load rules: \n")
        traceback.print_exc()
    return rule_list


def rule_match(file_path, content, count):
    global results
    is_find = False
    if os.path.abspath(file_path) not in results.keys():
        results[os.path.abspath(file_path)] = list()

    try:
        for r in rules:
            description = r[1]
            data = r[3]
            if r[2] == "1":
                match = re.findall(data, content, re.I | re.M | re.S)
                if match:
                    is_find = True
                    for m in match:
                        results[os.path.abspath(file_path)].append((os.path.abspath(file_path), count, description, data, m))
            elif r[2] == "2":
                if data in content:
                    is_find = True
                    results[os.path.abspath(file_path)].append((os.path.abspath(file_path), count, description, data))
    except UnicodeError:
        try:
            print(u"Location: {}\nLines   : {}\nError   : Unicode Error\n".format(os.path.abspath(file_path), count))
        except KeyboardInterrupt:
            exit(u"User quit!")
    except KeyboardInterrupt:
        exit(u"User quit!")
    return is_find


def radar(file_path):
    global rules
    count = 0
    is_find = False
    with open(file_path, 'r') as f:
        for line in f.readlines():
            count += 1
            content = line.strip()
            line_find = rule_match(file_path, content, count)
            if line_find:
                is_find = True
    if not is_find:
        with open(file_path, 'r') as f:
            file_content = f.read()
        rule_match(file_path, file_content, u"跨越多行")


if __name__ == "__main__":
    start_time = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", dest='dst', default="./", type=str, help="Directory or Single File Path")
    parser.add_argument("-c", dest='language', default="java", type=str,
                        help="code language rule,such as[common,java], default: [java]")
    parser.add_argument("-e", dest='ext', default="all", type=str,
                        help="file extension, default: [all] or set [jsp,jspx,java]")
    parser.add_argument("-r", dest='rule', default="./rules.json", type=str, help="rules path, default: [rules.json]")
    parser.add_argument("-w", dest='save', nargs='?', metavar='file_path', default='default', const='const',
                        help="set result save path, default:[results_datetime.txt]")
    parser.add_argument("-n", "--no-print", dest='noprint', default="", action="store_true",
                        help="don't print the result")

    if len(sys.argv) == 1:
        sys.argv.append('-h')
    args = parser.parse_args()
    language = args.language
    languages = language.split(',')
    dst = args.dst
    ext = args.ext
    rp = args.rule
    save_path = args.save
    no_print = args.noprint
    if not os.path.isfile(rp):
        exit(u"[-] Invalid rules file path")
    if no_print:
        no_print = True
    else:
        no_print = False
    fps = []
    results = dict()
    rules = load_rules(rp)
    print(u"[+] Load {} [{}] code language rules".format(len(rules), ",".join(languages).upper()))

    if os.path.isdir(dst):
        fps = get_files_path(dst, ext)
    elif os.path.isfile(dst):
        fps.append(dst)
    else:
        exit(u"[-] Invalid directory/file path: {}".format(dst))
    for fp in fps:
        radar(fp)

    hit_files = hit_items = 0
    for key in results.keys():
        if results[key] and len(results[key]) > 1 and results[key][1] != "":
            hit_files += 1
            hit_items += len(results[key])
        else:
            del results[key]
    if save_path == "default":
        save_path = "results_" + str(time.strftime("%H%M%S", time.localtime(time.time()))) + ".txt"
    check_info = u"[+] Check: {:5} files\n".format(len(fps))
    save_info = u"[+] Save : {}\n".format(os.path.abspath(save_path))
    hits_info = u"[+] Hits : {:5} files\n[+] Hits : {:5} items".format(hit_files, hit_items)
    if hit_files == 0:
        exit(u"[-] Find Nothing")
    else:
        with open(save_path, 'w') as f:
            for kv in sorted(results.items(), key=lambda x: len(x[1]), reverse=True):
                key, values = kv[0], kv[1]
                info = u"Location: {}\n".format(key)
                f.write(info)
                if not no_print:
                    sys.stdout.write(info)
                for value in values:
                    if len(value) == 4:
                        info = u"Lines   : {}\nDesc    : {}\nType    : 关键字搜索\nContent : {}\n\n".format(value[1], value[2], value[3]) + "\n"
                        f.write(info)
                        if not no_print:
                            sys.stdout.write(info)
                    elif len(value) == 5:
                        info = u"Lines   : {}\nDesc    : {}\nType    : 正则匹配\nRegex   : {}\nContent : {}\n\n".format(value[1], value[2], value[3], value[4])
                        f.write(info)
                        if not no_print:
                            sys.stdout.write(info)
                if not no_print:
                    sys.stdout.write("\n")
                f.write("\n" + "-"*150 + "\n")
                f.flush()
            f.write(check_info)
            f.write(hits_info)

    sys.stdout.write(check_info)
    sys.stdout.write(hits_info)
    sys.stdout.write("\n" + save_info + "\n")
    sys.stdout.write(u"[+] Ext  :       {}\n[+] Cost : {} seconds".format(ext, str(time.time() - start_time)[:5]))
