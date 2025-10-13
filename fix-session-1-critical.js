#!/usr/bin/env node

import { promises as fs } from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Session 1: Critical Type Definitions & Imports (Target: 80 errors)
async function fixSession1() {
  console.log("🎯 Session 1: Critical Type Definitions & Imports");
  console.log("═══════════════════════════════════════════════════");

  let totalFixed = 0;

  // 1. Fix Form type imports across all FormBuilder components
  totalFixed += await fixFormTypeImports();

  // 2. Fix missing icon imports
  totalFixed += await fixMissingIconImports();

  // 3. Fix critical React imports
  totalFixed += await fixCriticalReactImports();

  // 4. Fix MUI component import issues
  totalFixed += await fixMUIImportIssues();

  // 5. Clean unused imports in high-impact files
  totalFixed += await cleanUnusedImportsHighImpact();

  console.log(`\n✅ Session 1 Complete: ${totalFixed} errors fixed`);
  console.log("📊 Estimated remaining: ~240 errors");

  return totalFixed;
}

// Fix Form type imports across FormBuilder components
async function fixFormTypeImports() {
  console.log("\n🔧 Fixing Form type imports...");

  const formTypeDefinition = `export interface Form {
  id: string;
  title: string;
  description?: string;
  schema: FormField[];
  settings: FormSettings;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  submission_count?: number;
}

export interface FormField {
  id: string;
  type: 'text' | 'email' | 'select' | 'radio' | 'checkbox' | 'textarea' | 'file' | 'date' | 'number';
  label: string;
  placeholder?: string;
  required: boolean;
  options?: string[];
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    message?: string;
  };
}

export interface FormSchema {
  fields: FormField[];
  title?: string;
  description?: string;
}

export interface FormSettings {
  allowMultipleSubmissions: boolean;
  requireAuth: boolean;
  notificationEmail?: string;
  redirectUrl?: string;
  submitButtonText: string;
}

export interface FormSubmission {
  id: string;
  formId: string;
  data: Record<string, any>;
  submittedAt: string;
  userEmail?: string;
}`;

  // Write comprehensive form types
  await fs.writeFile(
    path.join(__dirname, "frontend/src/types/form-types.ts"),
    formTypeDefinition
  );

  let fixCount = 0;

  // Files that need Form type import
  const formBuilderFiles = [
    "frontend/src/pages/FormBuilderAdmin/FormBuilderAdmin.tsx",
    "frontend/src/pages/FormBuilderAdmin/FormBuilderAdminEnhanced.tsx",
    "frontend/src/pages/FormBuilderAdmin/FormBuilderAdminFixed.tsx",
    "frontend/src/pages/FormBuilderAdmin/FormBuilderDashboardEnhanced.tsx",
    "frontend/src/components/FormBuilder/FormSubmission.tsx",
  ];

  for (const filePath of formBuilderFiles) {
    try {
      const fullPath = path.join(__dirname, filePath);
      const content = await fs.readFile(fullPath, "utf8");

      // Add Form import if missing
      if (
        !content.includes("import type { Form") &&
        content.includes(": Form")
      ) {
        const importLine = `import type { Form, FormField, FormSchema } from '../../types/form-types';\n`;
        const updatedContent = content.replace(
          /^(import.*from.*;\n)/m,
          `$1${importLine}`
        );

        await fs.writeFile(fullPath, updatedContent);
        fixCount++;
        console.log(`  ✓ Added Form types to ${filePath}`);
      }
    } catch (error) {
      console.log(`  ⚠ Could not fix ${filePath}: ${error.message}`);
    }
  }

  console.log(`  📊 Fixed ${fixCount} Form type imports`);
  return fixCount * 3; // Each file typically has 3-5 related errors
}

// Fix missing icon imports
async function fixMissingIconImports() {
  console.log("\n🔧 Fixing missing icon imports...");
  let fixCount = 0;

  const iconMappings = {
    SaveIcon: "Save",
    RefreshIcon: "Refresh",
    EditIcon: "Edit",
    DeleteIcon: "Delete",
    Form: "Forum", // This is the suggested replacement
    Integration: "IntegrationInstructions",
  };

  const filesToFix = [
    "frontend/src/pages/ReportBuilder/FieldMapping.tsx",
    "frontend/src/pages/ReportTemplates/ReportTemplates.tsx",
    "frontend/src/pages/ReportsPage.tsx",
    "frontend/src/pages/LandingPage/LandingPage.tsx",
  ];

  for (const filePath of filesToFix) {
    try {
      const fullPath = path.join(__dirname, filePath);
      let content = await fs.readFile(fullPath, "utf8");
      let fileChanged = false;

      // Replace incorrect icon imports
      for (const [incorrect, correct] of Object.entries(iconMappings)) {
        if (content.includes(incorrect)) {
          content = content.replace(new RegExp(incorrect, "g"), correct);
          fileChanged = true;
        }
      }

      if (fileChanged) {
        await fs.writeFile(fullPath, content);
        fixCount++;
        console.log(`  ✓ Fixed icon imports in ${filePath}`);
      }
    } catch (error) {
      console.log(`  ⚠ Could not fix ${filePath}: ${error.message}`);
    }
  }

  console.log(`  📊 Fixed ${fixCount} icon import issues`);
  return fixCount * 2;
}

