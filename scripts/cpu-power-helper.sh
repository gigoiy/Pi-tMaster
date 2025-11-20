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
        /usr/bin/sudo echo "powersave" > /usr/bin/sudo /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
        /usr/bin/sudo echo "300000" > /usr/bin/sudo /sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq
        /usr/bin/sudo echo "600000" > /usr/bin/sudo /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq
        echo "OK"
        ;;
    "set-ondemand")
        /usr/bin/sudo echo "ondemand" > /usr/bin/sudo /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
        /usr/bin/sudo echo "600000" > /usr/bin/sudo /sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq
        /usr/bin/sudo echo "1500000" > /usr/bin/sudo /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq
        echo "OK"
        ;;
    *)
        echo "Invalid command: $1"
        exit 1
        ;;
esac

exit 0