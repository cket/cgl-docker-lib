
build:
	cd toil-leader && $(MAKE) build
	cd toil-worker && $(MAKE) build

push: build
	# Requires ~/.dockercfg
	cd toil-leader && $(MAKE) push
	cd toil-worker && $(MAKE) push

test: build
	./test/test.sh

clean:
	cd toil-leader && $(MAKE) clean
	cd toil-worker && $(MAKE) clean
