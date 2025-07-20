import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  webpack: (config, { isServer }) => {
    // Monaco Editor configuration
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        module: false,
        perf_hooks: false,
      };
    }

    // Handle Monaco Editor specific modules
    config.module.rules.push({
      test: /\.worker\.(js|ts)$/,
      use: {
        loader: 'worker-loader',
        options: {
          filename: 'static/[hash].worker.js',
          publicPath: '/_next/',
        },
      },
    });

    // Monaco Editor CSS handling
    config.module.rules.push({
      test: /\.ttf$/,
      type: 'asset/resource',
    });

    return config;
  },
  
  // Ensure proper transpilation of Monaco Editor
  transpilePackages: ['monaco-editor'],
  
  // Experimental features for better compatibility
  experimental: {
    esmExternals: 'loose',
  },
};

export default nextConfig;
