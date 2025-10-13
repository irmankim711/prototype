const fs = require('fs');
const path = require('path');

// Function to find all TypeScript files
function findTSFiles(dir, files = []) {
  const items = fs.readdirSync(dir);

  for (const item of items) {
    const fullPath = path.join(dir, item);
    const stat = fs.statSync(fullPath);

    if (stat.isDirectory() && !item.startsWith('.') && item !== 'node_modules') {
      findTSFiles(fullPath, files);
    } else if (item.endsWith('.tsx') || item.endsWith('.ts')) {
      files.push(fullPath);
    }
  }

  return files;
}

// Function to fix import syntax errors
function fixImportSyntax(filePath) {
  try {
    let content = fs.readFileSync(filePath, 'utf8');
    const originalContent = content;
    let changed = false;

    // Fix double curly braces in imports: } } from -> } from
    content = content.replace(/}\s*}\s*from/g, '} from');
    if (content !== originalContent) {
      changed = true;
    }

    // Fix malformed import statements with extra spaces and formatting
    // Pattern: "  import { someImport," followed by other lines, ending with "} } from"
    content = content.replace(/^(\s*)import\s*{\s*([^}]+)}\s*}\s*from\s*(['"][^'"]*['"])\s*;?\s*$/gm, '$1import { $2 } from $3;');
    if (content !== originalContent) {
      changed = true;
    }

    // Fix multiline imports that got broken
    // Look for pattern: import { followed by lines that don't end with }
    const lines = content.split('\n');
    let inImport = false;
    let importStart = -1;
    let importLines = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();

      if (line.startsWith('import {') && !line.includes('} from')) {
        inImport = true;
        importStart = i;
        importLines = [lines[i]];
      } else if (inImport) {
        importLines.push(lines[i]);

        if (line.includes('} from') || line.includes('from "') || line.includes("from '")) {
          // End of import found
          inImport = false;

          // Reconstruct the import
          let allImports = '';
          let fromPart = '';

          for (const importLine of importLines) {
            if (importLine.includes('from ')) {
              fromPart = importLine.substring(importLine.indexOf('from ')).trim();
              const beforeFrom = importLine.substring(0, importLine.indexOf('from ')).trim();
              if (beforeFrom && !beforeFrom.includes('import')) {
                allImports += beforeFrom.replace(/[{}]/g, '') + ', ';
              }
            } else {
              const cleanLine = importLine.replace(/import\s*{\s*/, '').replace(/}\s*$/, '').trim();
              if (cleanLine && !cleanLine.includes('from')) {
                allImports += cleanLine + ', ';
              }
            }
          }

          // Clean up the imports string
          allImports = allImports.replace(/,\s*$/, '').replace(/,\s*,/g, ',').trim();

          if (fromPart) {
            const leadingSpaces = lines[importStart].match(/^(\s*)/)[1];
            const newImport = `${leadingSpaces}import { ${allImports} } ${fromPart}`;

            // Replace the old multiline import with the new single line
            lines.splice(importStart, importLines.length, newImport);

            // Adjust the index since we removed lines
            i = importStart;
            changed = true;
          }
        }
      }
    }

    if (changed) {
      content = lines.join('\n');
    }

    // Fix remaining parsing issues
    // Remove duplicate 'import' keywords
    content = content.replace(/import\s+import\s+/g, 'import ');

    // Fix spacing issues in imports
    content = content.replace(/import\s*{\s*([^}]+)}\s*from/g, 'import { $1 } from');

    // Fix double spaces in from clauses
    content = content.replace(/}\s+from\s+/g, '} from ');

    // Ensure proper semicolons
    content = content.replace(/^(import\s+[^;]+)$/gm, '$1;');

    // Fix specific malformed patterns
    content = content.replace(/^(\s*)(import\s*{\s*)([^}]*)(}\s*}\s*from\s*.*)$/gm, '$1$2$3} from$4');

    // Save file if changed
    if (content !== originalContent) {
      fs.writeFileSync(filePath, content, 'utf8');
      return true;
    }

    return false;
  } catch (error) {
    console.error(`Error processing ${filePath}:`, error.message);
    return false;
  }
}

// Main execution
const frontendSrcPath = path.join(__dirname, 'frontend', 'src');
const allFiles = findTSFiles(frontendSrcPath);

console.log(`Found ${allFiles.length} TypeScript files to fix import syntax...`);

let fixedCount = 0;
let totalFiles = allFiles.length;

allFiles.forEach((filePath, index) => {
  const relativePath = path.relative(__dirname, filePath);

  if (fixImportSyntax(filePath)) {
    fixedCount++;
    console.log(`✅ Fixed: ${relativePath}`);
  }

  // Progress indicator
  if ((index + 1) % 50 === 0) {
    console.log(`Progress: ${index + 1}/${totalFiles} files processed...`);
  }
});

console.log('\n🎉 Import syntax fix completed!');
console.log(`📊 Summary:`);
console.log(`   - Total files processed: ${totalFiles}`);
console.log(`   - Files fixed: ${fixedCount}`);
console.log(`   - Files unchanged: ${totalFiles - fixedCount}`);

console.log('\n✨ Run eslint again to check remaining issues!');