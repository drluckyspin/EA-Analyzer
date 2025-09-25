import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET() {
  try {
    const versionPath = path.join(process.cwd(), 'version.json');
    const versionData = JSON.parse(fs.readFileSync(versionPath, 'utf8'));
    
    return NextResponse.json({
      status: 'healthy',
      version: versionData.VERSION,
      commit: versionData.COMMIT,
      buildTime: versionData.BUILD_TIME,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    return NextResponse.json({
      status: 'unhealthy',
      error: 'Failed to read version information',
      timestamp: new Date().toISOString(),
    }, { status: 500 });
  }
}
