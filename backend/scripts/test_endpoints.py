#!/usr/bin/env python3
"""
Endpoint Testing Script for Clover Calculator API
Run this script to verify all 14 new endpoints are working correctly.

Usage:
    python test_endpoints.py
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")

def print_section(message):
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"{message}")
    print(f"{'='*60}{Colors.RESET}\n")

# Test results tracker
results = {
    'passed': 0,
    'failed': 0,
    'errors': []
}

def test_endpoint(name, method, url, headers=None, data=None, expected_status=200):
    """Test an API endpoint"""
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)

        if response.status_code == expected_status:
            print_success(f"{name}: {response.status_code}")
            results['passed'] += 1
            return response.json() if response.content else None
        else:
            print_error(f"{name}: Expected {expected_status}, got {response.status_code}")
            print_error(f"   Response: {response.text[:200]}")
            results['failed'] += 1
            results['errors'].append(f"{name}: Status {response.status_code}")
            return None
    except Exception as e:
        print_error(f"{name}: {str(e)}")
        results['failed'] += 1
        results['errors'].append(f"{name}: {str(e)}")
        return None

def main():
    print_section("Clover Calculator API - Endpoint Testing")
    print_info(f"Testing against: {BASE_URL}")
    print_info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Step 1: Login
    print_section("Step 1: Authentication")
    print_info("Enter your credentials:")
    username = input("Username: ").strip() or "abhishekchoudhary"
    password = input("Password: ").strip() or "admin"

    login_data = {
        "username": username,
        "password": password
    }

    login_response = test_endpoint(
        "Login",
        "POST",
        f"{API_BASE}/auth/login/",
        data=login_data
    )

    if not login_response or 'tokens' not in login_response:
        print_error("Login failed! Cannot continue testing.")
        print_error("Make sure the server is running: python manage.py runserver")
        return

    token = login_response['tokens']['access']
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    print_success(f"Authenticated as: {username}")

    # Step 2: Get or create analysis ID
    print_section("Step 2: Get Analysis for Testing")
    analyses = test_endpoint(
        "List Analyses",
        "GET",
        f"{API_BASE}/analyses/",
        headers=headers
    )

    if analyses and analyses.get('results'):
        analysis_id = analyses['results'][0]['id']
        print_success(f"Using existing analysis ID: {analysis_id}")
    else:
        print_warning("No analyses found. Please create one via admin panel first.")
        print_info("Visit: http://localhost:8000/admin/analyses/analysis/add/")
        analysis_id = input("Enter analysis ID to use for testing: ").strip()
        if not analysis_id:
            print_error("Analysis ID required for testing!")
            return

    # Step 3: Test Device Catalog Endpoints
    print_section("Step 3: Device Catalog Endpoints")

    # GET device catalog
    devices = test_endpoint(
        "GET /catalog/devices/ (List)",
        "GET",
        f"{API_BASE}/analyses/catalog/devices/",
        headers=headers
    )

    device_id = None
    if devices and devices.get('results'):
        device_id = devices['results'][0]['id']
        print_success(f"Found device ID: {device_id}")

        # GET specific device
        test_endpoint(
            f"GET /catalog/devices/{device_id}/ (Detail)",
            "GET",
            f"{API_BASE}/analyses/catalog/devices/{device_id}/",
            headers=headers
        )

    # Step 4: Test SaaS Catalog Endpoints
    print_section("Step 4: SaaS Catalog Endpoints")

    # GET SaaS catalog
    saas_plans = test_endpoint(
        "GET /catalog/saas/ (List)",
        "GET",
        f"{API_BASE}/analyses/catalog/saas/",
        headers=headers
    )

    saas_id = None
    if saas_plans and saas_plans.get('results'):
        saas_id = saas_plans['results'][0]['id']
        print_success(f"Found SaaS plan ID: {saas_id}")

        # GET specific SaaS plan
        test_endpoint(
            f"GET /catalog/saas/{saas_id}/ (Detail)",
            "GET",
            f"{API_BASE}/analyses/catalog/saas/{saas_id}/",
            headers=headers
        )

    # Step 5: Test Merchant Hardware Endpoints
    print_section("Step 5: Merchant Hardware Endpoints")

    # CREATE hardware
    hardware_data = {
        "analysis": int(analysis_id),
        "item_type": "POS_TERMINAL",
        "item_name": "Square Terminal (Test)",
        "provider": "Square",
        "cost_type": "MONTHLY_LEASE",
        "amount": "60.00",
        "quantity": 2,
        "notes": "Test hardware created by automated script"
    }

    hardware = test_endpoint(
        "POST /hardware/ (Create)",
        "POST",
        f"{API_BASE}/analyses/hardware/",
        headers=headers,
        data=hardware_data,
        expected_status=201
    )

    if hardware and 'id' in hardware:
        hardware_id = hardware['id']
        print_success(f"Created hardware ID: {hardware_id}")

        # GET hardware list
        test_endpoint(
            "GET /hardware/ (List)",
            "GET",
            f"{API_BASE}/analyses/hardware/",
            headers=headers
        )

        # GET specific hardware
        test_endpoint(
            f"GET /hardware/{hardware_id}/ (Detail)",
            "GET",
            f"{API_BASE}/analyses/hardware/{hardware_id}/",
            headers=headers
        )

        # UPDATE hardware
        update_data = {**hardware_data, "quantity": 3}
        test_endpoint(
            f"PUT /hardware/{hardware_id}/ (Update)",
            "PUT",
            f"{API_BASE}/analyses/hardware/{hardware_id}/",
            headers=headers,
            data=update_data
        )

        # DELETE hardware
        test_endpoint(
            f"DELETE /hardware/{hardware_id}/ (Delete)",
            "DELETE",
            f"{API_BASE}/analyses/hardware/{hardware_id}/",
            headers=headers,
            expected_status=204
        )

    # Step 6: Test Pricing Model Endpoints
    print_section("Step 6: Pricing Model Endpoints")

    # CREATE pricing model
    pricing_data = {
        "analysis": int(analysis_id),
        "model_type": "COST_PLUS",
        "is_selected": True,
        "markup_percent": "0.50",
        "basis_points": 10,
        "per_transaction_fee": "0.10",
        "monthly_fee": "25.00",
        "notes": "Test pricing model"
    }

    pricing = test_endpoint(
        "POST /pricing-models/ (Create)",
        "POST",
        f"{API_BASE}/analyses/pricing-models/",
        headers=headers,
        data=pricing_data,
        expected_status=201
    )

    if pricing and 'id' in pricing:
        pricing_id = pricing['id']
        print_success(f"Created pricing model ID: {pricing_id}")

        # GET pricing models list
        test_endpoint(
            "GET /pricing-models/ (List)",
            "GET",
            f"{API_BASE}/analyses/pricing-models/",
            headers=headers
        )

        # GET specific pricing model
        test_endpoint(
            f"GET /pricing-models/{pricing_id}/ (Detail)",
            "GET",
            f"{API_BASE}/analyses/pricing-models/{pricing_id}/",
            headers=headers
        )

        # DELETE pricing model
        test_endpoint(
            f"DELETE /pricing-models/{pricing_id}/ (Delete)",
            "DELETE",
            f"{API_BASE}/analyses/pricing-models/{pricing_id}/",
            headers=headers,
            expected_status=204
        )

    # Step 7: Test Proposed Device Endpoints (if device exists)
    if device_id:
        print_section("Step 7: Proposed Device Endpoints")

        # CREATE proposed device
        proposed_device_data = {
            "analysis": int(analysis_id),
            "device": device_id,
            "quantity": 2,
            "pricing_type": "LEASE",
            "selected_price": "50.00",
            "notes": "Test proposed device"
        }

        proposed_device = test_endpoint(
            "POST /proposed-devices/ (Create)",
            "POST",
            f"{API_BASE}/analyses/proposed-devices/",
            headers=headers,
            data=proposed_device_data,
            expected_status=201
        )

        if proposed_device and 'id' in proposed_device:
            proposed_device_id = proposed_device['id']
            print_success(f"Created proposed device ID: {proposed_device_id}")

            # GET proposed devices list
            test_endpoint(
                "GET /proposed-devices/ (List)",
                "GET",
                f"{API_BASE}/analyses/proposed-devices/",
                headers=headers
            )

            # GET specific proposed device
            test_endpoint(
                f"GET /proposed-devices/{proposed_device_id}/ (Detail)",
                "GET",
                f"{API_BASE}/analyses/proposed-devices/{proposed_device_id}/",
                headers=headers
            )

            # DELETE proposed device
            test_endpoint(
                f"DELETE /proposed-devices/{proposed_device_id}/ (Delete)",
                "DELETE",
                f"{API_BASE}/analyses/proposed-devices/{proposed_device_id}/",
                headers=headers,
                expected_status=204
            )

    # Step 8: Test Proposed SaaS Endpoints (if SaaS exists)
    if saas_id:
        print_section("Step 8: Proposed SaaS Endpoints")

        # CREATE proposed SaaS
        proposed_saas_data = {
            "analysis": int(analysis_id),
            "saas_plan": saas_id,
            "quantity": 1,
            "monthly_cost": "14.95",
            "notes": "Test proposed SaaS"
        }

        proposed_saas = test_endpoint(
            "POST /proposed-saas/ (Create)",
            "POST",
            f"{API_BASE}/analyses/proposed-saas/",
            headers=headers,
            data=proposed_saas_data,
            expected_status=201
        )

        if proposed_saas and 'id' in proposed_saas:
            proposed_saas_id = proposed_saas['id']
            print_success(f"Created proposed SaaS ID: {proposed_saas_id}")

            # GET proposed SaaS list
            test_endpoint(
                "GET /proposed-saas/ (List)",
                "GET",
                f"{API_BASE}/analyses/proposed-saas/",
                headers=headers
            )

            # GET specific proposed SaaS
            test_endpoint(
                f"GET /proposed-saas/{proposed_saas_id}/ (Detail)",
                "GET",
                f"{API_BASE}/analyses/proposed-saas/{proposed_saas_id}/",
                headers=headers
            )

            # DELETE proposed SaaS
            test_endpoint(
                f"DELETE /proposed-saas/{proposed_saas_id}/ (Delete)",
                "DELETE",
                f"{API_BASE}/analyses/proposed-saas/{proposed_saas_id}/",
                headers=headers,
                expected_status=204
            )

    # Step 9: Test One-Time Fee Endpoints
    print_section("Step 9: One-Time Fee Endpoints")

    # CREATE one-time fee
    fee_data = {
        "analysis": int(analysis_id),
        "fee_type": "APPLICATION",
        "fee_name": "Application Fee (Test)",
        "amount": "99.00",
        "is_optional": False,
        "notes": "Test one-time fee"
    }

    fee = test_endpoint(
        "POST /onetime-fees/ (Create)",
        "POST",
        f"{API_BASE}/analyses/onetime-fees/",
        headers=headers,
        data=fee_data,
        expected_status=201
    )

    if fee and 'id' in fee:
        fee_id = fee['id']
        print_success(f"Created one-time fee ID: {fee_id}")

        # GET fees list
        test_endpoint(
            "GET /onetime-fees/ (List)",
            "GET",
            f"{API_BASE}/analyses/onetime-fees/",
            headers=headers
        )

        # GET specific fee
        test_endpoint(
            f"GET /onetime-fees/{fee_id}/ (Detail)",
            "GET",
            f"{API_BASE}/analyses/onetime-fees/{fee_id}/",
            headers=headers
        )

        # DELETE fee
        test_endpoint(
            f"DELETE /onetime-fees/{fee_id}/ (Delete)",
            "DELETE",
            f"{API_BASE}/analyses/onetime-fees/{fee_id}/",
            headers=headers,
            expected_status=204
        )

    # Final Summary
    print_section("Test Summary")
    total_tests = results['passed'] + results['failed']
    pass_rate = (results['passed'] / total_tests * 100) if total_tests > 0 else 0

    print(f"Total Tests: {total_tests}")
    print_success(f"Passed: {results['passed']}")
    if results['failed'] > 0:
        print_error(f"Failed: {results['failed']}")
    print(f"Pass Rate: {pass_rate:.1f}%\n")

    if results['errors']:
        print_warning("Errors encountered:")
        for error in results['errors']:
            print(f"  - {error}")
        print()

    if pass_rate == 100:
        print_success("🎉 All tests passed! All 14 endpoints are working correctly.")
    elif pass_rate >= 80:
        print_warning("⚠️  Most tests passed, but some endpoints need attention.")
    else:
        print_error("❌ Multiple endpoints are failing. Please review the errors above.")

    print_info(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print_error(f"\nUnexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
