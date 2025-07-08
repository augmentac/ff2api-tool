# FF2API Team Training Guide

## 🎯 Welcome to FF2API!

This guide will help you learn how to use FF2API effectively and safely. FF2API is our internal tool for converting CSV/Excel files into API data for freight processing.

## 🔐 Getting Started

### Accessing the Application

1. **Get the URL**: Your team administrator will provide the application URL
2. **Login**: Enter the team password when prompted
3. **Welcome Screen**: You'll see the main FF2API interface

**Important**: This is a shared environment - all team members use the same database.

## 📚 Basic Workflow

### Step 1: Setting Up Your Brokerage

1. **Select Brokerage** (Sidebar)
   - Choose existing brokerage from dropdown
   - OR create new brokerage by typing name

2. **Configure API Settings**
   - Click "➕ Create New" configuration
   - Enter configuration name (e.g., "Standard Mapping")
   - Add your API key
   - Test connection

### Step 2: Upload Your File

1. **Choose File**
   - Click "Choose a CSV or Excel file"
   - Select your data file
   - Supported: .csv, .xlsx, .xls

2. **File Requirements**
   - Maximum size: 200MB
   - First row should contain headers
   - Data should start from row 2

3. **Review Preview**
   - Check that data loaded correctly
   - Verify column names look right

### Step 3: Map Your Fields

1. **Automatic Mapping**
   - System suggests field mappings
   - Review suggestions carefully

2. **Manual Mapping**
   - Use dropdowns to map columns
   - Red fields are required
   - Yellow fields are recommended

3. **Required Fields**
   - Load Reference Number
   - Customer Name
   - Origin City
   - Destination City

### Step 4: Validate & Process

1. **Validate Data**
   - Click "Validate Mapping"
   - Review any errors
   - Fix issues if needed

2. **Process Data**
   - Click "Process Data" when ready
   - Monitor progress bar
   - Review results

## 💾 Backup Procedures

### Why Backups Matter

- **Ephemeral Storage**: Data disappears when container restarts
- **Shared Environment**: Everyone's work is in the same database
- **No Auto-Backup**: Manual backups are essential

### Daily Backup Routine

**End of Day Procedure** (Last person working):

1. **Check Sidebar**
   - Look for "💾 Database Management"
   - See backup recommendations

2. **Create Backup**
   - Click "📥 Download Backup"
   - Click "💾 Save Database Backup"
   - Save to shared company folder

3. **File Naming**
   - Use provided timestamp format
   - Example: `ff2api_backup_20240315_170000.json`

**Morning Procedure** (First person working):

1. **Check Database Status**
   - Look for "📭 Database is empty" message
   - If empty, database needs restoration

2. **Restore Process**
   - Click "📤 Restore from backup"
   - Upload most recent backup file
   - Click "🔄 Restore Database"
   - Verify configurations appear

### Emergency Backup

**When to Create Emergency Backup**:
- Before large file uploads
- Before major configuration changes
- When system shows warnings
- When container age > 24 hours

**How to Create**:
1. Look for "📥 Quick Backup" button
2. Or use regular backup process
3. Save with "emergency" prefix

## 🚨 Warning Signs & Actions

### Container Age Warnings

| Warning | Action Required |
|---------|----------------|
| ✅ Container stable (< 12h) | Normal operation |
| ⏰ Consider backup (12-24h) | Plan backup soon |
| ⚠️ Download backup (24-72h) | Create backup today |
| 🚨 Critical risk (> 72h) | Immediate backup |

### Database Size Warnings

- **Small database** (< 5 configs): Regular backups
- **Medium database** (5-20 configs): Weekly backups recommended
- **Large database** (> 20 configs): Daily backups essential

## 👥 Team Collaboration

### Shared Environment Rules

1. **Communicate**: Let team know about major operations
2. **Check First**: See if someone else is processing
3. **Backup Before**: Download backup before large uploads
4. **Name Clearly**: Use descriptive configuration names

### Configuration Naming

**Good Examples**:
- "ABC_Corp_Standard_Mapping"
- "XYZ_Logistics_LTL_Loads"
- "Regional_Carrier_Imports"

**Bad Examples**:
- "Test"
- "My_Config"
- "Temp"

