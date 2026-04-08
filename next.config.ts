import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',
  images: {
    unoptimized: true,
  },
  // Allow cross-origin access to Next.js dev resources for Playwright tests
  allowedDevOrigins: ['127.0.0.1', 'localhost'],
};

export default nextConfig;
