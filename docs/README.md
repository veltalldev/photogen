# Photo Gallery Documentation

This directory contains comprehensive documentation for the Photo Gallery project - a self-hosted, single-user photo gallery application with integrated AI image generation capabilities.

## Documentation Structure

```
docs/
├── README.md                             # This file
├── *.md                                  # Project-wide documentation
├── specs/                                # Technical specifications
│   ├── Database Schema Specification.md
│   ├── System Architecture.md
│   ├── API Contract.md
│   └── InvokeAI Integration.md
│
└── dev/                                  # Development documentation
    ├── Implementation Guide.md           # Overall implementation approach
    ├── Development Environment Setup.md  # Setup instructions
    ├── Testing Strategy.md               # Testing approach
    │
    ├── current/                          # Active development docs
    │   ├── Progress Trackers/            # Detailed task tracking
    │   └── Notes/                        # Working notes
    │
    └── archived/                         # Completed work documentation
        ├── Progress Trackers/            # Historical task tracking
        └── Notes/                        # Historical notes
```

## Root Level Documents

These documents provide high-level, project-wide information:

| Document | Description |
|----------|-------------|
| [Photo Gallery Project Overview](./Photo%20Gallery%20Project%20Overview%20%26%20Documentation%20Guide.md) | Project definition, core characteristics, and use cases |
| [Common Pitfalls & Design Rationale](./Common%20Pitfalls%20%26%20Design%20Rationale.md) | Philosophy, common pitfalls, and implementation guidance |
| [Development Environment Setup Guide](./Development%20Environment%20Setup%20Guide.md) | Environment setup for development |

## Technical Specifications (`specs/`)

The `specs/` directory contains detailed technical specifications:

| Document | Description |
|----------|-------------|
| [System Architecture](./specs/System%20Architecture.md) | High-level architecture and components |
| [Database Schema](./specs/Database%20Schema.md) | Complete database design and relationships |
| [API Contract](./specs/API%20Contract.md) | REST API endpoints and usage |
| [InvokeAI Integration](./specs/InvokeAI%20Integration.md) | Integration with InvokeAI for image generation |

## Development Documentation (`dev/`)

The `dev/` directory contains implementation-focused documentation:

| Document | Description |
|----------|-------------|
| [Implementation Guide](./dev/Implementation%20Guide.md) | Patterns, practices, and approaches |
| [Development Environment Setup](./dev/Development%20Environment%20Setup.md) | Detailed setup instructions |
| [Testing Strategy](./dev/Testing%20Strategy.md) | Testing approach and patterns |

### Current Development (`dev/current/`)

The `current/` subdirectory contains documentation for active development:

- **Progress Trackers**: Fine-grained task tracking for current work
- **Notes**: Working notes, decisions, and research for active tasks

### Archived Development (`dev/archived/`)

The `archived/` subdirectory contains documentation for completed work:

- **Progress Trackers**: Historical task tracking (preserved for reference)
- **Notes**: Historical notes and discussions from completed work

## Documentation Workflow

### When to Create Documents

- **Specifications**: Create before implementation begins
- **Progress Trackers**: Create at the start of each implementation task
- **Working Notes**: Create as needed during implementation
- **Implementation Guides**: Create based on patterns identified

### When to Update Documents

- **Specifications**: Update when design changes are approved
- **Implementation Guides**: Update when new patterns are established
- **Progress Trackers**: Update daily during active development

### When to Archive Documents

- **Progress Trackers**: Archive when the associated task is complete
- **Working Notes**: Archive when the implementation is complete
- **Specification Versions**: Archive when major revisions occur

## Using This Documentation

### For New Developers

1. Start with the [Project Overview](./Photo%20Gallery%20Project%20Overview%20%26%20Documentation%20Guide.md)
2. Review the [Common Pitfalls & Design Rationale](./Common%20Pitfalls%20%26%20Design%20Rationale.md)
3. Set up your environment using the [Development Environment Setup Guide](./Development%20Environment%20Setup%20Guide.md)
4. Understand the architecture from [System Architecture](./specs/System%20Architecture.md)
5. Review the [Implementation Guide](./dev/Implementation%20Guide.md)

### For Active Developers

1. Check the current progress in `dev/current/Progress Trackers/`
2. Review relevant specifications in `specs/`
3. Consult implementation guides in `dev/`
4. Document your work in `dev/current/Notes/`

### For Code Reviewers

1. Check the relevant specifications in `specs/`
2. Review the implementation guide for expected patterns
3. Verify progress against the related tracker

## Documentation Standards

1. **File Names**: Use Title Case with spaces for all documentation files
2. **Cross-References**: Use relative links when referencing other documents
3. **Images**: Store in an `images/` folder adjacent to the document
4. **Diagrams**: Create using Mermaid.js when possible for maintainability
5. **Code Examples**: Include meaningful comments and follow the project style guide
6. **Markdown**: Use consistent heading levels and formatting