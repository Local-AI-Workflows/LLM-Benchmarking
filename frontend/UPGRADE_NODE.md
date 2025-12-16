# Upgrading Node.js

The frontend requires **Node.js 18.0.0 or higher**. You currently have Node.js v12.22.9.

## Quick Upgrade Options

### Option 1: Using nvm (Node Version Manager) - Recommended

```bash
# Install nvm if you don't have it
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Reload your shell
source ~/.bashrc  # or ~/.zshrc

# Install Node.js 18 (LTS)
nvm install 18

# Use Node.js 18
nvm use 18

# Set as default
nvm alias default 18

# Verify
node --version  # Should show v18.x.x or higher
```

### Option 2: Using NodeSource Repository (Ubuntu/Debian)

```bash
# Remove old Node.js
sudo apt-get remove nodejs npm

# Add NodeSource repository for Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -

# Install Node.js 18
sudo apt-get install -y nodejs

# Verify
node --version  # Should show v18.x.x or higher
npm --version
```

### Option 3: Using Snap (Ubuntu)

```bash
# Remove old Node.js
sudo apt-get remove nodejs npm

# Install Node.js 18 via snap
sudo snap install node --classic --channel=18

# Verify
node --version
```

### Option 4: Download from Official Website

1. Visit https://nodejs.org/
2. Download the LTS version (18.x or higher)
3. Install the package
4. Verify: `node --version`

## After Upgrading

1. **Remove old node_modules** (if they exist):
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   ```

2. **Reinstall dependencies**:
   ```bash
   npm install
   ```

3. **Start the dev server**:
   ```bash
   npm run dev
   ```

## Verify Installation

```bash
# Check Node.js version (should be 18+)
node --version

# Check npm version (should be 8+)
npm --version

# Check if nvm is working (if using nvm)
nvm list
```

## Troubleshooting

### "Command not found: nvm"

After installing nvm, you need to reload your shell:
```bash
source ~/.bashrc
# or
source ~/.zshrc
```

### Multiple Node.js Versions

If you have multiple Node.js versions installed, make sure you're using the correct one:
```bash
# With nvm
nvm use 18

# Check which node is being used
which node
```

### Permission Errors

If you get permission errors, avoid using `sudo` with npm. Instead:
```bash
# Configure npm to use a directory you own
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
export PATH=~/.npm-global/bin:$PATH
```

