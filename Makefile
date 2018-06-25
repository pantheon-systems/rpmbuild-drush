
all: clean rpm

test:
	tests/confirm-rpm.sh

deps:
	gem install fpm

deps-macos:
	brew install rpm

rpm: fetch package

fetch:
	bash scripts/fetch.sh

package:
	bash scripts/build-rpm.sh

clean:
	rm -rf build*
	rm -rf pkgs

.PHONY: all
