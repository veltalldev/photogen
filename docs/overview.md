# Photo Gallery Project Overview

## Introduction

The Photo Gallery project is a self-hosted, single-user application that combines traditional photo management with AI image generation capabilities. It serves both as a portfolio project and a practical tool for personal use, providing an intuitive interface for organizing photos and creating AI-generated image variations using InvokeAI.

## Project Vision

This project aims to create a seamless bridge between a personal photo collection and AI-based image generation. Unlike general-purpose AI image tools, this application focuses on the specific workflow of using existing photos as inspiration for new AI-generated variations, while maintaining a well-organized gallery of both original and generated images.

## Key Features

### Photo Management
- **Gallery Interface**: Browse, view, and organize photos with a responsive, modern UI
- **Organization Tools**: Create albums, manage metadata, and organize collections
- **Search Capabilities**: Find photos based on various criteria including metadata
- **Sharing Features**: Generate secure, temporary links to share photos or albums

### AI Generation Integration
- **InvokeAI Integration**: Seamless connection to local or remote InvokeAI instances
- **Variation Generation**: Use existing photos as a starting point for AI-generated variations
- **Prompt Engineering**: Interactive interface for crafting and refining text prompts
- **Generation History**: Track the lineage and history of generated images
- **Alternative Management**: Compare and select from multiple generated variations

### System Features
- **Local-First Architecture**: All data stored locally for privacy and control
- **Remote Generation Option**: Connect to cloud-based InvokeAI instances via RunPod
- **Cost Management**: Track and optimize usage costs for remote generation
- **Efficient Storage**: Intelligent management of both original and generated images

## Technical Architecture

### Frontend
- **Framework**: Flutter for cross-platform compatibility
- **State Management**: Riverpod for predictable state management
- **Image Handling**: Progressive loading with caching for optimal performance
- **UI Components**: Custom components for photo viewing, comparison, and prompt engineering

### Backend
- **Server**: FastAPI Python backend for efficient API handling
- **Database**: PostgreSQL for structured data storage
- **File Storage**: Organized file system for photos, generations, and thumbnails
- **Integration**: API-based integration with InvokeAI (both local and remote)

### Core Workflows

1. **Photo Upload and Organization**
   - Upload photos to the gallery
   - Organize into albums
   - Generate and view thumbnails and full-resolution images

2. **AI Generation Flow**
   - Select source image from gallery
   - Craft prompt and generation parameters
   - Generate and review multiple variations
   - Select preferred variations
   - Save to gallery and organize

3. **Sharing Flow**
   - Select photos or albums to share
   - Generate secure, time-limited links
   - Share links with recipients
   - Track access and expiration

## Development Approach

The project follows these key principles:

1. **Focused Scope**: Maintains a deliberate focus on single-user, self-hosted use case
2. **Progressive Implementation**: Developed in logical milestones with working features at each stage
3. **Testing First**: Comprehensive testing strategy integrated throughout development
4. **Clear Documentation**: Detailed specifications and documentation for all components
5. **Separation of Concerns**: Clean architecture with clear boundaries between components

## Key Constraints

- **Single-User Design**: Optimized for personal use, not multi-tenant
- **Local Deployment**: Designed for self-hosting, not as a cloud service
- **InvokeAI Dependency**: Requires access to InvokeAI instance (local or remote)
- **Portfolio Quality**: Balances practical utility with demonstration of technical skills

## Project Structure

The project consists of several key components:

1. **Core Photo Gallery**: Traditional photo management functionality
2. **Generation Interface**: Workflow for creating and managing AI generations
3. **Backend Services**: API services handling database, file system, and integration
4. **InvokeAI Integration**: Connection to InvokeAI for image generation
5. **Frontend UI**: User interface components for all workflows

## Development Status

The project is currently in the initial development phase, focusing on establishing the core infrastructure. The roadmap includes:

1. **Current Phase**: Core Infrastructure Setup
   - Database schema implementation
   - File system structure
   - Basic API framework

2. **Next Phases**:
   - Basic photo management
   - Album organization
   - Sharing capabilities
   - InvokeAI integration
   - Remote backend support

## Getting Started

To begin working with the project:

1. Review the Development Environment Setup Guide
2. Understand the Core Philosophy and Common Pitfalls document
3. Review the Testing Strategy Guide for development workflows
4. Start with the current milestone tracked in the Backend Development Progress Tracker

## Documentation Structure

- **Specification Documents**: Define requirements and architecture
- **Implementation Guides**: Provide coding standards and approaches
- **Progress Trackers**: Track development progress for each component
- **Testing Guides**: Define testing approaches and standards
- **Deployment Guides**: Instructions for deployment and maintenance