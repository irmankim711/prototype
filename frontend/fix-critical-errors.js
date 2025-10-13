import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Critical fixes for remaining TypeScript errors
const criticalFixes = [
  {
    // Fix Form import for FormBuilder files
    files: ["**/FormBuilder*.tsx"],
    pattern: /^(?!.*import.*Form)/m,
    replacement: 'import { Form } from "../../types/form-types";\n',
    insertAt: "afterImports",
  },
  {
    // Fix missing icon imports
    files: ["**/ReportsPage.tsx"],
    pattern:
      /import \{ Assessment, Form, Analytics \} from "@mui\/icons-material";/,
    replacement:
      'import { Assessment, Forum as Form, Analytics } from "@mui/icons-material";',
  },
  {
    // Remove duplicate api exports
    files: ["**/api-old.ts"],
    pattern:
      /export const (fetchRecentReports|fetchReportStats|fetchReportTemplates|createReport|getReportStatus) = async[\s\S]*?};/g,
    replacement: "// Duplicate export removed",
    onlyFirst: true,
  },
  {
    // Fix undefined React in routeUtils
    files: ["**/routeUtils.ts"],
    pattern: /React\./g,
    replacement: "React.default.",
  },
];

// Apply fixes
function applyFixes() {
  console.log("🔧 Applying critical TypeScript fixes...\n");

  criticalFixes.forEach((fix, index) => {
    console.log(`${index + 1}. Processing ${fix.files}`);

    // Find matching files
    const files = findFiles(fix.files);

    files.forEach((file) => {
      try {
        let content = fs.readFileSync(file, "utf8");
        const originalContent = content;

        if (fix.pattern && fix.replacement) {
          if (fix.onlyFirst) {
            // Only replace the first occurrence for duplicates
            let replaced = false;
            content = content.replace(fix.pattern, (match) => {
              if (!replaced) {
                replaced = true;
                return fix.replacement;
              }
              return match;
            });
          } else {
            content = content.replace(fix.pattern, fix.replacement);
          }
        }

        if (content !== originalContent) {
          fs.writeFileSync(file, content, "utf8");
          console.log(`   ✓ Fixed ${path.relative(__dirname, file)}`);
        }
      } catch (error) {
        console.error(`   ❌ Error processing ${file}:`, error.message);
      }
    });
  });

  console.log("\n✅ Critical fixes applied!");
}

function findFiles(pattern) {
  // Simple glob-like file finding
  const srcDir = path.join(__dirname, "src");
  const files = [];

  function walkDir(dir) {
    const items = fs.readdirSync(dir, { withFileTypes: true });

    for (const item of items) {
      const fullPath = path.join(dir, item.name);

      if (
        item.isDirectory() &&
        !item.name.includes("node_modules") &&
        !item.name.includes("__tests__")
      ) {
        walkDir(fullPath);
      } else if (item.isFile()) {
        // Simple pattern matching
        const relativePath = path.relative(srcDir, fullPath);
        if (pattern.includes("**") && pattern.includes(".tsx")) {
          if (
            fullPath.endsWith(".tsx") &&
            relativePath.includes(
              pattern.replace("**/", "").replace(".tsx", "")
            )
          ) {
            files.push(fullPath);
          }
        } else if (pattern.includes(item.name)) {
          files.push(fullPath);
        }
      }
    }
  }

  walkDir(srcDir);
  return files;
}

// Run the script
applyFixes();
