# Common Pitfalls & Design Rationale

## Core Philosophy
This application is designed to be a focused, self-hosted, single-user photo gallery with AI image generation capabilities. It intentionally maintains a narrow scope to remain maintainable and user-friendly.

## Common Pitfalls to Avoid

### 1. Authentication & Authorization
**Pitfall**: Adding complex user management and permission systems.

**Rationale**: 
- This is a single-user application
- Authentication is handled at the deployment level
- Share links use simple, stateless tokens
- No need for role-based access control

### 2. Resource Management
**Pitfall**: Implementing complex GPU scheduling and resource management.

**Rationale**:
- Resource management is handled through architectural constraints:
  - Single queue for generation jobs
  - Maximum batch size of 10 images
  - One job processed at a time
- Users needing fine-grained control should use InvokeAI's web interface

### 3. AI Generation Interface
**Pitfall**: Building comprehensive prompt engineering tools and parameter controls.

**Rationale**:
- Application provides "more like this" functionality
- Not trying to replicate InvokeAI's primary interface
- Basic templates are provided, but prompt crafting is user's domain
- Complex generation tasks belong in InvokeAI's web UI

### 4. Caching & Performance
**Pitfall**: Implementing complex caching strategies and optimizations.

**Rationale**:
- Single-user workload is predictable
- Simple LRU caching is sufficient
- Local storage makes complex caching unnecessary
- File system handles most persistence needs

### 5. State Management
**Pitfall**: Using complex state management patterns designed for multi-user systems.

**Rationale**:
- Local-first architecture simplifies state
- No need for real-time updates
- Simple, unidirectional data flow is sufficient
- State conflicts are minimal in single-user context

### 6. API Design
**Pitfall**: Building complex API versioning and multi-tenant support.

**Rationale**:
- API serves single local user
- Version control through deployment
- Simple REST endpoints are sufficient
- No need for tenant isolation

### 7. Deployment
**Pitfall**: Creating complex deployment pipelines and scaling strategies.

**Rationale**:
- Single machine deployment
- Simple backup through file system
- Basic logging is sufficient
- No need for horizontal scaling

### 8. Security
**Pitfall**: Implementing complex security measures designed for multi-user systems.

**Rationale**:
- Basic file system permissions are sufficient
- Share links use simple token system
- No need for fine-grained access control
- Trust local user context

## Development Guidelines

### Keep It Simple
- Prefer simple, direct solutions
- Avoid premature optimization
- Question complexity-adding features
- Focus on core user needs

### Respect Boundaries
- Don't duplicate InvokeAI functionality
- Stay focused on gallery and "more like this" features
- Keep generation interface simple
- Maintain clear separation of concerns

### Embrace Constraints
- Single user simplifies architecture
- Local deployment enables simpler solutions
- File system provides natural organization
- Limited scope improves maintainability

### Consider the User
- Gallery first, generation second
- Simple, intuitive interfaces
- Clear workflow paths
- Minimal configuration needed

## When to Expand Scope

Consider expanding scope only when:
1. Core functionality is stable
2. New feature clearly benefits single-user case
3. Feature can't be better served by InvokeAI
4. Implementation maintains simplicity
5. Maintenance burden is minimal

## When to Refer to InvokeAI

Direct users to InvokeAI's web interface for:
1. Fine-tuning generation parameters
2. Complex prompt engineering
3. Advanced model options
4. Batch processing needs
5. Direct model interaction

## Maintenance Philosophy

Focus maintenance efforts on:
1. Core gallery functionality
2. Integration stability
3. Performance optimization
4. User experience improvements
5. Simplified workflows

Avoid maintenance traps:
1. Feature parity with InvokeAI
2. Complex optimization
3. Multi-user adaptations
4. Unnecessary abstraction
5. Premature generalization