import type { NextConfig } from "next";

const allowedDevOrigins = (
  process.env.ALLOWED_DEV_ORIGINS ?? "192.168.1.9"
)
  .split(",")
  .map((value) => value.trim())
  .filter(Boolean);

const nextConfig: NextConfig = {
  allowedDevOrigins,
};

export default nextConfig;
