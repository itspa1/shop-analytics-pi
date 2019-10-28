#!/bin/bash

#takes the first argument for the script that is some name for the interface on monitor mode else default is set to 'waln0mon'
IFACE="$1"
IFACE="${IFACE:-"wlan0mon"}"

#takes the second argument for the script that is 0 else default 1 is set
#by default channel hop is enabled for max packet capture
CHANNEL_HOP="$2"
CHANNEL_HOP="${CHANNEL_HOP:-1}"

# channel hop every 2 seconds
channel_hop() {

	IEEE80211bg="1 2 3 4 5 6 7 8 9 10 11"
	IEEE80211bg_intl="$IEEE80211b 12 13 14"
	IEEE80211a="36 40 44 48 52 56 60 64 149 153 157 161"
	IEEE80211bga="$IEEE80211bg $IEEE80211a"
	IEEE80211bga_intl="$IEEE80211bg_intl $IEEE80211a"

	while true ; do
        #TODO: Check if all channels are necessary?
        #channel hop between all the available channels
		for CHAN in $IEEE80211bga_intl ; do
			# echo "switching $IFACE to channel $CHAN"
			sudo iwconfig $IFACE channel $CHAN
			sleep 2
		done
	done
}

if [ "$CHANNEL_HOP" -ne 0 ] ; then
	# channel hop in the background
	channel_hop &
fi

#use tcpdump to get the probe-req on the interface
#use -tttt for full timestamp with date format
sudo tcpdump -tttt -l -I -i "$IFACE" -e -s 256 type mgt subtype probe-req 2> /dev/null
