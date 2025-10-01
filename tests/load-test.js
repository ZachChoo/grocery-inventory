import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
    stages: [
        { duration: '30s', target: 10 },
        { duration: '1m', target: 50 },
        { duration: '1m', target: 100 },
        { duration: '2m', target: 100 },
        { duration: '30s', target: 0 },
        
    ],
    thresholds: {
        http_req_duration: ['p(95)<250'], // 95% of requests should be below 250ms
        http_req_failed: ['rate<0.01'],   // Error rate should be less than 1%
        errors: ['rate<0.1']
    },
};

const BASE_URL = __ENV.BASE_URL || 'http://test_api:8000';

function randomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

// Test setup - runs once per VU (virtual user)
export function setup() {
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

    // Get all products
    let res = http.get(`${BASE_URL}/products/`, { headers: headers });
    check(res, {
        'get products status is 200': (r) => r.status === 200,
        'get products response time < 300ms': (r) => r.timings.duration < 300,
    }) ? errorRate.add(0) : errorRate.add(1);

    sleep(1);

    // Create a product
    const product_upc = randomInt(100000000, 999999999)
    const productData = {
        upc: product_upc,
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
        'create product response time < 400ms': (r) => r.timings.duration < 400,
    }) ? errorRate.add(0) : errorRate.add(1);

    sleep(1);

    // Get products with pagination
    res = http.get(`${BASE_URL}/products/?page=1&size=10`, { headers: headers });
    check(res, {
        'get paginated products status is 200': (r) => r.status === 200,
        'get paginated products response time < 300ms': (r) => r.timings.duration < 300,
    }) ? errorRate.add(0) : errorRate.add(1);

    sleep(1);

    // Create a sale
    const saleData = {
        product_upc: product_upc,
        sale_price: randomInt(1, 100) + 0.99,
        sale_start: new Date().toISOString().split('T')[0],
        sale_end: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0] // 7 days from now
    };

    res = http.post(
        `${BASE_URL}/sales/`,
        JSON.stringify(saleData),
        { headers: headers }
    );

    check(res, {
        'create sale status is 200': (r) => r.status === 200,
        'create sale response time < 400ms': (r) => r.timings.duration < 400,
    }) ? errorRate.add(0) : errorRate.add(1);

    sleep(1);

    // Get all sales
    res = http.get(`${BASE_URL}/sales/`, { headers: headers });
    check(res, {
        'get sales status is 200': (r) => r.status === 200,
        'get sales response time < 300ms': (r) => r.timings.duration < 300,
    }) ? errorRate.add(0) : errorRate.add(1);

    sleep(1);

    // Get current user info
    res = http.get(`${BASE_URL}/users/me`, { headers: headers });
    check(res, {
        'get current user status is 200': (r) => r.status === 200,
        'current user matches': (r) => r.json('username') === data.username,
        'get current user response time < 300ms': (r) => r.timings.duration < 300,
    }) ? errorRate.add(0) : errorRate.add(1);

    sleep(1);
}

export function teardown(data) {
    console.log('Load test completed');
}