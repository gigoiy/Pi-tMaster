#!/bin/bash
# CPU Power Management Helper Script for PitMaster

case "$1" in
    "get-status")
        governor=$(/usr/bin/sudo cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor)
        cur_freq=$(/usr/bin/sudo cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq)
        min_freq=$(/usr/bin/sudo cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq)
        max_freq=$(/usr/bin/sudo cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq)
        /usr/bin/sudo echo "$governor"
        /usr/bin/sudo echo "$cur_freq"
        /usr/bin/sudo echo "$min_freq"
        /usr/bin/sudo echo "$max_freq"
        ;;
    "set-powersave")
        echo "powersave" | /usr/bin/sudo tee /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
        echo "300000" | /usr/bin/sudo tee /sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq
        echo "600000" | /usr/bin/sudo tee /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq
        echo "OK"
        ;;
    "set-ondemand")
        echo "ondemand" | /usr/bin/sudo tee /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
        echo "600000" | /usr/bin/sudo tee /sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq
        echo "1500000" | /usr/bin/sudo tee /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq
        echo "OK"
        ;;
    *)
        echo "Invalid command: $1"
        exit 1
        ;;
esac

exit 0