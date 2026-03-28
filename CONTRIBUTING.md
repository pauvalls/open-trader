# Contributing to Open Trader

First off, thank you for considering contributing to Open Trader! 

## 🚀 Quick Start

1. **Fork** the repository
2. **Clone** your fork: `git clone https://github.com/YOUR_USERNAME/open-trader.git`
3. **Create** a branch: `git checkout -b feature/amazing-feature`
4. **Make** your changes
5. **Test** your changes locally
6. **Commit**: `git commit -m 'Add amazing feature'`
7. **Push**: `git push origin feature/amazing-feature`
8. **Open** a Pull Request

## 📋 Guidelines

### Code Style

- **Python**: Follow PEP 8
- **Type hints**: Use them wherever possible
- **Docstrings**: Google style docstrings
- **Async**: Prefer async/await for I/O operations

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: Add new strategy
fix: Correct RSI calculation
docs: Update README
refactor: Improve database queries
test: Add strategy backtests
chore: Update dependencies
```

### Pull Request Process

1. Update the CHANGELOG.md with your changes
2. Ensure tests pass (if they exist)
3. Update documentation as needed
4. Request review from maintainers

## 🐛 Reporting Bugs

Use GitHub Issues with the following template:

```markdown
**Description:**
Clear description of the bug

**Steps to reproduce:**
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior:**
What should happen

**Environment:**
- OS: [e.g. Ubuntu 20.04]
- Python: [e.g. 3.11]
- Version: [e.g. v0.1.0]
```

## 💡 Feature Requests

Use GitHub Issues with label `enhancement`:

- Describe the feature clearly
- Explain why it would be useful
- Suggest implementation if possible

## 🧪 Testing

Before submitting:

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Test endpoints
curl http://localhost:8000/health/
```

## 📝 Documentation

- Update README.md if adding features
- Add docstrings to new functions
- Update API docs (auto-generated from FastAPI)

## 🏷️ Releasing (Maintainers)

Use the release script:

```bash
./scripts/release.sh
```

This will:
1. Bump version
2. Update CHANGELOG.md
3. Create git tag
4. Push to GitHub

## 🌐 Translations

Help translate documentation:
- Copy `README_EN.md` to `README_XX.md`
- Translate content
- Add link in main README.md
- Submit PR

## ❓ Questions?

- Open a GitHub Discussion
- Tag `@pauvalls` for maintainer attention

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.
