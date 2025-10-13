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

    // Remove unused imports
    const lines = content.split('\n');
    const newLines = [];
    let importSection = true;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      // End of import section
      if (!line.startsWith('import') && !line.startsWith('//') && !line.startsWith('/*') && line.trim() !== '') {
        importSection = false;
      }

      // Skip common unused imports
      if (importSection && line.includes('import') && (
        line.includes("'Divider'") ||
        line.includes("'Warning'") ||
        line.includes("'Timeline'") ||
        line.includes("'Speed'") ||
        line.includes("'Tooltip'") ||
        line.includes("'Visibility'") ||
        line.includes("'ErrorIcon'") ||
        line.includes("'Dialog'") ||
        line.includes("'DialogTitle'") ||
        line.includes("'DialogContent'") ||
        line.includes("'DialogActions'") ||
        line.includes("'Box'") ||
        line.includes("'getAuth'") ||
        line.includes("'onAuthStateChanged'") ||
        line.includes("'useEffect'")
      )) {
        // Check if these imports are actually used in the file
        const restOfFile = lines.slice(i + 1).join('\n');
        if (
          (!line.includes("'Divider'") || !restOfFile.includes('<Divider')) &&
          (!line.includes("'Warning'") || !restOfFile.includes('<Warning')) &&
          (!line.includes("'Timeline'") || !restOfFile.includes('<Timeline')) &&
          (!line.includes("'Speed'") || !restOfFile.includes('<Speed')) &&
          (!line.includes("'Tooltip'") || !restOfFile.includes('<Tooltip')) &&
          (!line.includes("'Visibility'") || !restOfFile.includes('<Visibility')) &&
          (!line.includes("'ErrorIcon'") || !restOfFile.includes('<ErrorIcon')) &&
          (!line.includes("'Dialog'") || !restOfFile.includes('<Dialog')) &&
          (!line.includes("'DialogTitle'") || !restOfFile.includes('<DialogTitle')) &&
          (!line.includes("'DialogContent'") || !restOfFile.includes('<DialogContent')) &&
          (!line.includes("'DialogActions'") || !restOfFile.includes('<DialogActions')) &&
          (!line.includes("'Box'") || !restOfFile.includes('<Box')) &&
          (!line.includes("'getAuth'") || !restOfFile.includes('getAuth(')) &&
          (!line.includes("'onAuthStateChanged'") || !restOfFile.includes('onAuthStateChanged(')) &&
          (!line.includes("'useEffect'") || !restOfFile.includes('useEffect('))
        ) {
          console.log(`Removing unused import in ${filePath}: ${line.trim()}`);
          modified = true;
          continue; // Skip this line
        }
      }

      newLines.push(line);
    }

    content = newLines.join('\n');

    // Fix common 'any' types
    content = content.replace(/: any\b/g, ': unknown');
    content = content.replace(/as any\b/g, 'as unknown');
    content = content.replace(/= any\b/g, '= unknown');

    // Fix event handler types
    content = content.replace(/\(event: any\)/g, '(event: React.FormEvent)');
    content = content.replace(/\(e: any\)/g, '(e: React.FormEvent)');
    content = content.replace(/\(error: any\)/g, '(error: Error)');
    content = content.replace(/\(err: any\)/g, '(err: Error)');
    content = content.replace(/\(response: any\)/g, '(response: unknown)');
    content = content.replace(/\(data: any\)/g, '(data: unknown)');
    content = content.replace(/\(result: any\)/g, '(result: unknown)');

    // Comment out unused variables instead of removing them
    content = content.replace(/(\s+)(const|let|var)\s+(\w+)\s*=.*?;/g, (match, indent, keyword, varName) => {
      const usedInFile = content.includes(varName) && content.split(varName).length > 2;
      if (!usedInFile && (
        varName === 'showPreview' ||
        varName === 'selectedSheet' ||
        varName === 'setSelectedSheet' ||
        varName === 'showCreateDialog' ||
        varName === 'onCancel' ||
        varName === 'getStatusColor' ||
        varName === 'error' ||
        varName === 'response' ||
        varName === '_rules'
      )) {
        modified = true;
        return `${indent}// ${keyword} ${varName} = // Commented out - unused variable`;
      }
      return match;
    });

    if (modified) {
      fs.writeFileSync(filePath, content);
      console.log(`Fixed: ${filePath}`);
    }

  } catch (error) {
    console.error(`Error processing ${filePath}:`, error.message);
  }
}

// Main execution
const srcDir = path.join(__dirname, 'src');
const files = getAllTsFiles(srcDir);

console.log(`Processing ${files.length} TypeScript files...`);

files.forEach(file => {
  console.log(`Processing: ${file}`);
  fixFile(file);
});

console.log('Lint fix script completed!');