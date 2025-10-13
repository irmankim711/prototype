/**
 * Mobile-Optimized Form Builder Component
 * Touch-friendly form creation with drag-and-drop support
 */

import React from "react";
import { useState, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  Plus,
  Trash2,
  Settings,
  Eye,
  Save,
  ArrowUp,
  ArrowDown,
  GripVertical,
  Type,
  Mail,
  Hash,
  Calendar,
  List,
  MessageSquare,
  Phone,
  Link,
  CheckSquare,
  Image,
} from "lucide-react";
import { MobileHeader } from "./MobileNavigation";
import {
  MobileCard,
  MobileButton,
  MobileInput,
  MobileModal,
} from "./MobileComponents";
import { useTouchGestures, useViewport } from "../../hooks/useTouchGestures";

interface FormField {
  id: string;
  type: string;
  label: string;
  placeholder?: string;
  required: boolean;
  options?: string[];
  validation?: {
    minLength?: number;
    maxLength?: number;
    pattern?: string;
  };
}

interface FieldType {
  type: string;
  label: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  category: "basic" | "advanced" | "layout";
  description: string;
}

const fieldTypes: FieldType[] = [
  {
    type: "text",
    label: "Text Input",
    icon: Type,
    category: "basic",
    description: "Single line text input",
  },
  {
    type: "email",
    label: "Email",
    icon: Mail,
    category: "basic",
    description: "Email address input",
  },
  {
    type: "number",
    label: "Number",
    icon: Hash,
    category: "basic",
    description: "Numeric input",
  },
  {
    type: "phone",
    label: "Phone",
    icon: Phone,
    category: "basic",
    description: "Phone number input",
  },
  {
    type: "date",
    label: "Date",
    icon: Calendar,
    category: "basic",
    description: "Date picker",
  },
  {
    type: "select",
    label: "Dropdown",
    icon: List,
    category: "basic",
    description: "Dropdown selection",
  },
  {
    type: "textarea",
    label: "Long Text",
    icon: MessageSquare,
    category: "basic",
    description: "Multi-line text input",
  },
  {
    type: "checkbox",
    label: "Checkbox",
    icon: CheckSquare,
    category: "advanced",
    description: "Multiple choice selection",
  },
  {
    type: "url",
    label: "URL",
    icon: Link,
    category: "advanced",
    description: "Website URL input",
  },
  {
    type: "file",
    label: "File Upload",
    icon: Image,
    category: "advanced",
    description: "File upload field",
  },
];

