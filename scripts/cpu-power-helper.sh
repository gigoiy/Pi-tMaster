#!/bin/bash
# CPU Power Management Helper Script for PitMaster

case "$1" in
    "get-status")
        governor=$(sudo cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor)
        cur_freq=$(sudo cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq)
        min_freq=$(sudo cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq)
        max_freq=$(sudo cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq)
        sudo echo "$governor"
        sudo echo "$cur_freq"
        sudo echo "$min_freq"
        sudo echo "$max_freq"
        ;;
    "set-powersave")
        sudo echo "powersave" > sudo /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
        sudo echo "300000" > sudo /sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq
        sudo echo "600000" > sudo /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq
        echo "OK"
        ;;
    "set-ondemand")
        sudo echo "ondemand" > sudo /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
        sudo echo "600000" > sudo /sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq
        sudo echo "1500000" > sudo /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq
        echo "OK"
        ;;
    *)
        echo "Invalid command: $1"
        exit 1
        ;;
esac

exit 0