VERSION?=$(shell git describe --tags --abbrev=0 | sed 's/^v//')
TAG="servehub/stolon-standby-haproxy"

bump-tag:
	GIT_TAG=$$(echo "v${VERSION}" | awk -F. '{$$NF = $$NF + 1;} 1' | sed 's/ /./g'); \
	git tag $$GIT_TAG; \
	git push && git push --tags

build:
	@echo "==> Build..."
	docker build -t ${TAG}:latest -t ${TAG}:${VERSION} .

push:
	@echo "==> Publish new docker image..."
	docker push ${TAG}:${VERSION}
	docker push ${TAG}:latest
