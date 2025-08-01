"""
UI Components Module for FF2API
Contains reusable UI components and styling helpers
"""

import streamlit as st
import pandas as pd
import json
import re
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from src.backend.database import DatabaseManager
from src.backend.data_processor import DataProcessor
from src.backend.api_client import get_brokerage_key
import os
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_full_api_schema():
    """Get the complete API schema for validation - aligned with API requirements"""
    return {
        # Core Required Fields (Always Required)
        'load.loadNumber': {'type': 'string', 'required': True, 'description': 'Load Number'},
        'load.mode': {'type': 'string', 'required': True, 'description': 'Load Mode', 'enum': ['FTL', 'LTL', 'DRAYAGE']},
        'load.rateType': {'type': 'string', 'required': True, 'description': 'Rate Type', 'enum': ['SPOT', 'CONTRACT', 'DEDICATED', 'PROJECT']},
        'load.status': {'type': 'string', 'required': True, 'description': 'Load Status', 'enum': ['DRAFT', 'CUSTOMER_CONFIRMED', 'COVERED', 'DISPATCHED', 'AT_PICKUP', 'IN_TRANSIT', 'AT_DELIVERY', 'DELIVERED', 'POD_COLLECTED', 'CANCELED', 'ERROR']},
        
        # Route Information (Always Required - route array is required)
        'load.route.0.sequence': {'type': 'number', 'required': True, 'description': 'Stop Sequence'},
        'load.route.0.stopActivity': {'type': 'string', 'required': True, 'description': 'Stop Activity', 'enum': ['PICKUP', 'DELIVERY']},
        'load.route.0.address.street1': {'type': 'string', 'required': True, 'description': 'Address Street'},
        'load.route.0.address.city': {'type': 'string', 'required': True, 'description': 'Address City'},
        'load.route.0.address.stateOrProvince': {'type': 'string', 'required': True, 'description': 'Address State'},
        'load.route.0.address.postalCode': {'type': 'string', 'required': True, 'description': 'Address ZIP'},
        'load.route.0.address.country': {'type': 'string', 'required': True, 'description': 'Address Country'},
        'load.route.0.expectedArrivalWindowStart': {'type': 'date', 'required': True, 'description': 'Expected Arrival Start'},
        'load.route.0.expectedArrivalWindowEnd': {'type': 'date', 'required': True, 'description': 'Expected Arrival End'},
        
        # Delivery Stop Information (Usually required for most loads)
        'load.route.1.sequence': {'type': 'number', 'required': True, 'description': 'Delivery Stop Sequence'},
        'load.route.1.stopActivity': {'type': 'string', 'required': True, 'description': 'Delivery Stop Activity', 'enum': ['PICKUP', 'DELIVERY']},
        'load.route.1.address.street1': {'type': 'string', 'required': True, 'description': 'Delivery Address Street'},
        'load.route.1.address.city': {'type': 'string', 'required': True, 'description': 'Delivery Address City'},
        'load.route.1.address.stateOrProvince': {'type': 'string', 'required': True, 'description': 'Delivery Address State'},
        'load.route.1.address.postalCode': {'type': 'string', 'required': True, 'description': 'Delivery Address ZIP'},
        'load.route.1.address.country': {'type': 'string', 'required': True, 'description': 'Delivery Address Country'},
        'load.route.1.expectedArrivalWindowStart': {'type': 'date', 'required': True, 'description': 'Delivery Expected Arrival Start'},
        'load.route.1.expectedArrivalWindowEnd': {'type': 'date', 'required': True, 'description': 'Delivery Expected Arrival End'},
        
        # Customer Information - Fixed: only name is required, customerId is optional
        'customer.customerId': {'type': 'string', 'required': False, 'description': 'Customer ID'},
        'customer.name': {'type': 'string', 'required': True, 'description': 'Customer Name'},
        
        # Brokerage Information (Required object)
        'brokerage.contacts.0.name': {'type': 'string', 'required': False, 'description': 'Broker Contact Name'},
        'brokerage.contacts.0.email': {'type': 'string', 'required': False, 'description': 'Broker Email'},
        'brokerage.contacts.0.phone': {'type': 'string', 'required': False, 'description': 'Broker Phone'},
        'brokerage.contacts.0.role': {'type': 'array', 'required': 'conditional', 'description': 'Broker Contact Role', 'enum': ['ACCOUNT_MANAGER', 'OPERATIONS_REP', 'CARRIER_REP', 'CUSTOMER_TEAM']},
        
        # Load Items (Conditionally Required - if items provided, quantity and totalWeightLbs required)
        'load.items.0.quantity': {'type': 'number', 'required': 'conditional', 'description': 'Item Quantity'},
        'load.items.0.packageType': {'type': 'string', 'required': False, 'description': 'Package Type', 'enum': ['PALLET', 'PIECE', 'CARTON', 'TOTE', 'SKID', 'CRATE', 'BOX', 'DRUM', 'BUNDLE', 'OTHER']},
        'load.items.0.description': {'type': 'string', 'required': False, 'description': 'Item Description'},
        'load.items.0.totalWeightLbs': {'type': 'number', 'required': 'conditional', 'description': 'Total Weight'},
        'load.items.0.lengthInches': {'type': 'number', 'required': False, 'description': 'Length in Inches'},
        'load.items.0.widthInches': {'type': 'number', 'required': False, 'description': 'Width in Inches'},
        'load.items.0.heightInches': {'type': 'number', 'required': False, 'description': 'Height in Inches'},
        'load.items.0.freightClass': {'type': 'string', 'required': False, 'description': 'Freight Class', 'enum': ['50', '55', '60', '65', '70', '77.5', '85', '92.5', '100', '110', '125', '150', '175', '200', '250', '300', '400', '500']},
        'load.items.0.nmfc': {'type': 'string', 'required': False, 'description': 'NMFC Code'},
        'load.items.0.density': {'type': 'number', 'required': False, 'description': 'Density'},
        'load.items.0.pickupSequence': {'type': 'number', 'required': False, 'description': 'Pickup Sequence'},
        'load.items.0.deliverySequence': {'type': 'number', 'required': False, 'description': 'Delivery Sequence'},
        
        # Equipment Information (Conditionally Required - if equipment provided, equipmentType required)
        'load.equipment.equipmentType': {'type': 'string', 'required': 'conditional', 'description': 'Equipment Type', 'enum': ['DRY_VAN', 'FLATBED', 'REEFER', 'CONTAINER', 'OTHER']},
        'load.equipment.description': {'type': 'string', 'required': False, 'description': 'Equipment Description'},
        'load.equipment.minTemperatureF': {'type': 'number', 'required': False, 'description': 'Min Temperature F'},
        'load.equipment.maxTemperatureF': {'type': 'number', 'required': False, 'description': 'Max Temperature F'},
        'load.equipment.accessorials': {'type': 'array', 'required': False, 'description': 'Equipment Accessorials'},
        
        # Reference Numbers (Conditionally Required - if provided, name and value required)
        'load.referenceNumbers.0.name': {'type': 'string', 'required': 'conditional', 'description': 'Reference Number Name', 'enum': ['PRO_NUMBER', 'PICKUP_NUMBER', 'PO_NUMBER', 'TRAILER_NUMBER', 'TRUCK_NUMBER', 'SHIPPER_NUMBER', 'CONSIGNEE_NUMBER', 'OTHER']},
        'load.referenceNumbers.0.value': {'type': 'string', 'required': 'conditional', 'description': 'Reference Number Value'},
        
        # Bid Criteria (Conditionally Required - if bidCriteria provided, these become required)
        'bidCriteria.equipment': {'type': 'string', 'required': 'conditional', 'description': 'Required Equipment'},
        'bidCriteria.totalWeightLbs': {'type': 'number', 'required': 'conditional', 'description': 'Total Weight for Bidding'},
        'bidCriteria.targetCostUsd': {'type': 'number', 'required': 'conditional', 'description': 'Target Cost'},
        'bidCriteria.maxBidAmountUsd': {'type': 'number', 'required': 'conditional', 'description': 'Maximum Bid Amount'},
        'bidCriteria.service': {'type': 'string', 'required': False, 'description': 'Service Type', 'enum': ['STANDARD', 'PARTIAL', 'VOLUME', 'HOTSHOT', 'TIME_CRITICAL']},
        'bidCriteria.accessorials': {'type': 'array', 'required': False, 'description': 'Load Accessorials', 'enum': ['DETENTION', 'DETENTION_LOADING', 'DETENTION_UNLOADING', 'LAYOVER', 'AFTER_HOURS', 'WEEKEND', 'HOLIDAY', 'LUMPER', 'DRIVER_ASSIST', 'DRIVER_COUNT', 'SORT_AND_SEGREGATE', 'INSIDE_DELIVERY', 'INSIDE_PICKUP', 'LIFTGATE', 'FORKLIFT', 'LIMITED_ACCESS', 'RESIDENTIAL', 'CONSTRUCTION_SITE', 'TRADESHOW', 'MILITARY_BASE', 'TEAM_SERVICE', 'TRAILER_CLEANING', 'OVERSIZE', 'OVERWEIGHT', 'LOAD_BAR', 'STRAPS', 'CHAINS', 'TARPS', 'TARGETED_COMMODITY', 'HIGH_VISIBILITY', 'TEMPERATURE_REQUIREMENT', 'HIGH_VALUE', 'RAMPS', 'TONU', 'TWIC', 'TANKER_ENDORSED', 'FOOD_GRADE', 'TRAILER_INTERCHANGE', 'GENERAL_LIABILITY', 'BULK_HEAD', 'HAZMAT', 'E_TRACKING', 'POD_REQUIRED', 'NOTIFY_BEFORE_ARRIVAL', 'DELIVERY_APPOINTMENT', 'PICKUP_APPOINTMENT', 'SIGNATURE_REQUIRED']},
        'bidCriteria.minTemperatureF': {'type': 'number', 'required': False, 'description': 'Min Temperature F'},
        'bidCriteria.maxTemperatureF': {'type': 'number', 'required': False, 'description': 'Max Temperature F'},
        'bidCriteria.bidExpiration': {'type': 'string', 'required': False, 'description': 'Bid Expiration (RFC 3339 date-time)'},
        'bidCriteria.dimensions.heightInches': {'type': 'number', 'required': 'conditional', 'description': 'Height in Inches'},
        'bidCriteria.dimensions.lengthInches': {'type': 'number', 'required': 'conditional', 'description': 'Length in Inches'},
        'bidCriteria.dimensions.widthInches': {'type': 'number', 'required': 'conditional', 'description': 'Width in Inches'},
        'bidCriteria.flexAttributes.0.name': {'type': 'string', 'required': 'conditional', 'description': 'Flex Attribute Name'},
        'bidCriteria.flexAttributes.0.value': {'type': 'string', 'required': 'conditional', 'description': 'Flex Attribute Value'},
        
        # Carrier Information (Optional object - if provided, name and dotNumber conditionally required)
        'carrier.carrierId': {'type': 'string', 'required': False, 'description': 'Carrier ID'},
        'carrier.name': {'type': 'string', 'required': 'conditional', 'description': 'Carrier Name'},
        'carrier.dotNumber': {'type': 'number', 'required': 'conditional', 'description': 'DOT Number'},
        'carrier.mcNumber': {'type': 'number', 'required': False, 'description': 'MC Number'},
        'carrier.scac': {'type': 'string', 'required': False, 'description': 'SCAC Code'},
        'carrier.address.street1': {'type': 'string', 'required': 'conditional', 'description': 'Carrier Address Street'},
        'carrier.address.street2': {'type': 'string', 'required': False, 'description': 'Carrier Address Street 2'},
        'carrier.address.city': {'type': 'string', 'required': 'conditional', 'description': 'Carrier Address City'},
        'carrier.address.stateOrProvince': {'type': 'string', 'required': 'conditional', 'description': 'Carrier Address State'},
        'carrier.address.postalCode': {'type': 'string', 'required': 'conditional', 'description': 'Carrier Address ZIP'},
        'carrier.address.country': {'type': 'string', 'required': 'conditional', 'description': 'Carrier Address Country'},
        'carrier.contacts.0.id': {'type': 'string', 'required': False, 'description': 'Carrier Contact ID'},
        'carrier.contacts.0.name': {'type': 'string', 'required': False, 'description': 'Carrier Contact Name'},
        'carrier.contacts.0.email': {'type': 'string', 'required': False, 'description': 'Carrier Contact Email'},
        'carrier.contacts.0.phone': {'type': 'string', 'required': False, 'description': 'Carrier Contact Phone'},
        'carrier.contacts.0.role': {'type': 'string', 'required': 'conditional', 'description': 'Carrier Contact Role', 'enum': ['DISPATCHER', 'CARRIER_ADMIN']},
        'carrier.drivers.0.id': {'type': 'string', 'required': False, 'description': 'Driver ID'},
        'carrier.drivers.0.name': {'type': 'string', 'required': False, 'description': 'Driver Name'},
        'carrier.drivers.0.phone': {'type': 'string', 'required': 'conditional', 'description': 'Driver Phone'},
        
        # Tracking Events (Conditionally Required - if provided, eventType, eventSource, eventUtc required)
        'load.trackingEvents.0.eventType': {'type': 'string', 'required': 'conditional', 'description': 'Event Type', 'enum': ['INFO', 'PING', 'DRIVER_AT_PICKUP', 'DRIVER_AT_DELIVERY', 'PICKED_UP', 'DELIVERED', 'DELAYED']},
        'load.trackingEvents.0.eventSource': {'type': 'string', 'required': 'conditional', 'description': 'Event Source', 'enum': ['MACROPOINT', '4KITES', 'P44', 'SMC3', 'CARRIER_API', 'PHONE_EMAIL', 'TEXT', 'OTHER']},
        'load.trackingEvents.0.eventUtc': {'type': 'string', 'required': 'conditional', 'description': 'Event UTC (RFC 3339 date-time)'},
        'load.trackingEvents.0.city': {'type': 'string', 'required': False, 'description': 'Event City'},
        'load.trackingEvents.0.stateOrProvince': {'type': 'string', 'required': False, 'description': 'Event State'},
        'load.trackingEvents.0.latitude': {'type': 'number', 'required': False, 'description': 'Event Latitude'},
        'load.trackingEvents.0.longitude': {'type': 'number', 'required': False, 'description': 'Event Longitude'},
        'load.trackingEvents.0.temperatureF': {'type': 'number', 'required': False, 'description': 'Event Temperature'},
        'load.trackingEvents.0.notes': {'type': 'string', 'required': False, 'description': 'Event Notes'},
    }

