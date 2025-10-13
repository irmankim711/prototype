const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Function to recursively get all TypeScript/JSX files
function getAllTsFiles(dir, files = []) {
  const items = fs.readdirSync(dir);

  for (const item of items) {
    const fullPath = path.join(dir, item);
    const stat = fs.statSync(fullPath);

    if (stat.isDirectory() && !item.includes('node_modules') && !item.includes('.git')) {
      getAllTsFiles(fullPath, files);
    } else if (item.endsWith('.tsx') || item.endsWith('.ts')) {
      files.push(fullPath);
    }
  }

  return files;
}

// Function to fix common issues
function fixFile(filePath) {
  try {
    let content = fs.readFileSync(filePath, 'utf8');
    let modified = false;

    // Remove unused imports - check each import line
    const lines = content.split('\n');
    const newLines = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      let skipLine = false;

      // Check if this is an import line with unused imports
      if (line.includes('import') && line.includes('{')) {
        const restOfFile = lines.slice(i + 1).join('\n');

        // List of commonly unused imports to check
        const unusedImports = [
          'Divider', 'Warning', 'Timeline', 'Speed', 'Tooltip', 'Visibility',
          'ErrorIcon', 'Dialog', 'DialogTitle', 'DialogContent', 'DialogActions',
          'Box', 'getAuth', 'onAuthStateChanged', 'useEffect'
        ];

        for (const imp of unusedImports) {
          if (line.includes(`'${imp}'`) || line.includes(`"${imp}"`)) {
            // Check if used in file
            const usagePattern = new RegExp(`<${imp}|${imp}\\(`, 'g');
            if (!usagePattern.test(restOfFile)) {
              console.log(`Removing unused import in ${filePath}: ${imp}`);
              // Remove this import from the line
              const regex = new RegExp(`\\s*,?\\s*${imp}\\s*,?`, 'g');
              line = line.replace(regex, '');
              modified = true;
            }
          }
        }

        // If the import line is now empty or only has braces, skip it
        if (line.match(/import\s*\{\s*\}\s*from/) || line.trim() === 'import {') {
          skipLine = true;
          modified = true;
        }
      }

      if (!skipLine) {
        newLines.push(line);
      }
    }

    content = newLines.join('\n');

    // Fix common 'any' types
    const originalContent = content;
    content = content.replace(/:\s*any\b/g, ': unknown');
    content = content.replace(/as\s+any\b/g, 'as unknown');
    content = content.replace(/=\s*any\b/g, '= unknown');

    // Fix event handler types more specifically
    content = content.replace(/\(event:\s*any\)/g, '(event: React.FormEvent)');
    content = content.replace(/\(e:\s*any\)/g, '(e: React.FormEvent)');
    content = content.replace(/\(error:\s*any\)/g, '(error: Error)');
    content = content.replace(/\(err:\s*any\)/g, '(err: Error)');
    content = content.replace(/\(response:\s*any\)/g, '(response: unknown)');
    content = content.replace(/\(data:\s*any\)/g, '(data: unknown)');
    content = content.replace(/\(result:\s*any\)/g, '(result: unknown)');

    if (originalContent !== content) {
      modified = true;
    }

    // Comment out unused variables
    const unusedVars = [
      'showPreview', 'selectedSheet', 'setSelectedSheet', 'showCreateDialog',
      'onCancel', 'getStatusColor', 'error', 'response', '_rules'
    ];

    for (const varName of unusedVars) {
      const regex = new RegExp(`(\\s+)(const|let|var)\\s+(${varName})\\s*=([^;]*);`, 'g');
      const replacement = content.replace(regex, (match, indent, keyword, name, assignment) => {
        // Check if variable is actually used later in the file
        const afterDeclaration = content.substring(content.indexOf(match) + match.length);
        if (!afterDeclaration.includes(name) || afterDeclaration.split(name).length <= 2) {
          modified = true;
          return `${indent}// ${keyword} ${name} = ${assignment}; // Commented out - unused variable`;
        }
        return match;
      });
      content = replacement;
    }

    if (modified) {
      fs.writeFileSync(filePath, content);
      console.log(`Fixed: ${filePath}`);
      return true;
    }

  } catch (error) {
    console.error(`Error processing ${filePath}:`, error.message);
  }
  return false;
}

// Main execution
const srcDir = path.join(__dirname, 'src');
const files = getAllTsFiles(srcDir);

console.log(`Processing ${files.length} TypeScript files...`);

let fixedCount = 0;
files.forEach(file => {
  if (fixFile(file)) {
    fixedCount++;
  }
});

console.log(`Lint fix script completed! Fixed ${fixedCount} files.`);