#!/bin/bash
sysctl -w net.ipv4.tcp_allowed_congestion_control="reno cubic vegas"
