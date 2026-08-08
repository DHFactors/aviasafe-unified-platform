// k6 scenario: 100 concurrent users submitting voluntary safety reports.
//
// NOTE ON RATE LIMITING: /api/reports/vsr is throttled to 50/day per tenant.
// With 100 concurrent users you will (correctly) receive HTTP 429 responses
// once the limit is exhausted. This test therefore tracks two metrics:
//   - accepted_request_duration : latency of requests that were accepted (201)
//   - throttled_request_duration: latency of rate-limited requests (429)
// For a pure performance run with no throttling, disable rate limiting on the
// target backend (unset REDIS_URL / set REDIS_ENABLED=false) before running.
//
// Run:
//   k6 run -e LOADTEST_TOKEN=$LOADTEST_TOKEN load-tests/k6/report-submission.js

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';
import { BASE_URL, jsonHeaders, isAccepted, isThrottled } from './common.js';

const acceptedDuration = new Trend('accepted_request_duration');
const throttledDuration = new Trend('throttled_request_duration');

export const options = {
  scenarios: {
    reporters: {
      executor: 'constant-vus',
      vus: 100, // 100 concurrent users
      duration: '2m',
    },
  },
  thresholds: {
    accepted_request_duration: ['p(95)<500'], // success criterion for accepted submits
    http_req_duration: ['p(95)<500'], // overall responsiveness (incl. 429)
  },
};

export default function () {
  const payload = JSON.stringify({
    report_type: 'voluntary',
    is_anonymous: false,
    narrative: `Load test VSR ${__VU}-${__ITER}: crew reported go-around after unstable approach, tower visibility degraded during final phase of the sector.`,
    location: 'Kathmandu TIA',
    occurrence_date: new Date().toISOString(),
    severity_level: 3,
    probability_level: 2,
    occurrence_category: 'Airborne',
  });

  const res = http.post(`${BASE_URL}/api/reports/vsr`, payload, {
    headers: jsonHeaders(),
    tags: { scenario: 'report-submission' },
  });

  if (isAccepted(res)) acceptedDuration.add(res.timings.duration);
  if (isThrottled(res)) throttledDuration.add(res.timings.duration);

  check(res, {
    'accepted (201) or throttled (429)': (r) => isAccepted(r) || isThrottled(r),
  });

  sleep(0.5);
}
