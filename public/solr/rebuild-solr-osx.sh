#!/bin/sh
catalina stop
mvn package
sudo catalina start

