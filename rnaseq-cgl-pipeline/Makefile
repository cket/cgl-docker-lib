# Definitions
build_tool = runtime-container.DONE
git_commit ?= $(shell git log --pretty=oneline -n 1 -- ../rnaseq-cgl-pipeline | cut -f1 -d " ")
name = quay.io/ucsc_cgl/rnaseq-cgl-pipeline
tag = 2.0.0--${git_commit}

build: ${build_tool}

${build_tool}: Dockerfile.py
	python Dockerfile.py ${name} ${tag} build
	touch ${build_tool}

push: build
	# Requires ~/.dockercfg
	python Dockerfile.py ${name} ${tag} push

test: build
	python test.py

clean:
	-rm ${build_tool}
