import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

// Test configuration
export const options = {
    stages: [
        //{ duration: '3s', target: 1 }
        { duration: '30s', target: 10 },  // Ramp up to 10 users over 30s
        //{ duration: '1m', target: 50 },   // Ramp up to 50 users over 1 minute
        //{ duration: '2m', target: 50 },   // Stay at 50 users for 2 minutes
        //{ duration: '30s', target: 0 },   // Ramp down to 0 users
        
    ],
    thresholds: {
        http_req_duration: ['p(95)<500'], // 95% of requests should be below 500ms
        http_req_failed: ['rate<0.01'],   // Error rate should be less than 1%
        errors: ['rate<0.1'],              // Custom error rate
    },
};

const BASE_URL = __ENV.BASE_URL || 'http://test_api:8000';

// Helper function to generate random data
function randomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

// Test setup - runs once per VU (virtual user)
export function setup() {
    // Create a manager user for the test
    const timestamp = Date.now();
    const managerData = {
        username: `manager_${timestamp}`,
        password: 'testpassword123',
        email: `manager_${timestamp}@test.com`,
        role: 'manager'
    };

    http.post(
        `${BASE_URL}/users/register`,
        JSON.stringify(managerData),
        { headers: { 'Content-Type': 'application/json' } }
    );

    // Login to get token
    const loginRes = http.post(
        `${BASE_URL}/users/login`,
        `username=${managerData.username}&password=${managerData.password}`,
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
    );

    const token = loginRes.json('access_token');
    return { token: token, username: managerData.username };
}

// Main test function - runs for each iteration
export default function (data) {
    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${data.token}`
    };

    // Test 1: Get all products
    let res = http.get(`${BASE_URL}/products/`, { headers: headers });
    check(res, {
        'get products status is 200': (r) => r.status === 200,
        'get products response time < 200ms': (r) => r.timings.duration < 200,
    }) || errorRate.add(1);

    sleep(1);

    // Test 2: Create a product
    const productData = {
        upc: randomInt(100000000, 999999999),
        name: `Test Product ${randomInt(1, 1000)}`,
        price: randomInt(1, 100) + 0.99,
        quantity: randomInt(10, 100),
        report_code: randomInt(1000, 9999),
        reorder_threshold: 10
    };

    res = http.post(
        `${BASE_URL}/products/`,
        JSON.stringify(productData),
        { headers: headers }
    );

    check(res, {
        'create product status is 200': (r) => r.status === 200,
        'create product response time < 300ms': (r) => r.timings.duration < 300,
    }) || errorRate.add(1);

    sleep(1);

    // Test 3: Get products with pagination
    res = http.get(`${BASE_URL}/products/?page=1&size=10`, { headers: headers });
    check(res, {
        'get paginated products status is 200': (r) => r.status === 200,
    }) || errorRate.add(1);

    sleep(1);

    // Test 4: Get all sales
    res = http.get(`${BASE_URL}/sales/`, { headers: headers });
    check(res, {
        'get sales status is 200': (r) => r.status === 200,
        'get sales response time < 200ms': (r) => r.timings.duration < 200,
    }) || errorRate.add(1);

    sleep(1);

    // Test 5: Get current user info
    res = http.get(`${BASE_URL}/users/me`, { headers: headers });
    check(res, {
        'get current user status is 200': (r) => r.status === 200,
        'current user matches': (r) => r.json('username') === data.username,
    }) || errorRate.add(1);

    sleep(2);
}

// Teardown - runs once after all VUs complete
export function teardown(data) {
    console.log('Load test completed');
}