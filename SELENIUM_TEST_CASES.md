# SELENIUM UI TEST CASES

## Overview
Comprehensive test cases for UI automation using Selenium.

**Total Test Cases**: 95+
**Base URL**: `http://localhost:3000` or your deployed URL
**Browser Support**: Chrome, Firefox, Edge
**Framework**: Selenium WebDriver (Python/Java)

---

## Quick Reference

| Category | Test Cases | Priority |
|----------|-----------|----------|
| Authentication | 12 | HIGH |
| Form Management | 18 | HIGH |
| Report Generation | 15 | HIGH |
| Dashboard & Analytics | 10 | MEDIUM |
| User Profile & Settings | 10 | MEDIUM |
| Admin Functions | 8 | MEDIUM |
| Public Access | 8 | HIGH |
| Navigation & UI | 8 | LOW |
| Accessibility | 6 | MEDIUM |
| **TOTAL** | **95** | - |

---

## Test Environment Setup

### Required Dependencies
```python
# Python
pip install selenium pytest pytest-html webdriver-manager

# Java
// Add Selenium dependencies to pom.xml or build.gradle
```

### Browser Setup
```python
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

driver = webdriver.Chrome(ChromeDriverManager().install())
driver.get("http://localhost:3000")
driver.maximize_window()
```

### Page Object Locators
See [SELENIUM_LOCATORS.txt](SELENIUM_LOCATORS.txt) for complete reference.

---

## 1. AUTHENTICATION TESTS (12 Test Cases)

### TC-UI-AUTH-001: User Registration - Email
**Priority**: HIGH
**Steps**:
1. Navigate to `/` (landing page)
2. Click "Get Started" button
3. Click "Sign Up" tab
4. Enter email: `test@example.com`
5. Enter password: `Test@1234`
6. Enter confirm password: `Test@1234`
7. Check "I agree to terms" checkbox
8. Click "Sign Up" button

**Locators**:
```python
# Button
get_started_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Get Started')]")
# Tab
signup_tab = driver.find_element(By.XPATH, "//button[@role='tab' and contains(text(), 'Sign Up')]")
# Inputs
email_input = driver.find_element(By.CSS_SELECTOR, "input[type='email']")
password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password'][placeholder*='Password']")
# Checkbox
terms_checkbox = driver.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
# Submit
submit_btn = driver.find_element(By.XPATH, "//button[@type='submit' and contains(text(), 'Sign Up')]")
```

**Expected Results**:
- Redirect to dashboard `/dashboard`
- Welcome message displayed
- User menu shows email
- URL changes to dashboard

**Assertions**:
```python
assert driver.current_url.endswith("/dashboard")
assert "Welcome" in driver.page_source
```

---

### TC-UI-AUTH-002: User Registration - Google OAuth
**Priority**: HIGH
**Steps**:
1. Navigate to landing page
2. Click "Get Started"
3. Click "Sign Up" tab
4. Click "Continue with Google" button
5. Handle Google popup (switch to new window)
6. Enter Google credentials
7. Click "Allow" to grant permissions
8. Switch back to main window

**Locators**:
```python
google_btn = driver.find_element(By.XPATH, "//button[contains(., 'Google')]")
```

**Expected Results**:
- Successfully authenticated
- Redirected to dashboard
- Profile shows Google avatar

**Assertions**:
```python
assert driver.current_url.endswith("/dashboard")
profile_img = driver.find_element(By.CSS_SELECTOR, "img[alt*='Profile']")
assert profile_img.is_displayed()
```

---

### TC-UI-AUTH-003: User Login - Valid Credentials
**Priority**: HIGH
**Steps**:
1. Navigate to `/`
2. Click "Login" button
3. Enter email: `existing@example.com`
4. Enter password: `ValidPass123`
5. Click "Login" button

**Locators**:
```python
login_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
email_input = driver.find_element(By.NAME, "email")
password_input = driver.find_element(By.NAME, "password")
submit_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
```

**Expected Results**:
- Login successful
- Dashboard displayed
- Session persisted

**Assertions**:
```python
assert driver.current_url.endswith("/dashboard")
```

---

### TC-UI-AUTH-004: User Login - Invalid Password
**Priority**: HIGH
**Steps**:
1. Navigate to login
2. Enter valid email
3. Enter wrong password
4. Click login

**Expected Results**:
- Error message: "Invalid credentials"
- Stays on login page
- Error alert displayed in red

**Assertions**:
```python
error_msg = driver.find_element(By.CSS_SELECTOR, ".MuiAlert-standardError")
assert "Invalid" in error_msg.text
```

---

### TC-UI-AUTH-005: User Login - Empty Fields
**Priority**: MEDIUM
**Steps**:
1. Navigate to login
2. Leave email empty
3. Leave password empty
4. Click login button

**Expected Results**:
- Validation errors shown
- "Email is required"
- "Password is required"

**Assertions**:
```python
errors = driver.find_elements(By.CSS_SELECTOR, ".MuiFormHelperText-root.Mui-error")
assert len(errors) >= 2
```

---

### TC-UI-AUTH-006: Password Reset Flow
**Priority**: MEDIUM
**Steps**:
1. Navigate to login page
2. Click "Forgot Password?" link
3. Enter email address
4. Click "Send Reset Link"
5. Verify success message

