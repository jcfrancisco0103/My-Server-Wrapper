# 🚀 Release Management System Guide

## Overview
The Minecraft Server Wrapper now includes a comprehensive release management system that automatically handles version updates and generates GitHub release information.

## Features
- ✅ Automatic version incrementing (major.minor.patch)
- ✅ GitHub release tag generation
- ✅ Professional release titles
- ✅ Detailed release notes with proper formatting
- ✅ Version history tracking
- ✅ Bug fix vs feature release differentiation
- ✅ Automatic release file generation

## Usage Examples

### 1. Creating a Bug Fix Release
```python
# For bug fixes (increments patch version: 2.0.0 → 2.0.1)
bug_fixes = [
    "Fixed authentication session timeout issues",
    "Resolved password validation edge cases",
    "Fixed admin panel user approval notifications"
]

release_info = wrapper.create_bugfix_release(bug_fixes)
```

### 2. Creating a Feature Release
```python
# For new features (increments minor version: 2.0.0 → 2.1.0)
features = [
    "Added user profile management",
    "Enhanced admin dashboard with statistics",
    "Improved password strength requirements"
]

release_info = wrapper.create_feature_release(features, version_type="minor")
```

### 3. Creating a Major Release
```python
# For major changes (increments major version: 2.0.0 → 3.0.0)
major_features = [
    "Complete authentication system overhaul",
    "New web interface design",
    "Advanced user management"
]

release_info = wrapper.create_feature_release(features, version_type="major")
```

### 4. Custom Version Release
```python
# Specify exact version number
release_info = wrapper.create_new_release(
    custom_version="2.5.0",
    changes=["Custom version release"],
    is_bugfix=False
)
```

## Generated Output

### For each release, the system generates:

1. **Version Tag**: `v2.0.1`, `v2.1.0`, etc.
2. **Release Title**: 
   - 🐛 Bug Fix Release v2.0.1
   - ✨ Feature Release v2.1.0  
   - 🚀 Major Release v3.0.0
3. **Detailed Release Notes** with:
   - Professional formatting
   - Installation instructions
   - Requirements list
   - Change log
   - GitHub comparison links

### Files Created:
- `version_history.json` - Complete version history
- `release_X_X_X.md` - GitHub release template for each version

## GitHub Release Process

1. **Run the release creation method**
2. **Copy the generated release template** from the `.md` file
3. **Create a new release on GitHub** with:
   - Tag: Use the generated tag (e.g., `v2.0.1`)
   - Title: Use the generated title
   - Description: Use the generated release notes

## Example Generated Release Notes

```markdown
# 🐛 Bug Fix Release v2.0.1

This release addresses critical bugs and stability issues.

## 🐛 Bug Fixes
- Fixed authentication session timeout issues
- Resolved password validation edge cases
- Fixed admin panel user approval notifications

## 📦 Installation
1. Download the latest release
2. Extract the files to your desired directory
3. Run `python minecraft_server_wrapper.py`

## 📋 Requirements
- Python 3.7+
- Flask
- Flask-SocketIO
- psutil
- requests
- packaging

## 🔄 What's Changed
- Version updated from v2.0.0 to v2.0.1
- Fixed authentication session timeout issues
- Resolved password validation edge cases
- Fixed admin panel user approval notifications

**Full Changelog**: https://github.com/jcfrancisco0103/My-Server-Wrapper/compare/v2.0.0...v2.0.1
```

## Best Practices

1. **Use semantic versioning**:
   - Major: Breaking changes or major new features
   - Minor: New features, backward compatible
   - Patch: Bug fixes, small improvements

2. **Write clear change descriptions**:
   - Start with action verbs (Added, Fixed, Improved)
   - Be specific about what changed
   - Include user-facing impact

3. **Regular releases**:
   - Create releases for every significant change
   - Group related changes together
   - Don't wait too long between releases

## Integration with Development Workflow

The release management system is now integrated into the main wrapper class, so you can create releases directly from your application or create separate scripts for release management.

---

**Happy Releasing! 🎉**