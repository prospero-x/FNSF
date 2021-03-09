#!/usr/bin/env bash
for f in SBE*/**/*input.toml; do
    cargo run --release $f
done
