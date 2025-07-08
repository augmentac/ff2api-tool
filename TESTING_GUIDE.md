# FF2API - Complete Testing Guide

## Overview
This guide walks through testing the complete end-to-end workflow to ensure everything works properly.

## Test Data
Use the included `test_workflow.csv` file which contains 3 comprehensive freight records with all required fields.

## Step-by-Step Testing Guide

### 1. Initial Setup & Sidebar Appearance ✅
- Open http://localhost:8501
- **Verify**: Sidebar is expanded by default (not collapsed)
- **Verify**: Sidebar has clean, professional appearance
- **Verify**: Configuration section is prominently displayed

### 2. Configuration Creation
- In the sidebar, enter a brokerage name (e.g., "Test Brokerage")
- You should see "No configurations found. Create your first one:"
- Fill out the configuration form:
  - **Configuration name**: "Test Configuration"
  - **Description**: "Test configuration for workflow validation"
  - **API Base URL**: Leave as default (https://api.prod.goaugment.com)
  - **API Key**: Enter any valid-looking API key (e.g., "test-api-key-12345")
- Click "💾 Save Configuration"

### 3. Expected Behavior After Saving
- **Success Case**: Configuration should be saved to database
- **Error Case**: If API validation fails, you'll see an error message
- **Result**: Configuration should appear in sidebar dropdown for selection
- **Verify**: Session state should be updated with brokerage and API credentials

### 4. File Upload & Header Validation
- Click "Browse files" in the main workflow area
- Upload `test_workflow.csv`
- **Verify**: File loads successfully showing 3 records
- **Verify**: Data preview table appears with all columns
- **Verify**: Header validation completes without errors

### 5. Smart Field Mapping
- **Verify**: Intelligent field mapping suggestions appear
- **Verify**: Required fields are clearly marked
- **Verify**: Mapping interface is user-friendly and intuitive
- **Expected**: Most fields should auto-map correctly due to similar naming
- **Manual Action**: Adjust any mappings as needed

### 6. Validation & Configuration Save
- **Verify**: Data validation runs automatically
- **Verify**: Validation results are clearly displayed
- **Verify**: Configuration with field mappings is saved to database
- **Expected**: All 3 records should validate successfully

### 7. Process & Results
- **Verify**: Process button is enabled after validation
- **Verify**: Clear summary of records, fields, and status
- **Action**: Click "🚀 Process Data" to initiate processing
- **Expected**: Processing progress should be displayed
- **Result**: API submission results should be shown

## Test Scenarios

### Scenario A: New User First Time
1. Open application
2. Create brokerage and configuration
3. Upload test file
4. Complete mapping and validation
5. Process data

### Scenario B: Existing Configuration
1. Select existing brokerage from dropdown
2. Select existing configuration
3. Upload new file
4. Review header comparison
5. Adjust mappings if needed
6. Process data

### Scenario C: Error Handling
1. Test with invalid API key
2. Test with malformed CSV
3. Test with missing required fields
4. Verify appropriate error messages

## Success Criteria

### Configuration Management
- [x] Configurations persist to database
- [x] Sidebar shows saved configurations
- [x] API credentials are validated
- [x] Form state is properly managed

### File Processing
- [x] CSV files upload successfully
- [x] Data preview is accurate
- [x] Header validation works
- [x] Field mapping suggestions are intelligent

### Workflow Progression
- [x] User can progress through all 4 steps
- [x] Each step validates before proceeding
- [x] Clear progress indicators
- [x] Intuitive user interface

### Error Handling
- [x] Invalid API keys show appropriate errors
- [x] Malformed data is caught and reported
- [x] Network issues are handled gracefully
- [x] User-friendly error messages

## Known Limitations
- API validation requires actual API key for full testing
- Database persists in container (use docker volumes for production)
- File upload size limited to 50MB (configurable)

## Troubleshooting
- **Configuration not saving**: Check logs for database errors
- **API validation failing**: Verify API key format and network connectivity
- **File upload issues**: Check file format and size limits
- **Mapping problems**: Verify CSV headers match expected format

## Test Results Template
```
Test Date: _______________
Tester: __________________

[ ] Sidebar appearance and functionality
[ ] Configuration creation and persistence
[ ] File upload and validation
[ ] Field mapping intelligence
[ ] Data validation accuracy
[ ] End-to-end workflow completion
[ ] Error handling robustness

Notes:
_________________________
_________________________
_________________________
``` 