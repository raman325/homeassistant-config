#!/usr/local/bin/python3

import os, hjson, yaml
import sys, inspect
from collections import OrderedDict

# https://github.com/home-assistant/home-assistant/blob/dev/homeassistant/util/yaml/loader.py#L318-L331 for tags to support

# YAML Tag Objects (base object)
class BaseTag(yaml.YAMLObject):
    yaml_tag = u"!"

    def __init__(self, data):
        self.data = data

    def __repr__(self):
        return self.data

    @classmethod
    def from_yaml(cls, loader, node):
        return cls(node.value)

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, u"%s" % data.data)


# YAML tag objects (overwrite yaml_tag for each special case)
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


# generate list of special tag classes by reading this file. This should not have to be changed to support new tag types.
tag_obj_list = [
    value
    for name, value in inspect.getmembers(
        sys.modules[__name__],
        lambda member: inspect.isclass(member) and member.__module__ == __name__,
    )
    if issubclass(value, BaseTag) and name != "BaseTag"
]

# Hjson object hooks to handle special tags
# if value is a special tag, convert it appropriately
def encode_tag(item):
    for o in tag_obj_list:
        if isinstance(item, o):
            return o.yaml_tag + " " + item.data
    return None


# If value is a special tag, convert it appropriately. Also check for null cases
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
        raise TypeError(f"Object of type '{type_name}' is not JSON serializable")


# If value is a special tag, convert it to an object appropriately
def decode_tag(value):
    for o in tag_obj_list:
        tag_len = len(o.yaml_tag)
        if value[0:tag_len] == o.yaml_tag and value[tag_len] != "_":
            return o(value[(tag_len + 1) :])
    return None


# For each key/value pair returned by PyYAML, check if value is a special tag. Build new dictionary based on response.
def decode_ha(pairs, from_list=False):
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
            if isinstance(pair, str) and decode_tag(pair):
                new_pairs.append(decode_tag(pair))
            else:
                new_pairs.append(pair)

    if has_tuple:
        return OrderedDict(new_pairs)
    else:
        return new_pairs


# YAML representer to ensure that nulls don't get added to YAML files
def represent_none(self, _):
    return self.represent_scalar("tag:yaml.org,2002:null", "")


# Return a list of files in `path` that match the extension `ext`. Hacked to ensure that files in hjson/ are not found when searching parent directory
def findFiles(path, ext):
    list = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith("." + ext) and "hjson" not in root:
                list.append(os.path.join(root, file))
    return list


# Convert file extention from fromExt to toExt
def convertFileName(file, fromExt, toExt):
    return file[: (0 - len(fromExt))] + toExt


# Converts YAML files to HJSON. Expects source YAML files to be in the parent directory and target directory to be the current directory
# TODO: Make source and target paths configurable and more generic
def convertYamlToHjson():
    srcFiles = findFiles("..", "yaml")
    for srcFile in srcFiles:
        # hack to get source files one folder below but place destination files in current directory by removing one '.'
        destFile = convertFileName(srcFile, "yaml", "hjson")[1:]

        # create destination path if needed
        basePath = os.path.dirname(destFile)
        if not os.path.exists(basePath):
            os.makedirs(basePath)

        # read file into dict
        with open(srcFile, "r") as src:
            config = yaml.safe_load(src.read())

            # dump object to hjson while encoding tags
            with open(destFile, "w") as dest:
                dest.write(hjson.dumps(config, default=encode_ha, indent=4))
                dest.close()
            src.close()


# Converts HJSON files to YAML. Expects source HJSON files to be in the current directory and target directory to be the parent directory
# TODO: Make source and target paths configurable and more generic
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
                newYAML = yaml.safe_dump(
                    config, default_flow_style=False, sort_keys=False
                )
                if newYAML == "...\n":
                    dest.write("")
                else:
                    dest.write(newYAML)
                dest.close()
            src.close()


# add constructor and representer for every tag that HA uses
for o in tag_obj_list:
    yaml.SafeLoader.add_constructor(o.yaml_tag, o.from_yaml)
    yaml.SafeDumper.add_representer(o, o.to_yaml)

# add null representer so that null values don't get added to YAML files
yaml.SafeDumper.add_representer(type(None), represent_none)

# respect order of dictionary to make output deterministic
yaml.SafeDumper.add_representer(
    OrderedDict,
    lambda self, data: yaml.representer.SafeRepresenter.represent_dict(
        self, data.items()
    ),
)

# convertYamlToHjson()
# convertHjsonToYaml()
