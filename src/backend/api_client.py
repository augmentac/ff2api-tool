import requests
import json
import logging
from typing import Dict, List, Any, Optional

def get_brokerage_key(brokerage_name: str) -> str:
    """Convert brokerage name to API brokerage key"""
    # Mapping from display names to API keys
    BROKERAGE_KEY_MAPPING = {
        'schneider logistics': 'schneider-logistics-test',
        'schneider': 'schneider-logistics-test',
        'default': 'schneider-logistics-test',  # fallback
    }
    
    # Normalize the brokerage name for lookup
    normalized_name = brokerage_name.lower().strip()
    
    # Try exact match first
    if normalized_name in BROKERAGE_KEY_MAPPING:
        return BROKERAGE_KEY_MAPPING[normalized_name]
    
    # Try partial matches
    for key, value in BROKERAGE_KEY_MAPPING.items():
        if key in normalized_name or normalized_name in key:
            return value
    
    # Fallback to default or generate from name
    if 'schneider' in normalized_name.lower():
        return 'schneider-logistics-test'
    
    # Generate key from name as fallback
    return normalized_name.lower().replace(' ', '-').replace('_', '-')

class LoadsAPIClient:
    def __init__(self, base_url: str, api_key: Optional[str] = None, bearer_token: Optional[str] = None, auth_type: str = 'api_key', brokerage_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/') if base_url else "https://api.prod.goaugment.com"
        self.api_key = api_key
        self.auth_type = auth_type
        self.bearer_token = bearer_token
        self.brokerage_key = brokerage_key
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        
        # Handle different authentication types
        if self.auth_type == 'bearer_token':
            if not self.bearer_token:
                raise ValueError("Bearer token is required when auth_type is 'bearer_token'")
            # Set bearer token directly in session headers
            self.session.headers.update({
                'Authorization': f'Bearer {self.bearer_token}'
            })
        elif self.auth_type == 'api_key':
            if not self.api_key:
                raise ValueError("API key is required when auth_type is 'api_key'")
            # Use API key to refresh token (existing behavior)
            self._refresh_token()
        else:
            raise ValueError(f"Unsupported auth_type: {auth_type}. Must be 'api_key' or 'bearer_token'")
    
    def _refresh_token(self) -> Dict[str, Any]:
        """Refresh the bearer token using the API key (only for api_key auth_type)"""
        if self.auth_type != 'api_key':
            return {'success': False, 'message': 'Token refresh not available for bearer token authentication'}
        
        if not self.api_key:
            return {'success': False, 'message': 'API key not provided for token refresh'}
        
        try:
            response = requests.post(
                f"{self.base_url}/token/refresh",
                headers={'Content-Type': 'application/json'},
                json={'refreshToken': self.api_key},
                timeout=30
            )
            response.raise_for_status()
            
            try:
                token_data = response.json()
                self.bearer_token = token_data.get('accessToken')
                
                if self.bearer_token:
                    # Update session headers with new token
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.bearer_token}'
                    })
                    return {'success': True, 'message': 'Token refreshed successfully'}
                else:
                    return {'success': False, 'message': 'No access token received from refresh'}
            except json.JSONDecodeError:
                return {'success': False, 'message': f'Token refresh failed: Invalid JSON response from server. Status: {response.status_code}, Response: {response.text[:200]}'}
            except Exception as json_error:
                return {'success': False, 'message': f'Token refresh failed: JSON parsing error: {str(json_error)}'}
                
        except requests.exceptions.RequestException as e:
            error_detail = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                except (json.JSONDecodeError, ValueError) as json_error:
                    error_detail = e.response.text
                    logging.warning(f"Could not parse token refresh error response as JSON: {json_error}")
            return {'success': False, 'message': f'Token refresh failed: {error_detail}'}
        except Exception as e:
            return {'success': False, 'message': f'Token refresh error: {str(e)}'}
    
    def create_load(self, load_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a single load via API"""
        try:
            response = self.session.post(
                f"{self.base_url}/v2/loads",
                json=load_data,
                timeout=30
            )
            
            # Handle different response codes explicitly
            if response.status_code == 201:
                # Load created successfully
                try:
                    response_data = response.json()
                    # Extract load number from response
                    load_number = (response_data.get('loadNumber') or 
                                 response_data.get('load', {}).get('loadNumber') or
                                 response_data.get('id'))
                    return {
                        'success': True,
                        'data': response_data,
                        'status_code': response.status_code,
                        'load_number': load_number
                    }
                except json.JSONDecodeError:
                    return {
                        'success': True,
                        'data': {'message': 'Load created successfully (no response data)'},
                        'status_code': response.status_code,
                        'load_number': None  # Will be filled from original payload
                    }
            elif response.status_code == 200:
                # Success with response data
                try:
                    response_data = response.json()
                    # Extract load number from response
                    load_number = (response_data.get('loadNumber') or 
                                 response_data.get('load', {}).get('loadNumber') or
                                 response_data.get('id'))
                    return {
                        'success': True,
                        'data': response_data,
                        'status_code': response.status_code,
                        'load_number': load_number
                    }
                except json.JSONDecodeError:
                    return {
                        'success': True,
                        'data': {'message': 'Load processed successfully (no response data)'},
                        'status_code': response.status_code,
                        'load_number': None  # Will be filled from original payload
                    }
            elif response.status_code == 204:
                # No content but successful
                return {
                    'success': True,
                    'data': {'message': 'Load created successfully (no response data)'},
                    'status_code': response.status_code,
                    'load_number': None  # Will be filled from original payload
                }
            elif response.status_code == 400:
                # Bad request - invalid payload
                try:
                    error_details = response.json()
                    return {
                        'success': False,
                        'error': f'Bad request: {error_details}',
                        'status_code': response.status_code
                    }
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'error': f'Bad request: {response.text[:300]}',
                        'status_code': response.status_code
                    }
            elif response.status_code == 422:
                # Validation error - data format issues
                try:
                    error_details = response.json()
                    return {
                        'success': False,
                        'error': f'Validation error: {error_details}',
                        'status_code': response.status_code
                    }
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'error': f'Validation error: {response.text[:300]}',
                        'status_code': response.status_code
                    }
            elif response.status_code == 401:
                # Unauthorized - try token refresh only for API key auth
                if self.auth_type == 'api_key':
                    refresh_result = self._refresh_token()
                    if refresh_result['success']:
                        # Retry the request with new token
                        response = self.session.post(f"{self.base_url}/v2/loads", json=load_data, timeout=30)
                        if response.status_code in [200, 201, 204]:
                            try:
                                response_data = response.json()
                                # Extract load number from response
                                load_number = (response_data.get('loadNumber') or 
                                             response_data.get('load', {}).get('loadNumber') or
                                             response_data.get('id'))
                                return {
                                    'success': True,
                                    'data': response_data,
                                    'status_code': response.status_code,
                                    'load_number': load_number
                                }
                            except json.JSONDecodeError:
                                return {
                                    'success': True,
                                    'data': {'message': 'Load created successfully after token refresh'},
                                    'status_code': response.status_code,
                                    'load_number': None # Will be filled from original payload
                                }
                        else:
                            return {
                                'success': False,
                                'error': f'Authentication failed after token refresh: HTTP {response.status_code}',
                                'status_code': response.status_code
                            }
                    else:
                        return {
                            'success': False,
                            'error': f'Authentication failed: {refresh_result["message"]}',
                            'status_code': response.status_code
                        }
                else:
                    # Bearer token authentication - no refresh available
                    return {
                        'success': False,
                        'error': 'Bearer token authentication failed. Please check your bearer token.',
                        'status_code': response.status_code
                    }
            elif response.status_code == 403:
                return {
                    'success': False,
                    'error': 'Access forbidden. Check your API key permissions.',
                    'status_code': response.status_code
                }
            elif response.status_code == 404:
                return {
                    'success': False,
                    'error': 'API endpoint not found. Check the base URL.',
                    'status_code': response.status_code
                }
            elif response.status_code == 429:
                return {
                    'success': False,
                    'error': 'Rate limit exceeded. Please retry later.',
                    'status_code': response.status_code
                }
            elif response.status_code >= 500:
                return {
                    'success': False,
                    'error': f'Server error: HTTP {response.status_code}',
                    'status_code': response.status_code
                }
            else:
                # Other error codes
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text[:200]}',
                    'status_code': response.status_code
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Request timeout. Please try again.',
                'status_code': None
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Connection error. Check your network connectivity.',
                'status_code': None
            }
        except requests.exceptions.RequestException as e:
            error_detail = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                except (json.JSONDecodeError, ValueError):
                    error_detail = e.response.text
            return {
                'success': False,
                'error': error_detail,
                'status_code': getattr(e.response, 'status_code', None)
            }
        except Exception as e:
            # Catch any other unexpected errors
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'status_code': None
            }
    
    def bulk_create_loads(self, loads_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create multiple loads with detailed results"""
        results = []
        
        for i, load_data in enumerate(loads_data):
            result = self.create_load(load_data)
            result['row_index'] = i + 1
            results.append(result)
            
            # Note: Removed artificial delay - implement proper rate limiting if needed
            # import time
            # time.sleep(0.1)
        
        return results
    
    def validate_connection(self) -> Dict[str, Any]:
        """Test API connection and credentials"""
        if self.auth_type == 'bearer_token':
            # Use NEW endpoint for bearer token validation
            return self._validate_bearer_token_connection()
        else:
            # Keep EXISTING logic for API key validation
            return self._validate_api_key_connection()
    
    def _validate_bearer_token_connection(self) -> Dict[str, Any]:
        """Validate bearer token using new token endpoint with brokerageKey"""
        # Check if bearer token was provided
        if not self.bearer_token:
            return {'success': False, 'message': 'Bearer token not provided.'}
        
        # Check if brokerage key was provided
        if not self.brokerage_key:
            return {'success': False, 'message': 'Brokerage key required for bearer token validation.'}
        
        try:
            # Use new token endpoint with brokerageKey parameter
            url = f"{self.base_url}/token"
            params = {'brokerageKey': self.brokerage_key}
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    # Store access_token and expiresAt if needed for future use
                    if 'access_token' in response_data:
                        self.access_token = response_data['access_token']
                    if 'expiresAt' in response_data:
                        self.expires_at = response_data['expiresAt']
                    return {'success': True, 'message': 'Bearer token validation successful!'}
                except (json.JSONDecodeError, ValueError) as json_error:
                    logging.warning(f"Could not parse token response as JSON: {json_error}")
                    return {'success': True, 'message': 'Bearer token validation successful!'}
            elif response.status_code == 401:
                try:
                    error_data = response.json()
                    error_message = error_data.get('message', 'Invalid bearer token')
                    return {'success': False, 'message': f'Unauthorized: {error_message}'}
                except (json.JSONDecodeError, ValueError):
                    return {'success': False, 'message': 'Bearer token authentication failed. Please check your bearer token.'}
            else:
                return {'success': False, 'message': f'Unexpected response: HTTP {response.status_code}'}
                
        except Exception as e:
            logging.error(f"Bearer token validation error: {e}")
            return {'success': False, 'message': f'Connection error: {str(e)}'}
    
    def _validate_api_key_connection(self) -> Dict[str, Any]:
        """Validate API key using existing healthcheck endpoint"""
        # Check authentication setup
        if self.auth_type == 'api_key':
            # For API key auth, check if token refresh was successful
            if not self.bearer_token:
                return {'success': False, 'message': 'Token refresh failed. Please check your API key.'}
        
        try:
            # Use healthcheck endpoint to validate connection and authentication without creating data
            response = self.session.get("https://load.prod.goaugment.com/unstable/search/healthcheck", timeout=30)
            
            # Handle healthcheck response codes
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    return {'success': True, 'message': f'Connection and authentication successful! Healthcheck passed.'}
                except (json.JSONDecodeError, ValueError) as json_error:
                    logging.warning(f"Could not parse healthcheck response as JSON: {json_error}")
                    return {'success': True, 'message': 'Connection and authentication successful! Healthcheck passed.'}
            elif response.status_code == 204:
                return {'success': True, 'message': 'Connection and authentication successful! Healthcheck passed (no content).'}
            elif response.status_code == 201:
                # Unexpected for healthcheck but handle gracefully
                return {'success': True, 'message': 'Connection and authentication successful! Healthcheck passed.'}
            elif response.status_code == 401:
                # Try to refresh token once on 401 for API key auth
                refresh_result = self._refresh_token()
                if refresh_result['success']:
                    # Retry the healthcheck request with new token
                    response = self.session.get("https://load.prod.goaugment.com/unstable/search/healthcheck", timeout=30)
                    if response.status_code in [200, 201, 204]:
                        return {'success': True, 'message': 'Connection and authentication successful! (Token refreshed)'}
                    else:
                        return {'success': False, 'message': 'Authentication failed even after token refresh. Please check your API key.'}
                else:
                    return {'success': False, 'message': f'Authentication failed. Token refresh error: {refresh_result["message"]}'}
            elif response.status_code == 403:
                return {'success': False, 'message': 'Access forbidden. Check your API key permissions.'}
            elif response.status_code == 404:
                return {'success': False, 'message': 'API endpoint not found. Check the base URL.'}
            elif response.status_code == 400:
                try:
                    error_details = response.json()
                    return {
                        'success': False,
                        'message': f'Bad request: {error_details}',
                    }
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'message': f'Bad request: {response.text}',
                    }
            elif response.status_code == 422:
                try:
                    error_details = response.json()
                    return {
                        'success': False,
                        'message': f'Validation error: {error_details}',
                    }
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'message': f'Validation error: {response.text}',
                    }
            else:
                # Other error codes
                try:
                    error_details = response.json()
                    return {
                        'success': False,
                        'message': f'API error: {error_details}',
                    }
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'message': f'API error: {response.text}',
                    }
                
        except requests.exceptions.Timeout:
            return {'success': False, 'message': 'Connection timeout. Check your network connection.'}
        except requests.exceptions.SSLError:
            return {'success': False, 'message': 'SSL certificate error. Check the API URL.'}
        except requests.exceptions.ConnectionError:
            return {'success': False, 'message': 'Connection error. Check the API URL and network connectivity.'}
        except requests.exceptions.RequestException as e:
            return {'success': False, 'message': f'Request error: {str(e)}'}
        except Exception as e:
            return {'success': False, 'message': f'Unexpected error: {str(e)}'} 