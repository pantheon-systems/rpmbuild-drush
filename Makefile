# Read the version we are packaging from VERSIONS.txt
VERSION := $(shell cat VERSIONS.txt)

all: clean rpm

test: deps
	tests/confirm-rpm.sh

deps:
	gem install fpm

deps-macos:
	brew install rpm

deps-circle:
	sudo apt-get -y install rpm
	gem install package_cloud

rpm:
	bash scripts/build-rpm.sh

clean:
	rm -rf build*
	rm -rf pkgs

.PHONY: all
