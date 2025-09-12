/**
 * Conditional Logic Engine for Advanced Form Builder
 * Handles rule evaluation, field visibility, and dynamic form behavior
 */

import type {
  ConditionalRule,
  FormField,
  ConditionalContext,
  RuleEvaluation,
  FormFieldValue,
} from "../types/formBuilder";

export class ConditionalLogicEngine {
  private context: ConditionalContext;

  constructor() {
    this.context = {
      formData: {},
      fieldStates: {},
      evaluationResults: [],
    };
  }

  /**
   * Update form data and trigger rule evaluation
   */
  updateFormData(fieldId: string, value: FormFieldValue): ConditionalContext {
    this.context.formData[fieldId] = value;
    return this.evaluateAllRules();
  }

  /**
   * Set initial form data
   */
  setFormData(data: Record<string, FormFieldValue>): ConditionalContext {
    this.context.formData = { ...data };
    return this.evaluateAllRules();
  }

  /**
   * Initialize field states
   */
  initializeFieldStates(fields: FormField[]): void {
    fields.forEach((field) => {
      this.context.fieldStates[field.id] = {
        visible: !field.hidden,
        required: field.required || false,
        disabled: field.readonly || false,
        value: field.default_value || null,
      };
    });
  }

  /**
   * Evaluate all conditional rules
   */
  evaluateAllRules(): ConditionalContext {
    this.context.evaluationResults = [];

    // Get all rules from all fields
    const allRules = this.getAllRules();

    // Sort rules by priority (higher priority first)
    const sortedRules = allRules.sort(
      (a, b) => (b.priority || 0) - (a.priority || 0)
    );

    // Evaluate each rule
    sortedRules.forEach((rule) => {
      const evaluation = this.evaluateRule(rule);
      this.context.evaluationResults.push(evaluation);

      if (evaluation.passed) {
        this.applyRuleAction(rule);
      } else {
        this.revertRuleAction(rule);
      }
    });

    return { ...this.context };
  }

  /**
   * Evaluate a single conditional rule
   */
  private evaluateRule(rule: ConditionalRule): RuleEvaluation {
    const sourceValue = this.context.formData[rule.sourceFieldId];
    const targetValue = rule.value;

    let passed = false;

    switch (rule.condition) {
      case "equals":
        passed = sourceValue === targetValue;
        break;

      case "not_equals":
        passed = sourceValue !== targetValue;
        break;

      case "contains":
        if (
          typeof sourceValue === "string" &&
          typeof targetValue === "string"
        ) {
          passed = sourceValue
            .toLowerCase()
            .includes(targetValue.toLowerCase());
        } else if (Array.isArray(sourceValue)) {
          passed = sourceValue.includes(targetValue);
        }
        break;

      case "not_contains":
        if (
          typeof sourceValue === "string" &&
          typeof targetValue === "string"
        ) {
          passed = !sourceValue
            .toLowerCase()
            .includes(targetValue.toLowerCase());
        } else if (Array.isArray(sourceValue)) {
          passed = !sourceValue.includes(targetValue);
        }
        break;

      case "greater_than":
        if (
          typeof sourceValue === "number" &&
          typeof targetValue === "number"
        ) {
          passed = sourceValue > targetValue;
        } else if (
          typeof sourceValue === "string" &&
          typeof targetValue === "string"
        ) {
          passed = sourceValue.length > targetValue.length;
        }
        break;

      case "less_than":
        if (
          typeof sourceValue === "number" &&
          typeof targetValue === "number"
        ) {
          passed = sourceValue < targetValue;
        } else if (
          typeof sourceValue === "string" &&
          typeof targetValue === "string"
        ) {
          passed = sourceValue.length < targetValue.length;
        }
        break;

      case "greater_equal":
        if (
          typeof sourceValue === "number" &&
          typeof targetValue === "number"
        ) {
          passed = sourceValue >= targetValue;
        }
        break;

      case "less_equal":
        if (
          typeof sourceValue === "number" &&
          typeof targetValue === "number"
        ) {
          passed = sourceValue <= targetValue;
        }
        break;

      case "is_empty":
        passed =
          !sourceValue ||
          sourceValue === "" ||
          (Array.isArray(sourceValue) && sourceValue.length === 0);
        break;

      case "is_not_empty":
        passed =
          sourceValue !== null &&
          sourceValue !== undefined &&
          sourceValue !== "" &&
          (!Array.isArray(sourceValue) || sourceValue.length > 0);
        break;

      case "regex_match":
        if (
          typeof sourceValue === "string" &&
          typeof targetValue === "string"
        ) {
          try {
            const regex = new RegExp(targetValue);
            passed = regex.test(sourceValue);
          } catch {
            console.warn("Invalid regex pattern:", targetValue);
            passed = false;
          }
        }
        break;

      default:
        console.warn("Unknown condition:", rule.condition);
        passed = false;
    }

    return {
      ruleId: rule.id,
      passed,
      sourceValue,
      targetValue,
      condition: rule.condition,
    };
  }

