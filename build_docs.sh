#!/bin/bash

set -e

cd docs/
make html

tar -C _build/html --exclude=_sources -cjf _build/html.tar.bz2 .

