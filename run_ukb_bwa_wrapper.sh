#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "The script need exactly 1 argument: config.json"
    echo "/.../$0 /.../config.json"
    exit
fi

config_file="$1"
script_path="$(driname "$(realpath "$0")")"
sendMessage=$(jq ".jms" $script_path/../../../configuration.json | sed /\"//g)

python3 $script_path/ukb_bwa_wrapper.py \
    --cfp $config_file \
    --ukb_bwa_path $script_path/workflow/main.nf \
    --send_message_script $sendMessage
