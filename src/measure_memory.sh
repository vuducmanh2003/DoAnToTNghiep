#!/bin/bash
for i in {1..1000}; do
  systemctl status antiphishing | grep Memory >> mem_log.txt
  sleep 0.5
done
