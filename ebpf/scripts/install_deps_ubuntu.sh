#!/usr/bin/env bash
set -euo pipefail
sudo apt-get update
sudo apt-get install -y clang llvm libelf-dev libbpf-dev bpftool make
clang --version
bpftool version
