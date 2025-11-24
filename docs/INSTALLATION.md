# Installation Guide

## Package Managers

### Homebrew (macOS/Linux)

```bash
brew install kazefreeze/tap/pandabrew
```

### APT (Debian/Ubuntu)

```bash
# Download the .deb package
wget https://github.com/KazeFreeze/PandaBrew/releases/latest/download/pandabrew_<version>_linux_amd64.deb

# Install
sudo dpkg -i pandabrew_<version>_linux_amd64.deb

# Or install directly
sudo apt install ./pandabrew_<version>_linux_amd64.deb
```

### YUM/DNF (RHEL/Fedora/CentOS)

```bash
# Download the .rpm package
wget https://github.com/KazeFreeze/PandaBrew/releases/latest/download/pandabrew_<version>_linux_amd64.rpm

# Install with yum
sudo yum install pandabrew_<version>_linux_amd64.rpm

# Or with dnf
sudo dnf install pandabrew_<version>_linux_amd64.rpm
```

## Pre-built Binaries

Download the latest release for your platform from:
https://github.com/KazeFreeze/PandaBrew/releases/latest

### Linux

```bash
# Download and extract
curl -L https://github.com/KazeFreeze/PandaBrew/releases/latest/download/PandaBrew_<version>_Linux_x86_64.tar.gz | tar xz

# Install globally
sudo mv pandabrew /usr/local/bin/
sudo chmod +x /usr/local/bin/pandabrew

# Install man pages (optional)
sudo mkdir -p /usr/share/man/man1
sudo cp share/man/man1/*.gz /usr/share/man/man1/

# Update man database
sudo mandb

# Verify installation
pandabrew --version
man pandabrew
```

### macOS

```bash
# Download and extract
curl -L https://github.com/KazeFreeze/PandaBrew/releases/latest/download/PandaBrew_<version>_Darwin_x86_64.tar.gz | tar xz

# Install globally
sudo mv pandabrew /usr/local/bin/
sudo chmod +x /usr/local/bin/pandabrew

# Install man pages (optional)
sudo mkdir -p /usr/local/share/man/man1
sudo cp share/man/man1/*.gz /usr/local/share/man/man1/

# Verify installation
pandabrew --version
man pandabrew
```

**Note for Apple Silicon (M1/M2/M3):** Download the `Darwin_arm64` version instead of `Darwin_x86_64`.

### Windows

1. Download the ZIP file for Windows from the [releases page](https://github.com/KazeFreeze/PandaBrew/releases/latest)
2. Extract to a directory (e.g., `C:\Program Files\PandaBrew`)
3. Add the directory to your PATH environment variable:
   - Press `Win + X` and select "System"
   - Click "Advanced system settings"
   - Click "Environment Variables"
   - Under "System variables", find and edit "Path"
   - Add the PandaBrew directory path
4. Open a new terminal and verify: `pandabrew --version`

## Build from Source

### Requirements

- Go 1.23 or later
- Git

### Steps

```bash
# Clone the repository
git clone https://github.com/KazeFreeze/PandaBrew.git
cd PandaBrew

# Install dependencies
go mod tidy

# Run tests
go test -v ./...

# Build
go build -o pandabrew ./cmd/pandabrew

# Install globally (optional)
sudo mv pandabrew /usr/local/bin/
sudo chmod +x /usr/local/bin/pandabrew

# Verify installation
pandabrew --version
```

### Build with Custom Flags

```bash
# Build with version info
go build -ldflags="-s -w -X main.version=1.0.0 -X main.commit=$(git rev-parse HEAD)" \
  -o pandabrew ./cmd/pandabrew
```

## Verify Installation

```bash
# Check version
pandabrew --version

# View help
pandabrew --help

# Read manual (Linux/macOS)
man pandabrew
```

## Troubleshooting

### Permission Denied (Linux/macOS)

```bash
sudo chmod +x /usr/local/bin/pandabrew
```

### Command Not Found (Windows)

Make sure the PandaBrew directory is in your PATH environment variable. After adding to PATH, **restart your terminal**.

### Command Not Found (Linux/macOS)

```bash
# Check if binary is in PATH
which pandabrew

# If not, ensure /usr/local/bin is in PATH
echo $PATH | grep /usr/local/bin

# Add to PATH if missing (add to ~/.bashrc or ~/.zshrc)
export PATH="/usr/local/bin:$PATH"
```

### Man Pages Not Showing

```bash
# Linux - update man database
sudo mandb

# macOS - check man path
man -w pandabrew

# If man pages aren't found, verify they're installed
ls -la /usr/share/man/man1/pandabrew.1.gz     # Linux
ls -la /usr/local/share/man/man1/pandabrew.1.gz  # macOS
```

### Package Installation Conflicts

```bash
# Debian/Ubuntu - if there's a conflict
sudo apt remove pandabrew
sudo apt install ./pandabrew_<version>_linux_amd64.deb

# RHEL/Fedora - if there's a conflict
sudo yum remove pandabrew
sudo yum install pandabrew_<version>_linux_amd64.rpm
```

## Uninstallation

### Homebrew

```bash
brew uninstall pandabrew
```

### APT (Debian/Ubuntu)

```bash
sudo apt remove pandabrew
```

### YUM/DNF (RHEL/Fedora)

```bash
sudo yum remove pandabrew
# or
sudo dnf remove pandabrew
```

### Manual Installation

```bash
# Remove binary
sudo rm /usr/local/bin/pandabrew

# Remove man pages (optional)
sudo rm /usr/share/man/man1/pandabrew.1.gz     # Linux
sudo rm /usr/local/share/man/man1/pandabrew.1.gz  # macOS

# Update man database
sudo mandb  # Linux
```

## Platform-Specific Notes

### Linux
- Uses XDG directories for configuration
- Man pages integrate with system documentation
- Works with most terminal emulators

### macOS
- Compatible with both Intel and Apple Silicon
- Integrates with native Terminal and iTerm2
- May require security approval on first run (System Preferences → Security)

### Windows
- Works with PowerShell, Command Prompt, and Windows Terminal
- No ANSI color support in older Command Prompt versions
- Use Windows Terminal for best experience

## Updating

### Homebrew

```bash
brew upgrade pandabrew
```

### Package Managers

```bash
# Debian/Ubuntu
sudo apt update
sudo apt upgrade pandabrew

# RHEL/Fedora
sudo yum update pandabrew
# or
sudo dnf update pandabrew
```

### Manual Installation

Download and install the latest release following the installation steps above.

## Support

If you encounter installation issues:

1. Check the [GitHub Issues](https://github.com/KazeFreeze/PandaBrew/issues)
2. Review the [troubleshooting section](#troubleshooting)
3. Open a new issue with your platform and error details
