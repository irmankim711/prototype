/**
 * Secure Form Example
 * 
 * This component demonstrates how to integrate CSRF protection into existing forms.
 * It shows various approaches to adding CSRF tokens to forms.
 */

import React, { useState } from 'react';
import { CSRFTokenInput, useCSRFFormData } from '../CSRFTokenInput';
import { useCSRF } from '../../hooks/useCSRF';

interface FormData {
  username: string;
  email: string;
  message: string;
}

/**
 * Example 1: Basic form with automatic CSRF token input
 */
export const BasicSecureForm: React.FC = () => {
  const [formData, setFormData] = useState<FormData>({
    username: '',
    email: '',
    message: ''
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const response = await fetch('/api/submit-form', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
        credentials: 'include' // Important for CSRF cookies
      });
      
      if (response.ok) {
        alert('Form submitted successfully!');
      } else {
        alert('Form submission failed');
      }
    } catch (error) {
      console.error('Submission error:', error);
      alert('Submission error occurred');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* CSRF token is automatically included */}
      <CSRFTokenInput showErrors={true} />
      
      <div>
        <label htmlFor="username" className="block text-sm font-medium">
          Username
        </label>
        <input
          type="text"
          id="username"
          value={formData.username}
          onChange={(e) => setFormData({ ...formData, username: e.target.value })}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
          required
        />
      </div>
      
      <div>
        <label htmlFor="email" className="block text-sm font-medium">
          Email
        </label>
        <input
          type="email"
          id="email"
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
          required
        />
      </div>
      
      <div>
        <label htmlFor="message" className="block text-sm font-medium">
          Message
        </label>
        <textarea
          id="message"
          value={formData.message}
          onChange={(e) => setFormData({ ...formData, message: e.target.value })}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
          rows={4}
          required
        />
      </div>
      
      <button
        type="submit"
        className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
      >
        Submit Form
      </button>
    </form>
  );
};

/**
 * Example 2: Form with manual CSRF token handling
 */
export const ManualCSRFForm: React.FC = () => {
  const { csrfToken, isLoading, error } = useCSRF();
  const [formData, setFormData] = useState<FormData>({
    username: '',
    email: '',
    message: ''
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!csrfToken) {
      alert('CSRF token not available');
      return;
    }
    
    try {
      const response = await fetch('/api/submit-form', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': csrfToken // Manual CSRF token inclusion
        },
        body: JSON.stringify(formData),
        credentials: 'include'
      });
      
      if (response.ok) {
        alert('Form submitted successfully!');
      } else {
        alert('Form submission failed');
      }
    } catch (error) {
      console.error('Submission error:', error);
      alert('Submission error occurred');
    }
  };

  if (isLoading) {
    return <div>Loading security protection...</div>;
  }

  if (error) {
    return <div>Security error: {error}</div>;
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="username2" className="block text-sm font-medium">
          Username
        </label>
        <input
          type="text"
          id="username2"
          value={formData.username}
          onChange={(e) => setFormData({ ...formData, username: e.target.value })}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
          required
        />
      </div>
      
      <div>
        <label htmlFor="email2" className="block text-sm font-medium">
          Email
        </label>
        <input
          type="email"
          id="email2"
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
          required
        />
      </div>
      
      <div>
        <label htmlFor="message2" className="block text-sm font-medium">
          Message
        </label>
        <textarea
          id="message2"
          value={formData.message}
          onChange={(e) => setFormData({ ...formData, message: e.target.value })}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
          rows={4}
          required
        />
      </div>
      
      <button
        type="submit"
        className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
      >
        Submit Form (Manual CSRF)
      </button>
    </form>
  );
};

/**
 * Example 3: Form using useCSRFFormData hook
 */
export const HookBasedForm: React.FC = () => {
  const { csrfToken, createFormDataWithCSRF } = useCSRFFormData();
  const [formData, setFormData] = useState<FormData>({
    username: '',
    email: '',
    message: ''
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      // Create FormData with CSRF token automatically included
      const formDataWithCSRF = createFormDataWithCSRF(formData);
      
      const response = await fetch('/api/submit-form', {
        method: 'POST',
        body: formDataWithCSRF,
        credentials: 'include'
      });
      
      if (response.ok) {
        alert('Form submitted successfully!');
      } else {
        alert('Form submission failed');
      }
    } catch (error) {
      console.error('Submission error:', error);
      alert('Submission error occurred');
    }
  };

  if (!csrfToken) {
    return <div>CSRF protection not available</div>;
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="username3" className="block text-sm font-medium">
          Username
        </label>
        <input
          type="text"
          id="username3"
          value={formData.username}
          onChange={(e) => setFormData({ ...formData, username: e.target.value })}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
          required
        />
      </div>
      
      <div>
        <label htmlFor="email3" className="block text-sm font-medium">
          Email
        </label>
        <input
          type="email"
          id="email3"
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
          required
        />
      </div>
      
      <div>
        <label htmlFor="message3" className="block text-sm font-medium">
          Message
        </label>
        <textarea
          id="message3"
          value={formData.message}
          onChange={(e) => setFormData({ ...formData, message: e.target.value })}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
          rows={4}
          required
        />
      </div>
      
      <button
        type="submit"
        className="bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600"
      >
        Submit Form (Hook-based)
      </button>
    </form>
  );
};

/**
 * Example 4: Form with file upload and CSRF protection
 */
export const FileUploadForm: React.FC = () => {
  const { csrfToken, addCSRFToken } = useCSRFFormData();
  const [file, setFile] = useState<File | null>(null);
  const [description, setDescription] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!file) {
      alert('Please select a file');
      return;
    }
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('description', description);
      
      // Add CSRF token to FormData
      addCSRFToken(formData);
      
      const response = await fetch('/api/upload-file', {
        method: 'POST',
        body: formData,
        credentials: 'include'
      });
      
      if (response.ok) {
        alert('File uploaded successfully!');
      } else {
        alert('File upload failed');
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert('Upload error occurred');
    }
  };

  if (!csrfToken) {
    return <div>CSRF protection not available</div>;
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="file" className="block text-sm font-medium">
          File
        </label>
        <input
          type="file"
          id="file"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="mt-1 block w-full"
          required
        />
      </div>
      
      <div>
        <label htmlFor="description" className="block text-sm font-medium">
          Description
        </label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
          rows={3}
        />
      </div>
      
      <button
        type="submit"
        className="bg-orange-500 text-white px-4 py-2 rounded hover:bg-orange-600"
      >
        Upload File
      </button>
    </form>
  );
};

/**
 * Main example component that shows all examples
 */
export const SecureFormExamples: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <h1 className="text-3xl font-bold text-center mb-8">
        Secure Form Examples with CSRF Protection
      </h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Basic Automatic CSRF</h2>
          <BasicSecureForm />
        </div>
        
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Manual CSRF Handling</h2>
          <ManualCSRFForm />
        </div>
        
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Hook-based CSRF</h2>
          <HookBasedForm />
        </div>
        
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">File Upload with CSRF</h2>
          <FileUploadForm />
        </div>
      </div>
      
      <div className="mt-8 p-4 bg-blue-50 rounded-lg">
        <h3 className="text-lg font-semibold mb-2">Key Points:</h3>
        <ul className="list-disc list-inside space-y-1 text-sm">
          <li>All forms automatically include CSRF tokens</li>
          <li>Tokens are validated on the backend</li>
          <li>Automatic token refresh and management</li>
          <li>Multiple integration approaches available</li>
          <li>Production-ready security implementation</li>
        </ul>
      </div>
    </div>
  );
};

export default SecureFormExamples;
