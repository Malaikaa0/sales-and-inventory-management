import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';

export const errorRate = new Rate('errors');
export const saleDuration = new Trend('sale_post_duration');

export const options = {
  stages: [
    { duration: '5s', target: 5 },
    { duration: '15s', target: 10 },
    { duration: '5s', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.02'],
    http_req_duration: ['p(95)<1500'],
    errors: ['rate<0.02'],
  },
};

function extractCsrf(html) {
  const m = html.match(/name="csrfmiddlewaretoken"\s+value="([^"]+)"/);
  return m ? m[1] : '';
}

export function setup() {
  const jar = http.cookieJar();
  const loginPage = http.get(`${BASE_URL}/accounts/login/`);
  const csrf = extractCsrf(loginPage.body);

  const loginRes = http.post(
    `${BASE_URL}/accounts/login/`,
    {
      username: 'cashier',
      password: 'demo-pass-123',
      csrfmiddlewaretoken: csrf,
    },
    {
      headers: { Referer: `${BASE_URL}/accounts/login/` },
      redirects: 0,
    }
  );
  if (loginRes.status !== 302) {
    throw new Error(`Setup login failed: status ${loginRes.status}`);
  }
  const cookies = jar.cookiesForURL(BASE_URL);
  const sessionid = cookies.sessionid ? cookies.sessionid[0] : '';

  const posPage = http.get(`${BASE_URL}/transactions/new-sale/`, {
    headers: { Cookie: `sessionid=${sessionid}` },
  });
  const posCsrf = extractCsrf(posPage.body);

  const itemsRes = http.get(`${BASE_URL}/get-items/?term=`, {
    headers: { Cookie: `sessionid=${sessionid}` },
  });
  const items = JSON.parse(itemsRes.body);
  // Pick a seeded item with high stock, or first item in stock
  items.sort((a, b) => b.stock - a.stock);
  const item = items[0];

  const custRes = http.get(`${BASE_URL}/accounts/get_customers/?term=`, {
    headers: { Cookie: `sessionid=${sessionid}` },
  });
  const customers = JSON.parse(custRes.body).results;
  const customer = customers[0];

  return {
    sessionid,
    csrftoken: posCsrf,
    itemId: item.id,
    itemPrice: Number(item.price),
    customerId: customer.id,
  };
}

export default function (data) {
  const headers = {
    Cookie: `sessionid=${data.sessionid}`,
  };

  const dash = http.get(`${BASE_URL}/`, { headers });
  const dashOk = check(dash, { 'dashboard 200': (r) => r.status === 200 });
  errorRate.add(!dashOk);

  const search = http.get(`${BASE_URL}/get-items/?term=a`, { headers });
  const searchOk = check(search, { 'item search 200': (r) => r.status === 200 });
  errorRate.add(!searchOk);

  const custSearch = http.get(`${BASE_URL}/accounts/get_customers/?term=a`, { headers });
  const custOk = check(custSearch, { 'customer search 200': (r) => r.status === 200 });
  errorRate.add(!custOk);

  // Only create sales on 1 out of 4 iterations to avoid exhausting seeded stock while testing write concurrency
  if (__ITER % 4 === 0) {
    const posRes = http.get(`${BASE_URL}/transactions/new-sale/`, { headers });
    const csrf = extractCsrf(posRes.body) || data.csrftoken;
    const payload = JSON.stringify({
      customer: data.customerId,
      items: [{ id: data.itemId, quantity: 1 }],
      tax_percentage: 0,
      amount_paid: data.itemPrice,
      redeem_points: 0,
    });
    const postRes = http.post(`${BASE_URL}/transactions/new-sale/`, payload, {
      headers: {
        Cookie: `sessionid=${data.sessionid}`,
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf,
        Referer: `${BASE_URL}/transactions/new-sale/`,
      },
    });
    saleDuration.add(postRes.timings.duration);
    const saleOk = check(postRes, {
      'sale POST 200': (r) => r.status === 200,
      'sale status success': (r) => {
        try {
          return JSON.parse(r.body).status === 'success';
        } catch (e) {
          return false;
        }
      },
    });
    errorRate.add(!saleOk);
  }

  sleep(0.2);
}
