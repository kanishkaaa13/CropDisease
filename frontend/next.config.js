/** @type {import('next').NextConfig} */
const nextConfig = {
  // Allow images from the backend
  images: {
    remotePatterns: [
      {
        protocol: "http",
        hostname: "localhost",
        port: "8000",
        pathname: "/**",
      },
      {
        protocol: "http",
        hostname: "backend",
        port: "8000",
        pathname: "/**",
      },
    ],
  },
  // Forward /api/* calls to backend during development
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
