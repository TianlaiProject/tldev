#! /usr/bin/env bash

while read line
do
kill -INT $line
done < .proc_pid.txt