def get_dynamic_field_requirements(api_schema, current_mappings):
    """
    Determine which fields should be required based on current mappings.
    Core required fields are always required.
    Conditional fields become required when related fields are mapped.
    """
    # Always required fields
    always_required = {k: v for k, v in api_schema.items() if v.get('required') is True}
    
    # Start with always required fields
    dynamic_required = always_required.copy()
    
    # Check if any fields from conditional groups are mapped
    mapped_fields = set(current_mappings.keys())
    
    # Conditional requirement groups
    conditional_groups = {
        'bidCriteria': [
            'bidCriteria.equipment', 'bidCriteria.totalWeightLbs', 'bidCriteria.targetCostUsd',
            'bidCriteria.maxBidAmountUsd', 'bidCriteria.dimensions.heightInches',
            'bidCriteria.dimensions.lengthInches', 'bidCriteria.dimensions.widthInches',
            'bidCriteria.flexAttributes.0.name', 'bidCriteria.flexAttributes.0.value'
        ],
        'carrier': [
            'carrier.name', 'carrier.dotNumber', 'carrier.address.street1',
            'carrier.address.city', 'carrier.address.stateOrProvince',
            'carrier.address.postalCode', 'carrier.address.country',
            'carrier.contacts.0.role', 'carrier.drivers.0.phone'
        ],
        'items': [
            'load.items.0.quantity', 'load.items.0.totalWeightLbs'
        ],
        'equipment': [
            'load.equipment.equipmentType'
        ],
        'referenceNumbers': [
            'load.referenceNumbers.0.name', 'load.referenceNumbers.0.value'
        ],
        'trackingEvents': [
            'load.trackingEvents.0.eventType', 'load.trackingEvents.0.eventSource',
            'load.trackingEvents.0.eventUtc'
        ],
        'brokerageContacts': [
            'brokerage.contacts.0.role'
        ]
    }
    
    # For each conditional group, check if any field is mapped
    for group_name, group_fields in conditional_groups.items():
        group_has_mapping = any(field in mapped_fields for field in group_fields)
        
        if group_has_mapping:
            # Add all conditional fields from this group as required
            for field in group_fields:
                if field in api_schema and api_schema[field].get('required') == 'conditional':
                    dynamic_required[field] = api_schema[field]
    
    # ENHANCEMENT: Preserve previously mapped fields as "user required"
    # This ensures optional fields don't disappear from UI after mapping
    if current_mappings:
        previously_mapped = set(current_mappings.keys())
        for field in previously_mapped:
            if (field in api_schema and 
                field not in dynamic_required and 
                current_mappings[field] and 
                current_mappings[field] != 'Select column...'):
                # Mark as user-mapped to keep in UI
                field_info = api_schema[field].copy()
                field_info['user_mapped'] = True
                field_info['display_category'] = 'previously_mapped'
                dynamic_required[field] = field_info
    
    return dynamic_required

def sync_field_mapping_state(db_mappings, session_mappings):
    """Ensure database and session state are synchronized"""
    # Merge mappings with session state taking precedence for active changes
    synchronized_mappings = db_mappings.copy() if db_mappings else {}
    
    if session_mappings:
        # Only update if session has newer valid changes
        for field, mapping in session_mappings.items():
            if mapping and mapping != 'Select column...':
                synchronized_mappings[field] = mapping
    
    return synchronized_mappings

# Common enum fields registry for better UX
COMMON_ENUM_FIELDS = {
    'load.mode': {
        'values': ['FTL', 'LTL', 'DRAYAGE'],
        'descriptions': {
            'FTL': 'Full Truckload - Single shipper uses entire truck',
            'LTL': 'Less Than Truckload - Shared truck space', 
            'DRAYAGE': 'Short-distance transport (port/rail to warehouse)'
        },
        'common_alternatives': {
            'full truckload': 'FTL', 'ftl': 'FTL',
            'less than truckload': 'LTL', 'ltl': 'LTL',
            'drayage': 'DRAYAGE'
        }
    },
    'load.rateType': {
        'values': ['SPOT', 'CONTRACT', 'DEDICATED', 'PROJECT'],
        'descriptions': {
            'SPOT': 'One-time market rate shipment',
            'CONTRACT': 'Pre-negotiated rates and terms',
            'DEDICATED': 'Reserved carrier capacity',
            'PROJECT': 'Specialized project shipping'
        }
    },
    'load.status': {
        'values': ['DRAFT', 'CUSTOMER_CONFIRMED', 'COVERED', 'DISPATCHED', 'AT_PICKUP', 'IN_TRANSIT', 'AT_DELIVERY', 'DELIVERED', 'POD_COLLECTED', 'CANCELED', 'ERROR'],
        'descriptions': {
            'DRAFT': 'Load created but not confirmed',
            'CUSTOMER_CONFIRMED': 'Customer has confirmed the load',
            'COVERED': 'Carrier assigned to load',
            'DISPATCHED': 'Load dispatched to carrier'
        }
    }
}

def validate_manual_value_realtime(field_path, manual_value, api_schema):
    """Real-time validation for manual values with enum support"""
    if field_path not in api_schema:
        return False, "Field not found in API schema"
    
    field_info = api_schema[field_path]
    
    # Enum validation (most important)
    if field_info.get('enum'):
        enum_values = field_info['enum']
        if manual_value not in enum_values:
            return False, f"Must be one of: {', '.join(enum_values)}"
        return True, f"✅ Valid enum value"
    
    # Type validation
    field_type = field_info.get('type', 'string')
    if field_type == 'number':
        try:
            float(manual_value)
            return True, "✅ Valid number"
        except ValueError:
            return False, "Must be a valid number"
    
    elif field_type == 'date':
        try:
            import pandas as pd
            pd.to_datetime(manual_value)
            return True, "✅ Valid date format"
        except:
            return False, "Must be valid date (YYYY-MM-DD or ISO format)"
    
    # String fields - generally valid
    return True, "✅ Valid text value"

def create_smart_manual_value_interface(field_path, field_info, current_value=None):
    """Intelligent manual value interface that adapts to field type"""
    
    # Extract current manual value if exists
    current_manual = None
    if current_value and current_value.startswith("MANUAL_VALUE:"):
        current_manual = current_value.replace("MANUAL_VALUE:", "")
    
    st.markdown(f"**Set Manual Default Value for:** `{field_path}`")
    st.caption(f"📋 {field_info.get('description', 'No description available')}")
    
    # Check if field has enum constraints
    if field_info.get('enum'):
        # ENUM FIELD - Provide dropdown selection
        enum_options = field_info['enum']
        st.markdown(f"*Valid options: {', '.join(enum_options)}*")
        
        # Find current selection index
        current_index = 0
        if current_manual and current_manual in enum_options:
            current_index = enum_options.index(current_manual) + 1
        
        selected_value = st.selectbox(
            f"Select default value for {field_info.get('description', field_path)}",
            options=['-- Select Value --'] + enum_options,
            index=current_index,
            key=f"manual_enum_{field_path}",
            help=f"This value will be applied to ALL records for {field_path}"
        )
        
        # Show enum description if available
        if selected_value != '-- Select Value --':
            enum_info = COMMON_ENUM_FIELDS.get(field_path, {})
            descriptions = enum_info.get('descriptions', {})
            if selected_value in descriptions:
                st.caption(f"💡 {descriptions[selected_value]}")
        
        return selected_value if selected_value != '-- Select Value --' else None
        
    else:
        # NON-ENUM FIELD - Provide text input with validation
        field_type = field_info.get('type', 'string')
        
        # Provide type-specific input
        if field_type == 'number':
            manual_value = st.number_input(
                f"Default numeric value for {field_info.get('description', field_path)}",
                value=float(current_manual) if current_manual and current_manual.replace('.', '').replace('-', '').isdigit() else 0.0,
                key=f"manual_number_{field_path}",
                help=f"This numeric value will be applied to ALL records for {field_path}"
            )
            return str(manual_value) if manual_value != 0.0 else None
            
        elif field_type == 'date':
            manual_value = st.text_input(
                f"Default date value for {field_info.get('description', field_path)}",
                value=current_manual or '',
                key=f"manual_date_{field_path}",
                placeholder="YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS.000Z",
                help=f"Date format: YYYY-MM-DD or full ISO format. Applied to ALL records for {field_path}"
            )
            
            # Real-time validation for dates
            if manual_value:
                is_valid, msg = validate_manual_value_realtime(field_path, manual_value, {field_path: field_info})
                if is_valid:
                    st.success(msg)
                else:
                    st.error(msg)
            
            return manual_value if manual_value else None
            
        else:
            # String field
            manual_value = st.text_input(
                f"Default text value for {field_info.get('description', field_path)}",
                value=current_manual or '',
                key=f"manual_text_{field_path}",
                help=f"This text value will be applied to ALL records for {field_path}"
            )
            return manual_value if manual_value else None

def show_enhanced_configuration_summary(field_mappings, api_schema):
    """Show configuration summary with enum value highlights"""
    manual_count = 0
    enum_manual_count = 0
    csv_mappings = 0
    invalid_enum_count = 0
    
    for field, mapping in field_mappings.items():
        if mapping.startswith("MANUAL_VALUE:"):
            manual_count += 1
            manual_value = mapping.replace("MANUAL_VALUE:", "")
            
            # Check if it's an enum field
            if field in api_schema and api_schema[field].get('enum'):
                enum_manual_count += 1
                enum_values = api_schema[field]['enum']
                if manual_value not in enum_values:
                    invalid_enum_count += 1
        else:
            csv_mappings += 1
    
    # Display summary with color coding
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "📋 Total Mappings", 
            len(field_mappings),
            help="Total number of mapped fields"
        )
    
    with col2:
        st.metric(
            "📝 Manual Values", 
            manual_count,
            delta=f"{enum_manual_count} enum fields" if enum_manual_count > 0 else None,
            help="Fields with manual default values"
        )
    
    with col3:
        st.metric(
            "📊 CSV Mappings", 
            csv_mappings,
            help="Fields mapped to CSV columns"
        )
    
    # Show detailed manual value information
    if manual_count > 0:
        with st.expander(f"📝 Manual Value Details ({manual_count} fields)", expanded=False):
            for field, mapping in field_mappings.items():
                if mapping.startswith("MANUAL_VALUE:"):
                    manual_value = mapping.replace("MANUAL_VALUE:", "")
                    
                    col_field, col_value, col_type = st.columns([2, 1, 1])
                    
                    with col_field:
                        st.text(field)
                    
                    with col_value:
                        # Check if it's an enum field
                        if field in api_schema and api_schema[field].get('enum'):
                            enum_values = api_schema[field]['enum']
                            if manual_value in enum_values:
                                st.success(f"**{manual_value}**")
                            else:
                                st.error(f"**{manual_value}** ⚠️")
                        else:
                            st.info(f"**{manual_value}**")
                    
                    with col_type:
                        if field in api_schema and api_schema[field].get('enum'):
                            st.caption("🎯 Enum")
                        elif field in api_schema:
                            st.caption(f"📋 {api_schema[field].get('type', 'string')}")
                        else:
                            st.caption("❓ Unknown")
    
    # Warnings for invalid enum values
    if invalid_enum_count > 0:
        st.warning(f"⚠️ {invalid_enum_count} manual value(s) don't match their enum constraints. These may cause processing errors.")

def save_manual_value_immediately(field, manual_value, db_manager, brokerage_name):
    """Immediately save manual value to database and session state"""
    from src.frontend.mapping_validation import _immediate_save_field_mapping
    
    manual_mapping = f"MANUAL_VALUE:{manual_value}"
    
    # Update session state
    if 'field_mappings' not in st.session_state:
        st.session_state.field_mappings = {}
    st.session_state.field_mappings[field] = manual_mapping
    
    # Save to database immediately
    _immediate_save_field_mapping(field, manual_mapping, db_manager, brokerage_name)

def update_field_mapping_and_requirements(field, selected_column, current_mappings, api_schema):
    """Update field mapping and recalculate requirements based on new mapping"""
    # Update the mapping
    if selected_column and selected_column != "-- Select Column --":
        current_mappings[field] = selected_column
    elif field in current_mappings:
        del current_mappings[field]
    
    # Recalculate requirements based on updated mappings
    updated_required_fields = get_dynamic_field_requirements(api_schema, current_mappings)
    
    return current_mappings, updated_required_fields

