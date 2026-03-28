# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Multi-strategy consensus system (combines RSI, MACD, Bollinger)
- Machine learning preparation hooks
- Additional technical indicators framework

## [0.2.0] - 2024-03-28

### Added
- 🔔 **Alert System**: Telegram and Discord notifications for trading signals
- 📊 **New Strategies**: 
  - MACD strategy with customizable periods
  - Bollinger Bands strategy with confirmation mode
- 📱 **Dashboard**: Real-time web dashboard with auto-refresh
- 🚀 **Railway Deployment**: Production-ready Dockerfile and Railway config
- 🌍 **Multi-language Support**: Documentation in Spanish and English
- 🔒 **Security**: Non-root user in Docker containers
- 📈 **Strategy Scanner**: Multi-strategy consensus endpoint

### Changed
- Improved paper trading order execution with P&L tracking
- Enhanced strategy router with unified signal format
- Optimized Dockerfile with multi-stage build

### Fixed
- RSI calculation edge cases with insufficient data
- Position averaging calculation in paper trading

## [0.1.0] - 2024-03-28

### Added
- 🏗️ **Initial Release**: Core trading system architecture
- 💰 **Paper Trading**: Virtual balance simulation with real market data
- 📈 **RSI Strategy**: Relative Strength Index implementation
- 📡 **Market Data**: Binance integration via CCXT
- 🔌 **REST API**: FastAPI endpoints for trading operations
- 🗄️ **Database**: SQLite with SQLAlchemy async support
- 🐳 **Docker Support**: Docker Compose configuration
- 📚 **API Documentation**: Auto-generated OpenAPI/Swagger docs

### Technical
- Python 3.11+ with FastAPI
- Async/await throughout
- Pandas for data analysis
- TA-Lib for technical indicators

---

## Template for New Releases

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes in existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Now removed features

### Fixed
- Bug fixes

### Security
- Security improvements
```

---

## Release Checklist

- [ ] Update version in `main.py`
- [ ] Update version in `railway.toml`
- [ ] Update CHANGELOG.md
- [ ] Tag release: `git tag -a vX.Y.Z -m "Release X.Y.Z"`
- [ ] Push tags: `git push origin vX.Y.Z`
- [ ] Create GitHub Release
- [ ] Deploy to Railway

---

## Versioning Guide

Given a version number MAJOR.MINOR.PATCH:

1. **MAJOR** - Incompatible API changes
2. **MINOR** - Added functionality (backwards compatible)
3. **PATCH** - Bug fixes (backwards compatible)

Examples:
- `0.1.0` → `0.1.1`: Bug fix in RSI calculation
- `0.1.0` → `0.2.0`: New strategy added (MACD)
- `0.2.0` → `1.0.0`: Breaking API changes for live trading