### Conflict Resolution

**If you see unexpected data**:
1. Don't panic
2. Check with team
3. Restore from recent backup if needed
4. Document what happened

## 🔧 Troubleshooting

### Common Issues

#### "File won't upload"
- **Check**: File size (< 200MB)
- **Check**: File format (.csv, .xlsx, .xls)
- **Try**: Different browser
- **Try**: Clear browser cache

#### "No mapping suggestions"
- **Cause**: Column names don't match patterns
- **Solution**: Map manually using dropdowns
- **Tip**: Use standard column names for better auto-mapping

#### "API connection failed"
- **Check**: API key is correct
- **Check**: Internet connection
- **Try**: Test connection again
- **Contact**: Team lead if persistent

#### "Validation errors"
- **Review**: Error messages carefully
- **Fix**: Data format issues
- **Check**: Required fields are mapped
- **Verify**: Date formats (YYYY-MM-DD preferred)

#### "Processing failed"
- **Check**: Internet connection
- **Verify**: All required fields mapped
- **Try**: Smaller batch size
- **Contact**: Support if recurring

### Getting Help

1. **Check this guide** first
2. **Ask team members** for advice
3. **Contact team lead** for access issues
4. **Create GitHub issue** for bugs
5. **Email IT support** for urgent issues

## 📊 Best Practices

### File Preparation

1. **Clean Data**
   - Remove empty rows
   - Fix inconsistent formatting
   - Validate required fields

2. **Standard Headers**
   - Use consistent column names
   - Avoid special characters
   - Keep names descriptive

3. **Date Formats**
   - Use YYYY-MM-DD format
   - Ensure consistency
   - Avoid text dates

### Configuration Management

1. **Descriptive Names**
   - Include company/carrier name
   - Mention load type
   - Version if needed

2. **Regular Updates**
   - Update configurations when needed
   - Test after changes
   - Backup before major changes

3. **Documentation**
   - Add descriptions to configurations
   - Note special requirements
   - Share knowledge with team

### Backup Management

1. **Daily Routine**
   - Last person creates backup
   - First person restores if needed
   - Store in shared folder

2. **File Organization**
   - Use consistent naming
   - Keep multiple versions
   - Clean up old backups

3. **Verification**
   - Test restore process monthly
   - Verify backup integrity
   - Document any issues

## 📅 Weekly Team Routine

### Monday Morning
- [ ] First person checks database status
- [ ] Restore from weekend backup if needed
- [ ] Verify key configurations present

### During the Week
- [ ] Normal operations
- [ ] Create backups after major changes
- [ ] Monitor container age warnings

### Friday Evening
- [ ] Last person creates weekly backup
- [ ] Store in designated folder
- [ ] Clean up test configurations

## 🎓 Training Checklist

### Basic Skills
- [ ] Can access application
- [ ] Can create/select brokerage
- [ ] Can upload files successfully
- [ ] Can map fields correctly
- [ ] Can process data

### Backup Skills
- [ ] Can create backup
- [ ] Can restore from backup
- [ ] Knows when to backup
- [ ] Understands file naming

### Team Skills
- [ ] Follows communication protocol
- [ ] Uses proper naming conventions
- [ ] Checks before major operations
- [ ] Helps team members

### Troubleshooting
- [ ] Can resolve common issues
- [ ] Knows when to ask for help
- [ ] Can interpret error messages
- [ ] Follows escalation process

## 📞 Quick Reference

### Daily Actions
1. **Morning**: Check database, restore if needed
2. **Working**: Upload, map, process files
3. **Evening**: Create backup, save to shared folder

### Emergency Contacts
- **Team Lead**: [Contact Info]
- **IT Support**: [Contact Info] 
- **Application Issues**: Create GitHub issue

### Key URLs
- **Application**: [Your deployment URL]
- **GitHub Issues**: [Repository issues URL]
- **Documentation**: [Repository README]

---

## 🎉 You're Ready!

Congratulations! You now know how to:
- Use FF2API safely and effectively
- Follow proper backup procedures
- Collaborate with your team
- Troubleshoot common issues

**Remember**: When in doubt, ask for help. We're all here to support each other! 