def load_custom_css():
    """Load custom CSS styles with fallback mechanisms"""
    try:
        # Try multiple possible paths for CSS file
        possible_paths = [
            'src/frontend/styles.css',
            '/app/src/frontend/styles.css',
            './src/frontend/styles.css',
            'styles.css'
        ]
        
        css_content = None
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        css_content = f.read()
                    break
                except Exception as e:
                    continue
        
        if css_content:
            st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)
        else:
            # Fallback: inline essential CSS with space-saving improvements
            fallback_css = """
            <style>
            :root {
                --primary-color: #2563eb;
                --success-color: #10b981;
                --warning-color: #f59e0b;
                --error-color: #ef4444;
                --background-light: #f8fafc;
                --text-primary: #1e293b;
                --text-secondary: #64748b;
            }
            
            /* Compact success/warning/error alerts */
            .stAlert[data-baseweb="notification"] {
                padding: 0.5rem 1rem !important;
                margin: 0.5rem 0 !important;
                border-radius: 0.5rem !important;
            }
            
            .stSuccess {
                background: rgba(16, 185, 129, 0.1) !important;
                border: 1px solid rgba(16, 185, 129, 0.2) !important;
                border-left: 4px solid #10b981 !important;
            }
            
            .stWarning {
                background: rgba(245, 158, 11, 0.1) !important;
                border: 1px solid rgba(245, 158, 11, 0.2) !important;
                border-left: 4px solid #f59e0b !important;
            }
            
            .stError {
                background: rgba(239, 68, 68, 0.1) !important;
                border: 1px solid rgba(239, 68, 68, 0.2) !important;
                border-left: 4px solid #ef4444 !important;
            }
            
            /* Compact headers */
            .markdown-text-container h3 {
                margin: 1rem 0 0.5rem 0 !important;
                font-size: 1.25rem !important;
            }
            
            .markdown-text-container h4 {
                margin: 0.75rem 0 0.25rem 0 !important;
                font-size: 1.1rem !important;
            }
            
            /* Reduced spacing between elements */
            .element-container {
                margin-bottom: 0.5rem !important;
            }
            
            /* Compact expander styling */
            .streamlit-expander {
                margin: 0.25rem 0 !important;
            }
            
            /* Compact caption styling */
            .caption {
                margin: 0.25rem 0 !important;
                font-size: 0.875rem !important;
            }
            
            .main-header {
                background: linear-gradient(135deg, var(--primary-color), #1d4ed8);
                padding: 2rem;
                border-radius: 1rem;
                margin-bottom: 2rem;
                color: white;
            }
            .custom-card {
                background: white;
                border-radius: 0.75rem;
                padding: 1rem;
                border: 1px solid #e2e8f0;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                margin-bottom: 0.5rem;
            }
            .metric-card {
                background: white;
                border-radius: 0.75rem;
                padding: 1rem;
                border: 1px solid #e2e8f0;
                text-align: center;
            }
            .metric-value {
                font-size: 1.5rem;
                font-weight: 700;
                color: var(--primary-color);
                margin-bottom: 0.25rem;
            }
            .metric-label {
                color: var(--text-secondary);
                font-size: 0.875rem;
                font-weight: 500;
            }
            
            /* Force sidebar to stay expanded */
            .css-1d391kg {
                width: 21rem !important;
                min-width: 21rem !important;
            }
            
            /* Ensure sidebar visibility */
            .css-1lcbmhc {
                display: flex !important;
            }
            
            /* Sidebar toggle button styling */
            .css-1v3fvcr {
                position: fixed;
                top: 10px;
                left: 10px;
                z-index: 999;
            }
            </style>
            """
            st.markdown(fallback_css, unsafe_allow_html=True)
            
            # Add JavaScript to maintain sidebar state
            sidebar_js = """
            <script>
            // Force sidebar to stay expanded after file upload
            function maintainSidebarState() {
                const sidebar = document.querySelector('.css-1d391kg');
                if (sidebar) {
                    sidebar.style.width = '21rem';
                    sidebar.style.minWidth = '21rem';
                    sidebar.style.display = 'flex';
                }
                
                const sidebarContent = document.querySelector('.css-1lcbmhc');
                if (sidebarContent) {
                    sidebarContent.style.display = 'flex';
                }
            }
            
            // Run on page load and after updates
            document.addEventListener('DOMContentLoaded', maintainSidebarState);
            window.addEventListener('load', maintainSidebarState);
            
            // Use MutationObserver to watch for DOM changes
            const observer = new MutationObserver(maintainSidebarState);
            observer.observe(document.body, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ['style', 'class']
            });
            
            // Ensure sidebar stays expanded on rerun
            setTimeout(maintainSidebarState, 100);
            setTimeout(maintainSidebarState, 500);
            setTimeout(maintainSidebarState, 1000);
            </script>
            """
            st.markdown(sidebar_js, unsafe_allow_html=True)
            
    except Exception as e:
        # Silent fallback - don't break the app if CSS fails
        pass

def render_main_header():
    """Render the main application header with fallback"""
    try:
        st.markdown("""
            <div style="background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); padding: 1rem 2rem; border-radius: 0.5rem; margin-bottom: 1rem;">
                <h2 style="color: white; margin: 0; font-size: 1.5rem; font-weight: 700;">{CSV} FF2API</h2>
                <p style="color: rgba(255,255,255,0.9); margin: 0.25rem 0 0 0; font-size: 0.9rem;">flat file to API processing with Augment</p>
            </div>
        """, unsafe_allow_html=True)
    except:
        # Fallback to standard Streamlit components
        st.title("{CSV} FF2API")
        st.markdown("**flat file to API processing with Augment**")

def render_workflow_progress(current_step: int = 1):
    """Render workflow progress indicator for streamlined workflow"""
    try:
        steps = [
            {"num": 1, "label": "File Upload", "icon": "📂", "desc": "Upload CSV and validate headers"},
            {"num": 2, "label": "Smart Mapping", "icon": "🔗", "desc": "Map fields with intelligent suggestions"},
            {"num": 3, "label": "Quality Check", "icon": "✅", "desc": "Validate data quality and save configuration"},
            {"num": 4, "label": "Process & Results", "icon": "🚀", "desc": "Process data and view results"}
        ]
        
        # Create a compact horizontal progress bar using columns
        st.markdown("""
            <div style="background: white; padding: 0.75rem 1rem; border-radius: 0.5rem; border: 1px solid #e2e8f0; margin-bottom: 1rem;">
        """, unsafe_allow_html=True)
        
        # Use streamlit columns for better compatibility
        cols = st.columns([1, 0.2, 1, 0.2, 1, 0.2, 1])
        
        for i, step in enumerate(steps):
            if step["num"] < current_step:
                status_text = "✅"
                text_color = "#10b981"
            elif step["num"] == current_step:
                status_text = "🔄"
                text_color = "#2563eb"
            else:
                status_text = "⏳"
                text_color = "#94a3b8"
            
            # Step content
            with cols[i * 2]:
                st.markdown(f"""
                    <div style="text-align: center;">
                        <div style="color: {text_color}; font-size: 1.1rem; margin-bottom: 0.25rem;">{step['icon']}</div>
                        <div style="color: {text_color}; font-weight: 600; font-size: 0.7rem; line-height: 1.2;">{step['label']}</div>
                        <div style="color: {text_color}; font-size: 0.6rem;">{status_text}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            # Connector line (except for last step)
            if i < len(steps) - 1:
                connector_color = "#10b981" if step["num"] < current_step else "#e2e8f0"
                with cols[i * 2 + 1]:
                    st.markdown(f"""
                        <div style="text-align: center; padding-top: 1rem;">
                            <div style="width: 100%; height: 2px; background: {connector_color};"></div>
                        </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
            
    except:
        # Fallback to simple text
        st.info(f"📍 Current Step: {current_step} of 4")

def render_step_card(step_number: int, title: str, description: str, icon: str = "📋"):
    """Render a step card with fallback"""
    try:
        st.markdown(f"""
            <div style="background: white; border-radius: 0.75rem; padding: 1.5rem; border: 1px solid #e2e8f0; margin-bottom: 1rem;">
                <div style="display: flex; align-items: center;">
                    <div style="width: 3rem; height: 3rem; border-radius: 50%; background: #2563eb; color: white; display: flex; align-items: center; justify-content: center; font-weight: 600; margin-right: 1rem;">
                        {step_number}
                    </div>
                    <div>
                        <h3 style="margin: 0; color: #1e293b;">{icon} {title}</h3>
                        <p style="margin: 0; color: #64748b; font-size: 0.9rem;">{description}</p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    except:
        # Fallback to standard components
        st.subheader(f"Step {step_number}: {icon} {title}")
        st.write(description)
        st.markdown("---")

def render_custom_card(title: str, content: str = "", icon: str = "📋", card_type: str = "default"):
    """Render a custom card with fallback"""
    try:
        st.markdown(f"""
            <div class="custom-card">
                <div style="display: flex; align-items: center; margin-bottom: 1rem; padding-bottom: 0.75rem; border-bottom: 2px solid #e2e8f0;">
                    <span style="font-size: 1.5rem; margin-right: 0.75rem;">{icon}</span>
                    <h3 style="margin: 0; color: #1e293b;">{title}</h3>
                </div>
                {f'<div>{content}</div>' if content else ''}
            </div>
        """, unsafe_allow_html=True)
    except:
        # Fallback to expander
        with st.expander(f"{icon} {title}", expanded=True):
            if content:
                st.write(content)

def render_status_badge(text: str, status: str = "info"):
    """Render a status badge with fallback"""
    try:
        colors = {
            "success": "#10b981",
            "warning": "#f59e0b", 
            "error": "#ef4444",
            "info": "#2563eb"
        }
        color = colors.get(status, "#2563eb")
        return f'<span style="background: {color}20; color: {color}; padding: 0.25rem 0.75rem; border-radius: 1rem; font-size: 0.8rem; font-weight: 600;">{text}</span>'
    except:
        return text

def render_metric_card(value: str, label: str, delta: str = "", delta_positive: bool = True):
    """Render a metric card with fallback"""
    try:
        delta_html = ""
        if delta:
            delta_color = "#10b981" if delta_positive else "#ef4444"
            delta_html = f'<div style="color: {delta_color}; font-size: 0.8rem; margin-top: 0.25rem;">{delta}</div>'
        
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
                {delta_html}
            </div>
        """, unsafe_allow_html=True)
    except:
        # Fallback to st.metric
        st.metric(label, value, delta if delta else None)

def create_enhanced_file_uploader(key: str = "file_uploader"):
    """Create a simplified file uploader"""
    st.markdown("### 📁 Upload Your File")
    st.caption("Select a CSV or Excel file containing your freight data")
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['csv', 'xlsx', 'xls'],
        key=key,
        help="Supported formats: CSV, Excel (.xlsx, .xls). Maximum size: 50MB"
    )
    
    # No success message here - will be handled by main workflow
    return uploaded_file

def create_connection_status_card(api_credentials: Optional[Dict[str, str]], auth_type: str = 'api_key'):
    """Create a connection status card with fallback"""
    if api_credentials:
        try:
            auth_display = "🔑 API Key" if auth_type == 'api_key' else "🎫 Bearer Token"
            st.markdown(f"""
                <div style="background: rgba(16, 185, 129, 0.1); padding: 1.5rem; border-radius: 0.75rem; border: 1px solid rgba(16, 185, 129, 0.2); margin-bottom: 1rem;">
                    <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                        <span style="font-size: 1.5rem; margin-right: 0.5rem;">✅</span>
                        <strong style="color: #10b981;">API Connection Active</strong>
                    </div>
                    <p style="margin: 0; color: #64748b; font-size: 0.9rem;">
                        Connected to: {api_credentials.get('base_url', 'Unknown')}<br/>
                        Authentication: {auth_display}
                    </p>
                </div>
            """, unsafe_allow_html=True)
        except:
            auth_display = "API Key" if auth_type == 'api_key' else "Bearer Token"
            st.success(f"✅ API Connected to: {api_credentials.get('base_url', 'Unknown')} ({auth_display})")
    else:
        try:
            st.markdown("""
                <div style="background: rgba(245, 158, 11, 0.1); padding: 1.5rem; border-radius: 0.75rem; border: 1px solid rgba(245, 158, 11, 0.2); margin-bottom: 1rem;">
                    <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                        <span style="font-size: 1.5rem; margin-right: 0.5rem;">⚠️</span>
                        <strong style="color: #f59e0b;">API Connection Required</strong>
                    </div>
                    <p style="margin: 0; color: #64748b; font-size: 0.9rem;">
                        Please configure your API credentials to continue
                    </p>
                </div>
            """, unsafe_allow_html=True)
        except:
            st.warning("⚠️ API Connection Required - Please configure your credentials")

def create_data_preview_card(df: pd.DataFrame):
    """Create a compact, collapsible data preview card"""
    if df is not None and not df.empty:
        # Compact metrics in a single line
        total_records = len(df)
        total_cols = len(df.columns)
        non_empty_cols = df.count().sum()
        completeness = (non_empty_cols / (total_records * total_cols) * 100)
        
        # Compact summary with expandable details
        with st.expander(f"👀 Data Preview - {total_records} records, {total_cols} columns, {completeness:.0f}% complete", expanded=False):
            # Detailed metrics in compact format
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Records", total_records)
            with col2:
                st.metric("Columns", total_cols)
            with col3:
                st.metric("Data Points", non_empty_cols)
            with col4:
                st.metric("Complete", f"{completeness:.1f}%")
            
            # Data table with reduced height
            st.dataframe(df.head(5), use_container_width=True, height=200)
            if total_records > 5:
                st.caption(f"Showing first 5 rows of {total_records} total records")

