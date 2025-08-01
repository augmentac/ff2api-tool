# ENHANCED FIELD MAPPING VALIDATION AND PERSISTENCE FUNCTIONS

import pandas as pd
import streamlit as st
from datetime import datetime
from src.backend.api_client import get_brokerage_key

def _render_update_configuration_form(config_to_update, brokerage_name, db_manager):
    """Render configuration update form that preserves field mappings"""
    st.markdown("### 🔧 Update Configuration")
    st.markdown(f"**Configuration:** {config_to_update['name']}")
    
    # Initialize form state if not exists
    if 'update_form_state' not in st.session_state:
        st.session_state.update_form_state = {
            'api_base_url': config_to_update['api_credentials'].get('base_url', 'https://api.prod.goaugment.com'),
            'api_key': config_to_update['api_credentials'].get('api_key', ''),
            'auth_type': config_to_update.get('auth_type', 'api_key'),
            'bearer_token': config_to_update.get('bearer_token', '') or ''
        }
    
    form_state = st.session_state.update_form_state
    
    with st.form("update_configuration_form", clear_on_submit=False):
        st.markdown("**Update Configuration Details**")
        
        # API Base URL
        form_state['api_base_url'] = st.text_input(
            "API Base URL *",
            value=form_state['api_base_url'],
            help="The base URL for the freight API"
        )
        
        # Authentication Type Selection
        form_state['auth_type'] = st.selectbox(
            "Authentication Type *",
            options=['api_key', 'bearer_token'],
            index=0 if form_state['auth_type'] == 'api_key' else 1,
            help="Select the authentication method"
        )
        
        # Conditional authentication fields
        if form_state['auth_type'] == 'api_key':
            form_state['api_key'] = st.text_input(
                "API Key *",
                value=form_state['api_key'],
                type="password",
                help="Your API key for authentication"
            )
            form_state['bearer_token'] = ''
        else:
            form_state['bearer_token'] = st.text_input(
                "Bearer Token *",
                value=form_state['bearer_token'],
                type="password", 
                help="Your bearer token for authentication"
            )
            form_state['api_key'] = ''
        
        # Form submission
        col1, col2 = st.columns([1, 1])
        
        with col1:
            update_submitted = st.form_submit_button("🔄 Update Configuration", use_container_width=True)
        
        with col2:
            if st.form_submit_button("❌ Cancel", use_container_width=True):
                st.session_state.show_update_form = False
                if 'update_form_state' in st.session_state:
                    del st.session_state.update_form_state
                if 'config_update_error' in st.session_state:
                    del st.session_state.config_update_error
                if 'config_update_success' in st.session_state:
                    del st.session_state.config_update_success
                st.rerun()
    
    # Handle form submission
    if update_submitted:
        _handle_update_configuration(config_to_update, brokerage_name, db_manager)
    
    # Display success/error messages
    if 'config_update_success' in st.session_state:
        st.success(st.session_state.config_update_success)
        del st.session_state.config_update_success
    
    if 'config_update_error' in st.session_state:
        st.error(st.session_state.config_update_error)
        del st.session_state.config_update_error

