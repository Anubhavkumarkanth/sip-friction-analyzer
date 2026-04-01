# Contributing to SIP Friction Analyzer

Thank you for your interest in contributing to SIP Friction Analyzer! We welcome contributions from everyone.

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 16+
- Git

### Development Setup

**1. Clone and Navigate**
```bash
git clone <repository-url>
cd "Sip Friction Analyzer"
```

**2. Setup Backend**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
python main.py
# Backend runs at http://localhost:8000
```

**3. Setup Frontend**
```bash
cd frontend
npm install
npm run dev
# Frontend runs at http://localhost:5173
```

**4. Open API Documentation**
- Navigate to `http://localhost:8000/docs` for Swagger UI
- Explore and test API endpoints interactively

## Project Structure

```
├── engine/              # Business logic
│   ├── simulation.py   # SIP calculations
│   └── friction.py     # Metrics (CCR, Discipline Score, etc.)
├── frontend/            # React + TypeScript
│   ├── src/
│   │   ├── components/ # UI components
│   │   ├── pages/      # Page components
│   │   ├── services/   # API calls
│   │   ├── types/      # TypeScript interfaces
│   │   └── utils/      # Helpers
│   ├── jest.config.js  # Test configuration
│   └── tsconfig.json   # TypeScript configuration
├── models.py            # Database models
├── database.py          # DB connection
├── auth.py              # Authentication
├── main.py              # FastAPI app
└── requirements.txt     # Python dependencies
```

## Development Guidelines

### Code Style
- **Python**: Follow PEP 8
  ```bash
  pip install pylint
  pylint engine/ models.py
  ```
- **Frontend**: Use ESLint
  ```bash
  npm run lint
  ```

### TypeScript
Write all new components in TypeScript. Use proper types from `src/types/index.ts`.

```typescript
import { FC } from 'react';
import { MyComponentProps } from '../types';

const MyComponent: FC<MyComponentProps> = ({ prop1, prop2 }) => {
  // Component code
};

export default MyComponent;
```

### Testing

**Backend Tests**
```bash
pytest test_backend.py -v
```

**Frontend Tests**
```bash
npm test
npm test -- --coverage
```

### Git Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and test**
   ```bash
   npm run lint          # Check code quality
   npm test              # Run tests
   npm run build         # Build production
   ```

3. **Commit with meaningful messages**
   ```bash
   git commit -m "feat: add new simulation feature"
   git commit -m "fix: resolve validation bug"
   git commit -m "docs: update README"
   ```

4. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Adding/updating tests
- `chore:` Dependency updates, tooling

## Pull Request Process

1. Update documentation if needed
2. Add/update tests for new features
3. Ensure all tests pass: `npm test`
4. Ensure build passes: `npm run build`
5. Request review from maintainers
6. Address feedback and iterate

## Reporting Issues

When reporting bugs, please include:
- Steps to reproduce
- Expected behavior
- Actual behavior
- Screenshots/error logs
- Environment details (OS, browser, versions)

## Feature Requests

When suggesting features, describe:
- User problem being solved
- Proposed solution
- Alternative approaches considered
- Impact on users

## Technology Choices

### Why TypeScript?
- Type safety prevents runtime errors
- Better IDE support and autocomplete
- Easier refactoring
- Self-documenting code

### Why React + Vite?
- Fast development experience
- Excellent component reusability
- Mature ecosystem
- TypeScript support out of the box

### Why FastAPI?
- Modern async Python framework
- Automatic API documentation
- High performance
- Type hints throughout

## Questions?

- Open a GitHub Issue for questions
- Check existing issues before asking
- Look at closed issues for resolved topics

---

**Thank you for contributing!** 🎉

Your contributions make SIP Friction Analyzer better for everyone.