  /**
   * Apply rule action to target fields
   */
  private applyRuleAction(rule: ConditionalRule): void {
    rule.targetFieldIds.forEach((fieldId) => {
      if (!this.context.fieldStates[fieldId]) {
        this.context.fieldStates[fieldId] = {
          visible: true,
          required: false,
          disabled: false,
          value: null,
        };
      }

      const fieldState = this.context.fieldStates[fieldId];

      switch (rule.action) {
        case "show":
          fieldState.visible = true;
          break;

        case "hide":
          fieldState.visible = false;
          break;

        case "require":
          fieldState.required = true;
          break;

        case "disable":
          fieldState.disabled = true;
          break;

        case "set_value":
          fieldState.value = rule.value;
          this.context.formData[fieldId] = rule.value;
          break;

        case "calculate": {
          const calculatedValue = this.calculateFieldValue(rule);
          if (calculatedValue !== null) {
            fieldState.value = calculatedValue;
            this.context.formData[fieldId] = calculatedValue;
          }
          break;
        }
      }
    });
  }

  /**
   * Revert rule action (when rule condition is false)
   */
  private revertRuleAction(rule: ConditionalRule): void {
    rule.targetFieldIds.forEach((fieldId) => {
      const fieldState = this.context.fieldStates[fieldId];
      if (!fieldState) return;

      switch (rule.action) {
        case "show":
          // Don't automatically hide unless explicitly hidden by another rule
          break;

        case "hide":
          fieldState.visible = true;
          break;

        case "require":
          // Don't automatically unrequire unless specified
          break;

        case "disable":
          fieldState.disabled = false;
          break;

        case "set_value":
          // Clear the set value
          fieldState.value = null;
          delete this.context.formData[fieldId];
          break;
      }
    });
  }

  /**
   * Calculate field value based on rule
   */
  private calculateFieldValue(rule: ConditionalRule): FormFieldValue | null {
    // This is a simplified calculation engine
    // In a real implementation, you might use a formula parser

    if (typeof rule.value === "string" && rule.value.includes("{")) {
      // Parse formula like "{field1} + {field2}"
      let formula = rule.value;

      // Replace field references with actual values
      Object.keys(this.context.formData).forEach((key) => {
        const value = this.context.formData[key];
        if (typeof value === "number") {
          formula = formula.replace(
            new RegExp(`{${key}}`, "g"),
            value.toString()
          );
        }
      });

      try {
        // WARNING: eval is dangerous in production - use a proper formula parser
        const result = Function('"use strict"; return (' + formula + ")")();
        return typeof result === "number" ? result : null;
      } catch (e) {
        console.warn("Calculation error:", e);
        return null;
      }
    }

    return rule.value;
  }

  /**
   * Get all rules from all fields
   */
  private getAllRules(): ConditionalRule[] {
    // This would typically be passed in during initialization
    // For now, return empty array - rules should be stored in the engine
    return [];
  }

  /**
   * Add rules to the engine
   */
  addRules(_rules: ConditionalRule[]): void {
    // Store rules for evaluation
    // Implementation depends on how you want to store rules
  }

  /**
   * Get current field state
   */
  getFieldState(fieldId: string) {
    return (
      this.context.fieldStates[fieldId] || {
        visible: true,
        required: false,
        disabled: false,
        value: null,
      }
    );
  }

  /**
   * Get all field states
   */
  getAllFieldStates() {
    return { ...this.context.fieldStates };
  }

  /**
   * Get evaluation results for debugging
   */
  getEvaluationResults(): RuleEvaluation[] {
    return [...this.context.evaluationResults];
  }

  /**
   * Reset the engine state
   */
  reset(): void {
    this.context = {
      formData: {},
      fieldStates: {},
      evaluationResults: [],
    };
  }

