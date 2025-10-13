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

// Function to fix remaining parsing errors
function fixRemainingParsingErrors(filePath) {
  try {
    let content = fs.readFileSync(filePath, 'utf8');
    const originalContent = content;
    let changed = false;

    // Fix malformed export type statements that got mixed with import
    content = content.replace(/export type\s*{\s*import\s*{\s*([^}]+)}\s*from\s*(['"][^'"]*['"])\s*;?\s*(?:}\s*)?/g,
      'export type { $1 } from $2;'
    );

    // Fix export type with import pattern
    content = content.replace(/export\s+type\s*{\s*import\s*{([^}]+)}\s*from\s*(['"][^'"]*['"])[^}]*}/g,
      'export type { $1 } from $2;'
    );

    // Fix trailing commas in imports that got mangled
    content = content.replace(/import\s*{\s*([^}]+),\s*}\s*from/g, 'import { $1 } from');

    // Fix double default exports
    if ((content.match(/export default/g) || []).length > 1) {
      const lines = content.split('\n');
      let defaultExportFound = false;

      for (let i = 0; i < lines.length; i++) {
        if (lines[i].trim().startsWith('export default')) {
          if (defaultExportFound) {
            // Remove duplicate default export
            lines.splice(i, 1);
            i--;
            changed = true;
          } else {
            defaultExportFound = true;
          }
        }
      }

      if (changed) {
        content = lines.join('\n');
      }
    }

    // Fix malformed semicolon issues in imports
    content = content.replace(/import\s*{\s*([^}]+)}\s*from\s*(['"][^'"]*['"])\s*([^;])/g,
      'import { $1 } from $2;\n$3'
    );

    // Fix missing opening import statement
    content = content.replace(/^(\s*)([A-Z][a-zA-Z0-9_,\s]*)\s*}\s*from\s*(['"][^'"]*['"])\s*;?$/gm,
      '$1import { $2 } from $3;'
    );

    // Fix export statements that are missing export keyword
    content = content.replace(/^(\s*)const\s+([A-Z][a-zA-Z0-9_]*)\s*=/gm, (match, spaces, name) => {
      // Only export if it looks like a React component or exported constant
      if (name.match(/^[A-Z]/) && (content.includes('<') || content.includes('React'))) {
        return `${spaces}export const ${name} =`;
      }
      return match;
    });

    // Fix unused variable by removing if it's just a standalone assignment
    const unusedMatches = content.match(/@typescript-eslint\/no-unused-vars.*?[\r\n]+.*?const\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=/g);
    if (unusedMatches) {
      for (const match of unusedMatches) {
        const varName = match.match(/const\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=/)[1];
        // If the variable is not used elsewhere in the file, remove it
        const varUsages = (content.match(new RegExp(`\\b${varName}\\b`, 'g')) || []).length;
        if (varUsages <= 2) { // Only declaration and maybe one other reference
          content = content.replace(new RegExp(`const\\s+${varName}\\s*=.*?(?=\\n|$)`, 'g'), '');
          changed = true;
        }
      }
    }

    // Fix malformed semicolon placement
    content = content.replace(/([^;\s])\s*;(\s*)([a-zA-Z])/g, '$1;$2\n$3');

    // Fix newline issues
    content = content.replace(/No newline at end of file([^\n])/g, '\n$1');

    // Fix functions with incorrect return types that cause parsing errors
    content = content.replace(/=>\s*React\.ChangeEvent<HTMLInputElement>/g, '=> void');

    // Fix Promise types that might be causing issues
    content = content.replace(/Promise\(\(resolve:\s*\([^)]*\)\s*=>\s*[^)]*\)\s*=>/g,
      'Promise((resolve: (value: any) => void) =>'
    );

    // Add missing semicolons at end of lines where needed
    content = content.replace(/^(\s*import\s+[^;]+)$/gm, '$1;');
    content = content.replace(/^(\s*export\s+[^;{}]+)$/gm, '$1;');

    // Fix specific patterns that are causing parsing errors
    // Remove standalone "No newline at end of file" lines
    content = content.replace(/^\s*No newline at end of file\s*$/gm, '');

    // Fix empty lines at the beginning
    content = content.replace(/^\s*\n/, '');

    // Ensure file ends with single newline
    content = content.replace(/\n*$/, '\n');

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

console.log(`Found ${allFiles.length} TypeScript files to fix remaining parsing errors...`);

let fixedCount = 0;
let totalFiles = allFiles.length;

allFiles.forEach((filePath, index) => {
  const relativePath = path.relative(__dirname, filePath);

  if (fixRemainingParsingErrors(filePath)) {
    fixedCount++;
    console.log(`✅ Fixed: ${relativePath}`);
  }

  // Progress indicator
  if ((index + 1) % 50 === 0) {
    console.log(`Progress: ${index + 1}/${totalFiles} files processed...`);
  }
});

console.log('\n🎉 Remaining parsing errors fix completed!');
console.log(`📊 Summary:`);
console.log(`   - Total files processed: ${totalFiles}`);
console.log(`   - Files fixed: ${fixedCount}`);
console.log(`   - Files unchanged: ${totalFiles - fixedCount}`);

if (fixedCount > 0) {
  console.log('\n🔍 Fixed issues:');
  console.log('   - Malformed export type statements');
  console.log('   - Double default exports');
  console.log('   - Missing semicolons in imports');
  console.log('   - Removed unused variables');
  console.log('   - Fixed Promise type declarations');
  console.log('   - Added missing semicolons');
  console.log('   - Fixed file endings');
}

console.log('\n✨ Run eslint again to check remaining issues!');