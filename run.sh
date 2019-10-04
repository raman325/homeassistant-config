set -x
# set script to fail on error
set -Eeuo pipefail
# pull latest configs from git
/volume1/@appstore/git/bin/git pull origin
# check config validity
sudo docker exec ha python -m homeassistant --script check_config --config /config
# turn off error check
set +Eeuo pipefail
# pull latest docker image and restart HA
../run_homeassistant.sh
