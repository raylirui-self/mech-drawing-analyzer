# Contributing to Mechanical Drawing Analyzer

Thank you for your interest in contributing! We welcome contributions from the community.

## How to Contribute

### Reporting Bugs
- Use the GitHub Issues page
- Describe the bug in detail
- Include steps to reproduce
- Attach sample drawings if possible (ensure no proprietary data)

### Suggesting Features
- Open a GitHub Issue with the "enhancement" label
- Describe the feature and its use case
- Discuss implementation approach if you have ideas

### Code Contributions

1. **Fork the Repository**
   ```bash
   git clone https://github.com/raylirui-self/mech-drawing-analyzer.git
   cd mech-drawing-analyzer
   ```

2. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Changes**
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

4. **Test Your Changes**
   ```bash
   pytest tests/
   ```

5. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "Add feature: description of your changes"
   ```

6. **Push to Your Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**
   - Go to the original repository
   - Click "New Pull Request"
   - Select your branch
   - Describe your changes

## Code Style

- Use Black for Python formatting
- Follow PEP 8 guidelines
- Add type hints where possible
- Write docstrings for all functions

## Testing

- Write tests for new features
- Ensure all tests pass before submitting PR
- Aim for >80% code coverage

## Documentation

- Update README if adding new features
- Add docstrings to new functions
- Include examples in documentation

## Acknowledgments

Contributors who submit accepted PRs will be added to the contributors list.