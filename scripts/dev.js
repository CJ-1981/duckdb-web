#!/usr/bin/env node

/**
 * Smart dev server script that tries ports in sequence:
 * 3000 → 3001 → 3002 → 3003
 *
 * Usage: node scripts/dev.js
 * Or: npm run dev (with package.json script)
 */

/* eslint-disable @typescript-eslint/no-require-imports */
const { spawn } = require('child_process');
const net = require('net');

const PORTS = [3000, 3001, 3002, 3003];

/**
 * Check if a port is available
 */
function isPortAvailable(port) {
  return new Promise((resolve) => {
    const server = net.createServer();

    server.once('error', () => {
      resolve(false);
    });

    server.once('listening', () => {
      server.close();
      resolve(true);
    });

    server.listen(port);
  });
}

/**
 * Find first available port
 */
async function findAvailablePort() {
  for (const port of PORTS) {
    console.log(`🔍 Checking port ${port}...`);
    const available = await isPortAvailable(port);

    if (available) {
      console.log(`✅ Port ${port} is available!`);
      return port;
    }

    console.log(`❌ Port ${port} is in use`);
  }

  console.error('❌ All ports (3000-3003) are in use!');
  process.exit(1);
}

/**
 * Start Next.js dev server
 */
async function startDevServer() {
  console.log('🚀 Starting Next.js dev server...\n');

  const port = await findAvailablePort();

  console.log(`\n🎯 Starting on port ${port}...\n`);

  // Set PORT environment variable and spawn Next.js
  const env = { ...process.env, PORT: port.toString() };
  const child = spawn('next', ['dev'], {
    env,
    stdio: 'inherit',
    shell: true
  });

  child.on('error', (err) => {
    console.error('❌ Failed to start dev server:', err);
    process.exit(1);
  });

  child.on('exit', (code) => {
    process.exit(code || 0);
  });
}

startDevServer();
