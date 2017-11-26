#!/bin/bash

sudo tc class change dev $1  parent 5:1 classid 5:$2 htb rate $3  ceil $4