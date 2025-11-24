#!/bin/sh
# Post-installation script for PandaBrew packages
# Updates the man page database after installation

if command -v mandb >/dev/null 2>&1; then
  mandb -q 2>/dev/null || true
fi
