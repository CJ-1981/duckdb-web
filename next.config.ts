import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Production optimization
  reactStrictMode: true,
  compress: true,

  // Output configuration
  // Use 'export' for static deployment to Vercel
  // Change to 'standalone' for full-stack deployment
  output: 'export',

  // Image optimization (disabled for static export)
  images: {
    unoptimized: true,
  },

  // Allow cross-origin access to Next.js dev resources for Playwright tests
  allowedDevOrigins: ['127.0.0.1', 'localhost'],

  // Environment variables (exposed to browser)
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  }
};

export default nextConfig;
