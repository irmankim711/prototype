import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Fix React UMD global issues by adding proper React imports
function fixReactUMDIssues(filePath) {
  let content = fs.readFileSync(filePath, "utf8");

  // Check if file has React JSX but no React import
  const hasJSX = /(\<[A-Z][^>]*\>|\<\/[A-Z][^>]*\>|React\.)/g.test(content);
  const hasReactImport = /import.*React.*from.*['"]react['"]/.test(content);

  if (hasJSX && !hasReactImport) {
    // Find where to insert the React import
    const lines = content.split("\n");
    let insertIndex = 0;

    // Find the first import statement or the beginning of file
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].trim().startsWith("import ")) {
        insertIndex = i;
        break;
      }
    }

    // Insert React import
    lines.splice(insertIndex, 0, 'import React from "react";');
    content = lines.join("\n");

    fs.writeFileSync(filePath, content, "utf8");
    console.log(
      `✓ Added React import to ${path.relative(__dirname, filePath)}`
    );
    return true;
  }

  return false;
}

// Get all TypeScript files
function getAllTsxFiles(dir) {
  const files = [];
  const items = fs.readdirSync(dir, { withFileTypes: true });

  for (const item of items) {
    const fullPath = path.join(dir, item.name);
    if (
      item.isDirectory() &&
      !item.name.includes("__tests__") &&
      !item.name.includes("node_modules")
    ) {
      files.push(...getAllTsxFiles(fullPath));
    } else if (
      item.isFile() &&
      item.name.endsWith(".tsx") &&
      !item.name.includes(".test.")
    ) {
      files.push(fullPath);
    }
  }

  return files;
}

const srcDir = path.join(__dirname, "src");
const files = getAllTsxFiles(srcDir);

console.log("🔧 Fixing React UMD global issues...\n");

let fixedCount = 0;
for (const file of files) {
  try {
    if (fixReactUMDIssues(file)) {
      fixedCount++;
    }
  } catch (error) {
    console.error(`❌ Error processing ${file}:`, error.message);
  }
}

console.log(`\n✅ Fixed ${fixedCount} files with React UMD issues`);
