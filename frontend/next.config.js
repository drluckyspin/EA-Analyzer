const fs = require("fs");
const path = require("path");

// Get version information from version.json
function getVersionInfo() {
  try {
    const versionPath = path.join(__dirname, "version.json");
    const versionData = JSON.parse(fs.readFileSync(versionPath, "utf8"));
    const buildDate = new Date().toISOString();

    return {
      NEXT_PUBLIC_VERSION: versionData.VERSION,
      NEXT_PUBLIC_COMMIT: versionData.COMMIT,
      NEXT_PUBLIC_BUILD_TIME: versionData.BUILD_TIME,
      NEXT_PUBLIC_BUILD_DATE: buildDate,
    };
  } catch (error) {
    console.warn("Could not read version.json:", error.message);
    return {
      NEXT_PUBLIC_VERSION: "1.0.0",
      NEXT_PUBLIC_COMMIT: "unknown",
      NEXT_PUBLIC_BUILD_TIME: "unknown",
      NEXT_PUBLIC_BUILD_DATE: new Date().toISOString(),
    };
  }
}

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  env: {
    NEXT_PUBLIC_API_URL:
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
    ...getVersionInfo(),
  },
};

module.exports = nextConfig;
