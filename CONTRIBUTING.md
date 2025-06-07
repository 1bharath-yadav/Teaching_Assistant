# Contributing to TDS Teaching Assistant

Thank you for considering contributing to the TDS Teaching Assistant project! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Enhancements](#suggesting-enhancements)
  - [Code Contributions](#code-contributions)
- [Development Process](#development-process)
  - [Setting Up Development Environment](#setting-up-development-environment)
  - [Running Tests](#running-tests)
  - [Style Guidelines](#style-guidelines)
- [Pull Request Process](#pull-request-process)
- [Community](#community)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

This section guides you through submitting a bug report. Following these guidelines helps maintainers understand your report, reproduce the behavior, and find related reports.

**Before Submitting A Bug Report:**

- Check if the bug has already been reported in the issues.
- Determine which repository the problem should be reported in.
- Check if the issue persists in the latest version.

**How to Submit a Good Bug Report:**

Bugs are tracked as issues. Create an issue and provide the following information:

- Use a clear and descriptive title
- Describe the exact steps which reproduce the problem
- Provide specific examples to demonstrate the steps
- Describe the behavior you observed after following the steps
- Explain which behavior you expected to see instead and why
- Include screenshots and animated GIFs which show you following the described steps
- Include details about your environment (OS, browser, etc.)

### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion, including completely new features and minor improvements to existing functionality.

**Before Submitting An Enhancement Suggestion:**

- Check if the enhancement has already been suggested in the issues.
- Determine which repository the enhancement should be suggested in.

**How to Submit a Good Enhancement Suggestion:**

Enhancement suggestions are tracked as issues. Create an issue and provide the following information:

- Use a clear and descriptive title
- Provide a step-by-step description of the suggested enhancement
- Provide specific examples to demonstrate the steps
- Describe the current behavior and explain which behavior you expected to see instead
- Explain why this enhancement would be useful to most users
- List some other applications where this enhancement exists, if applicable
- Include screenshots and animated GIFs which help you demonstrate the idea

### Code Contributions

#### Your First Code Contribution

Unsure where to begin contributing? You can start by looking through these `beginner` and `help-wanted` issues:

- **Beginner issues** - issues which should only require a few lines of code, and a test or two.
- **Help wanted issues** - issues which should be a bit more involved than `beginner` issues.

Both issue lists are sorted by total number of comments. While not perfect, the number of comments is a reasonable proxy for the impact a given change will have.

#### Local Development

The project can be developed locally. For instructions on how to set up your local development environment, see the [Development Guide](docs/DEVELOPMENT_GUIDE.md).

## Development Process

### Setting Up Development Environment

1. Fork the repository and clone your fork
2. Create a new branch:
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. Setup the development environment:
   ```bash
   ./setup.sh
   ```
4. Make your changes
5. Test your changes:
   ```bash
   make test
   ```
6. Push to the branch
7. Open a Pull Request

### Running Tests

- Run all tests: `make test`
- Run unit tests: `make test-unit`
- Run integration tests: `make test-integration`

### Style Guidelines

#### Git Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line
- Consider starting the commit message with an applicable emoji:
  - ✨ (sparkles) for new features
  - 🐛 (bug) for bug fixes
  - 📚 (books) for documentation changes
  - 🧹 (broom) for code refactoring
  - ⚡️ (zap) for performance improvements

#### Python Style Guide

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use type hints
- Write docstrings for all functions, classes, and modules
- Use Black and isort for formatting

#### JavaScript/TypeScript Style Guide

- Follow the [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- Use TypeScript for type checking
- Use ESLint and Prettier for formatting

## Pull Request Process

1. Update the README.md or documentation with details of changes if appropriate
2. Update the tests to cover your changes
3. Make sure all tests pass
4. The PR should work for Python 3.9+
5. Get approval from a maintainer

## Community

- Join our [Discord server](https://discord.gg/your-discord-server)
- Follow the project on [Twitter](https://twitter.com/your-twitter-handle)
- Subscribe to our [newsletter](https://your-newsletter-url.com)