def _handle_update_configuration(config_to_update, brokerage_name, db_manager):
    """Handle updating existing configuration while preserving field mappings"""
    form_state = st.session_state.update_form_state
    
    api_base_url = form_state['api_base_url'].strip()
    auth_type = form_state['auth_type']
    api_key = form_state['api_key'].strip()
    bearer_token = form_state['bearer_token'].strip()
    
    # Validate required fields based on auth type
    if auth_type == 'api_key' and not api_key:
        st.session_state.config_update_error = "Please provide an API key for API key authentication"
        return
    elif auth_type == 'bearer_token' and not bearer_token:
        st.session_state.config_update_error = "Please provide a bearer token for bearer token authentication"
        return
    
    if not api_base_url:
        st.session_state.config_update_error = "Please provide an API base URL"
        return
    
    # Test API connection
    with st.spinner("Testing updated API connection..."):
        try:
            from src.backend.api_client import LoadsAPIClient
            
            # Get brokerage key for API validation
            brokerage_key = get_brokerage_key(brokerage_name)
            
            if auth_type == 'api_key':
                client = LoadsAPIClient(api_base_url, api_key=api_key, auth_type='api_key', brokerage_key=brokerage_key)
            else:  # bearer_token
                client = LoadsAPIClient(api_base_url, bearer_token=bearer_token, auth_type='bearer_token', brokerage_key=brokerage_key)
            
            result = client.validate_connection()
        
            if result['success']:
                # Update configuration in database while preserving field mappings
                try:
                    # Build updated API credentials based on auth type
                    if auth_type == 'api_key':
                        api_credentials = {
                            'base_url': api_base_url,
                            'api_key': api_key
                        }
                        save_bearer_token = None
                    else:  # bearer_token
                        api_credentials = {
                            'base_url': api_base_url
                        }
                        save_bearer_token = bearer_token
                    
                    # CRITICAL: Preserve existing field mappings
                    existing_mappings = config_to_update.get('field_mappings', {})
                    existing_headers = config_to_update.get('file_headers')
                    
                    # Update configuration in database
                    updated_config_id = db_manager.save_brokerage_configuration(
                        brokerage_name=brokerage_name,
                        configuration_name=config_to_update['name'],
                        field_mappings=existing_mappings,  # Preserve existing mappings
                        api_credentials=api_credentials,
                        file_headers=existing_headers,     # Preserve existing headers
                        description=config_to_update.get('description', ''),
                        auth_type=auth_type,
                        bearer_token=save_bearer_token
                    )
                    
                    # Explicitly increment version in database after save
                    import sqlite3
                    db_conn = sqlite3.connect(db_manager.db_path)
                    db_cursor = db_conn.cursor()
                    try:
                        db_cursor.execute('''
                            UPDATE brokerage_configurations 
                            SET version = version + 1
                            WHERE brokerage_name = ? AND configuration_name = ?
                        ''', (brokerage_name, config_to_update['name']))
                        db_conn.commit()
                    except Exception as version_error:
                        logging.warning(f"Failed to increment version: {version_error}")
                    finally:
                        db_conn.close()
                    
                    # Update session state configuration
                    updated_config = {
                        'id': updated_config_id,
                        'name': config_to_update['name'],
                        'brokerage_name': brokerage_name,
                        'configuration_name': config_to_update['name'],
                        'description': config_to_update.get('description', ''),
                        'api_credentials': api_credentials,
                        'auth_type': auth_type,
                        'bearer_token': save_bearer_token,
                        'field_mappings': existing_mappings,  # Preserved mappings
                        'file_headers': existing_headers,     # Preserved headers
                        'version': config_to_update.get('version', 1) + 1,  # Increment version
                        'updated_at': str(datetime.now()),
                        'field_count': len(existing_mappings)
                    }
                    
                    # Update selected configuration in session state
                    st.session_state.selected_configuration = updated_config
                    st.session_state.api_credentials = api_credentials
                    st.session_state.config_to_update = updated_config
                    
                    # Clear update form state
                    if 'update_form_state' in st.session_state:
                        del st.session_state.update_form_state
                    
                    # Hide update form and show success
                    st.session_state.show_update_form = False
                    st.session_state.config_update_success = "✅ Configuration updated successfully! Field mappings preserved."
                    
                    st.rerun()
                    
                except Exception as db_error:
                    st.session_state.config_update_error = f"❌ Failed to update configuration: {str(db_error)}"
                    
            else:
                st.session_state.config_update_error = f"❌ API connection failed: {result['message']}"
        except Exception as e:
            st.session_state.config_update_error = f"❌ Failed to test connection: {str(e)}"

def _validate_field_mapping(field: str, selected_column: str, df, field_info: dict) -> bool:
    """Simplified validation: Allow any CSV header to map to any API field"""
    try:
        # Only check if the selected column exists in the CSV
        return selected_column in df.columns
    except Exception:
        return False

def _immediate_save_field_mapping(field: str, selected_column: str, db_manager, brokerage_name: str):
    """Immediately save a single field mapping to the database"""
    try:
        config = st.session_state.get('selected_configuration')
        if not config:
            return
            
        # Get current field mappings from session state
        current_mappings = st.session_state.get('field_mappings', {}).copy()
        current_mappings[field] = selected_column
        
        # Get file headers if available
        file_headers = st.session_state.get('file_headers')
        
        # Save the updated configuration to database
        db_manager.save_brokerage_configuration(
            brokerage_name=brokerage_name,
            configuration_name=config['name'],
            field_mappings=current_mappings,
            api_credentials=config['api_credentials'],
            file_headers=file_headers,
            description=config.get('description', ''),
            auth_type=config.get('auth_type', 'api_key'),
            bearer_token=config.get('bearer_token')
        )
        
        # Update the session state configuration and field mappings to reflect the save
        st.session_state.selected_configuration['field_mappings'] = current_mappings
        st.session_state.selected_configuration['updated_at'] = datetime.now().isoformat()
        
        # ENHANCEMENT: Ensure session state field_mappings stays synchronized with database
        st.session_state.field_mappings = current_mappings.copy()
        
    except Exception as e:
        raise e