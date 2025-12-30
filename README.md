<div align="center">
    <h1>Lichess Chess Bot</h1>
    <h4>Professional automated chess assistant for Lichess.org featuring Stockfish engine integration and advanced humanization algorithms</h4>
    <img width="60%" src="assets/screen.png" alt="Chess Bot Preview">
</div>

## Features

- **Stockfish Integration**: Configurable engine depth and skill levels
- **Modern GUI**: Real-time board visualization with move suggestions
- **Smart Humanization**: Randomized timing patterns to simulate human play
- **Dual Modes**: Fully automated or suggestion-only operation
- **Cross-Platform**: Windows and Linux support

## Installation

### Option 1: Pre-built Release (Recommended)

1. Download from [GitHub Releases](https://github.com/kWAYTV/helping-hand/releases)
2. Extract and configure `config.ini` (see `config.example.ini`)
3. Export your Lichess cookies (see [Authentication](#authentication))
4. Run the executable

### Option 2: From Source

```bash
git clone https://github.com/kWAYTV/helping-hand.git
cd helping-hand
pip install -r requirements.txt
```

**Dependencies** (place in `deps/` folder):

- [Stockfish Engine](https://stockfishchess.org/download/)
- [GeckoDriver](https://github.com/mozilla/geckodriver/releases)
- [xPath Finder Extension](https://addons.mozilla.org/en-US/firefox/addon/xpath_finder/) (.xpi file)

## Authentication

This bot uses cookie-based authentication. Export your Lichess cookies using one of these browser extensions:

- [Chrome Extension](https://chrome.google.com/webstore/detail/%E3%82%AF%E3%83%83%E3%82%AD%E3%83%BCjson%E3%83%95%E3%82%A1%E3%82%A4%E3%83%AB%E5%87%BA%E5%8A%9B-for-puppet/nmckokihipjgplolmcmjakknndddifde)
- [Firefox Extension](https://addons.mozilla.org/en-US/firefox/addon/%E3%82%AF%E3%83%83%E3%82%AD%E3%83%BCjson%E3%83%95%E3%82%A1%E3%82%A4%E3%83%AB%E5%87%BA%E5%8A%9B-for-puppeteer/)

**Steps:**
1. Log in to [lichess.org](https://lichess.org) in your browser
2. Use the extension to export cookies while on the Lichess site
3. The extension will save a file named `lichess.org.cookies.json`
4. Place this file in the `deps/` folder

## Configuration

Essential `config.ini` settings:

```ini
[engine]
depth = 5          # Analysis depth (1-20)
skill-level = 14   # Engine strength (0-20)

[general]
auto-play = true   # Auto-execute moves
move-key = end     # Manual trigger key
log-level = INFO   # Logging verbosity
```

## Usage

### AutoPlay Mode

Fully automated gameplay with built-in humanization delays (0.3-3.0s randomization).

### Suggestion Mode

Displays engine recommendations requiring manual confirmation via hotkey or GUI.

### GUI Features

- Live chess board with position tracking
- Engine move suggestions with visual arrows
- Real-time game information and statistics
- Color-coded activity log with auto-scroll
- Manual control panel

## Disclaimer

**This is a proof of concept (POC) for educational and research purposes only.**

The developers assume no responsibility or liability for any consequences arising from the use of this software. Users are solely responsible for:

- Compliance with Lichess Terms of Service
- Any account actions or penalties
- Legal implications in their jurisdiction

Use at your own risk.
