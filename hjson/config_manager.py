#!/usr/local/bin/python3

import os, hjson, yaml
from collections import OrderedDict

# https://github.com/home-assistant/home-assistant/blob/dev/homeassistant/util/yaml.py#L319-L331 for tags to support

# YAML Objects
class Secret(yaml.YAMLObject):
    yaml_tag = u'!secret'

    def __init__(self, secret):
        self.secret = secret

    def __repr__(self):
        return self.secret

    @classmethod
    def from_yaml(cls, loader, node):
        return Secret(node.value)

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, u'%s' % data)

class Include(yaml.YAMLObject):
    yaml_tag = u'!include'

    def __init__(self, include):
        self.include = include

    def __repr__(self):
        return self.include

    @classmethod
    def from_yaml(cls, loader, node):
        return Include(node.value)

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, u'%s' % data)

# Hjson object hooks to handle tags
def encode_ha(z):
    if isinstance(z, Secret):
        return "!secret " + z.secret
    elif isinstance(z, Include):
        return "!include " + z.include
    elif isinstance(z, None):
        return ""
    elif z is None:
        return ""
    else:
        type_name = z.__class__.__name__
        raise TypeError("Object of type '{type_name}' is not JSON serializable")

def decode_ha(item):
    for key in item:
        if isinstance(item[key], str):
            if item[key][0:7] == "!secret":
                item[key] = Secret(item[key][8:])
            elif item[key][0:8] == "!include":
                item[key] = Include(item[key][9:])
            elif item == "":
                item[key] = None
    return item

# YAML representer to ensure that nulls don't get added to YAML files
def represent_none(self, _):
    return self.represent_scalar('tag:yaml.org,2002:null', '')

def findFiles(path, ext):
    list = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith("." + ext) and "hjson" not in root:
                list.append(os.path.join(root, file))
    return list

def convertFileName(file, fromExt, toExt):
    return file[:(0-len(fromExt))] + toExt

def convertYamltoHjson():
    srcFiles = findFiles("..", "yaml")
    for srcFile in srcFiles:
        # hack to get source files one folder below but place destination files in current directory by removing one '.'
        destFile = convertFileName(srcFile, "yaml", "hjson")[1:]

        #create destination path if needed
        basePath = os.path.dirname(destFile)
        if not os.path.exists(basePath):
            os.makedirs(basePath)

        with open(srcFile, 'r') as src:
            config = yaml.load(src.read())

            with open(destFile, 'w') as dest:
                dest.write(hjson.dumps(config, default=encode_ha, indent=4))
                dest.close()
            src.close()

def convertHjsonToYaml():
    srcFiles = findFiles(".", "hjson")
    for srcFile in srcFiles:
        # hack to get source files in current directory but place destination files one directory below by adding one '.'
        destFile = "." + convertFileName(srcFile, "hjson", "yaml")
        # destFile = convertFileName(srcFile, "hjson", "yaml")
        
        #create destination path if needed
        basePath = os.path.dirname(destFile)
        if not os.path.exists(basePath):
            os.makedirs(basePath)

        with open(srcFile, 'r') as src:
            config = hjson.loads(src.read(), object_hook=decode_ha, object_pairs_hook=OrderedDict)

            with open(destFile, 'w') as dest:
                newYAML = yaml.dump(config, default_flow_style=False, sort_keys=False)
                if newYAML == "...\n":
                    dest.write("")
                else:
                    dest.write(newYAML)
                dest.close()
            src.close()

yaml.SafeLoader.add_constructor('!secret', Secret.from_yaml)
yaml.SafeLoader.add_constructor('!include', Include.from_yaml)
yaml.add_representer(Secret, Secret.to_yaml)
yaml.add_representer(Include, Include.to_yaml)
yaml.add_representer(type(None), represent_none)
yaml.add_representer(OrderedDict, lambda self, data: yaml.representer.SafeRepresenter.represent_dict(self, data.items()))

# convertYamlToHjson()
# convertHjsonToYaml()