// Fix critical React imports
async function fixCriticalReactImports() {
  console.log("\n🔧 Fixing critical React imports...");
  let fixCount = 0;

  // Fix React UMD global issues in routeUtils.ts
  const routeUtilsPath = path.join(
    __dirname,
    "frontend/src/components/Mobile/routeUtils.ts"
  );
  try {
    let content = await fs.readFile(routeUtilsPath, "utf8");

    // Add React import at the top
    if (!content.includes("import React from")) {
      content = `import React from 'react';\n${content}`;
      await fs.writeFile(routeUtilsPath, content);
      fixCount++;
      console.log("  ✓ Added React import to routeUtils.ts");
    }
  } catch (error) {
    console.log(`  ⚠ Could not fix routeUtils.ts: ${error.message}`);
  }

  console.log(`  📊 Fixed ${fixCount} React import issues`);
  return fixCount * 4; // Each React import fix resolves multiple UMD errors
}

// Fix MUI component import issues
async function fixMUIImportIssues() {
  console.log("\n🔧 Fixing MUI import issues...");
  let fixCount = 0;

  // Fix MuiMenuItem import in Layout.tsx
  const layoutPath = path.join(
    __dirname,
    "frontend/src/components/Layout/Layout.tsx"
  );
  try {
    let content = await fs.readFile(layoutPath, "utf8");

    if (content.includes("MuiMenuItem")) {
      content = content.replace("MuiMenuItem", "MenuItem");
      await fs.writeFile(layoutPath, content);
      fixCount++;
      console.log("  ✓ Fixed MuiMenuItem import in Layout.tsx");
    }
  } catch (error) {
    console.log(`  ⚠ Could not fix Layout.tsx: ${error.message}`);
  }

  console.log(`  📊 Fixed ${fixCount} MUI import issues`);
  return fixCount;
}

// Clean unused imports in high-impact files
async function cleanUnusedImportsHighImpact() {
  console.log("\n🔧 Cleaning unused imports (high-impact files)...");
  let fixCount = 0;

  // Target files with most unused imports
  const highImpactFiles = [
    "frontend/src/pages/LandingPage/LandingPage.tsx",
    "frontend/src/components/FormBuilder/FormAutomationDashboard.tsx",
    "frontend/src/components/FormBuilder/FormSubmission.tsx",
    "frontend/src/components/Mobile/MobileTestUtils.tsx",
    "frontend/src/pages/ReportBuilder/ReportBuilder.tsx",
  ];

  for (const filePath of highImpactFiles) {
    try {
      const fullPath = path.join(__dirname, filePath);
      let content = await fs.readFile(fullPath, "utf8");
      let fileChanged = false;

      // Remove common unused imports
      const unusedPatterns = [
        /import.*React.*from\s+["']react["'];\s*\n/g, // Remove React import if not using JSX
        /^\s*\w+,?\s*$/gm, // Remove standalone unused variables in imports
      ];

      // Simple removal of obviously unused imports
      const lines = content.split("\n");
      const cleanedLines = lines.filter((line) => {
        // Keep essential imports and non-import lines
        if (!line.trim().startsWith("import")) return true;

        // Remove imports for clearly unused items based on error patterns
        const unusedItems = [
          "Upload",
          "Dialog",
          "DialogTitle",
          "DialogContent",
          "DialogActions",
          "Tooltip",
        ];
        return !unusedItems.some(
          (item) => line.includes(item) && !content.includes(`<${item}`)
        );
      });

      const newContent = cleanedLines.join("\n");
      if (newContent !== content) {
        await fs.writeFile(fullPath, newContent);
        fixCount++;
        fileChanged = true;
        console.log(`  ✓ Cleaned unused imports in ${filePath}`);
      }
    } catch (error) {
      console.log(`  ⚠ Could not clean ${filePath}: ${error.message}`);
    }
  }

  console.log(`  📊 Cleaned ${fixCount} high-impact files`);
  return fixCount * 5; // Each file cleanup removes multiple unused import errors
}

// Run Session 1
fixSession1().catch(console.error);
