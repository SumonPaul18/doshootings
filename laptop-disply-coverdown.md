আপনার ল্যাপটপের ডিসপ্লে বন্ধ করার পরেও উবুন্টু সার্ভার চালু রাখতে, আপনি নিম্নলিখিত পদক্ষেপগুলি অনুসরণ করতে পারেন:

1. **ল্যাপটপের পাওয়ার সেটিংস পরিবর্তন করুন**:
   - টার্মিনাল খুলুন এবং `sudo nano /etc/systemd/logind.conf` কমান্ডটি চালান।
   - `HandleLidSwitch` এবং `HandleLidSwitchDocked` এর মান `ignore` এ পরিবর্তন করুন। উদাহরণস্বরূপ:
     ```
     HandleLidSwitch=ignore
     HandleLidSwitchDocked=ignore
     ```
   - ফাইলটি সংরক্ষণ করুন এবং টার্মিনাল থেকে বেরিয়ে আসুন।

2. **সিস্টেমড রিস্টার্ট করুন**:
   - টার্মিনালে `sudo systemctl restart systemd-logind` কমান্ডটি চালান।

এই পরিবর্তনগুলি করার পর, আপনার ল্যাপটপের ডিসপ্লে বন্ধ করলেও এটি স্লিপ মোডে যাবে না এবং উবুন্টু সার্ভার চালু থাকবে[1](https://qastack.net.bd/ubuntu/141866/keep-ubuntu-server-running-on-a-laptop-with-the-lid-closed)।


Here's a shell script that automates the process of modifying the power settings to keep the Ubuntu server running even when the laptop display is closed:

Create a Shell Script
```
nano update_power_settings.sh
```

```sh
#!/bin/bash

# Step 1: Modify logind.conf to ignore lid switch
LOGIND_CONF="/etc/systemd/logind.conf"

# Backup the original logind.conf
sudo cp $LOGIND_CONF ${LOGIND_CONF}.bak

# Update HandleLidSwitch and HandleLidSwitchDocked settings
sudo sed -i 's/#HandleLidSwitch=.*/HandleLidSwitch=ignore/' $LOGIND_CONF
sudo sed -i 's/#HandleLidSwitchDocked=.*/HandleLidSwitchDocked=ignore/' $LOGIND_CONF

# Step 2: Restart systemd-logind service
sudo systemctl restart systemd-logind

echo "Power settings updated successfully. Lid switch is now ignored."
```

You can save this script to a file, for example `update_power_settings.sh`, and run it with the following command:

```sh
chmod +x update_power_settings.sh
sudo ./update_power_settings.sh
```

This script will:
1. Backup the original `logind.conf` file.
2. Update the `HandleLidSwitch` and `HandleLidSwitchDocked` settings to `ignore`.
3. Restart the `systemd-logind` service to apply the changes.