const MobileFormBuilder: React.FC = () => {
  const navigate = useNavigate();
  const { isMobile } = useViewport();

  const [formTitle, setFormTitle] = useState("Untitled Form");
  const [formDescription, setFormDescription] = useState("");
  const [fields, setFields] = useState<FormField[]>([]);
  const [selectedFieldId, setSelectedFieldId] = useState<string | null>(null);
  const [showFieldTypes, setShowFieldTypes] = useState(false);
  const [showFieldEditor, setShowFieldEditor] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [draggedField, setDraggedField] = useState<FormField | null>(null);
  const [isDirty, setIsDirty] = useState(false);

  // Generate unique field ID
  const generateFieldId = () =>
    `field_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

  // Add new field
  const addField = useCallback((fieldType: string) => {
    const newField: FormField = {
      id: generateFieldId(),
      type: fieldType,
      label: `New ${fieldType} field`,
      placeholder: `Enter ${fieldType}...`,
      required: false,
    };

    if (fieldType === "select" || fieldType === "checkbox") {
      newField.options = ["Option 1", "Option 2"];
    }

    setFields((prev: any) => [...prev, newField]);
    setSelectedFieldId(newField.id);
    setShowFieldTypes(false);
    setShowFieldEditor(true);
    setIsDirty(true);

    // Haptic feedback
    if ("vibrate" in navigator) {
      navigator.vibrate(50);
    }
  }, []);

  // Update field
  const updateField = useCallback(
    (fieldId: string, updates: Partial<FormField>) => {
      setFields((prev: any) =>
        prev.map((field: any) =>
          field.id === fieldId ? { ...field, ...updates } : field
        )
      );
      setIsDirty(true);
    },
    []
  );

  // Delete field
  const deleteField = useCallback((fieldId: string) => {
    setFields((prev: any) => prev.filter((field: any) => field.id !== fieldId));
    setSelectedFieldId(null);
    setShowFieldEditor(false);
    setIsDirty(true);

    // Haptic feedback
    if ("vibrate" in navigator) {
      navigator.vibrate([50, 50, 50]);
    }
  }, []);

  // Move field up
  const moveFieldUp = useCallback((fieldId: string) => {
    setFields((prev: any) => {
      const index = prev.findIndex((field: any) => field.id === fieldId);
      if (index <= 0) return prev;

      const newFields = [...prev];
      [newFields[index - 1], newFields[index]] = [
        newFields[index],
        newFields[index - 1],
      ];
      return newFields;
    });
    setIsDirty(true);
  }, []);

  // Move field down
  const moveFieldDown = useCallback((fieldId: string) => {
    setFields((prev: any) => {
      const index = prev.findIndex((field: any) => field.id === fieldId);
      if (index >= prev.length - 1) return prev;

      const newFields = [...prev];
      [newFields[index], newFields[index + 1]] = [
        newFields[index + 1],
        newFields[index],
      ];
      return newFields;
    });
    setIsDirty(true);
  }, []);

  // Save form
  const saveForm = useCallback(async () => {
    try {
      // Simulate API call
      await new Promise((resolve: any) => setTimeout(resolve, 1000));

      const formData = {
        title: formTitle,
        description: formDescription,
        fields: fields,
      };

      console.log("Saving form:", formData);
      setIsDirty(false);

      // Show success feedback
      if ("vibrate" in navigator) {
        navigator.vibrate([100, 50, 100]);
      }

      // Navigate back or show success message
      navigate("/forms");
    } catch (error) {
      console.error("Failed to save form:", error);
    }
  }, [formTitle, formDescription, fields, navigate]);

  // Handle back navigation
  const handleBack = useCallback(() => {
    if (isDirty) {
      const shouldDiscard = window.confirm(
        "You have unsaved changes. Are you sure you want to leave?"
      );
      if (!shouldDiscard) return;
    }
    navigate("/forms");
  }, [isDirty, navigate]);

  // Get selected field
  const selectedField = fields.find((field: any) => field.id === selectedFieldId);

  // Render field type selector
  const renderFieldTypeSelector = () => {
    const basicFields = fieldTypes.filter(
      (field: any) => field.category === "basic"
    );
    const advancedFields = fieldTypes.filter(
      (field: any) => field.category === "advanced"
    );

    return (
      <MobileModal
        isOpen={showFieldTypes}
        onClose={() => setShowFieldTypes(false)}
        title="Add Field"
        showHandle
      >
        <div className="field-types-container">
          <div className="field-category">
            <h3 className="field-category-title">Basic Fields</h3>
            <div className="field-types-grid">
              {basicFields.map((fieldType: any) => (
                <button
                  key={fieldType.type}
                  onClick={() => addField(fieldType.type)}
                  className="field-type-button"
                >
                  <div className="field-type-icon">
                    <fieldType.icon size={24} />
                  </div>
                  <div className="field-type-content">
                    <span className="field-type-label">{fieldType.label}</span>
                    <span className="field-type-description">
                      {fieldType.description}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div className="field-category">
            <h3 className="field-category-title">Advanced Fields</h3>
            <div className="field-types-grid">
              {advancedFields.map((fieldType: any) => (
                <button
                  key={fieldType.type}
                  onClick={() => addField(fieldType.type)}
                  className="field-type-button"
                >
                  <div className="field-type-icon">
                    <fieldType.icon size={24} />
                  </div>
                  <div className="field-type-content">
                    <span className="field-type-label">{fieldType.label}</span>
                    <span className="field-type-description">
                      {fieldType.description}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </MobileModal>
    );
  };

  // Render field editor
  const renderFieldEditor = () => {
    if (!selectedField) return null;

    return (
      <MobileModal
        isOpen={showFieldEditor}
        onClose={() => setShowFieldEditor(false)}
        title="Edit Field"
        showHandle
      >
        <div className="field-editor">
          <MobileInput
            label="Field Label"
            value={selectedField.label}
            onChange={(value: any) =>
              updateField(selectedField.id, { label: value })
            }
            placeholder="Enter field label"
          />

          <MobileInput
            label="Placeholder Text"
            value={selectedField.placeholder || ""}
            onChange={(value: any) =>
              updateField(selectedField.id, { placeholder: value })
            }
            placeholder="Enter placeholder text"
          />

          <div className="field-options">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={selectedField.required}
                onChange={(e: any) =>
                  updateField(selectedField.id, { required: e.target.checked })
                }
              />
              <span>Required field</span>
            </label>
          </div>

          {(selectedField.type === "select" ||
            selectedField.type === "checkbox") && (
            <div className="field-choices">
              <h4>Options</h4>
              {selectedField.options?.map((option, index) => (
                <div key={index} className="choice-item">
                  <MobileInput
                    value={option}
                    onChange={(value: any) => {
                      const newOptions = [...(selectedField.options || [])];
                      newOptions[index] = value;
                      updateField(selectedField.id, { options: newOptions });
                    }}
                    placeholder={`Option ${index + 1}`}
                  />
                  <MobileButton
                    variant="ghost"
                    size="small"
                    onClick={() => {
                      const newOptions = selectedField.options?.filter(
                        (_, i) => i !== index
                      );
                      updateField(selectedField.id, { options: newOptions });
                    }}
                  >
                    <Trash2 size={16} />
                  </MobileButton>
                </div>
              ))}
              <MobileButton
                variant="ghost"
                size="small"
                onClick={() => {
                  const newOptions = [
                    ...(selectedField.options || []),
                    "New option",
                  ];
                  updateField(selectedField.id, { options: newOptions });
                }}
                startIcon={<Plus size={16} />}
              >
                Add Option
              </MobileButton>
            </div>
          )}

          <div className="field-editor-actions">
            <MobileButton
              variant="danger"
              onClick={() => {
                deleteField(selectedField.id);
                setShowFieldEditor(false);
              }}
              startIcon={<Trash2 size={16} />}
            >
              Delete Field
            </MobileButton>
          </div>
        </div>
      </MobileModal>
    );
  };

  // Render field preview
  const renderFieldPreview = (field: FormField) => {
    const fieldTypeInfo = fieldTypes.find((type: any) => type.type === field.type);
    const Icon = fieldTypeInfo?.icon || Type;

    return (
      <MobileCard
        key={field.id}
        className={`field-preview ${
          selectedFieldId === field.id ? "selected" : ""
        }`}
        onTap={() => {
          setSelectedFieldId(field.id);
          setShowFieldEditor(true);
        }}
        interactive
      >
        <div className="field-preview-content">
          <div className="field-preview-header">
            <div className="field-preview-icon">
              <Icon size={20} />
            </div>
            <div className="field-preview-info">
              <h4 className="field-preview-label">{field.label}</h4>
              <span className="field-preview-type">{fieldTypeInfo?.label}</span>
            </div>
            <button className="field-preview-drag">
              <GripVertical size={16} />
            </button>
          </div>

          <div className="field-preview-actions">
            <button
              onClick={(e: any) => {
                e.stopPropagation();
                moveFieldUp(field.id);
              }}
              className="field-action-button"
              disabled={fields.indexOf(field) === 0}
              aria-label="Move up"
            >
              <ArrowUp size={16} />
            </button>
            <button
              onClick={(e: any) => {
                e.stopPropagation();
                moveFieldDown(field.id);
              }}
              className="field-action-button"
              disabled={fields.indexOf(field) === fields.length - 1}
              aria-label="Move down"
            >
              <ArrowDown size={16} />
            </button>
            <button
              onClick={(e: any) => {
                e.stopPropagation();
                setSelectedFieldId(field.id);
                setShowFieldEditor(true);
              }}
              className="field-action-button"
              aria-label="Edit field"
            >
              <Settings size={16} />
            </button>
          </div>
        </div>
      </MobileCard>
    );
  };

  // Render form preview
  const renderFormPreview = () => (
    <MobileModal
      isOpen={showPreview}
      onClose={() => setShowPreview(false)}
      title="Form Preview"
      showHandle
    >
      <div className="form-preview">
        <div className="form-preview-header">
          <h2>{formTitle}</h2>
          {formDescription && <p>{formDescription}</p>}
        </div>

        <div className="form-preview-fields">
          {fields.map((field: any) => (
            <div key={field.id} className="preview-field">
              <label className="preview-field-label">
                {field.label}
                {field.required && <span className="required">*</span>}
              </label>

              {field.type === "textarea" ? (
                <textarea
                  placeholder={field.placeholder}
                  className="preview-input"
                  rows={3}
                />
              ) : field.type === "select" ? (
                <select className="preview-input">
                  <option value="">Choose an option</option>
                  {field.options?.map((option, index) => (
                    <option key={index} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              ) : field.type === "checkbox" ? (
                <div className="preview-checkboxes">
                  {field.options?.map((option, index) => (
                    <label key={index} className="preview-checkbox">
                      <input type="checkbox" />
                      <span>{option}</span>
                    </label>
                  ))}
                </div>
              ) : (
                <input
                  type={field.type}
                  placeholder={field.placeholder}
                  className="preview-input"
                />
              )}
            </div>
          ))}
        </div>

        <MobileButton variant="primary" fullWidth>
          Submit Form
        </MobileButton>
      </div>
    </MobileModal>
  );

  return (
    <div className="mobile-form-builder">
      <MobileHeader
        title="Form Builder"
        showBack
        onBack={handleBack}
        rightActions={
          <div className="header-actions">
            <MobileButton
              variant="ghost"
              size="small"
              onClick={() => setShowPreview(true)}
              startIcon={<Eye size={16} />}
            >
              Preview
            </MobileButton>
            <MobileButton
              variant="primary"
              size="small"
              onClick={saveForm}
              startIcon={<Save size={16} />}
            >
              Save
            </MobileButton>
          </div>
        }
      />

      <div className="form-builder-content">
        {/* Form Settings */}
        <section className="form-settings">
          <MobileCard>
            <MobileInput
              label="Form Title"
              value={formTitle}
              onChange={setFormTitle}
              placeholder="Enter form title"
            />
            <MobileInput
              label="Description (Optional)"
              value={formDescription}
              onChange={setFormDescription}
              placeholder="Enter form description"
            />
          </MobileCard>
        </section>

        {/* Form Fields */}
        <section className="form-fields">
          <div className="section-header">
            <h3>Form Fields</h3>
            <MobileButton
              variant="primary"
              size="small"
              onClick={() => setShowFieldTypes(true)}
              startIcon={<Plus size={16} />}
            >
              Add Field
            </MobileButton>
          </div>

          {fields.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">
                <Type size={48} />
              </div>
              <h4>No fields added yet</h4>
              <p>Add your first field to get started building your form</p>
              <MobileButton
                variant="primary"
                onClick={() => setShowFieldTypes(true)}
                startIcon={<Plus size={16} />}
              >
                Add Field
              </MobileButton>
            </div>
          ) : (
            <div className="fields-list">{fields.map(renderFieldPreview)}</div>
          )}
        </section>

        {/* Bottom Actions */}
        <section className="bottom-actions">
          <MobileButton
            variant="secondary"
            fullWidth
            onClick={() => setShowPreview(true)}
            startIcon={<Eye size={16} />}
          >
            Preview Form
          </MobileButton>
        </section>
      </div>

      {/* Modals */}
      {renderFieldTypeSelector()}
      {renderFieldEditor()}
      {renderFormPreview()}
    </div>
  );
};

export default MobileFormBuilder;
