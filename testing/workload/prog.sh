#!/bin/bash
for i in {1..1000}
do
	echo $i >> $1
	sleep 1
done
