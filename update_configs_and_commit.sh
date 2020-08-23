./convert_configs_from_hjson_to_yaml.sh
chmod -R 755 *
git add .
git commit -m "$*"
git push origin
