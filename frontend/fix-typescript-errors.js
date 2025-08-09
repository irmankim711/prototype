#!/usr/bin/env node

/**
 * TypeScript Error Cleanup Script
 * Fixes common TypeScript compilation errors systematically
 */

import fs from "fs";
import path from "path";
import { execSync } from "child_process";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Common fixes to apply
const fixes = [
  {
    name: "Remove unused React imports",
    pattern: /import React,\s*\{\s*([^}]*)\s*\}\s*from\s*['"]react['"];/g,
    replacement: (match, destructured) => {
      // If destructured imports exist, keep them but remove React
      if (destructured.trim()) {
        return `import { ${destructured.trim()} } from "react";`;
      }
      return ""; // Remove the entire import if only React was imported
    },
  },
  {
    name: "Fix date-fns import",
    pattern:
      /import\s*\{\s*formatDistanceToNow\s*\}\s*from\s*['"]date-fns['"];/g,
    replacement: 'import { formatDistanceToNow } from "date-fns";',
  },
  {
    name: "Fix Error constructor calls",
    pattern: /throw new Error\(/g,
    replacement: "throw Error(",
  },
  {
    name: "Fix implicit any parameters",
    pattern: /\(\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\)\s*=>/g,
    replacement: "($1: any) =>",
  },
];

// Files to process (exclude test files for now)
const srcDir = path.join(__dirname, "src");

function getAllTsxFiles(dir) {
  const files = [];
  const items = fs.readdirSync(dir, { withFileTypes: true });

  for (const item of items) {
    const fullPath = path.join(dir, item.name);
    if (item.isDirectory() && !item.name.includes("__tests__")) {
      files.push(...getAllTsxFiles(fullPath));
    } else if (
      item.isFile() &&
      (item.name.endsWith(".tsx") || item.name.endsWith(".ts")) &&
      !item.name.includes(".test.")
    ) {
      files.push(fullPath);
    }
  }

  return files;
}

function cleanUnusedImports(content) {
  const lines = content.split("\n");
  const importLines = [];
  const usedIdentifiers = new Set();

  // Find all import statements and extract identifiers
  const importRegex = /import\s*\{([^}]+)\}\s*from/g;
  let match;

  // Collect all imported identifiers
  const allImports = [];
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (line.trim().startsWith("import ") && line.includes("{")) {
      const match = line.match(
        /import\s*\{([^}]+)\}\s*from\s*['"']([^'"']+)['"'];?/
      );
      if (match) {
        const imports = match[1].split(",").map((imp) => {
          const parts = imp.trim().split(" as ");
          return parts[parts.length - 1].trim();
        });
        allImports.push({
          line: i,
          imports,
          originalLine: line,
          module: match[2],
        });
      }
    }
  }

  // Find used identifiers in the rest of the file
  const contentWithoutImports = lines.slice(allImports.length || 10).join("\n");
  allImports.forEach(({ imports }) => {
    imports.forEach((identifier) => {
      // Check if identifier is used in the content
      const regex = new RegExp(`\\b${identifier}\\b`, "g");
      if (regex.test(contentWithoutImports)) {
        usedIdentifiers.add(identifier);
      }
    });
  });

  // Rebuild import statements with only used identifiers
  allImports.forEach(({ line, imports, originalLine, module }) => {
    const usedImportsFromThisModule = imports.filter((imp) =>
      usedIdentifiers.has(imp)
    );

    if (usedImportsFromThisModule.length > 0) {
      lines[line] = `import { ${usedImportsFromThisModule.join(
        ", "
      )} } from "${module}";`;
    } else {
      lines[line] = ""; // Remove unused import line
    }
  });

  return lines.join("\n");
}

function processFile(filePath) {
  console.log(`Processing: ${path.relative(srcDir, filePath)}`);

  let content = fs.readFileSync(filePath, "utf8");
  let modified = false;

  // Apply each fix
  for (const fix of fixes) {
    const originalContent = content;
    if (typeof fix.replacement === "function") {
      content = content.replace(fix.pattern, fix.replacement);
    } else {
      content = content.replace(fix.pattern, fix.replacement);
    }

    if (content !== originalContent) {
      console.log(`  ✓ Applied: ${fix.name}`);
      modified = true;
    }
  }

  // Clean unused imports
  const cleanedContent = cleanUnusedImports(content);
  if (cleanedContent !== content) {
    content = cleanedContent;
    console.log(`  ✓ Cleaned unused imports`);
    modified = true;
  }

  if (modified) {
    fs.writeFileSync(filePath, content, "utf8");
    console.log(`  ✓ File updated`);
  } else {
    console.log(`  - No changes needed`);
  }
}

// Main execution
console.log("🔧 Starting TypeScript Error Cleanup...\n");

try {
  const files = getAllTsxFiles(srcDir);
  console.log(`Found ${files.length} TypeScript files to process\n`);

  let processedCount = 0;
  for (const file of files) {
    try {
      processFile(file);
      processedCount++;
    } catch (error) {
      console.error(`❌ Error processing ${file}:`, error.message);
    }
  }

  console.log(
    `\n✅ Processed ${processedCount}/${files.length} files successfully`
  );
  console.log("\n🧪 Running TypeScript check...");

  // Run TypeScript check to see remaining errors
  try {
    execSync("npm run build 2>&1", { cwd: __dirname, stdio: "pipe" });
    console.log("✅ All TypeScript errors fixed!");
  } catch (error) {
    const output = error.stdout?.toString() || error.message;
    const errorLines = output
      .split("\n")
      .filter((line) => line.includes("error TS"));
    console.log(`⚠️  ${errorLines.length} TypeScript errors remaining`);

    if (errorLines.length <= 10) {
      console.log("\nRemaining errors:");
      errorLines.slice(0, 10).forEach((line) => console.log(`  ${line}`));
    }
  }
} catch (error) {
  console.error("❌ Script failed:", error.message);
  process.exit(1);
}
