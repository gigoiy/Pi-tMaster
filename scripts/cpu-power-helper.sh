#!/bin/bash
# CPU Power Management Helper Script for PitMaster

case "$1" in
    "get-status")
        governor=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor)
        cur_freq=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq)
        min_freq=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq)
        max_freq=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq)
        echo "$governor"
        echo "$cur_freq"
        echo "$min_freq"
        echo "$max_freq"
        ;;
    "set-powersave")
        sudo echo "powersave" > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
        sudo echo "300000" > /sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq
        sudo echo "600000" > /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq
        echo "OK"
        ;;
    "set-ondemand")
        sudo echo "ondemand" > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
        sudo echo "600000" > /sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq
        sudo echo "1500000" > /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq
        echo "OK"
        ;;
    *)
        echo "Invalid command: $1"
        exit 1
        ;;
esac

exit 0