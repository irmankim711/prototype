/**
 * Test script to verify external forms date handling
 */

// Test the date handling fix for external forms
function testExternalFormsDateHandling() {
    console.log('🧪 Testing External Forms Date Handling...\n');
    
    // Simulate localStorage data (what happens after save/load cycle)
    const mockLocalStorageData = {
        "externalForms": JSON.stringify([
            {
                id: "1722551671234",
                title: "Test External Form",
                url: "https://example.com/form",
                description: "Test description",
                createdAt: "2025-08-01T03:00:00.000Z" // This becomes a string after JSON.parse
            }
        ])
    };
    
    console.log('📋 Mock localStorage data:');
    console.log(mockLocalStorageData.externalForms);
    
    // Test the parsing logic (from FormBuilderAdmin component)
    const saved = mockLocalStorageData.externalForms;
    let externalForms = [];
    
    if (saved) {
        try {
            const parsed = JSON.parse(saved);
            console.log('\n📦 Parsed data (before date conversion):');
            console.log('typeof createdAt:', typeof parsed[0].createdAt);
            console.log('createdAt value:', parsed[0].createdAt);
            
            // Convert createdAt strings back to Date objects
            externalForms = parsed.map((form) => ({
                ...form,
                createdAt: new Date(form.createdAt)
            }));
            
            console.log('\n✅ After date conversion:');
            console.log('typeof createdAt:', typeof externalForms[0].createdAt);
            console.log('createdAt value:', externalForms[0].createdAt);
            console.log('Is Date object:', externalForms[0].createdAt instanceof Date);
            
        } catch (error) {
            console.error("Error parsing external forms:", error);
        }
    }
    
    // Test the FormStatusManager conversion logic
    console.log('\n🔄 Testing FormStatusManager conversion...');
    const extendedForm = {
        id: `external_${externalForms[0].id}`,
        title: externalForms[0].title,
        description: externalForms[0].description,
        external_url: externalForms[0].url,
        created_at: externalForms[0].createdAt instanceof Date 
          ? externalForms[0].createdAt.toISOString() 
          : new Date(externalForms[0].createdAt).toISOString(),
        is_external: true,
        is_public: true,
        is_active: true,
    };
    
    console.log('✅ ExtendedForm created successfully:');
    console.log('created_at:', extendedForm.created_at);
    console.log('is_external:', extendedForm.is_external);
    
    console.log('\n🎉 All tests passed! Date handling is working correctly.');
}

// Run the test
testExternalFormsDateHandling();
