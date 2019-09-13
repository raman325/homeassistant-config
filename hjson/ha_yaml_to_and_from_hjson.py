#!/usr/local/bin/python3

import os, hjson, yaml
import sys, inspect
from collections import OrderedDict

# https://github.com/home-assistant/home-assistant/blob/dev/homeassistant/util/yaml/loader.py#L318-L331 for tags to support

# YAML Tag Objects
class BaseTag(yaml.YAMLObject):
    yaml_tag = u"!"

    def __init__(self, data):
        self.data = data

    def __repr__(self):
        return self.data

    @classmethod
    def from_yaml(cls, loader, node):
        return BaseTag(node.value)

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, u"%s" % data)


class Secret(BaseTag):
    yaml_tag = u"!secret"


class Include(BaseTag):
    yaml_tag = u"!include"


class EnvVar(BaseTag):
    yaml_tag = u"!env_var"


class IncludeDirList(BaseTag):
    yaml_tag = u"!include_dir_list"


class IncludeDirMergeList(BaseTag):
    yaml_tag = u"!include_dir_merge_list"


class IncludeDirNamed(BaseTag):
    yaml_tag = u"!include_dir_named"


class IncludeDirMergeNamed(BaseTag):
    yaml_tag = u"!include_dir_merge_named"


# generate list of special tag classes
tag_obj_list = [
    value
    for name, value in inspect.getmembers(
        sys.modules[__name__],
        lambda member: inspect.isclass(member) and member.__module__ == __name__,
    )
    if issubclass(value, BaseTag) and name != "BaseTag"
]

# Hjson object hooks to handle special tags
def encode_tag(item):
    for o in tag_obj_list:
        if isinstance(item, o):
            return o.yaml_tag + " " + o.data
    return None


def encode_ha(z):
    tag = encode_tag(z)
    if tag:
        return tag
    elif isinstance(z, None):
        return ""
    elif z is None:
        return ""
    else:
        type_name = z.__class__.__name__
        raise TypeError("Object of type '{type_name}' is not JSON serializable")


def decode_tag(value):
    for o in tag_obj_list:
        tag_len = len(o.yaml_tag)
        if value[0:tag_len] == o.yaml_tag:
            return o(value[(tag_len + 1) :])

    return None


def decode_ha(pairs):
    new_pairs = []
    has_tuple = False
    for pair in pairs:
        if isinstance(pair, tuple):
            has_tuple = True
            key = pair[0]
            value = pair[1]
            if isinstance(value, list):
                new_pairs.append((key, decode_ha(value)))
            elif isinstance(value, str):
                tag_value = decode_tag(value)
                if tag_value:
                    new_pairs.append((key, tag_value))
                elif value == "":
                    new_pairs.append((key, None))
                else:
                    new_pairs.append((key, value))
            else:
                new_pairs.append((key, value))
        else:
            new_pairs.append(pair)

    if has_tuple:
        return OrderedDict(new_pairs)
    else:
        return new_pairs


# YAML representer to ensure that nulls don't get added to YAML files
def represent_none(self, _):
    return self.represent_scalar("tag:yaml.org,2002:null", "")


def findFiles(path, ext):
    list = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith("." + ext) and "hjson" not in root:
                list.append(os.path.join(root, file))
    return list


def convertFileName(file, fromExt, toExt):
    return file[: (0 - len(fromExt))] + toExt


def convertYamltoHjson():
    srcFiles = findFiles("..", "yaml")
    for srcFile in srcFiles:
        # hack to get source files one folder below but place destination files in current directory by removing one '.'
        destFile = convertFileName(srcFile, "yaml", "hjson")[1:]

        # create destination path if needed
        basePath = os.path.dirname(destFile)
        if not os.path.exists(basePath):
            os.makedirs(basePath)

        with open(srcFile, "r") as src:
            config = yaml.load(src.read())

            with open(destFile, "w") as dest:
                dest.write(hjson.dumps(config, default=encode_ha, indent=4))
                dest.close()
            src.close()


def convertHjsonToYaml():
    srcFiles = findFiles(".", "hjson")
    for srcFile in srcFiles:
        # hack to get source files in current directory but place destination files one directory below by adding one '.'
        destFile = "." + convertFileName(srcFile, "hjson", "yaml")
        # destFile = convertFileName(srcFile, "hjson", "yaml")

        # create destination path if needed
        basePath = os.path.dirname(destFile)
        if not os.path.exists(basePath):
            os.makedirs(basePath)

        with open(srcFile, "r") as src:
            config = hjson.loads(src.read(), object_pairs_hook=decode_ha)

            with open(destFile, "w") as dest:
                newYAML = yaml.dump(config, default_flow_style=False, sort_keys=False)
                if newYAML == "...\n":
                    dest.write("")
                else:
                    dest.write(newYAML)
                dest.close()
            src.close()


for o in tag_obj_list:
    yaml.SafeLoader.add_constructor(o.yaml_tag, o.from_yaml)
    yaml.add_representer(o, o.to_yaml)

yaml.add_representer(type(None), represent_none)
yaml.add_representer(
    OrderedDict,
    lambda self, data: yaml.representer.SafeRepresenter.represent_dict(
        self, data.items()
    ),
)

# convertYamlToHjson()
# convertHjsonToYaml()
