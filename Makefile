.PHONY: test
test:
	nosetests test/

.PHONY: release
release:
	npx standard-version . && git push --follow-tags origin master