**Locators**:
```python
forgot_link = driver.find_element(By.LINK_TEXT, "Forgot Password?")
reset_email = driver.find_element(By.NAME, "email")
send_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Send')]")
```

**Expected Results**:
- Success message displayed
- "Reset link sent to your email"

**Assertions**:
```python
success = driver.find_element(By.CSS_SELECTOR, ".MuiAlert-standardSuccess")
assert "sent" in success.text.lower()
```

---

### TC-UI-AUTH-007: Logout Functionality
**Priority**: HIGH
**Steps**:
1. Login as user
2. Click profile menu (top-right)
3. Click "Logout" option
4. Confirm logout

**Locators**:
```python
profile_menu = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Account']")
profile_menu.click()
logout_btn = driver.find_element(By.XPATH, "//li[contains(text(), 'Logout')]")
```

**Expected Results**:
- Redirected to landing page
- Session cleared
- Cannot access protected pages

**Assertions**:
```python
assert driver.current_url.endswith("/")
driver.get("http://localhost:3000/dashboard")
assert "login" in driver.current_url.lower() or driver.current_url.endswith("/")
```

---

### TC-UI-AUTH-008: Session Persistence
**Priority**: MEDIUM
**Steps**:
1. Login successfully
2. Navigate to dashboard
3. Close browser
4. Reopen browser
5. Navigate to app URL

**Expected Results**:
- Still logged in
- Dashboard displayed immediately
- No login required

**Assertions**:
```python
driver.quit()
driver = webdriver.Chrome()
driver.get("http://localhost:3000")
assert "dashboard" in driver.current_url or "Dashboard" in driver.page_source
```

---

### TC-UI-AUTH-009: Email Verification Required
**Priority**: MEDIUM
**Steps**:
1. Register with new email
2. Attempt to access protected features
3. Verify email verification prompt

**Expected Results**:
- Banner: "Please verify your email"
- Link to resend verification

**Assertions**:
```python
banner = driver.find_element(By.CSS_SELECTOR, ".verification-banner")
assert "verify" in banner.text.lower()
```

---

### TC-UI-AUTH-010: Protected Route Access
**Priority**: HIGH
**Steps**:
1. Clear all cookies/session
2. Navigate directly to `/dashboard`
3. Verify redirect

**Expected Results**:
- Redirected to login page
- URL contains login route

**Assertions**:
```python
driver.delete_all_cookies()
driver.get("http://localhost:3000/dashboard")
time.sleep(2)
assert "login" in driver.current_url.lower() or driver.current_url.endswith("/")
```

---