  /**
   * Validate conditional logic setup
   */
  validateRules(
    rules: ConditionalRule[],
    fields: FormField[]
  ): {
    valid: boolean;
    errors: string[];
    warnings: string[];
  } {
    const errors: string[] = [];
    const warnings: string[] = [];
    const fieldIds = new Set(fields.map((f) => f.id));

    rules.forEach((rule) => {
      // Check if source field exists
      if (!fieldIds.has(rule.sourceFieldId)) {
        errors.push(
          `Rule ${rule.id}: Source field ${rule.sourceFieldId} does not exist`
        );
      }

      // Check if target fields exist
      rule.targetFieldIds.forEach((targetId) => {
        if (!fieldIds.has(targetId)) {
          errors.push(
            `Rule ${rule.id}: Target field ${targetId} does not exist`
          );
        }
      });

      // Check for circular dependencies
      if (rule.targetFieldIds.includes(rule.sourceFieldId)) {
        warnings.push(`Rule ${rule.id}: Circular dependency detected`);
      }

      // Validate condition value types
      if (
        ["greater_than", "less_than", "greater_equal", "less_equal"].includes(
          rule.condition
        )
      ) {
        if (typeof rule.value !== "number") {
          warnings.push(
            `Rule ${rule.id}: Numeric condition with non-numeric value`
          );
        }
      }
    });

    return {
      valid: errors.length === 0,
      errors,
      warnings,
    };
  }
}

/**
 * Rule Builder Helper Functions
 */
export class RuleBuilder {
  private rule: Partial<ConditionalRule>;

  constructor() {
    this.rule = {
      id: this.generateId(),
      targetFieldIds: [],
    };
  }

  private generateId(): string {
    return `rule_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  when(sourceFieldId: string): RuleBuilder {
    this.rule.sourceFieldId = sourceFieldId;
    return this;
  }

  equals(value: FormFieldValue): RuleBuilder {
    this.rule.condition = "equals";
    this.rule.value = value;
    return this;
  }

  notEquals(value: FormFieldValue): RuleBuilder {
    this.rule.condition = "not_equals";
    this.rule.value = value;
    return this;
  }

  contains(value: string): RuleBuilder {
    this.rule.condition = "contains";
    this.rule.value = value;
    return this;
  }

  isEmpty(): RuleBuilder {
    this.rule.condition = "is_empty";
    return this;
  }

  isNotEmpty(): RuleBuilder {
    this.rule.condition = "is_not_empty";
    return this;
  }

  greaterThan(value: number): RuleBuilder {
    this.rule.condition = "greater_than";
    this.rule.value = value;
    return this;
  }

  lessThan(value: number): RuleBuilder {
    this.rule.condition = "less_than";
    this.rule.value = value;
    return this;
  }

  matches(pattern: string): RuleBuilder {
    this.rule.condition = "regex_match";
    this.rule.value = pattern;
    return this;
  }

  then(): RuleActionBuilder {
    return new RuleActionBuilder(this.rule);
  }

  build(): ConditionalRule {
    if (!this.rule.sourceFieldId || !this.rule.condition || !this.rule.action) {
      throw new Error(
        "Incomplete rule: missing source field, condition, or action"
      );
    }

    return this.rule as ConditionalRule;
  }
}

export class RuleActionBuilder {
  private rule: Partial<ConditionalRule>;

  constructor(rule: Partial<ConditionalRule>) {
    this.rule = rule;
  }

  show(...fieldIds: string[]): RuleActionBuilder {
    this.rule.action = "show";
    this.rule.targetFieldIds = fieldIds;
    return this;
  }

  hide(...fieldIds: string[]): RuleActionBuilder {
    this.rule.action = "hide";
    this.rule.targetFieldIds = fieldIds;
    return this;
  }

  require(...fieldIds: string[]): RuleActionBuilder {
    this.rule.action = "require";
    this.rule.targetFieldIds = fieldIds;
    return this;
  }

  disable(...fieldIds: string[]): RuleActionBuilder {
    this.rule.action = "disable";
    this.rule.targetFieldIds = fieldIds;
    return this;
  }

  setValue(value: FormFieldValue, ...fieldIds: string[]): RuleActionBuilder {
    this.rule.action = "set_value";
    this.rule.value = value;
    this.rule.targetFieldIds = fieldIds;
    return this;
  }

  calculate(formula: string, ...fieldIds: string[]): RuleActionBuilder {
    this.rule.action = "calculate";
    this.rule.value = formula;
    this.rule.targetFieldIds = fieldIds;
    return this;
  }

  withPriority(priority: number): RuleActionBuilder {
    this.rule.priority = priority;
    return this;
  }

  build(): ConditionalRule {
    if (!this.rule.sourceFieldId || !this.rule.condition || !this.rule.action) {
      throw new Error(
        "Incomplete rule: missing source field, condition, or action"
      );
    }

    return this.rule as ConditionalRule;
  }
}

// Example usage:
/*
const rule = new RuleBuilder()
  .when('age')
  .greaterThan(18)
  .then()
  .show('consent_checkbox')
  .withPriority(10)
  .build();

const engine = new ConditionalLogicEngine();
engine.addRules([rule]);
engine.updateFormData('age', 25);
*/
