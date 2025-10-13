import requests
import json

def test_form_builder_integration():
    """Test if forms created in Form Builder appear in Public Forms"""
    
    # Test creating a form through Form Builder API
    form_data = {
        'title': 'Test Integration Form',
        'description': 'Testing Form Builder to Public Forms integration',
        'schema': {
            'fields': [
                {
                    'id': 'name',
                    'type': 'text',
                    'label': 'Name',
                    'required': True
                },
                {
                    'id': 'email', 
                    'type': 'email',
                    'label': 'Email',
                    'required': True
                }
            ]
        },
        'is_public': True,
        'is_active': True
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer dev-bypass-token'
    }

    try:
        # Create form via Form Builder endpoint
        response = requests.post('http://localhost:5000/api/forms/', 
                                json=form_data, 
                                headers=headers)

        print('Form Creation Response:')
        print(f'Status: {response.status_code}')
        print(f'Response: {response.text}')

        if response.status_code == 201:
            # Check if it appears in Public Forms
            public_response = requests.get('http://localhost:5000/api/public/forms')
            print('\nPublic Forms Response:')
            print(f'Status: {public_response.status_code}')
            
            if public_response.status_code == 200:
                forms = public_response.json().get('forms', [])
                print(f'Total public forms: {len(forms)}')
                
                # Look for our test form
                test_form = None
                for form in forms:
                    if form.get('title') == 'Test Integration Form':
                        test_form = form
                        break
                
                if test_form:
                    print('✅ SUCCESS: Form created in Form Builder appears in Public Forms!')
                    print(f'Form ID: {test_form["id"]}')
                    print(f'Title: {test_form["title"]}')
                    print(f'Is Public: {test_form["is_public"]}')
                else:
                    print('❌ ISSUE: Form created but not visible in Public Forms')
                    print('Available forms:')
                    for form in forms:
                        print(f'  - {form.get("title", "Untitled")} (ID: {form.get("id")}, Public: {form.get("is_public")})')
            else:
                print(f'Error fetching public forms: {public_response.text}')
        else:
            print('Form creation failed')
            
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    test_form_builder_integration()