### TC-UI-AUTH-011: Remember Me Checkbox
**Priority**: LOW
**Steps**:
1. Login page
2. Check "Remember Me" checkbox
3. Login
4. Close browser (don't logout)
5. Reopen and navigate to app

**Expected Results**:
- Session persisted longer
- Auto-login on return

---

### TC-UI-AUTH-012: Two-Factor Authentication
**Priority**: MEDIUM
**Steps**:
1. Login with 2FA enabled account
2. Enter email and password
3. Verify 2FA code prompt
4. Enter 6-digit code
5. Submit

**Expected Results**:
- 2FA modal displayed
- Code input field visible
- Login successful after valid code

---

## 2. FORM MANAGEMENT TESTS (18 Test Cases)

### TC-UI-FORM-001: Create New Form - Basic
**Priority**: HIGH
**Steps**:
1. Login and navigate to dashboard
2. Click "Create Form" FAB button (bottom-right)
3. Step 1: Enter form title: "Customer Survey"
4. Enter description: "Feedback collection"
5. Click "Next" button
6. Step 2: Add fields (covered in next test)
7. Click "Next"
8. Step 3: Review settings
9. Click "Create Form"

**Locators**:
```python
# FAB
create_fab = driver.find_element(By.CSS_SELECTOR, "button.MuiFab-root")
# Inputs
title_input = driver.find_element(By.NAME, "title")
desc_input = driver.find_element(By.NAME, "description")
# Navigation
next_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Next')]")
create_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Create')]")
```

**Expected Results**:
- Form created successfully
- Success snackbar: "Form created"
- Redirected to form builder or form list
- Form visible in dashboard

**Assertions**:
```python
success_msg = driver.find_element(By.CSS_SELECTOR, ".MuiSnackbar-root")
assert "created" in success_msg.text.lower()
```

---

### TC-UI-FORM-002: Add Form Fields - All Types
**Priority**: HIGH
**Steps**:
1. In form builder (Step 2)
2. Click "Add Field" button
3. Select field type: "Text"
4. Enter label: "Full Name"
5. Toggle "Required" switch
6. Click "Add Field"
7. Repeat for other types: Email, Number, Textarea, Date, Dropdown, Checkbox, Radio

**Locators**:
```python
add_field_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Add Field')]")
field_type_select = driver.find_element(By.NAME, "fieldType")
label_input = driver.find_element(By.NAME, "fieldLabel")
required_switch = driver.find_element(By.CSS_SELECTOR, "input[type='checkbox'][name='required']")
```

**Expected Results**:
- All 8 field types added
- Each field displays correctly in preview
- Field order maintained

**Assertions**:
```python
fields = driver.find_elements(By.CSS_SELECTOR, ".form-field-item")
assert len(fields) == 8
```

---

### TC-UI-FORM-003: Reorder Form Fields - Drag & Drop
**Priority**: MEDIUM
**Steps**:
1. In form builder with 3+ fields
2. Locate drag handle on field 1
3. Drag field 1 below field 3
4. Release
5. Verify new order

**Locators**:
```python
from selenium.webdriver.common.action_chains import ActionChains

field1 = driver.find_element(By.XPATH, "//div[@data-field-index='0']")
field3 = driver.find_element(By.XPATH, "//div[@data-field-index='2']")

actions = ActionChains(driver)
actions.drag_and_drop(field1, field3).perform()
```

**Expected Results**:
- Fields reordered
- Preview updates immediately

**Assertions**:
```python
first_field = driver.find_element(By.XPATH, "//div[@data-field-index='0']//label")
assert "Email" in first_field.text  # Assuming Email was 2nd before
```

---

### TC-UI-FORM-004: Delete Form Field
**Priority**: MEDIUM
**Steps**:
1. In form builder
2. Hover over field to delete
3. Click delete icon (trash)
4. Confirm deletion in modal
5. Verify field removed

**Locators**:
```python
field = driver.find_element(By.XPATH, "//div[@data-field-index='1']")
delete_btn = field.find_element(By.CSS_SELECTOR, "button[aria-label='Delete']")
delete_btn.click()

# Confirm modal
confirm_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Delete')]")
confirm_btn.click()
```

**Expected Results**:
- Field removed from list
- Total field count decreased

---

### TC-UI-FORM-005: Edit Existing Form
**Priority**: HIGH
**Steps**:
1. Navigate to forms list `/dashboard`
2. Locate form card
3. Click "Edit" icon button
4. Modify form title
5. Add new field
6. Click "Save Changes"

**Locators**:
```python
form_card = driver.find_element(By.XPATH, "//div[contains(@class, 'form-card')]")
edit_btn = form_card.find_element(By.CSS_SELECTOR, "button[aria-label='Edit']")
save_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Save')]")
```

**Expected Results**:
- Changes saved
- Success message
- Updated form displays new data

---

### TC-UI-FORM-006: Publish Form (Draft to Active)
**Priority**: HIGH
**Steps**:
1. In form list, find draft form
2. Click "More" menu (3 dots)
3. Click "Publish"
4. Confirm in dialog
5. Verify status change

**Locators**:
```python
more_menu = driver.find_element(By.CSS_SELECTOR, "button[aria-label='More']")
more_menu.click()
publish_option = driver.find_element(By.XPATH, "//li[contains(text(), 'Publish')]")
publish_option.click()
```

**Expected Results**:
- Status badge: "Active" (green)
- Form accessible publicly

**Assertions**:
```python
status_badge = driver.find_element(By.CSS_SELECTOR, ".MuiChip-root")
assert "active" in status_badge.text.lower()
```

---

### TC-UI-FORM-007: Make Form Public
**Priority**: HIGH
**Steps**:
1. Edit form
2. Go to "Settings" tab
3. Toggle "Make Public" switch
4. Save form

**Locators**:
```python
settings_tab = driver.find_element(By.XPATH, "//button[@role='tab' and contains(text(), 'Settings')]")
settings_tab.click()
public_switch = driver.find_element(By.CSS_SELECTOR, "input[name='isPublic']")
from selenium.webdriver.common.action_chains import ActionChains
ActionChains(driver).move_to_element(public_switch).click().perform()
```

**Expected Results**:
- Form available at `/forms/public`
- Public link generated

---

### TC-UI-FORM-008: Generate Access Code
**Priority**: MEDIUM
**Steps**:
1. Edit form
2. Settings tab
3. Click "Generate Access Code" button
4. Copy code displayed
5. Save form

**Locators**:
```python
generate_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Generate Code')]")
access_code = driver.find_element(By.CSS_SELECTOR, "input[readonly][value]")
code_value = access_code.get_attribute("value")
```

**Expected Results**:
- 6-8 character code generated
- Code copyable
- Form accessible via code

---

### TC-UI-FORM-009: Delete Form
**Priority**: MEDIUM
**Steps**:
1. In forms list
2. Click delete icon on form card
3. Confirm deletion modal
4. Enter form title to confirm (if required)
5. Click "Delete Permanently"

**Locators**:
```python
delete_btn = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Delete']")
confirm_input = driver.find_element(By.NAME, "confirmTitle")
confirm_input.send_keys("Form Title")
delete_confirm_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Delete')]")
```

**Expected Results**:
- Form removed from list
- Success message: "Form deleted"
- Cannot be recovered

---

### TC-UI-FORM-010: View Form Submissions
**Priority**: HIGH
**Steps**:
1. Click on form card
2. Navigate to "Responses" tab
3. View table of submissions
4. Check pagination

**Locators**:
```python
responses_tab = driver.find_element(By.XPATH, "//button[contains(text(), 'Responses')]")
responses_tab.click()
table = driver.find_element(By.CSS_SELECTOR, "table.MuiTable-root")
rows = table.find_elements(By.TAG_NAME, "tr")
```

**Expected Results**:
- All submissions displayed
- Columns: Date, User, Responses
- Pagination working

**Assertions**:
```python
assert len(rows) > 1  # Header + at least 1 data row
```

---

### TC-UI-FORM-011: Filter Form Submissions
**Priority**: MEDIUM
**Steps**:
1. In Responses tab
2. Click "Filter" button
3. Select field to filter
4. Enter filter value
5. Click "Apply"

**Locators**:
```python
filter_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Filter')]")
field_select = driver.find_element(By.NAME, "filterField")
value_input = driver.find_element(By.NAME, "filterValue")
apply_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Apply')]")
```

**Expected Results**:
- Filtered results shown
- Count updated

---

### TC-UI-FORM-012: Export Submissions to CSV
**Priority**: MEDIUM
**Steps**:
1. Responses tab
2. Click "Export" button
3. Select "CSV" format
4. Click "Download"

**Locators**:
```python
export_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Export')]")
csv_option = driver.find_element(By.XPATH, "//li[contains(text(), 'CSV')]")
download_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Download')]")
```

**Expected Results**:
- CSV file downloaded
- Contains all submission data

---

### TC-UI-FORM-013: Form Validation - Required Fields
**Priority**: HIGH
**Steps**:
1. Navigate to public form
2. Leave required field empty
3. Click submit
4. Verify error message

**Expected Results**:
- Error: "This field is required"
- Form not submitted
- Focus on first error field

**Assertions**:
```python
error = driver.find_element(By.CSS_SELECTOR, ".MuiFormHelperText-root.Mui-error")
assert "required" in error.text.lower()
```

---

### TC-UI-FORM-014: Form Validation - Email Format
**Priority**: HIGH
**Steps**:
1. Public form with email field
2. Enter invalid email: "notanemail"
3. Tab out or submit
4. Verify validation error

**Expected Results**:
- Error: "Invalid email format"

---

### TC-UI-FORM-015: Form Submission Success
**Priority**: HIGH
**Steps**:
1. Fill all required fields
2. Click submit
3. Verify success page

**Expected Results**:
- Success message displayed
- Submission ID shown
- Option to submit another

---

### TC-UI-FORM-016: Duplicate Form
**Priority**: MEDIUM
**Steps**:
1. Forms list
2. Click "More" menu
3. Click "Duplicate"
4. Verify copy created

**Expected Results**:
- New form created with "(Copy)" suffix
- All fields duplicated

---

### TC-UI-FORM-017: Search Forms
**Priority**: MEDIUM
**Steps**:
1. Dashboard with many forms
2. Enter search term in search bar
3. Verify filtered results

**Locators**:
```python
search_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='Search']")
search_input.send_keys("Customer")
```

**Expected Results**:
- Only matching forms shown

---

### TC-UI-FORM-018: Pagination in Forms List
**Priority**: LOW
**Steps**:
1. Dashboard with 20+ forms
2. Scroll to bottom
3. Click "Next" page button
4. Verify page 2 loaded

**Locators**:
```python
next_btn = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Go to next page']")
```

**Expected Results**:
- Different forms displayed
- Page indicator updated

---

## 3. REPORT GENERATION TESTS (15 Test Cases)

### TC-UI-REPORT-001: Create Basic Report
**Priority**: HIGH
**Steps**:
1. Navigate to `/reports`
2. Click "Create Report" button
3. Select data source (form) from dropdown
4. Enter report title: "Monthly Analysis"
5. Select chart type: "Bar"
6. Click "Generate Report"

**Locators**:
```python
create_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Create Report')]")
source_select = driver.find_element(By.CSS_SELECTOR, "select[name='dataSource']")
title_input = driver.find_element(By.NAME, "reportTitle")
chart_select = driver.find_element(By.NAME, "chartType")
generate_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Generate')]")
```

**Expected Results**:
- Report generation starts
- Progress indicator shown
- Report displayed when complete

**Assertions**:
```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

wait = WebDriverWait(driver, 30)
report_view = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".report-view")))
assert report_view.is_displayed()
```

---

### TC-UI-REPORT-002: Add Multiple Charts
**Priority**: HIGH
**Steps**:
1. In report builder
2. Add Bar chart
3. Click "Add Another Chart"
4. Add Pie chart
5. Click "Add Another Chart"
6. Add Line chart
7. Generate report

**Locators**:
```python
add_chart_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Add Chart')]")
```

**Expected Results**:
- All 3 charts displayed in report
- Charts render correctly

**Assertions**:
```python
charts = driver.find_elements(By.CSS_SELECTOR, "canvas")
assert len(charts) == 3
```

---

### TC-UI-REPORT-003: Configure Chart Data
**Priority**: HIGH
**Steps**:
1. Report builder
2. Select chart
3. Configure X-axis: Select field
4. Configure Y-axis: Select aggregation (Count, Sum, Avg)
5. Add filters
6. Preview chart

**Locators**:
```python
xaxis_select = driver.find_element(By.NAME, "xAxis")
yaxis_select = driver.find_element(By.NAME, "yAxis")
aggregation_select = driver.find_element(By.NAME, "aggregation")
preview_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Preview')]")
```

**Expected Results**:
- Chart updates in real-time
- Data accurately represented

---

### TC-UI-REPORT-004: Apply Data Filters
**Priority**: MEDIUM
**Steps**:
1. Report builder
2. Click "Add Filter" button
3. Select field to filter
4. Select operator (equals, contains, greater than)
5. Enter filter value
6. Click "Apply Filter"
7. Generate report

**Locators**:
```python
add_filter_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Add Filter')]")
field_select = driver.find_element(By.NAME, "filterField")
operator_select = driver.find_element(By.NAME, "filterOperator")
value_input = driver.find_element(By.NAME, "filterValue")
```

**Expected Results**:
- Only filtered data in report
- Chart reflects filtered results

---

### TC-UI-REPORT-005: Export Report as PDF
**Priority**: HIGH
**Steps**:
1. View generated report
2. Click "Export" button
3. Select "PDF" option
4. Click "Download"
5. Wait for download

**Locators**:
```python
export_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Export')]")
pdf_option = driver.find_element(By.XPATH, "//li[contains(text(), 'PDF')]")
download_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Download')]")
```

**Expected Results**:
- PDF file downloaded
- Contains all charts and data
- Proper formatting

---

### TC-UI-REPORT-006: Export Report as Excel
**Priority**: HIGH
**Steps**:
1. View report
2. Click Export > Excel
3. Download

**Expected Results**:
- XLSX file downloaded
- Data in spreadsheet format

---

### TC-UI-REPORT-007: Export Report as Word
**Priority**: MEDIUM
**Steps**:
1. View report
2. Click Export > Word
3. Download

**Expected Results**:
- DOCX file downloaded
- Charts embedded as images

---

### TC-UI-REPORT-008: Save Report
**Priority**: HIGH
**Steps**:
1. Generate report
2. Click "Save" button
3. Enter report name
4. Click "Save"

**Locators**:
```python
save_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Save')]")
name_input = driver.find_element(By.NAME, "reportName")
confirm_save = driver.find_element(By.XPATH, "//button[contains(text(), 'Confirm')]")
```

**Expected Results**:
- Report saved to account
- Visible in Reports list

---

### TC-UI-REPORT-009: View Report History
**Priority**: MEDIUM
**Steps**:
1. Navigate to `/report-history`
2. View table of all reports
3. Verify columns: Title, Date, Status, Actions

**Locators**:
```python
history_link = driver.find_element(By.LINK_TEXT, "Report History")
table = driver.find_element(By.CSS_SELECTOR, "table")
```

**Expected Results**:
- All saved reports listed
- Sorted by date (newest first)

---

### TC-UI-REPORT-010: Delete Report
**Priority**: MEDIUM
**Steps**:
1. Report History page
2. Click delete icon on report row
3. Confirm deletion

**Expected Results**:
- Report removed from list
- Success message

---

### TC-UI-REPORT-011: Share Report
**Priority**: MEDIUM
**Steps**:
1. View report
2. Click "Share" button
3. Enter email address
4. Click "Send"

**Locators**:
```python
share_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Share')]")
email_input = driver.find_element(By.NAME, "shareEmail")
send_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Send')]")
```

**Expected Results**:
- Share link generated
- Email sent confirmation

---

### TC-UI-REPORT-012: Clone/Duplicate Report
**Priority**: LOW
**Steps**:
1. Report History
2. Click "More" menu
3. Click "Duplicate"

**Expected Results**:
- New report created
- Same configuration as original

---

### TC-UI-REPORT-013: AI Enhance Report
**Priority**: MEDIUM
**Steps**:
1. View report
2. Click "AI Enhance" button
3. Wait for AI processing
4. View AI-generated insights

**Locators**:
```python
ai_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'AI Enhance')]")
```

**Expected Results**:
- Insights section added
- Recommendations displayed

---

### TC-UI-REPORT-014: Real-time Report Preview
**Priority**: MEDIUM
**Steps**:
1. Report builder
2. Make changes to chart config
3. Observe preview panel

**Expected Results**:
- Preview updates immediately
- No manual refresh needed

---

### TC-UI-REPORT-015: Report Template Selection
**Priority**: MEDIUM
**Steps**:
1. Create Report
2. Click "Use Template"
3. Select pre-made template
4. Customize and generate

**Expected Results**:
- Template applied
- Pre-configured charts loaded

---

## 4. DASHBOARD & ANALYTICS TESTS (10 Test Cases)

### TC-UI-DASH-001: View Dashboard Overview
**Priority**: HIGH
**Steps**:
1. Login and land on `/dashboard`
2. Verify all widgets load

**Expected Results**:
- Total Forms card displayed
- Total Submissions card
- Active Users card
- Recent Activity list

**Assertions**:
```python
cards = driver.find_elements(By.CSS_SELECTOR, ".dashboard-card")
assert len(cards) >= 4
```

---

### TC-UI-DASH-002: Quick Actions - Create Form
**Priority**: HIGH
**Steps**:
1. Dashboard
2. Click "Create Form" quick action card
3. Verify form builder opens

**Expected Results**:
- Redirected to form builder

---

### TC-UI-DASH-003: Quick Actions - Generate Report
**Priority**: HIGH
**Steps**:
1. Dashboard
2. Click "Generate Report" card
3. Verify report builder opens

---

### TC-UI-DASH-004: View Recent Forms
**Priority**: MEDIUM
**Steps**:
1. Dashboard
2. Scroll to "Recent Forms" section
3. Verify 5 most recent forms shown

**Expected Results**:
- Forms sorted by last modified
- Click to open form

---

### TC-UI-DASH-005: View Analytics Chart
**Priority**: MEDIUM
**Steps**:
1. Dashboard
2. Locate "Submissions Over Time" chart
3. Verify data displayed

**Expected Results**:
- Line chart with submission trends
- Last 7 days by default

---

### TC-UI-DASH-006: Filter Analytics by Date Range
**Priority**: MEDIUM
**Steps**:
1. Dashboard analytics section
2. Click date range picker
3. Select "Last 30 days"
4. Apply filter

**Locators**:
```python
date_picker = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Select date range']")
option_30d = driver.find_element(By.XPATH, "//li[contains(text(), '30 days')]")
```

**Expected Results**:
- Chart updates with 30-day data

---

### TC-UI-DASH-007: Search Forms from Dashboard
**Priority**: MEDIUM
**Steps**:
1. Dashboard
2. Enter search term in search bar
3. Verify results filtered

---

### TC-UI-DASH-008: View Form Statistics
**Priority**: MEDIUM
**Steps**:
1. Dashboard
2. Click on form card
3. View detailed stats: Views, Submissions, Completion Rate

---

### TC-UI-DASH-009: Notifications Panel
**Priority**: LOW
**Steps**:
1. Dashboard
2. Click notifications icon (bell)
3. View recent notifications

**Locators**:
```python
notifications_btn = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Notifications']")
```

**Expected Results**:
- Notification dropdown opens
- Recent activities listed

---

### TC-UI-DASH-010: Refresh Dashboard Data
**Priority**: LOW
**Steps**:
1. Dashboard
2. Click refresh button
3. Verify data reloads

**Expected Results**:
- Loading indicator shown
- Updated data displayed

---

## 5. USER PROFILE & SETTINGS TESTS (10 Test Cases)

### TC-UI-PROFILE-001: View Profile
**Priority**: MEDIUM
**Steps**:
1. Click profile menu (top-right)
2. Click "Profile"
3. Navigate to `/profile`

**Locators**:
```python
profile_menu = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Account']")
profile_option = driver.find_element(By.XPATH, "//li[contains(text(), 'Profile')]")
```

**Expected Results**:
- Profile page displayed
- 4 tabs: Overview, Security, Preferences, Activity

---

### TC-UI-PROFILE-002: Update Profile Information
**Priority**: HIGH
**Steps**:
1. Profile page > Overview tab
2. Click "Edit" button
3. Update display name
4. Update phone number
5. Update bio
6. Click "Save Changes"

**Locators**:
```python
edit_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Edit')]")
name_input = driver.find_element(By.NAME, "displayName")
phone_input = driver.find_element(By.NAME, "phoneNumber")
bio_input = driver.find_element(By.NAME, "bio")
save_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Save')]")
```

**Expected Results**:
- Changes saved
- Success message
- Profile updated immediately

---

### TC-UI-PROFILE-003: Upload Avatar
**Priority**: MEDIUM
**Steps**:
1. Profile page
2. Hover over avatar
3. Click "Change Photo"
4. Select image file
5. Upload

**Locators**:
```python
avatar = driver.find_element(By.CSS_SELECTOR, "img[alt*='Avatar']")
upload_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
upload_input.send_keys("/path/to/image.jpg")
```

**Expected Results**:
- Avatar updated
- New image displayed

---

### TC-UI-PROFILE-004: Change Password
**Priority**: HIGH
**Steps**:
1. Profile > Security tab
2. Enter current password
3. Enter new password
4. Confirm new password
5. Click "Change Password"

**Locators**:
```python
security_tab = driver.find_element(By.XPATH, "//button[contains(text(), 'Security')]")
current_pwd = driver.find_element(By.NAME, "currentPassword")
new_pwd = driver.find_element(By.NAME, "newPassword")
confirm_pwd = driver.find_element(By.NAME, "confirmPassword")
change_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Change Password')]")
```

**Expected Results**:
- Password updated
- Success notification
- Re-login required

---

### TC-UI-PROFILE-005: Enable Two-Factor Authentication
**Priority**: MEDIUM
**Steps**:
1. Security tab
2. Toggle "Enable 2FA" switch
3. Scan QR code
4. Enter verification code
5. Save backup codes

**Locators**:
```python
twofa_switch = driver.find_element(By.CSS_SELECTOR, "input[name='enable2FA']")
code_input = driver.find_element(By.NAME, "verificationCode")
```

**Expected Results**:
- 2FA enabled
- Backup codes displayed

---

### TC-UI-PROFILE-006: Update Preferences - Theme
**Priority**: LOW
**Steps**:
1. Profile > Preferences tab
2. Select theme: "Dark"
3. Click "Save"

**Locators**:
```python
preferences_tab = driver.find_element(By.XPATH, "//button[contains(text(), 'Preferences')]")
theme_select = driver.find_element(By.NAME, "theme")
from selenium.webdriver.support.ui import Select
Select(theme_select).select_by_value("dark")
```

**Expected Results**:
- UI switches to dark mode
- Preference saved

---

### TC-UI-PROFILE-007: Update Preferences - Language
**Priority**: LOW
**Steps**:
1. Preferences tab
2. Select language dropdown
3. Choose "Spanish"
4. Save

**Expected Results**:
- UI text changes to Spanish

---

### TC-UI-PROFILE-008: Update Notification Settings
**Priority**: MEDIUM
**Steps**:
1. Preferences tab
2. Toggle email notifications
3. Toggle push notifications
4. Save

**Locators**:
```python
email_notif = driver.find_element(By.NAME, "emailNotifications")
push_notif = driver.find_element(By.NAME, "pushNotifications")
```

**Expected Results**:
- Settings saved
- Notifications behavior updated

---

### TC-UI-PROFILE-009: View Activity Log
**Priority**: LOW
**Steps**:
1. Profile > Activity tab
2. View list of recent activities

**Expected Results**:
- Login events listed
- Form creations listed
- Report generations listed

---

### TC-UI-PROFILE-010: Delete Account
**Priority**: LOW
**Steps**:
1. Security tab
2. Scroll to "Danger Zone"
3. Click "Delete Account"
4. Enter password to confirm
5. Confirm deletion

**Expected Results**:
- Account deleted
- Logged out
- Data removed

---

## 6. ADMIN FUNCTIONS TESTS (8 Test Cases)

### TC-UI-ADMIN-001: Access Admin Panel
**Priority**: HIGH (Admin only)
**Steps**:
1. Login as admin user
2. Navigate to `/admin/forms`

**Expected Results**:
- Admin panel accessible
- All users' forms visible

---

### TC-UI-ADMIN-002: View All Users
**Priority**: HIGH
**Steps**:
1. Admin panel
2. Navigate to "Users" section
3. View user list

**Expected Results**:
- All registered users listed
- User details visible

---

### TC-UI-ADMIN-003: Edit User Role
**Priority**: HIGH
**Steps**:
1. Users section
2. Select user
3. Click "Edit Role"
4. Change role to "Admin"
5. Save

**Expected Results**:
- User role updated
- User gains admin privileges

---

### TC-UI-ADMIN-004: Deactivate User
**Priority**: MEDIUM
**Steps**:
1. Select user
2. Click "Deactivate"
3. Confirm

**Expected Results**:
- User status: Inactive
- User cannot login

---

### TC-UI-ADMIN-005: View All Forms (All Users)
**Priority**: MEDIUM
**Steps**:
1. Admin > Forms
2. View all forms across all users

**Expected Results**:
- All forms displayed
- Owner info shown

---

### TC-UI-ADMIN-006: Delete Any Form
**Priority**: MEDIUM
**Steps**:
1. Admin forms list
2. Select form (any owner)
3. Delete

**Expected Results**:
- Form deleted successfully

---

### TC-UI-ADMIN-007: View System Analytics
**Priority**: LOW
**Steps**:
1. Admin dashboard
2. View system-wide stats

**Expected Results**:
- Total users
- Total forms
- Total submissions

---

### TC-UI-ADMIN-008: Export User Data
**Priority**: LOW
**Steps**:
1. Admin > Users
2. Click "Export All Users"
3. Download CSV

**Expected Results**:
- CSV with all user data

---

## 7. PUBLIC ACCESS TESTS (8 Test Cases)

### TC-UI-PUBLIC-001: Access Public Forms List
**Priority**: HIGH
**Steps**:
1. Navigate to `/forms/public` (no login)
2. View public forms

**Expected Results**:
- Public forms displayed
- No authentication required

---

### TC-UI-PUBLIC-002: View Public Form Details
**Priority**: HIGH
**Steps**:
1. Public forms page
2. Click on form card
3. View form

**Expected Results**:
- Form details shown
- Fields visible

---

### TC-UI-PUBLIC-003: Submit Public Form
**Priority**: HIGH
**Steps**:
1. Open public form
2. Fill all fields
3. Submit

**Expected Results**:
- Submission successful
- Thank you page displayed

---

### TC-UI-PUBLIC-004: Access Form with Access Code
**Priority**: HIGH
**Steps**:
1. Navigate to `/access-forms`
2. Enter valid access code
3. Submit

**Expected Results**:
- Form unlocked
- Can submit form

---

### TC-UI-PUBLIC-005: Invalid Access Code
**Priority**: MEDIUM
**Steps**:
1. Access forms page
2. Enter invalid code
3. Submit

**Expected Results**:
- Error: "Invalid access code"

---

### TC-UI-PUBLIC-006: Public Form - Required Field Validation
**Priority**: HIGH
**Steps**:
1. Public form
2. Skip required field
3. Submit

**Expected Results**:
- Validation error
- Cannot submit

---

### TC-UI-PUBLIC-007: Public Form - Email Validation
**Priority**: MEDIUM
**Steps**:
1. Public form with email field
2. Enter invalid email
3. Submit

**Expected Results**:
- Email format error

---

### TC-UI-PUBLIC-008: Multiple Submissions from Same User
**Priority**: LOW
**Steps**:
1. Submit form once
2. Navigate back
3. Submit again

**Expected Results**:
- Both submissions accepted (unless limited)

---

## 8. NAVIGATION & UI TESTS (8 Test Cases)

### TC-UI-NAV-001: Sidebar Navigation
**Priority**: MEDIUM
**Steps**:
1. Login to dashboard
2. Verify sidebar visible
3. Click each menu item
4. Verify navigation

**Locators**:
```python
sidebar = driver.find_element(By.CSS_SELECTOR, "nav.sidebar")
menu_items = sidebar.find_elements(By.TAG_NAME, "a")
```

**Expected Results**:
- 6+ menu items
- Each navigates correctly

---

### TC-UI-NAV-002: Sidebar Collapse/Expand
**Priority**: LOW
**Steps**:
1. Click hamburger menu icon
2. Verify sidebar collapses
3. Click again
4. Verify sidebar expands

**Locators**:
```python
toggle_btn = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Toggle sidebar']")
```

**Expected Results**:
- Sidebar width changes
- Icons only when collapsed

---

### TC-UI-NAV-003: Breadcrumb Navigation
**Priority**: LOW
**Steps**:
1. Navigate to nested page
2. View breadcrumb trail
3. Click parent breadcrumb

**Expected Results**:
- Navigates to parent page

---

### TC-UI-NAV-004: Browser Back Button
**Priority**: MEDIUM
**Steps**:
1. Navigate through pages
2. Click browser back button
3. Verify previous page loads

**Expected Results**:
- History works correctly

---

### TC-UI-NAV-005: Direct URL Access
**Priority**: MEDIUM
**Steps**:
1. Login
2. Copy form URL
3. Open in new tab

**Expected Results**:
- Page loads directly
- Session maintained

---

### TC-UI-NAV-006: 404 Page
**Priority**: LOW
**Steps**:
1. Navigate to invalid URL
2. Verify 404 page

**Expected Results**:
- Error page displayed
- Link to return home

---

### TC-UI-NAV-007: Mobile Responsive Layout
**Priority**: MEDIUM
**Steps**:
1. Resize browser to mobile width (375px)
2. Verify responsive layout

**Expected Results**:
- Mobile-friendly layout
- Hamburger menu visible

---

### TC-UI-NAV-008: Header Logo Navigation
**Priority**: LOW
**Steps**:
1. Any page
2. Click logo in header
3. Verify returns to dashboard

**Expected Results**:
- Navigates to home/dashboard

---

## 9. ACCESSIBILITY TESTS (6 Test Cases)

### TC-UI-A11Y-001: Keyboard Navigation
**Priority**: MEDIUM
**Steps**:
1. Use Tab key to navigate
2. Verify focus order
3. Press Enter to activate

**Expected Results**:
- All interactive elements focusable
- Logical tab order

---

### TC-UI-A11Y-002: Screen Reader Support
**Priority**: MEDIUM
**Steps**:
1. Enable screen reader
2. Navigate through page
3. Verify ARIA labels present

**Expected Results**:
- Elements properly labeled
- Meaningful descriptions

---

### TC-UI-A11Y-003: Color Contrast
**Priority**: LOW
**Steps**:
1. Run contrast checker
2. Verify WCAG AA compliance

**Expected Results**:
- Contrast ratio >= 4.5:1 for text

---

### TC-UI-A11Y-004: Form Labels
**Priority**: MEDIUM
**Steps**:
1. Inspect form inputs
2. Verify each has label

**Expected Results**:
- All inputs labeled
- Labels associated correctly

---

### TC-UI-A11Y-005: Error Messages
**Priority**: MEDIUM
**Steps**:
1. Trigger validation error
2. Verify error announced

**Expected Results**:
- Error message visible
- aria-invalid attribute set

---

### TC-UI-A11Y-006: Skip to Content Link
**Priority**: LOW
**Steps**:
1. Tab from page load
2. First focus: "Skip to content"
3. Activate link

**Expected Results**:
- Skips to main content

---

## Summary

**Total Test Cases**: 95
**Estimated Execution Time**: 6-8 hours (full suite)
**Priority Breakdown**:
- HIGH: 52 test cases
- MEDIUM: 35 test cases
- LOW: 8 test cases

---

## Test Automation Best Practices

1. **Use Page Object Model** - Separate locators from test logic
2. **Wait Strategies** - Use explicit waits (WebDriverWait)
3. **Test Data Management** - Use fixtures/data providers
4. **Screenshot on Failure** - Capture evidence
5. **Parallel Execution** - Run tests concurrently
6. **CI/CD Integration** - Automate test runs
7. **Test Reports** - Generate HTML reports (pytest-html)

---

## Sample Test Code Structure

```python
# conftest.py
import pytest
from selenium import webdriver

@pytest.fixture
def driver():
    driver = webdriver.Chrome()
    driver.maximize_window()
    yield driver
    driver.quit()

# test_authentication.py
def test_user_login_valid(driver):
    driver.get("http://localhost:3000")
    # ... test steps
    assert driver.current_url.endswith("/dashboard")

# page_objects/login_page.py
class LoginPage:
    def __init__(self, driver):
        self.driver = driver

    def login(self, email, password):
        self.driver.find_element(By.NAME, "email").send_keys(email)
        self.driver.find_element(By.NAME, "password").send_keys(password)
        self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
```

---

**Document Version**: 1.0
**Last Updated**: 2025-01-15
**Total Test Cases**: 95
