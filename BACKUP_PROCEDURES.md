# FF2API Backup Procedures

## 📋 Overview

This document provides detailed procedures for backing up and restoring data in the FF2API application. Since the application runs on Streamlit Cloud with ephemeral storage, regular backups are critical for data preservation.

## ⚠️ Important Notes

- **Ephemeral Storage**: All data is lost when the container restarts
- **Shared Database**: All team members share the same database
- **Manual Process**: Backups must be created and restored manually
- **No Automation**: No automated backup system is in place

## 💾 Backup Procedures

### Daily Backup Routine

**Recommended Schedule**: End of each business day

1. **Check Database Status**
   - Look for backup recommendations in the sidebar
   - Note container uptime and data volume

2. **Create Backup**
   - Go to sidebar "💾 Database Management" section
   - Click "📥 Download Backup"
   - Click "💾 Save Database Backup" when it appears

3. **Save Backup File**
   - File format: `ff2api_backup_YYYYMMDD_HHMMSS.json`
   - Save to shared company folder
   - Include date and time in filename

### Emergency Backup

**When to Use**: Before major operations, container issues, or data corruption

1. **Quick Backup Button**
   - Available during critical warnings
   - Click "📥 Quick Backup" if visible
   - Download "💾 Download Emergency Backup"

2. **Manual Emergency Backup**
   - Navigate to sidebar management section
   - Create backup immediately
   - Save with "emergency" prefix

### Backup File Organization

**Folder Structure**:
```
Company_Shared_Folder/
├── ff2api_backups/
│   ├── daily/
│   │   ├── ff2api_backup_20240101_170000.json
│   │   └── ff2api_backup_20240102_170000.json
│   ├── emergency/
│   │   └── ff2api_emergency_backup_20240101_120000.json
│   └── archive/
│       └── older_backups/
```

**Retention Policy**:
- Keep daily backups for 30 days
- Keep emergency backups for 90 days
- Archive monthly backups permanently

## 🔄 Restore Procedures

### Daily Restore (Morning Routine)

**When to Use**: Start of business day, after container restart

1. **Check Database Status**
   - Look for "📭 Database is empty" message
   - Sidebar shows restore options

2. **Restore Process**
   - Click "📤 Restore from backup"
   - Upload most recent backup file
   - Click "🔄 Restore Database"
   - Wait for "✅ Database restored successfully!"

3. **Verify Restoration**
   - Check configuration count
   - Verify recent upload history
   - Test key functionality

### Emergency Restore

**When to Use**: Data corruption, accidental deletion, system issues

1. **Assess Situation**
   - Determine what data was lost
   - Identify most recent good backup
   - Check with team about recent changes

2. **Restore Process**
   - Follow standard restore procedure
   - Use emergency backup if available
   - Verify data integrity after restore

3. **Post-Restore Actions**
   - Inform team of restoration
   - Create immediate backup
   - Monitor for issues

## 🔍 Backup Validation

### Backup File Verification

1. **File Size Check**
   - Typical backup: 50KB - 5MB
   - Empty database: < 10KB
   - Large datasets: > 1MB

2. **Content Verification**
   - Open backup file in text editor
   - Check for valid JSON structure
   - Verify backup_info section exists

3. **Integrity Checks**
   - Ensure brokerage_configurations section present
   - Check upload_history for recent entries
   - Verify created_at timestamps

### Test Restore Process

**Monthly Procedure**:
1. Create test backup
2. Clear database (if safe)
3. Restore from backup
4. Verify all data present
5. Document any issues

## 📊 Monitoring & Alerts

### Backup Recommendations

The system provides automatic recommendations:

- **🟢 Low Risk**: < 12 hours, < 5 configs
- **🟡 Medium Risk**: 12-24 hours, 5-20 configs
- **🔴 High Risk**: > 24 hours, > 20 configs
- **🚨 Critical**: > 72 hours, > 50 configs

### Container Age Monitoring

| Status | Time | Action Required |
|--------|------|----------------|
| ✅ Stable | < 12 hours | Normal operation |
| ⏰ Reminder | 12-24 hours | Consider backup |
| ⚠️ Warning | 24-72 hours | Backup recommended |
| 🚨 Critical | > 72 hours | Immediate backup |

## 🛠️ Troubleshooting

### Common Issues

1. **"Invalid backup file format"**
   - Solution: Verify JSON structure
   - Check file wasn't corrupted
   - Try different backup file

2. **"Database restored but data missing"**
   - Solution: Check backup file date
   - Verify backup contains expected data
   - May need older backup file

3. **"Restore failed: Database error"**
   - Solution: Clear browser cache
   - Refresh application
   - Try smaller backup file

### Recovery Scenarios

**Scenario 1: Container Restarted**
- Database is empty
- Use most recent daily backup
- Standard restore procedure

**Scenario 2: Data Corruption**
- Some data appears incorrect
- Use emergency backup
- May lose recent changes

**Scenario 3: Accidental Deletion**
- Specific configurations missing
- Use backup from before deletion
- Restore and re-add recent changes

## 👥 Team Coordination

### Backup Responsibilities

**Daily Backup Person**: Last person working each day
**Morning Restore Person**: First person working each day
**Backup Verification**: Weekly rotation among team members

### Communication Protocol

1. **Backup Created**
   - Notify team via Slack/email
   - Include backup filename
   - Note any issues

2. **Restore Needed**
   - Check with team before restoring
   - Confirm backup file to use
   - Announce restoration complete

3. **Issues Encountered**
   - Document problem clearly
   - Include error messages
   - Escalate to technical support

## 📈 Best Practices

### Backup Best Practices

1. **Regular Schedule**: Daily backups minimum
2. **Multiple Copies**: Keep several backup versions
3. **Safe Storage**: Use shared company folder
4. **Clear Naming**: Include date/time in filename
5. **Verification**: Periodically test restore process

### Data Management

1. **Clean Database**: Remove old test data
2. **Organize Configs**: Use clear naming conventions
3. **Document Changes**: Note major updates
4. **Monitor Usage**: Track database growth

### Security Considerations

1. **Access Control**: Limit backup folder access
2. **Encryption**: Backup files contain encrypted data
3. **Retention**: Follow company data retention policy
4. **Audit Trail**: Log backup/restore activities

## 📞 Support Contacts

- **Technical Issues**: IT Support Team
- **Process Questions**: Team Lead
- **Data Recovery**: Database Administrator
- **Access Problems**: System Administrator

---

**Remember**: Regular backups are your only protection against data loss. Make it a habit! 