def create_mapping_progress_indicator(total_fields: int, mapped_fields: int):
    """Create a mapping progress indicator with fallback"""
    progress = mapped_fields / total_fields if total_fields > 0 else 0
    percentage = int(progress * 100)
    
    try:
        st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 0.75rem; border: 1px solid #e2e8f0; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <strong>Field Mapping Progress</strong>
                    <span style="color: #2563eb; font-weight: 600;">{mapped_fields}/{total_fields} fields</span>
                </div>
                <div style="background: #e2e8f0; height: 8px; border-radius: 4px; overflow: hidden;">
                    <div style="background: #2563eb; height: 100%; width: {percentage}%; transition: width 0.3s ease;"></div>
                </div>
                <div style="text-align: center; margin-top: 0.5rem; color: #64748b; font-size: 0.9rem;">
                    {percentage}% Complete
                </div>
            </div>
        """, unsafe_allow_html=True)
    except:
        # Fallback to Streamlit progress bar
        st.subheader("Field Mapping Progress")
        st.progress(progress)
        st.write(f"{mapped_fields}/{total_fields} fields mapped ({percentage}% complete)")

def create_validation_summary_card(validation_errors: list, total_records: int):
    """Create a smart validation summary - detailed only when needed"""
    error_count = len(validation_errors)
    success_count = total_records - error_count
    success_rate = (success_count / total_records * 100) if total_records > 0 else 100
    
    if error_count == 0:
        # Perfect validation - minimal display
        st.success("✅ Perfect! All Records Valid")
        return True
    elif success_rate >= 90:
        # Minor issues - compact warning
        st.warning(f"⚠️ {error_count} minor issues found ({success_rate:.0f}% valid)")
        with st.expander(f"View {error_count} validation issues", expanded=False):
            for i, error in enumerate(validation_errors[:5]):
                st.caption(f"Row {error.get('row', i+1)}: {str(error)[:100]}...")
            if error_count > 5:
                st.caption(f"... and {error_count - 5} more issues")
        return True
    else:
        # Significant issues - show details
        st.error(f"❌ {error_count} validation issues found ({success_rate:.0f}% valid)")
        
        # Compact metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total", total_records)
        with col2:
            st.metric("Valid", success_count, f"{success_rate:.0f}%")
        with col3:
            st.metric("Issues", error_count, f"{100-success_rate:.0f}%")
        
        # Error details
        with st.expander("View validation errors", expanded=True):
            for i, error in enumerate(validation_errors[:10]):
                st.error(f"Row {error.get('row', i+1)}: {str(error)}")
            if error_count > 10:
                st.info(f"... and {error_count - 10} more validation issues")
        
        return False

def create_processing_progress_display():
    """Create a compact processing progress display"""
    if 'processing_step' not in st.session_state:
        st.session_state.processing_step = 0
    
    steps = [
        "Preparing data...",
        "Validating records...",
        "Formatting for API...",
        "Submitting to API...",
        "Processing responses...",
        "Generating results..."
    ]
    
    current_step = st.session_state.processing_step
    progress = (current_step + 1) / len(steps)
    
    # Compact progress indicator
    if current_step < len(steps):
        st.info(f"⚡ Processing: {steps[current_step]} ({current_step + 1}/{len(steps)})")
        st.progress(progress)
    else:
        st.success("✅ Processing complete!")

def create_results_summary_card(success_count: int, failure_count: int, total_time: float):
    """Create a compact results summary with smart messaging"""
    total_count = success_count + failure_count
    success_rate = (success_count / total_count * 100) if total_count > 0 else 0
    
    # Single consolidated message with all key information
    if success_rate == 100:
        st.success(f"🎉 Processing Complete! All {total_count} records processed successfully in {total_time:.1f}s")
    elif success_rate >= 90:
        st.warning(f"⚠️ Processing mostly successful: {success_count}/{total_count} records processed ({success_rate:.0f}% success) in {total_time:.1f}s")
    else:
        st.error(f"❌ Processing issues: Only {success_count}/{total_count} records successful ({success_rate:.0f}%) in {total_time:.1f}s")
    
    # Compact metrics in a single row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Records", total_count)
    with col2:
        st.metric("Successful", success_count, f"{success_rate:.0f}%")
    with col3:
        st.metric("Failed", failure_count, f"{100-success_rate:.0f}%")
    with col4:
        st.metric("Processing Time", f"{total_time:.1f}s", f"{total_time/total_count:.2f}s per record")

def create_enhanced_button(text: str, button_type: str = "primary", icon: str = "", disabled: bool = False, 
                          help_text: str = "", key: Optional[str] = None, use_container_width: bool = True):
    """Create an enhanced button with custom styling"""
    
    button_class = ""
    if button_type == "success":
        button_class = "success-button"
    elif button_type == "warning":
        button_class = "warning-button"
    elif button_type == "error":
        button_class = "error-button"
    
    # Create the button
    if button_class:
        # Use custom CSS class
        button_clicked = st.button(
            f"{icon} {text}" if icon else text,
            disabled=disabled,
            help=help_text if help_text else None,
            key=key,
            use_container_width=use_container_width
        )
        
        # Apply custom styling via CSS injection
        if button_class:
            st.markdown(f"""
                <style>
                .stButton:last-child > button {{
                    background: var(--{button_type}-color) !important;
                }}
                .stButton:last-child > button:hover {{
                    filter: brightness(110%) !important;
                }}
                </style>
            """, unsafe_allow_html=True)
    else:
        # Convert button_type to valid Streamlit button type
        streamlit_type = "primary" if button_type in ["primary", "secondary"] else "primary"
        button_clicked = st.button(
            f"{icon} {text}" if icon else text,
            disabled=disabled,
            help=help_text if help_text else None,
            key=key,
            use_container_width=use_container_width,
            type=streamlit_type
        )
    
    return button_clicked

def create_field_mapping_card(csv_field: str, api_field: str, confidence: Optional[float] = None, 
                             sample_data: Optional[List[str]] = None):
    """Create a field mapping visualization card with fallback"""
    
    confidence_color = "#10b981" if confidence and confidence > 0.8 else "#f59e0b"
    confidence_text = f"{confidence*100:.0f}%" if confidence else "Manual"
    
    sample_preview = ""
    if sample_data:
        preview_items = sample_data[:3]
        sample_preview = f"""
            <div style="margin-top: 0.5rem; font-size: 0.8rem; color: #64748b;">
                <strong>Sample:</strong> {', '.join(str(x) for x in preview_items)}
                {' ...' if len(sample_data) > 3 else ''}
            </div>
        """
    
    try:
        st.markdown(f"""
            <div style="background: white; border: 1px solid #e2e8f0; 
                        border-radius: 0.5rem; padding: 1rem; margin-bottom: 0.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <div style="font-weight: 600; color: #1e293b; margin-bottom: 0.25rem;">
                            📄 {csv_field}
                        </div>
                        <div style="color: #64748b; font-size: 0.9rem;">
                            ➡️ {api_field}
                        </div>
                        {sample_preview}
                    </div>
                    <div style="text-align: center;">
                        <span style="background: rgba(37, 99, 235, 0.1); color: {confidence_color}; 
                                     padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.8rem; font-weight: 600;">
                            {confidence_text}
                        </span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    except:
        # Fallback to simple text display
        st.write(f"📄 **{csv_field}** ➡️ {api_field} ({confidence_text})")
        if sample_data:
            st.caption(f"Sample: {', '.join(str(x) for x in sample_data[:3])}")
        st.divider()

