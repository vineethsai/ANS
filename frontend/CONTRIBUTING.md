# Contributing to ANS Frontend

Thank you for considering contributing to the Agent Name Service Frontend! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

Please help us keep the ANS community open and inclusive. By participating, you are expected to uphold this code of conduct.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue tracker to see if the problem has already been reported. When you are creating a bug report, include as many details as possible:

- A clear and descriptive title
- Steps to reproduce the behavior
- What you expected to happen
- What actually happened
- Screenshots (if applicable)
- Environment details (browser, OS, etc.)

### Suggesting Enhancements

When suggesting enhancements, include:

- A clear and descriptive title
- Detailed explanation of the proposed enhancement
- Explain why this enhancement would be useful to most ANS users
- List any relevant examples to demonstrate the enhancement

### Pull Requests

1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests to ensure no regressions
5. Commit your changes (`git commit -m 'Add some amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Pull Request Guidelines

- Document new code with clear comments
- Update documentation if necessary
- Keep PRs focused on a single concern
- Write meaningful commit messages
- Include tests for new features or bug fixes
- Ensure the code follows the existing style

## Development Setup

1. Clone the repository: `git clone https://github.com/yourusername/ans.git`
2. Install dependencies: `cd ans/frontend && npm install`
3. Start the development server: `npm start`
4. Run tests: `npm test`

## Coding Style and Guidelines

### TypeScript

- Use TypeScript for all new code
- Define interfaces for props and state
- Use types from libraries when available

### React Components

- Use functional components with hooks
- Keep components small and focused
- Extract reusable logic into custom hooks
- Use proper prop validation

### CSS

- Follow the existing naming conventions
- Use CSS classes instead of inline styles
- Consider responsive design principles

## Git Workflow

- Branch from `main` for features and fixes
- Use descriptive branch names (e.g., `feature/agent-registration-form`)
- Make regular, small commits with clear messages
- Reference issues in commit messages when applicable

## Testing

- Write tests for new functionality
- Ensure existing tests pass
- Run `npm test` before submitting a PR

## Documentation

- Keep the README up-to-date
- Document complex logic with comments
- Update API documentation when making changes

## Questions?

If you have any questions about contributing, please open an issue or contact the maintainers directly.

Thank you for your contributions! 