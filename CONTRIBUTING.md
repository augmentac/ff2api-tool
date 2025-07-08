# Contributing to FF2API

Thank you for your interest in contributing to FF2API! This document provides guidelines for contributing to the project.

## 🎯 Project Overview

FF2API is a freight file-to-API processing tool designed for internal company use. It provides a web interface for uploading CSV/Excel files and mapping them to API endpoints.

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- Git
- Modern web browser

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd FF2API
   ```

2. **Set up development environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Create necessary directories**
   ```bash
   mkdir -p data/{uploads,mappings,logs} config
   ```

4. **Run the application**
   ```bash
   streamlit run src/frontend/app.py
   ```

## 📋 How to Contribute

### 🐛 Reporting Bugs

1. **Check existing issues** first to avoid duplicates
2. **Use the bug report template** when creating new issues
3. **Include detailed information**:
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details
   - Screenshots if applicable

### 💡 Suggesting Features

1. **Use the feature request template**
2. **Describe the problem** the feature would solve
3. **Explain the proposed solution**
4. **Consider technical implications**

### 🔧 Code Contributions

#### Before You Start

1. **Create an issue** to discuss major changes
2. **Check existing pull requests** to avoid duplicates
3. **Ensure you understand** the project structure

#### Development Process

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the coding standards
   - Add tests if applicable
   - Update documentation

4. **Test your changes**
   ```bash
   # Run the application locally
   streamlit run src/frontend/app.py
   
   # Test file uploads with sample data
   # Test different file formats
   # Test error conditions
   ```

5. **Commit your changes**
   ```bash
   git commit -m "feat: add your feature description"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**

## 🏗️ Project Structure

```
FF2API/
├── src/
│   ├── frontend/
│   │   ├── app.py              # Main Streamlit application
│   │   └── ui_components.py    # UI components and helpers
│   ├── backend/
│   │   ├── database.py         # Database operations
│   │   ├── data_processor.py   # Data processing logic
│   │   └── api_client.py       # API client integration
│   └── models/                 # Data models (if any)
├── data/                       # Database and uploads (gitignored)
├── config/                     # Configuration files
├── .streamlit/                 # Streamlit configuration
├── requirements.txt            # Python dependencies
├── docker-compose.yml          # Docker configuration
└── README.md                   # Project documentation
```

## 📝 Coding Standards

### Python Code Style

- **PEP 8**: Follow Python style guidelines
- **Type hints**: Use type hints where appropriate
- **Docstrings**: Document functions and classes
- **Error handling**: Include proper exception handling

### Example Code Style

```python
def process_file(file_path: str, mapping: dict) -> tuple[bool, str]:
    """
    Process uploaded file with given mapping.
    
    Args:
        file_path: Path to the uploaded file
        mapping: Field mapping configuration
        
    Returns:
        Tuple of (success, message)
    """
    try:
        # Implementation here
        return True, "Success"
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        return False, str(e)
```

### Frontend Guidelines

- **Streamlit conventions**: Follow Streamlit best practices
- **UI consistency**: Maintain consistent styling
- **User experience**: Prioritize clear, intuitive interfaces
- **Error messages**: Provide helpful error messages

## 🧪 Testing

### Manual Testing

1. **File Upload Testing**
   - Test CSV and Excel files
   - Test various file sizes
   - Test malformed files

2. **Mapping Testing**
   - Test field mapping interface
   - Test validation logic
   - Test edge cases

3. **API Integration Testing**
   - Test successful API calls
   - Test error conditions
   - Test rate limiting

### Test Data

- Use sample data from `sample_data/` directory
- Remove sensitive information from test files
- Test with various data formats and edge cases

## 📚 Documentation

### Code Documentation

- **Docstrings**: Document all functions and classes
- **Comments**: Explain complex logic
- **Type hints**: Use for better code clarity

### User Documentation

- **README updates**: Keep README current
- **Deployment docs**: Update deployment instructions
- **Changelog**: Document all changes

## 🔒 Security Guidelines

### Data Privacy

- **No sensitive data**: Never commit sensitive information
- **Encryption**: Use proper encryption for credentials
- **Access control**: Implement appropriate access controls

### Code Security

- **Input validation**: Validate all user inputs
- **SQL injection**: Use parameterized queries
- **File security**: Validate uploaded files

## 🌟 Best Practices

### Git Workflow

1. **Small commits**: Make focused, atomic commits
2. **Clear messages**: Write descriptive commit messages
3. **Branch naming**: Use descriptive branch names
4. **Pull requests**: Keep PRs focused and reviewable

### Code Quality

1. **DRY principle**: Don't repeat yourself
2. **Single responsibility**: Functions should do one thing
3. **Error handling**: Handle errors gracefully
4. **Performance**: Consider performance implications

## 🎨 UI/UX Guidelines

### Design Principles

- **Simplicity**: Keep interfaces clean and simple
- **Consistency**: Maintain consistent styling
- **Accessibility**: Consider accessibility requirements
- **Responsiveness**: Ensure mobile-friendly design

### Streamlit Specific

- **Session state**: Use session state appropriately
- **Caching**: Implement caching where beneficial
- **Progress indicators**: Show progress for long operations
- **Error handling**: Display user-friendly error messages

## 🤝 Community Guidelines

### Communication

- **Be respectful**: Treat all contributors with respect
- **Be constructive**: Provide helpful feedback
- **Be patient**: Allow time for responses
- **Be collaborative**: Work together toward common goals

### Code Review

- **Be thorough**: Review code carefully
- **Be specific**: Provide specific feedback
- **Be helpful**: Suggest improvements
- **Be open**: Accept feedback gracefully

## 📞 Getting Help

### Resources

- **Documentation**: Check existing documentation first
- **Issues**: Search existing issues for answers
- **Examples**: Look at existing code for patterns

### Contact

- **GitHub Issues**: For bugs and feature requests
- **Pull Requests**: For code contributions
- **Discussions**: For general questions

## 📄 License

By contributing to FF2API, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to FF2API! Your contributions help make the tool better for everyone. 