def create_company_settings_card(customer_name: str, last_used: Optional[str] = None, fields_mapped: int = 0):
    """Create a company settings overview card with fallback"""
    last_used_text = f"Last used: {last_used}" if last_used else "Never used"
    
    try:
        st.markdown(f"""
            <div style="background: white; border-radius: 0.75rem; padding: 1.5rem; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h4 style="margin: 0; color: #1e293b;">🏢 {customer_name}</h4>
                        <p style="margin: 0.25rem 0 0 0; color: #64748b; font-size: 0.9rem;">
                            {last_used_text}
                        </p>
                    </div>
                    <div style="text-align: right;">
                        <div style="background: rgba(37, 99, 235, 0.1); color: #2563eb; 
                                    padding: 0.5rem; border-radius: 0.5rem; font-weight: 600;">
                            {fields_mapped} fields mapped
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    except:
        # Fallback to simple display
        st.subheader(f"🏢 {customer_name}")
        st.write(f"{last_used_text} • {fields_mapped} fields mapped")
        st.divider()

def show_tooltip(text: str, tooltip: str):
    """Show text with a tooltip with fallback"""
    try:
        st.markdown(f"""
            <span title="{tooltip}" style="border-bottom: 1px dotted #64748b; cursor: help;">
                {text}
            </span>
        """, unsafe_allow_html=True)
    except:
        # Fallback to simple text with help text
        st.write(f"{text} ❓")
        st.caption(tooltip)

# Additional helper functions for better compatibility
def safe_render_html(html_content: str, fallback_text: str = ""):
    """Safely render HTML with fallback"""
    try:
        st.markdown(html_content, unsafe_allow_html=True)
    except:
        if fallback_text:
            st.write(fallback_text)

def create_simple_card(title: str, content: str = "", icon: str = "📋"):
    """Create a simple card that always works"""
    st.markdown(f"### {icon} {title}")
    if content:
        st.write(content)
    st.markdown("---")

def create_alert_card(message: str, alert_type: str = "info"):
    """Create an alert card with fallback"""
    icons = {
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
        "info": "ℹ️"
    }
    
    icon = icons.get(alert_type, "ℹ️")
    
    if alert_type == "success":
        st.success(f"{icon} {message}")
    elif alert_type == "warning":
        st.warning(f"{icon} {message}")
    elif alert_type == "error":
        st.error(f"{icon} {message}")
    else:
        st.info(f"{icon} {message}")

def create_divider_with_text(text: str):
    """Create a divider with text"""
    try:
        st.markdown(f"""
            <div style="text-align: center; margin: 2rem 0;">
                <div style="border-top: 1px solid #e2e8f0; position: relative;">
                    <span style="background: white; padding: 0 1rem; position: absolute; top: -0.5rem; left: 50%; transform: translateX(-50%); color: #64748b; font-size: 0.9rem;">
                        {text}
                    </span>
                </div>
            </div>
        """, unsafe_allow_html=True)
    except:
        st.markdown(f"--- {text} ---")

def render_loading_spinner(text: str = "Loading..."):
    """Render a loading spinner with text"""
    with st.spinner(text):
        pass 

def create_step_navigation_buttons(current_step: int, can_proceed: bool = False, next_step_callback=None):
    """Create navigation buttons for workflow steps"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if current_step > 1:
            if st.button("⬅️ Previous Step", key=f"prev_step_{current_step}"):
                st.session_state.current_step = max(1, current_step - 1)
                st.rerun()
    
    with col3:
        if can_proceed and current_step < 6:
            if st.button("Next Step ➡️", type="primary", key=f"next_step_{current_step}"):
                st.session_state.current_step = min(6, current_step + 1)
                if next_step_callback:
                    next_step_callback()
                st.rerun()

def create_enhanced_mapping_interface(df, existing_mappings, data_processor):
    """Create an enhanced, more user-friendly mapping interface"""
    st.subheader("🔗 Smart Field Mapping")
    
    # Get the API schema
    api_schema = get_full_api_schema()
    
    # Initialize mappings
    if existing_mappings:
        field_mappings = existing_mappings.copy()
    else:
        field_mappings = {}
    
    # Get dynamic requirements based on current mappings
    required_fields = get_dynamic_field_requirements(api_schema, field_mappings)
    optional_fields = {k: v for k, v in api_schema.items() if k not in required_fields}
    
    # Progress indicator for mapping completeness
    total_required = len(required_fields)
    mapped_required = len([f for f in required_fields.keys() if f in field_mappings])
    
    if total_required > 0:
        progress = mapped_required / total_required
        st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; border: 1px solid #e2e8f0;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <strong>Required Fields Progress</strong>
                    <span style="color: #2563eb;">{mapped_required}/{total_required} completed</span>
                </div>
                <div style="background: #e2e8f0; height: 8px; border-radius: 4px;">
                    <div style="background: #2563eb; height: 100%; width: {progress*100}%; border-radius: 4px; transition: width 0.3s;"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Smart mapping suggestions
    if not existing_mappings:
        with st.spinner("🧠 Generating smart mapping suggestions..."):
            try:
                suggested_mappings = data_processor.suggest_mapping(list(df.columns), api_schema, df)
                if suggested_mappings:
                    st.success(f"✨ Generated {len(suggested_mappings)} smart mapping suggestions!")
                    field_mappings.update(suggested_mappings)
                    # Recalculate requirements after adding suggestions
                    required_fields = get_dynamic_field_requirements(api_schema, field_mappings)
                    optional_fields = {k: v for k, v in api_schema.items() if k not in required_fields}
                else:
                    st.info("💡 No automatic suggestions found. Please map fields manually below.")
            except Exception as e:
                st.warning(f"⚠️ Could not generate smart mappings: {str(e)}")
    
    # Add refresh button to recalculate requirements
    col_refresh, col_spacer = st.columns([1, 3])
    with col_refresh:
        if st.button("🔄 Refresh Requirements", help="Recalculate which fields are required based on current mappings"):
            # Store current mapping values from session state
            current_session_mappings = {}
            for key in st.session_state:
                if key.startswith('field_mapping_'):
                    field_name = key.replace('field_mapping_', '')
                    value = st.session_state[key]
                    if value and value != "-- Select Column --":
                        current_session_mappings[field_name] = value
            
            # Recalculate requirements
            required_fields = get_dynamic_field_requirements(api_schema, current_session_mappings)
            optional_fields = {k: v for k, v in api_schema.items() if k not in required_fields}
            st.rerun()

    # Tabbed interface for better organization
    tab1, tab2 = st.tabs(["⭐ Required Fields", "📄 Optional Fields"])
    
    updated_mappings = field_mappings.copy()
    
    with tab1:
        st.markdown("### Required Fields (Must be mapped)")
        if not required_fields:
            st.info("No required fields found in the API schema.")
        else:
            for field, field_info in required_fields.items():
                create_field_mapping_row(field, field_info, df, updated_mappings, required=True)
    
    with tab2:
        st.markdown("### Optional Fields (Enhance your data)")
        
        # Group optional fields by category for better UX - Enhanced keyword patterns
        # Create helper functions for better field categorization
        def is_pricing_bid_field(f):
            return ('bid' in f.lower() or 'cost' in f.lower() or 'rate' in f.lower() or 
                   'pricing' in f.lower() or 'target' in f.lower() or 'max' in f.lower() or
                   'bidcriteria' in f.lower() or 'dimensions' in f.lower() or 'flexattributes' in f.lower())
        
        def is_load_info_field(f):
            return ('items' in f or 'equipment' in f or 'weight' in f or 
                   'package' in f.lower() or 'quantity' in f.lower() or 'freight' in f.lower() or
                   'nmfc' in f.lower() or 'density' in f.lower() or 'sequence' in f.lower() or
                   'reference' in f.lower() or 'tracking' in f.lower())
        
        def is_location_field(f):
            return ('address' in f or 'route' in f or 'location' in f.lower() or 
                   'street' in f.lower() or 'city' in f.lower() or 'state' in f.lower() or
                   'postal' in f.lower() or 'country' in f.lower() or 'arrival' in f.lower() or
                   'completion' in f.lower() or 'latitude' in f.lower() or 'longitude' in f.lower())
        
        def is_contact_carrier_field(f):
            return ('contact' in f or 'carrier' in f or 'driver' in f or 
                   'brokerage' in f or 'customer' in f or 'phone' in f.lower() or
                   'email' in f.lower() or 'role' in f.lower() or 'name' in f.lower() or
                   'dot' in f.lower() or 'mc' in f.lower() or 'scac' in f.lower())
        
        # Categorize with priority order to prevent duplicates
        pricing_fields = [f for f in optional_fields.keys() if is_pricing_bid_field(f)]
        load_fields = [f for f in optional_fields.keys() if not is_pricing_bid_field(f) and is_load_info_field(f)]
        location_fields = [f for f in optional_fields.keys() if not is_pricing_bid_field(f) and not is_load_info_field(f) and is_location_field(f)]
        contact_fields = [f for f in optional_fields.keys() if not is_pricing_bid_field(f) and not is_load_info_field(f) and not is_location_field(f) and is_contact_carrier_field(f)]
        other_fields = [f for f in optional_fields.keys() if not is_pricing_bid_field(f) and not is_load_info_field(f) and not is_location_field(f) and not is_contact_carrier_field(f)]
        
        categories = {
            "💰 Pricing & Bids": pricing_fields,
            "📦 Load Information": load_fields,
            "📍 Location Details": location_fields,
            "👥 Contacts & Carriers": contact_fields,
            "📋 Other Fields": other_fields
        }
        
        for category_name, category_fields in categories.items():
            if category_fields:
                with st.expander(f"{category_name} ({len(category_fields)} fields)", expanded=False):
                    for field in category_fields:
                        if field in optional_fields:
                            create_field_mapping_row(field, optional_fields[field], df, updated_mappings, required=False)
    
    # Action buttons with better UX
    st.markdown("---")
    st.markdown("### Mapping Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("✅ Apply All Mappings", type="primary", use_container_width=True, key="enhanced_apply_mappings"):
            st.session_state.field_mappings = updated_mappings
            mapped_required_after = len([f for f in required_fields.keys() if f in updated_mappings])
            st.success(f"Applied {len(updated_mappings)} mappings! ({mapped_required_after}/{total_required} required fields mapped)")
            if mapped_required_after == total_required:
                st.session_state.current_step = max(st.session_state.get('current_step', 1), 5)
            st.rerun()
    
    with col2:
        if st.button("🧠 Auto-Map Fields", use_container_width=True, key="enhanced_auto_map"):
            with st.spinner("🔄 Generating fresh mapping suggestions..."):
                try:
                    fresh_mappings = data_processor.suggest_mapping(list(df.columns), api_schema, df)
                    st.session_state.field_mappings = fresh_mappings
                    st.success("Generated fresh automatic mappings!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to generate mappings: {str(e)}")
    
    with col3:
        if st.button("🗑️ Clear All", use_container_width=True, key="enhanced_clear_mappings"):
            st.session_state.field_mappings = {}
            st.info("Cleared all mappings")
            st.rerun()
    
    with col4:
        if st.button("💾 Save & Continue", type="secondary", use_container_width=True, key="enhanced_save_continue"):
            st.session_state.field_mappings = updated_mappings
            mapped_required_after = len([f for f in required_fields.keys() if f in updated_mappings])
            if mapped_required_after == total_required:
                st.session_state.current_step = max(st.session_state.get('current_step', 1), 5)
                st.success("✅ Mappings saved! Moving to validation step...")
                st.rerun()
            else:
                st.warning(f"⚠️ Please map all {total_required} required fields before continuing. Currently mapped: {mapped_required_after}")
    
    return updated_mappings

def create_field_mapping_row(field: str, field_info: dict, df, updated_mappings: dict, required: bool = False):
    """Create a single field mapping row with enhanced UX"""
    col1, col2, col3 = st.columns([3, 2, 1])
    
    with col1:
        # Field description with better formatting
        required_indicator = "⭐" if required else "📄"
        color = "#dc2626" if required else "#64748b"
        
        st.markdown(f"""
            <div style="padding: 0.5rem; background: {'rgba(239, 68, 68, 0.05)' if required else 'rgba(248, 250, 252, 1)'}; 
                        border-radius: 0.5rem; border-left: 3px solid {color};">
                <div style="font-weight: 600; color: {color};">
                    {required_indicator} {field_info.get('description', field)}
                </div>
                <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.25rem;">
                    <code>{field}</code>
                </div>
                {f'<div style="font-size: 0.75rem; color: #dc2626; margin-top: 0.25rem;"><strong>Required Field</strong></div>' if required else ''}
            </div>
        """, unsafe_allow_html=True)
        
        # Display enum options separately to avoid HTML rendering issues
        if field_info.get('enum'):
            st.caption(f"**Options:** {', '.join(str(option) for option in field_info['enum'])}")
    
    with col2:
        # Column selection with current mapping highlighted
        current_mapping = updated_mappings.get(field, None)
        column_options = ["None"] + list(df.columns)
        
        if current_mapping and current_mapping.startswith('MANUAL_VALUE:'):
            default_index = 0
        elif current_mapping and current_mapping in column_options:
            default_index = column_options.index(current_mapping)
        else:
            default_index = 0
        
        selected_column = st.selectbox(
            "Map to CSV column",
            options=column_options,
            index=default_index,
            key=f"enhanced_mapping_{field}",
            label_visibility="collapsed"
        )
        
        if selected_column != "None":
            updated_mappings[field] = selected_column
            # Show sample data preview
            if selected_column in df.columns:
                sample_data = df[selected_column].dropna().head(3).tolist()
                if sample_data:
                    st.caption(f"Sample: {', '.join(str(x)[:20] for x in sample_data)}")
        elif field in updated_mappings and not updated_mappings[field].startswith('MANUAL_VALUE:'):
            if field in updated_mappings:
                del updated_mappings[field]
    
    with col3:
        # Manual value option with modal-like interface
        if st.button("✏️", key=f"enhanced_manual_{field}", help="Enter manual value"):
            manual_value = st.text_input(
                f"Manual value for {field_info['description']}", 
                key=f"enhanced_manual_input_{field}",
                placeholder="Enter value..."
            )
            if manual_value:
                updated_mappings[field] = f"MANUAL_VALUE:{manual_value}"
                st.success(f"✅ Set manual value: {manual_value}")

 

def create_brokerage_selection_interface(db_manager):
    """Create brokerage selection interface with configuration management"""
    st.markdown("### Select Brokerage")
    
    # Get all existing brokerages
    brokerages = db_manager.get_all_brokerages()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Brokerage selection
        brokerage_options = ["Create New Brokerage"] + [b['name'] for b in brokerages]
        
        selected_option = st.selectbox(
            "Choose a brokerage",
            options=brokerage_options,
            key="brokerage_selection",
            help="Select an existing brokerage or create a new one"
        )
        
        if selected_option == "Create New Brokerage":
            brokerage_name = st.text_input(
                "New Brokerage Name",
                key="new_brokerage_name",
                placeholder="Enter brokerage name..."
            )
        else:
            brokerage_name = selected_option
    
    with col2:
        if selected_option != "Create New Brokerage":
            # Show brokerage info
            brokerage_info = next((b for b in brokerages if b['name'] == selected_option), None)
            if brokerage_info:
                st.markdown(f"""
                    <div style="background: #f8fafc; padding: 1rem; border-radius: 0.5rem; border-left: 3px solid #3b82f6;">
                        <div style="font-weight: 600; color: #1e293b;">📊 Brokerage Info</div>
                        <div style="margin-top: 0.5rem; font-size: 0.9rem; color: #64748b;">
                            <div>📁 {brokerage_info['config_count']} configurations</div>
                            <div>📅 Last used: {brokerage_info['last_used'] or 'Never'}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
    
    if brokerage_name:
        return brokerage_name
    else:
        st.info("👆 Please select or enter a brokerage name to continue")
        return None

def create_configuration_management_interface(brokerage_name, db_manager):
    """Create configuration management interface"""
    st.markdown("### Configuration Management")
    
    # Get existing configurations for this brokerage
    configurations = db_manager.get_brokerage_configurations(brokerage_name)
    
    if configurations:
        # Show existing configurations
        st.markdown("#### Existing Configurations")
        
        config_option = st.radio(
            "Choose configuration option:",
            ["Use existing configuration", "Create new configuration"],
            key="config_option"
        )
        
        if config_option == "Use existing configuration":
            # Configuration selection interface
            selected_config = None
            
            for i, config in enumerate(configurations):
                with st.expander(f"📁 {config['name']}", expanded=i==0):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        auth_type = config.get('auth_type', 'api_key')
                        auth_display = "🔑 API Key" if auth_type == 'api_key' else "🎫 Bearer Token"
                        st.markdown(f"""
                            **Description:** {config.get('description', 'No description')}
                            
                            **Fields mapped:** {config['field_count']}
                            
                            **Authentication:** {auth_display}
                            
                            **Created:** {config['created_at'][:10]}
                            
                            **Last used:** {config['last_used_at'][:10] if config['last_used_at'] else 'Never'}
                        """)
                    
                    with col2:
                        if st.button(f"📋 Preview", key=f"preview_config_{i}"):
                            st.json(config['field_mappings'])
                    
                    with col3:
                        if st.button(f"✅ Select", type="primary", key=f"select_config_{i}"):
                            selected_config = config
                            st.session_state.selected_configuration = config
                            st.session_state.brokerage_name = brokerage_name
                            st.session_state.api_credentials = config['api_credentials']
                            st.rerun()
            
            if 'selected_configuration' in st.session_state:
                config = st.session_state.selected_configuration
                st.success(f"✅ Selected configuration: {config['name']}")
                return config
        
        else:  # Create new configuration
            return create_new_configuration_interface(brokerage_name)
    
    else:
        # No existing configurations
        st.info("🆕 No existing configurations found. Let's create your first one!")
        return create_new_configuration_interface(brokerage_name)

def create_new_configuration_interface(brokerage_name):
    """Create interface for new configuration setup"""
    st.markdown("#### New Configuration Setup")
    
    col1, col2 = st.columns(2)
    
    with col1:
        config_name = st.text_input(
            "Configuration Name",
            placeholder="e.g., 'Standard Loads', 'LTL Shipments'",
            key="new_config_name"
        )
        
        description = st.text_area(
            "Description (Optional)",
            placeholder="Describe this configuration...",
            key="new_config_description"
        )
    
    with col2:
        st.markdown("#### API Credentials")
        
        api_base_url = st.text_input(
            "API Base URL",
            value="https://api.prod.goaugment.com",
            key="new_config_api_url"
        )
        
        api_key = st.text_input(
            "API Key",
            type="password",
            key="new_config_api_key"
        )
    
    if config_name and api_base_url and api_key:
        # Test API connection
        if st.button("🔍 Test API Connection", key="test_new_config_api"):
            try:
                from src.backend.api_client import LoadsAPIClient
                
                # Get brokerage key for API validation
                brokerage_key = get_brokerage_key(brokerage_name)
                client = LoadsAPIClient(api_base_url, api_key=api_key, auth_type='api_key', brokerage_key=brokerage_key)
                result = client.validate_connection()
                
                if result['success']:
                    st.success("✅ API connection successful!")
                    
                    # Store configuration details for use in mapping
                    st.session_state.new_configuration = {
                        'brokerage_name': brokerage_name,
                        'configuration_name': config_name,
                        'description': description,
                        'api_credentials': {
                            'base_url': api_base_url,
                            'api_key': api_key
                        }
                    }
                    return 'new_configuration'
                else:
                    st.error(f"❌ API connection failed: {result['message']}")
            except Exception as e:
                st.error(f"❌ Connection test failed: {str(e)}")
    
    return None

def create_header_validation_interface(file_headers, db_manager, brokerage_name, configuration_name):
    """Create interface for header validation against saved configuration"""
    st.markdown("#### File Header Validation")
    
    # Get saved configuration if it exists
    saved_config = db_manager.get_brokerage_configuration(brokerage_name, configuration_name)
    
    if saved_config and saved_config.get('file_headers'):
        # Compare headers
        comparison = db_manager.compare_file_headers(saved_config['file_headers'], file_headers)
        
        if comparison['status'] == 'identical':
            # Compact success message - no separate success box
            return comparison
            
        elif comparison['status'] == 'changed':
            st.warning("⚠️ File headers have changed from saved configuration")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if comparison['missing']:
                    st.markdown("#### ❌ Missing Headers")
                    st.caption("These headers were in the saved configuration but are missing from your file:")
                    for header in comparison['missing']:
                        st.markdown(f"• `{header}`")
            
            with col2:
                if comparison['added']:
                    st.markdown("#### ➕ New Headers")
                    st.caption("These headers are new in your file:")
                    for header in comparison['added']:
                        st.markdown(f"• `{header}`")
            
            with col3:
                if comparison['common']:
                    st.markdown("#### ✅ Matching Headers")
                    st.caption(f"{len(comparison['common'])} headers match:")
                    with st.expander("View matching headers"):
                        for header in comparison['common']:
                            st.markdown(f"• `{header}`")
            
            # Configuration update options
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 Update Configuration", type="primary", key="update_config_headers"):
                    st.session_state.update_configuration_headers = True
                    st.info("💡 Configuration will be updated with new headers after mapping")
            
            with col2:
                if st.button("⚠️ Continue with Current Headers", key="continue_current_headers"):
                    st.session_state.ignore_header_changes = True
                    st.info("⚠️ Proceeding with current headers - some mappings may need adjustment")
        
        return comparison
    
    else:
        # New configuration - no comparison needed
        st.info("🆕 New configuration - file headers will be saved with the mapping")
        return {'status': 'new_config', 'changes': [], 'missing': [], 'added': file_headers}

def create_enhanced_mapping_with_validation(df, existing_configuration, data_processor, header_comparison):
    """Enhanced mapping interface with configuration validation and required-first approach"""
    # Remove duplicate header - it's already shown in the main workflow
    
    # Initialize tab state management
    if 'mapping_tab_index' not in st.session_state:
        st.session_state.mapping_tab_index = 0
    
    # Get the API schema
    api_schema = get_full_api_schema()
    
    # Initialize mappings
    if existing_configuration:
        field_mappings = existing_configuration['field_mappings'].copy()
        st.info(f"📋 Starting with saved configuration mappings ({len(field_mappings)} fields)")
    else:
        field_mappings = {}
    
    # Handle header changes
    if header_comparison and header_comparison['status'] == 'changed':
        # Remove mappings for missing headers
        for missing_header in header_comparison['missing']:
            fields_to_remove = [k for k, v in field_mappings.items() if v == missing_header]
            for field in fields_to_remove:
                del field_mappings[field]
        
        if header_comparison['missing']:
            st.warning(f"⚠️ Removed {len(header_comparison['missing'])} mappings for missing headers")
    
    # Generate smart mappings for new fields
    if not field_mappings or (header_comparison and header_comparison.get('added')):
        with st.spinner("🧠 Generating smart mapping suggestions..."):
            try:
                suggested_mappings = data_processor.suggest_mapping(list(df.columns), api_schema, df)
                
                # Only add suggestions that don't conflict with existing mappings
                for field, column in suggested_mappings.items():
                    if field not in field_mappings:
                        field_mappings[field] = column
                
                if suggested_mappings:
                    st.success(f"✨ Generated {len(suggested_mappings)} smart mapping suggestions!")
            except Exception as e:
                st.warning(f"⚠️ Could not generate smart mappings: {str(e)}")
    
    # Get dynamic requirements based on current mappings
    required_fields = get_dynamic_field_requirements(api_schema, field_mappings)
    optional_fields = {k: v for k, v in api_schema.items() if k not in required_fields}
    
    # Enhanced progress tracking
    total_required = len(required_fields)
    mapped_required = len([f for f in required_fields.keys() if f in field_mappings])
    progress = mapped_required / total_required if total_required > 0 else 1
    
    # Enhanced progress indicator with better visual design
    progress_color = '#10b981' if progress == 1 else '#3b82f6'
    st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); 
            padding: 1.25rem; 
            border-radius: 0.75rem; 
            border: 1px solid #e2e8f0; 
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                <div style="font-weight: 600; color: #1e293b; font-size: 1rem;">
                    📋 Required Fields Progress
                </div>
                <div style="
                    background: {progress_color}; 
                    color: white; 
                    padding: 0.25rem 0.75rem; 
                    border-radius: 1rem; 
                    font-size: 0.8rem; 
                    font-weight: 600;
                ">
                    {mapped_required}/{total_required}
                </div>
            </div>
            <div style="background: #e2e8f0; height: 8px; border-radius: 4px; overflow: hidden;">
                <div style="
                    background: {progress_color}; 
                    height: 100%; 
                    width: {progress*100}%; 
                    border-radius: 4px; 
                    transition: all 0.3s ease;
                    box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
                "></div>
            </div>
            {f'<div style="margin-top: 0.75rem; color: #10b981; font-size: 0.9rem; font-weight: 500;">✅ All required fields mapped! Ready to proceed.</div>' if progress == 1 else f'<div style="margin-top: 0.75rem; color: #64748b; font-size: 0.9rem;">🔄 {total_required - mapped_required} more required field{"s" if total_required - mapped_required > 1 else ""} to map</div>'}
        </div>
    """, unsafe_allow_html=True)
    
    # Custom tab interface with persistent state
    total_optional = len(optional_fields)
    mapped_optional = len([f for f in optional_fields.keys() if f in field_mappings])
    
    # Create custom tab buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(
            f"⭐ Required Fields ({mapped_required}/{total_required})",
            type="primary" if st.session_state.mapping_tab_index == 0 else "secondary",
            use_container_width=True,
            key="required_tab_btn"
        ):
            st.session_state.mapping_tab_index = 0
    
    with col2:
        if st.button(
            f"📄 Optional Fields ({mapped_optional}/{total_optional})",
            type="primary" if st.session_state.mapping_tab_index == 1 else "secondary",
            use_container_width=True,
            key="optional_tab_btn"
        ):
            st.session_state.mapping_tab_index = 1
    
    # Add some spacing
    st.markdown("---")
    
    updated_mappings = field_mappings.copy()
    
    # Show content based on selected tab
    if st.session_state.mapping_tab_index == 0:
        # Required Fields Tab
        st.markdown("### ⭐ Required Fields (Must be mapped)")
        st.caption("These fields are required by the API and must be mapped before you can proceed.")
        
        if not required_fields:
            st.info("No required fields found in the API schema.")
        else:
            for field, field_info in required_fields.items():
                create_enhanced_field_mapping_row(field, field_info, df, updated_mappings, required=True, header_comparison=header_comparison)
    
    else:
        # Optional Fields Tab
        st.markdown("### 📄 Optional Fields (Enhance your data)")
        
        # Progressive disclosure - show summary first
        if mapped_optional == 0:
            st.info(f"💡 {total_optional} optional fields available to enhance your data")
        else:
            st.success(f"✨ {mapped_optional}/{total_optional} optional fields mapped")
        
        # Smart categorization with progressive disclosure
        processed_fields = set()
        categories = {
            "💰 Pricing & Bids": [],
            "📦 Load Information": [],
            "📍 Location Details": [],
            "👥 Contacts & Carriers": [],
            "📋 Other Fields": []
        }
        
        # Categorize fields (priority order) - Enhanced keyword patterns to catch all new fields
        for field in optional_fields.keys():
            if field in processed_fields:
                continue
            if ('bid' in field.lower() or 'cost' in field.lower() or 'rate' in field.lower() or 
                'pricing' in field.lower() or 'target' in field.lower() or 'max' in field.lower() or
                'bidcriteria' in field.lower() or 'dimensions' in field.lower() or 'flexattributes' in field.lower()):
                categories["💰 Pricing & Bids"].append(field)
            elif ('items' in field or 'equipment' in field or 'weight' in field or 
                  'package' in field.lower() or 'quantity' in field.lower() or 'freight' in field.lower() or
                  'nmfc' in field.lower() or 'density' in field.lower() or 'sequence' in field.lower() or
                  'reference' in field.lower() or 'tracking' in field.lower()):
                categories["📦 Load Information"].append(field)
            elif ('address' in field or 'route' in field or 'location' in field.lower() or 
                  'street' in field.lower() or 'city' in field.lower() or 'state' in field.lower() or
                  'postal' in field.lower() or 'country' in field.lower() or 'arrival' in field.lower() or
                  'completion' in field.lower() or 'latitude' in field.lower() or 'longitude' in field.lower()):
                categories["📍 Location Details"].append(field)
            elif ('contact' in field or 'carrier' in field or 'driver' in field or 
                  'brokerage' in field or 'customer' in field or 'phone' in field.lower() or
                  'email' in field.lower() or 'role' in field.lower() or 'name' in field.lower() or
                  'dot' in field.lower() or 'mc' in field.lower() or 'scac' in field.lower()):
                categories["👥 Contacts & Carriers"].append(field)
            else:
                categories["📋 Other Fields"].append(field)
            processed_fields.add(field)
        
        # Render categories with smart defaults
        for category_name, category_fields in categories.items():
            if category_fields:
                mapped_in_category = len([f for f in category_fields if f in updated_mappings])
                # Auto-expand if fields are mapped, otherwise collapsed for cleaner UI
                expand_default = mapped_in_category > 0 or len(category_fields) <= 3
                
                with st.expander(f"{category_name} ({mapped_in_category}/{len(category_fields)})", expanded=expand_default):
                    for field in category_fields:
                        if field in optional_fields:
                            create_enhanced_field_mapping_row(field, optional_fields[field], df, updated_mappings, required=False, header_comparison=header_comparison)
    
    # Enhanced sticky action bar with better visual design
    st.markdown("---")
    
    # Create a prominent action bar with better styling
    st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid #e2e8f0;
            border-radius: 0.75rem;
            padding: 1.25rem;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        ">
            <div style="
                font-weight: 600; 
                color: #1e293b; 
                font-size: 1rem; 
                margin-bottom: 0.75rem;
                text-align: center;
            ">
                🎯 Mapping Actions
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Show contextual actions based on current state
    if mapped_required < total_required:
        # Focus on completing required mappings
        st.markdown("**Complete Required Fields First**")
        col1, col2 = st.columns([3, 2])
        with col1:
            if st.button("✅ Apply Current Mappings", type="primary", use_container_width=True, key="enhanced_apply_partial_v2"):
                st.session_state.field_mappings = updated_mappings
                mapped_required_after = len([f for f in required_fields.keys() if f in updated_mappings])
                st.success(f"Applied {len(updated_mappings)} mappings! ({mapped_required_after}/{total_required} required fields mapped)")
                # Don't rerun - just update the state and let the interface update naturally
        with col2:
            if st.button("🧠 Auto-Map Remaining", use_container_width=True, key="enhanced_auto_map_v2"):
                with st.spinner("🔄 Generating fresh mapping suggestions..."):
                    try:
                        fresh_mappings = data_processor.suggest_mapping(list(df.columns), api_schema, df)
                        st.session_state.field_mappings = fresh_mappings
                        st.success("Generated fresh automatic mappings!")
                        # Don't rerun - just update the state and let the interface update naturally
                    except Exception as e:
                        st.error(f"Failed to generate mappings: {str(e)}")
        
        # Secondary actions in a cleaner layout
        st.markdown("**Additional Options**")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Reset All Mappings", use_container_width=True, key="enhanced_reset_all_v2"):
                st.session_state.field_mappings = {}
                st.info("Reset all mappings")
                # Don't rerun - just update the state and let the interface update naturally
        with col2:
            if st.button("💾 Save Progress", use_container_width=True, key="save_partial_config_btn"):
                st.warning(f"⚠️ Please map all {total_required} required fields before saving")
    else:
        # Required mappings complete - show prominent completion actions
        st.success("🎉 **All Required Fields Mapped!** Ready to proceed.")
        col1, col2 = st.columns([3, 2])
        with col1:
            if st.button("✅ Apply All Mappings", type="primary", use_container_width=True, key="enhanced_apply_complete_v2"):
                st.session_state.field_mappings = updated_mappings
                st.success(f"Applied {len(updated_mappings)} mappings! All required fields mapped ✅")
                # Don't rerun - just update the state and let the interface update naturally
        with col2:
            if st.button("💾 Save & Continue", type="primary", use_container_width=True, key="save_complete_config_btn"):
                st.session_state.ready_to_save_config = True
                st.success("✅ Ready to proceed!")
    
    return updated_mappings

def create_enhanced_field_mapping_row(field: str, field_info: dict, df, updated_mappings: dict, required: bool = False, header_comparison=None):
    """Enhanced field mapping row with change indicators"""
    # Generate a unique key suffix to prevent duplicates
    field_hash = abs(hash(field)) % 10000
    key_suffix = f"{field_hash}"
    
    # Two-column layout for cleaner design
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Enhanced field card with better visual design
        required_indicator = "⭐" if required else "📄"
        color = "#dc2626" if required else "#64748b"
        
        # Check if this field's mapping might be affected by header changes
        current_mapping = updated_mappings.get(field)
        change_indicator_text = ""
        
        if header_comparison and current_mapping:
            if current_mapping in header_comparison.get('missing', []):
                change_indicator_text = " ⚠️ Header missing"
            elif current_mapping in header_comparison.get('added', []):
                change_indicator_text = " ✨ New header"
        
        # Compact field description with minimal visual noise
        description = field_info.get('description', field)
        if len(description) > 50:
            description = description[:47] + "..."
        
        required_text = " (Required)" if required else ""
        
        # Build enum options text safely
        enum_text = ""
        if field_info.get('enum'):
            enum_options = field_info['enum'][:3]
            enum_text = f' • Options: {", ".join(str(opt) for opt in enum_options)}{"..." if len(field_info["enum"]) > 3 else ""}'
        
        # Enhanced field card design with subtle background and better spacing
        background_style = 'rgba(239, 68, 68, 0.05)' if required else 'rgba(248, 250, 252, 1)'
        border_color = '#dc2626' if required else '#cbd5e1'
        
        st.markdown(f"""
            <div style="
                padding: 0.75rem; 
                background: {background_style}; 
                border-radius: 0.5rem; 
                border: 1px solid {border_color}; 
                margin-bottom: 0.5rem;
                transition: all 0.2s ease;
            ">
                <div style="font-weight: 500; color: {color}; font-size: 0.95rem; margin-bottom: 0.25rem;">
                    {required_indicator} {description}{required_text}{change_indicator_text}
                </div>
                <div style="font-size: 0.75rem; color: #64748b; margin-bottom: 0.25rem;">
                    <code style="font-size: 0.7rem; background: rgba(0,0,0,0.05); padding: 0.1rem 0.3rem; border-radius: 0.2rem;">{field}</code>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Display enum options separately to avoid HTML rendering issues
        if enum_text:
            st.caption(enum_text)
    
    with col2:
        # Enhanced mapping controls with integrated manual value option
        st.markdown("**Mapping Options**")
        
        current_mapping = updated_mappings.get(field, None)
        column_options = ["None"] + list(df.columns) + ["📝 Manual Value"]
        
        # Highlight problematic mappings
        if header_comparison and current_mapping in header_comparison.get('missing', []):
            st.warning(f"⚠️ '{current_mapping}' header is missing from file")
        
        # Determine default selection
        if current_mapping and current_mapping.startswith('MANUAL_VALUE:'):
            default_index = len(column_options) - 1  # Manual Value option
        elif current_mapping and current_mapping in column_options:
            default_index = column_options.index(current_mapping)
        else:
            default_index = 0
        
        selected_option = st.selectbox(
            "Map to CSV column or enter manual value",
            options=column_options,
            index=default_index,
            key=f"enhanced_mapping_v2_{field}_{key_suffix}",
            label_visibility="collapsed"
        )
        
        # Handle different mapping options
        if selected_option == "📝 Manual Value":
            manual_value = st.text_input(
                "Enter manual value",
                value=current_mapping.replace('MANUAL_VALUE:', '') if current_mapping and current_mapping.startswith('MANUAL_VALUE:') else '',
                key=f"enhanced_manual_input_v2_{field}_{key_suffix}",
                placeholder="Enter value..."
            )
            if manual_value:
                updated_mappings[field] = f"MANUAL_VALUE:{manual_value}"
                st.success(f"✏️ Manual: {manual_value}")
            elif field in updated_mappings:
                del updated_mappings[field]
        elif selected_option != "None":
            updated_mappings[field] = selected_option
            # Show enhanced sample data preview
            if selected_option in df.columns:
                sample_data = df[selected_option].dropna().head(3).tolist()
                if sample_data:
                    sample_text = ', '.join(str(x)[:12] + ('...' if len(str(x)) > 12 else '') for x in sample_data)
                    st.caption(f"📋 **Sample:** {sample_text}")
        else:
            # Remove mapping if "None" is selected
            if field in updated_mappings:
                del updated_mappings[field] 

# =============================================================================
# Learning-Enhanced Mapping Interface
# =============================================================================

def create_learning_enhanced_mapping_interface(df, existing_mappings, data_processor, 
                                             db_manager=None, brokerage_name=None, 
                                             configuration_name=None):
    """Create an enhanced mapping interface with learning system integration"""
    st.subheader("🧠 Smart Field Mapping with Learning")
    
    # Clear rendering guard at the start of each render cycle
    if 'field_rendering_guard' in st.session_state:
        st.session_state.field_rendering_guard.clear()
    
    # Clear global widget keys to prevent stale key collisions
    if 'global_widget_keys' in st.session_state:
        st.session_state.global_widget_keys.clear()
    
    # Get the API schema
    api_schema = get_full_api_schema()
    
    # FIXED: Single source of truth - database first approach
    field_mappings = {}
    
    # Enhanced restoration logic to preserve all mapped fields
    authoritative_mappings = existing_mappings.copy() if existing_mappings else {}
    session_mappings = st.session_state.get('field_mappings', {})
    
    # Merge intelligently - database as base, session state for active changes
    final_mappings = authoritative_mappings.copy()
    if session_mappings:
        # Only update if session has valid mappings (not cleared by UI reset)
        for field, mapping in session_mappings.items():
            if mapping and mapping != 'Select column...':
                final_mappings[field] = mapping
    
    # Ensure session state has complete mapping set (preserves optional fields)
    field_mappings = final_mappings
    st.session_state.field_mappings = final_mappings.copy()
    st.session_state.mapping_source = 'synchronized'
    
    # Enhanced configuration display with enum information
    if existing_mappings:
        show_enhanced_configuration_summary(existing_mappings, api_schema)
    
    # Generate smart suggestions with learning enhancement
    suggested_mappings = {}
    if not field_mappings:  # Only generate suggestions if no mappings exist
        with st.spinner("🧠 Generating smart mapping suggestions..."):
            try:
                if db_manager and brokerage_name:
                    # Use learning-enhanced suggestions
                    suggested_mappings = data_processor.suggest_mapping_with_learning(
                        list(df.columns), api_schema, df, db_manager, brokerage_name
                    )
                    
                    # Show learning insights
                    insights = data_processor.get_learning_insights(brokerage_name, db_manager)
                    if insights.get('total_sessions', 0) > 0:
                        st.info(f"📊 Learning from {insights['total_sessions']} previous sessions "
                               f"(avg {insights['avg_acceptance_rate']:.1f} suggestions accepted)")
                else:
                    # Fallback to basic suggestions
                    suggested_mappings = data_processor.suggest_mapping(list(df.columns), api_schema, df)
                
                if suggested_mappings:
                    st.success(f"✨ Generated {len(suggested_mappings)} smart mapping suggestions!")
                    field_mappings.update(suggested_mappings)
                else:
                    st.info("💡 No automatic suggestions found. Please map fields manually below.")
            except Exception as e:
                st.warning(f"⚠️ Could not generate smart mappings: {str(e)}")
    
    # Store original suggested mappings for learning tracking
    if 'suggested_mappings' not in st.session_state:
        st.session_state.suggested_mappings = suggested_mappings.copy()
    
    # Show learning recommendations if available
    if db_manager and brokerage_name:
        suggestions = data_processor.suggest_field_improvements(brokerage_name, db_manager)
        if suggestions:
            with st.expander("🎯 Learning Recommendations", expanded=False):
                for suggestion in suggestions[:3]:  # Show top 3
                    st.warning(f"💡 {suggestion['suggestion']}")
    
    # Get dynamic requirements based on current mappings
    current_mappings = st.session_state.get('field_mappings', {})
    required_fields = get_dynamic_field_requirements(api_schema, current_mappings)
    optional_fields = {k: v for k, v in api_schema.items() if k not in required_fields}
    
    # Progress tracking - use current session state if available
    total_required = len(required_fields)
    current_mappings = st.session_state.get('field_mappings', field_mappings)
    mapped_required = len([f for f in required_fields.keys() if f in current_mappings])
    
    if total_required > 0:
        progress = mapped_required / total_required
        st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; border: 1px solid #e2e8f0;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <strong>Required Fields Progress</strong>
                    <span style="color: #2563eb;">{mapped_required}/{total_required} completed</span>
                </div>
                <div style="background: #e2e8f0; height: 8px; border-radius: 4px;">
                    <div style="background: #2563eb; height: 100%; width: {progress*100}%; border-radius: 4px; transition: width 0.3s;"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Initialize mapping tab state
    if 'mapping_tab_index' not in st.session_state:
        st.session_state.mapping_tab_index = 0
    
    # Create custom tab interface
    tab_names = ["⭐ Required Fields", "📄 Optional Fields"]
    
    # Custom tab buttons
    tab_cols = st.columns(len(tab_names))
    for i, tab_name in enumerate(tab_names):
        with tab_cols[i]:
            # Use stable key for tab buttons
            if st.button(tab_name, key=f"learning_tab_{i}_{brokerage_name or 'default'}_stable", 
                        type="primary" if st.session_state.mapping_tab_index == i else "secondary",
                        use_container_width=True):
                st.session_state.mapping_tab_index = i
                # Allow explicit user tab clicks to expand the mapping section
                # Only prevent expansion during active processing (not after validation)
                is_processing_active = st.session_state.get('processing_in_progress', False)
                processing_completed = st.session_state.get('processing_completed', False)
                
                # Allow expansion for explicit user interactions unless actively processing
                if not is_processing_active and not processing_completed:
                    st.session_state.mapping_section_expanded = True
    
    # Tab content - use session state as the authoritative source for user changes
    # Don't overwrite session state if it already has user changes
    # Only initialize session state if it's empty or doesn't exist
    if not st.session_state.get('field_mappings'):
        st.session_state.field_mappings = field_mappings.copy()
    else:
        # Merge any new database mappings with existing session state (preserving user changes)
        for field, mapping in field_mappings.items():
            if field not in st.session_state.field_mappings:
                st.session_state.field_mappings[field] = mapping
    
    # Use session state as the working set to ensure user changes persist
    updated_mappings = st.session_state.field_mappings.copy()
    
    if st.session_state.mapping_tab_index == 0:
        # Required Fields Tab
        st.markdown("### ⭐ Required Fields (Must be mapped)")
        if not required_fields:
            st.info("No required fields found in the API schema.")
        else:
            for field, field_info in required_fields.items():
                create_learning_enhanced_field_mapping_row(
                    field, field_info, df, updated_mappings, 
                    required=True, db_manager=db_manager, 
                    brokerage_name=brokerage_name
                )
    
    elif st.session_state.mapping_tab_index == 1:
        # Optional Fields Tab
        st.markdown("### 📄 Optional Fields (Enhance your data)")
        
        # Group optional fields by category with priority-based assignment to prevent duplicates
        processed_fields = set()
        categories = {
            "💰 Pricing & Bids": [],
            "📦 Load Information": [],
            "📍 Location Details": [],
            "👥 Contacts & Carriers": [],
            "📋 Other Fields": []
        }
        
        # Categorize fields with priority order to prevent duplicates
        for field in optional_fields.keys():
            if field in processed_fields:
                continue
            # Priority order: Pricing & Bids > Load Information > Location > Contacts > Other
            # Enhanced keyword patterns to catch all new fields
            if ('bid' in field.lower() or 'cost' in field.lower() or 'rate' in field.lower() or 
                'pricing' in field.lower() or 'target' in field.lower() or 'max' in field.lower() or
                'bidcriteria' in field.lower() or 'dimensions' in field.lower() or 'flexattributes' in field.lower()):
                categories["💰 Pricing & Bids"].append(field)
            elif ('items' in field or 'equipment' in field or 'weight' in field or 
                  'package' in field.lower() or 'quantity' in field.lower() or 'freight' in field.lower() or
                  'nmfc' in field.lower() or 'density' in field.lower() or 'sequence' in field.lower() or
                  'reference' in field.lower() or 'tracking' in field.lower()):
                categories["📦 Load Information"].append(field)
            elif ('address' in field or 'route' in field or 'location' in field.lower() or 
                  'street' in field.lower() or 'city' in field.lower() or 'state' in field.lower() or
                  'postal' in field.lower() or 'country' in field.lower() or 'arrival' in field.lower() or
                  'completion' in field.lower() or 'latitude' in field.lower() or 'longitude' in field.lower()):
                categories["📍 Location Details"].append(field)
            elif ('contact' in field or 'carrier' in field or 'driver' in field or 
                  'brokerage' in field or 'customer' in field or 'phone' in field.lower() or
                  'email' in field.lower() or 'role' in field.lower() or 'name' in field.lower() or
                  'dot' in field.lower() or 'mc' in field.lower() or 'scac' in field.lower()):
                categories["👥 Contacts & Carriers"].append(field)
            else:
                categories["📋 Other Fields"].append(field)
            processed_fields.add(field)
        
        for category_name, category_fields in categories.items():
            if category_fields:
                with st.expander(f"{category_name} ({len(category_fields)} fields)", expanded=False):
                    for field in category_fields:
                        if field in optional_fields:
                            create_learning_enhanced_field_mapping_row(
                                field, optional_fields[field], df, updated_mappings,
                                required=False, db_manager=db_manager,
                                brokerage_name=brokerage_name
                            )
    
    # Action buttons
    st.markdown("---")
    st.markdown("### Mapping Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("✅ Apply All Mappings", type="primary", use_container_width=True, 
                    key="learning_apply_mappings"):
            
            # Track mapping interaction for learning
            if db_manager and brokerage_name:
                session_id = st.session_state.get('session_id', 'unknown')
                try:
                    # Use current session state for tracking since field rows update it directly
                    current_mappings = st.session_state.get('field_mappings', updated_mappings)
                    tracking_result = data_processor.track_mapping_interaction(
                        session_id, brokerage_name, configuration_name or '',
                        list(df.columns), st.session_state.suggested_mappings,
                        current_mappings, df, db_manager
                    )
                    
                    if tracking_result:
                        st.session_state.learning_interaction_id = tracking_result.get('interaction_id')
                        logger.info(f"Tracked mapping interaction: {tracking_result}")
                        
                except Exception as e:
                    logger.error(f"Failed to track mapping interaction: {e}")
            
            # updated_mappings is already in sync with session state via field row updates
            current_mappings = st.session_state.get('field_mappings', updated_mappings)
            st.session_state.field_mappings = current_mappings
            mapped_required_after = len([f for f in required_fields.keys() if f in current_mappings])
            st.success(f"Applied {len(current_mappings)} mappings! ({mapped_required_after}/{total_required} required fields mapped)")
            
            if mapped_required_after == total_required:
                st.session_state.current_step = max(st.session_state.get('current_step', 1), 5)
    
    with col2:
        if st.button("🧠 Refresh Suggestions", use_container_width=True, 
                    key="learning_refresh_suggestions"):
            with st.spinner("🔄 Generating fresh mapping suggestions..."):
                try:
                    if db_manager and brokerage_name:
                        fresh_mappings = data_processor.suggest_mapping_with_learning(
                            list(df.columns), api_schema, df, db_manager, brokerage_name
                        )
                    else:
                        fresh_mappings = data_processor.suggest_mapping(list(df.columns), api_schema, df)
                    
                    st.session_state.suggested_mappings = fresh_mappings.copy()
                    st.session_state.field_mappings = fresh_mappings
                    st.success("Generated fresh automatic mappings!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to generate mappings: {str(e)}")
    
    with col3:
        if st.button("🗑️ Clear All", use_container_width=True, 
                    key="learning_clear_mappings"):
            st.session_state.field_mappings = {}
            st.session_state.suggested_mappings = {}
            st.info("Cleared all mappings")
            st.rerun()
    
    with col4:
        if st.button("💾 Save & Continue", type="secondary", use_container_width=True, 
                    key="learning_save_continue"):
            
            # Track mapping interaction for learning
            if db_manager and brokerage_name:
                session_id = st.session_state.get('session_id', 'unknown')
                try:
                    # Use current session state for tracking since field rows update it directly
                    current_mappings = st.session_state.get('field_mappings', updated_mappings)
                    tracking_result = data_processor.track_mapping_interaction(
                        session_id, brokerage_name, configuration_name or '',
                        list(df.columns), st.session_state.suggested_mappings,
                        current_mappings, df, db_manager
                    )
                    
                    if tracking_result:
                        st.session_state.learning_interaction_id = tracking_result.get('interaction_id')
                        
                except Exception as e:
                    logger.error(f"Failed to track mapping interaction: {e}")
            
            # updated_mappings is already in sync with session state via field row updates
            current_mappings = st.session_state.get('field_mappings', updated_mappings)
            st.session_state.field_mappings = current_mappings
            mapped_required_after = len([f for f in required_fields.keys() if f in current_mappings])
            
            if mapped_required_after == total_required:
                st.session_state.current_step = max(st.session_state.get('current_step', 1), 5)
                st.success("✅ Mappings saved! Moving to validation step...")
                st.rerun()
            else:
                st.warning(f"⚠️ Please map all {total_required} required fields before continuing. "
                          f"Currently mapped: {mapped_required_after}")
    
    # Return the current session state since field rows update it directly
    return st.session_state.get('field_mappings', updated_mappings)

def create_learning_enhanced_field_mapping_row(field: str, field_info: dict, df, 
                                             updated_mappings: dict, required: bool = False,
                                             db_manager=None, brokerage_name=None):
    """Create a field mapping row with learning indicators and robust key management"""
    
    # Initialize global key registries for comprehensive collision detection
    if 'global_widget_keys' not in st.session_state:
        st.session_state.global_widget_keys = set()
    
    if 'field_rendering_guard' not in st.session_state:
        st.session_state.field_rendering_guard = set()
    
    # Create a unique field identifier to prevent duplicate rendering
    field_render_id = f"{field}_{required}_{st.session_state.get('mapping_tab_index', 0)}"
    
    # Guard against duplicate rendering in the same cycle
    if field_render_id in st.session_state.field_rendering_guard:
        st.error(f"🔴 Duplicate field rendering detected: {field}")
        st.error(f"🔍 Debug info - Field ID: {field_render_id}, Tab: {st.session_state.get('mapping_tab_index', 0)}, Required: {required}")
        st.error(f"🔍 Current guard contents: {sorted(list(st.session_state.field_rendering_guard))}")
        return
    
    st.session_state.field_rendering_guard.add(field_render_id)
    
    # Create absolutely unique keys with comprehensive collision detection
    def generate_unique_key(base_name: str, field_context: str) -> str:
        """Generate a guaranteed unique key with collision detection"""
        # Base key components
        sanitized_field = re.sub(r'[^a-zA-Z0-9]', '_', field)
        sanitized_brokerage = re.sub(r'[^a-zA-Z0-9]', '', brokerage_name or 'default')
        tab_index = st.session_state.get('mapping_tab_index', 0)
        
        # Generate base key with multiple uniqueness factors
        base_key = f"{base_name}_{sanitized_field}_{required}_{tab_index}_{sanitized_brokerage}_{field_context}"
        
        # Check for collisions and add suffix if needed
        counter = 0
        unique_key = base_key
        while unique_key in st.session_state.global_widget_keys:
            counter += 1
            unique_key = f"{base_key}_{counter}"
            
            # Safety check to prevent infinite loops
            if counter > 100:
                st.error(f"🔴 Key generation failure for field: {field}")
                unique_key = f"{base_key}_{int(time.time()*1000)}"
                break
        
        # Register the key
        st.session_state.global_widget_keys.add(unique_key)
        return unique_key
    
    # Generate unique keys for all widgets
    selectbox_key = generate_unique_key("learning_mapping", "selectbox")
    manual_button_key = generate_unique_key("learning_manual", "button")
    manual_input_key = generate_unique_key("learning_manual_input", "input")
    
    col1, col2, col3 = st.columns([3, 2, 1])
    
    with col1:
        # Get learning confidence if available
        learning_confidence = None
        learning_source = None
        
        if db_manager and brokerage_name:
            try:
                suggestions = db_manager.get_learning_suggestions(brokerage_name, field)
                if suggestions:
                    learning_confidence = suggestions[0]['confidence']
                    learning_source = suggestions[0]['source']
            except Exception:
                pass
        
        # Field description with learning indicators
        required_indicator = "⭐" if required else "📄"
        color = "#dc2626" if required else "#64748b"
        
        learning_badge = ""
        if learning_confidence and learning_confidence > 0.7:
            learning_badge = f'<div style="display: inline-block; background: #10b981; color: white; padding: 0.125rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; margin-left: 0.5rem;">🧠 {learning_confidence:.1%}</div>'
        elif learning_confidence and learning_confidence > 0.5:
            learning_badge = f'<div style="display: inline-block; background: #f59e0b; color: white; padding: 0.125rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; margin-left: 0.5rem;">🧠 {learning_confidence:.1%}</div>'
        
        # Main field display
        st.markdown(f"""
            <div style="padding: 0.5rem; background: {'rgba(239, 68, 68, 0.05)' if required else 'rgba(248, 250, 252, 1)'}; 
                        border-radius: 0.5rem; border-left: 3px solid {color};">
                <div style="font-weight: 600; color: {color};">
                    {required_indicator} {field_info.get('description', field)} {learning_badge}
                </div>
                <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.25rem;">
                    <code>{field}</code>
                </div>
                {f'<div style="font-size: 0.75rem; color: #dc2626; margin-top: 0.25rem;"><strong>Required Field</strong></div>' if required else ''}
            </div>
        """, unsafe_allow_html=True)
        
        # Display enum options separately to avoid HTML rendering issues
        if field_info.get('enum'):
            st.caption(f"**Options:** {', '.join(str(option) for option in field_info['enum'])}")
    
    with col2:
        # Column selection with learning highlights
        # Use updated_mappings as primary source (which includes both database and session state)
        current_mapping = updated_mappings.get(field, None)
        column_options = ["None"] + list(df.columns)
        
        if current_mapping and current_mapping.startswith('MANUAL_VALUE:'):
            default_index = 0
        elif current_mapping and current_mapping in column_options:
            default_index = column_options.index(current_mapping)
        else:
            default_index = 0
        
        selected_column = st.selectbox(
            "Map to CSV column",
            options=column_options,
            index=default_index,
            key=selectbox_key,
            label_visibility="collapsed"
        )
        
        # ENHANCED: Update with immediate validation and state synchronization
        if selected_column != "None":
            updated_mappings[field] = selected_column
            
            # Validate the mapping change
            mapping_valid = _validate_field_mapping(field, selected_column, df, field_info)
            if mapping_valid:
                # Update session state immediately to persist across tab switches
                if 'field_mappings' not in st.session_state:
                    st.session_state.field_mappings = updated_mappings.copy()
                else:
                    # Update only this field, preserving other mappings
                    st.session_state.field_mappings[field] = selected_column
                
                # IMMEDIATE PERSISTENCE: Auto-save to database if configuration exists
                if (st.session_state.get('selected_configuration') and 
                    db_manager and brokerage_name):
                    try:
                        _immediate_save_field_mapping(field, selected_column, db_manager, brokerage_name)
                        st.session_state.mapping_auto_saved = True
                    except Exception as e:
                        st.session_state.mapping_save_error = f"Auto-save failed: {str(e)}"
            else:
                # Revert invalid mapping
                updated_mappings[field] = None
                st.warning(f"⚠️ Invalid mapping for {field}. Please select a compatible column.")
            
            # Show sample data preview
            if selected_column in df.columns:
                sample_data = df[selected_column].dropna().head(3).tolist()
                if sample_data:
                    st.caption(f"Sample: {', '.join(str(x)[:20] for x in sample_data)}")
        elif field in updated_mappings and not updated_mappings[field].startswith('MANUAL_VALUE:'):
            # Remove from both local mappings and session state
            if field in updated_mappings:
                del updated_mappings[field]
            # Ensure session state is properly maintained
            if 'field_mappings' in st.session_state:
                if field in st.session_state.field_mappings:
                    del st.session_state.field_mappings[field]
            else:
                # If no session state, initialize with current updated_mappings
                st.session_state.field_mappings = updated_mappings.copy()
    
    with col3:
        # Enhanced manual value option with enum support
        
        # Show current manual value if exists
        current_mapping = updated_mappings.get(field, None)
        if current_mapping and current_mapping.startswith("MANUAL_VALUE:"):
            manual_val = current_mapping.replace("MANUAL_VALUE:", "")
            if field_info.get('enum'):
                st.success(f"📝 **{manual_val}**")
                st.caption("(enum value)")
            else:
                st.success(f"📝 **{manual_val}**")
        
        # Manual value button
        if st.button("✏️ Manual", key=manual_button_key, help="Set manual default value", use_container_width=True):
            st.session_state[f"show_manual_{field}"] = True
        
        # Manual value interface
        if st.session_state.get(f"show_manual_{field}", False):
            with st.container():
                st.markdown("---")
                
                # Use the smart manual value interface
                manual_value = create_smart_manual_value_interface(field, field_info, current_mapping)
                
                col_save, col_cancel = st.columns(2)
                with col_save:
                    if st.button("💾 Save", key=f"save_manual_{field}", use_container_width=True):
                        if manual_value:
                            # Save manual value
                            save_manual_value_immediately(field, manual_value, db_manager, brokerage_name)
                            updated_mappings[field] = f"MANUAL_VALUE:{manual_value}"
                            
                            # Update session state
                            if 'field_mappings' not in st.session_state:
                                st.session_state.field_mappings = updated_mappings.copy()
                            else:
                                st.session_state.field_mappings[field] = f"MANUAL_VALUE:{manual_value}"
                            
                            st.session_state[f"show_manual_{field}"] = False
                            st.success(f"✅ Manual value '{manual_value}' saved!")
                            st.rerun()
                        else:
                            st.warning("Please enter a value")
                
                with col_cancel:
                    if st.button("❌ Cancel", key=f"cancel_manual_{field}", use_container_width=True):
                        st.session_state[f"show_manual_{field}"] = False
                        st.rerun()

def create_learning_analytics_dashboard(db_manager, brokerage_name):
    """Create a dashboard showing learning analytics"""
    st.subheader("📊 Learning Analytics")
    
    try:
        analytics = db_manager.get_mapping_analytics(brokerage_name)
        
        if analytics['interaction_stats']['total_interactions'] == 0:
            st.info("No learning data available yet. Start mapping files to build learning patterns!")
            return
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Sessions", 
                analytics['interaction_stats']['total_interactions']
            )
        
        with col2:
            st.metric(
                "Avg Suggestions Accepted", 
                f"{analytics['interaction_stats']['avg_suggestions_accepted']:.1f}"
            )
        
        with col3:
            st.metric(
                "Avg Processing Success", 
                f"{analytics['interaction_stats']['avg_processing_success']:.1%}"
            )
        
        with col4:
            st.metric(
                "Avg Manual Corrections", 
                f"{analytics['interaction_stats']['avg_manual_corrections']:.1f}"
            )
        
        # Top patterns
        if analytics['top_patterns']:
            st.markdown("### 🎯 Top Learning Patterns")
            for pattern in analytics['top_patterns'][:5]:
                st.markdown(f"**`{pattern['api_field']}`** "
                           f"(confidence: {pattern['avg_confidence']:.1%}, "
                           f"used: {pattern['usage_count']} times)")
        
        # Learning progress over time
        if analytics['learning_progress']:
            st.markdown("### 📈 Learning Progress Over Time")
            progress_df = pd.DataFrame(analytics['learning_progress'])
            if not progress_df.empty:
                st.line_chart(progress_df.set_index('date')['acceptance_rate'])
        
    except Exception as e:
        st.error(f"Error loading learning analytics: {e}")

def update_learning_with_processing_results(session_id: str, success_rate: float, 
                                          data_processor, db_manager):
    """Update learning system with processing results"""
    if db_manager and session_id:
        try:
            data_processor.update_learning_with_processing_results(
                session_id, success_rate, db_manager
            )
            logger.info(f"Updated learning system with success rate: {success_rate:.1%}")
        except Exception as e:
            logger.error(f"Failed to update learning system: {e}")

def cleanup_learning_data_interface(db_manager, data_processor):
    """Interface for cleaning up old learning data"""
    st.subheader("🧹 Learning Data Cleanup")
    
    days_to_keep = st.slider(
        "Days of learning data to keep",
        min_value=30,
        max_value=365,
        value=90,
        step=30,
        help="Learning data older than this will be removed"
    )
    
    if st.button("Clean Up Learning Data", type="secondary"):
        with st.spinner("Cleaning up old learning data..."):
            result = data_processor.cleanup_learning_data(db_manager, days_to_keep)
            
            if result['success']:
                st.success(result['message'])
            else:
                st.error(f"Cleanup failed: {result['error']}")

def generate_sample_api_preview(df: pd.DataFrame, field_mappings: Dict[str, str], data_processor) -> Dict[str, Any]:
    """Generate a sample API preview from the first row of mapped data"""
    
    # If no mappings, return empty structure
    if not field_mappings:
        return {
            "message": "No field mappings configured yet",
            "preview": {
                "load": {},
                "customer": {},
                "brokerage": {}
            }
        }
    
    # If DataFrame is empty, return empty structure
    if df.empty:
        return {
            "message": "No data available for preview",
            "preview": {
                "load": {},
                "customer": {},
                "brokerage": {}
            }
        }
    
    try:
        # Get the first row for preview
        first_row_df = df.head(1).copy()
        
        # Apply field mappings to the first row
        mapped_df, mapping_errors = data_processor.apply_mapping(first_row_df, field_mappings)
        
        if mapping_errors:
            return {
                "message": f"Mapping errors found: {', '.join(mapping_errors)}",
                "preview": {
                    "load": {},
                    "customer": {},
                    "brokerage": {}
                }
            }
        
        # Format the mapped data for API (this will give us the proper nested structure)
        api_preview_list = data_processor.format_for_api(mapped_df)
        
        if api_preview_list:
            api_preview = api_preview_list[0]  # Get the first (and only) preview
            
            # Clean up the preview for display
            cleaned_preview = {}
            for key, value in api_preview.items():
                if value is not None and value != "" and value != {} and value != []:
                    cleaned_preview[key] = value
            
            return {
                "message": "Sample API preview generated from first row",
                "preview": cleaned_preview,
                "mapped_fields": list(field_mappings.keys()),
                "source_row": first_row_df.iloc[0].to_dict()
            }
        else:
            return {
                "message": "No valid API preview could be generated",
                "preview": {
                    "load": {},
                    "customer": {},
                    "brokerage": {}
                }
            }
            
    except Exception as e:
        return {
            "message": f"Error generating API preview: {str(e)}",
            "preview": {
                "load": {},
                "customer": {},
                "brokerage": {}
            }
        }

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
        from datetime import datetime
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
        
        # Update the session state configuration to reflect the save
        st.session_state.selected_configuration['field_mappings'] = current_mappings
        st.session_state.selected_configuration['updated_at'] = datetime.now().isoformat()
        
    except Exception as e:
        raise e