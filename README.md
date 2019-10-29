# homeassistant-config
My Home-Assistant configs

I manage my configs using HJSON because I find JSON easier to write and maintain than YAML and wanted the ability to support comments. The HJSON files are in `hjson/` along with some Python code (`hjson/ha_yaml_to_and_from_hjson.py`) that can be used to convert HJSON to YAML and vice versa.

The code is a bit of a hack and would require some modifications to support general purpose use cases.