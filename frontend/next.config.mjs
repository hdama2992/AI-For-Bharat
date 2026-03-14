/** @type {import('next').NextConfig} */
const nextConfig = {
  // Allow images from any domain for crop photos
  images: { unoptimized: true },
  // Disable x-powered-by header
  poweredByHeader: false,
};

export default nextConfig;
