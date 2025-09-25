import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET() {
  try {
    const versionPath = path.join(process.cwd(), 'version.json');
    const versionData = JSON.parse(fs.readFileSync(versionPath, 'utf8'));
    
    return NextResponse.json({
      version: versionData.VERSION,
      commit: versionData.COMMIT,
      buildTime: versionData.BUILD_TIME,
      buildDate: new Date().toISOString(),
    });
  } catch (error) {
    return NextResponse.json({
      version: '1.0.0',
      commit: 'unknown',
      buildTime: 'unknown',
      buildDate: new Date().toISOString(),
    });
  }
}
