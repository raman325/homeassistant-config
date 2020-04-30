chmod -R 755 *
./convert_configs_from_hjson_to_yaml.sh
git add .
git commit -m "$*"
git push origin
