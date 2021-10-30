# exit when any command fails
set -e

# Check for failed command and echo result
check_exit() {
  exit_code=$?
  if [[ exit_code -ne 0  ]]; then
    echo "\"${last_command}\" command failed with exit code $exit_code."
  fi
}

# keep track of the last executed command
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
# echo an error message before exiting if needed
trap 'check_exit' EXIT

./convert_configs_from_hjson_to_yaml.sh
#sudo chmod -R 755 *
git add .
git commit -m "$*"
git push origin
