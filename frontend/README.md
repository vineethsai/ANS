# Agent Name Service (ANS) Frontend

This is the frontend for the Agent Name Service (ANS), providing a modern and responsive user interface for managing AI agents, resolving ANS names, and registering new agents in the ANS system.

## Overview

The ANS Frontend is built with React, TypeScript, and Vite to provide a fast and efficient user experience. It connects to the ANS backend API to perform agent management operations.

![ANS Dashboard](./docs/images/dashboard.png)

## Features

- **Agent Directory**: View and filter registered agents by protocol, capability, and provider
- **Name Resolution**: Resolve agent names to their endpoint records
- **Agent Registration**: Register new agents with the ANS system
- **Health Monitoring**: Real-time monitoring of ANS server status

## Prerequisites

- Node.js 16.0.0 or later
- npm 7.0.0 or later
- ANS backend server running at http://localhost:8000

## Quick Start

1. Clone the repository:

```bash
git clone https://github.com/yourusername/ans.git
cd ans/frontend
```

2. Install dependencies:

```bash
npm install
```

3. Start the development server:

```bash
npm start
```

This will start the development server at http://localhost:3000

## Build for Production

To create a production build:

```bash
npm run build
```

The build output will be in the `dist` directory.

## Serve Production Build

To serve the production build locally:

```bash
npm run serve
```

## Project Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── api/             # API service functions
│   ├── components/      # React components
│   ├── App.tsx          # Main application component
│   ├── App.css          # Global styles
│   └── main.tsx         # Application entry point
├── index.html           # HTML entry point
├── tsconfig.json        # TypeScript configuration
├── vite.config.ts       # Vite configuration
└── package.json         # Dependencies and scripts
```

## Architecture

The frontend follows a component-based architecture with these key elements:

- **API Services**: Handles communication with the ANS backend
- **React Components**: Reusable UI components for different views
- **React Router**: Manages navigation between different views
- **TypeScript**: Provides type safety and better developer experience

## Backend Connection

The frontend connects to the ANS backend at http://localhost:8000. Ensure the backend server is running before using the frontend.

## Contributing

We welcome contributions! Please see our [Contributing Guide](./CONTRIBUTING.md) for details on how to submit pull requests, report issues, and suggest improvements.

## License

This project is licensed under the [MIT License](./LICENSE).

## Acknowledgments

- All contributors who have helped shape and improve this project
- The ANS team for their work on the backend system 