# Root cause analysis — N4: the same sale sent twice is recorded twice

Defect: [N4](N4.md), Major / P2 (lowered from P1 after the UI evidence in N4.md). Sending the identical sale request twice records two sales (ids 122 and 123 in the latest run) and reduces stock twice. A double click, a browser retry or a client retry after a timeout charges the customer twice and makes stock wrong.

## 5 Whys

1. **Why were two sales recorded?** The server handled both POSTs as separate, valid sales. Each one created a `Sale` and reduced stock.
2. **Why could the server not tell they were the same sale?** The request has no unique identifier for the checkout, and the server does not check for duplicates.
3. **Why is there no identifier?** The API was designed as "the till sends the cart, the server does the rest". Every POST is treated as a new sale, and idempotency was never part of the design.
4. **Why was idempotency not designed in?** The point of sale was expected to be used only by the till page, where the button is assumed to be clicked once. Network retries and API clients were not considered, and no requirement covered repeated requests. A3 only came from this project's test analysis.
5. **Why was this not found before?** The tests send each request once and check that request's result. No test repeated a request or measured stock across repeated requests.

**Root cause:** the sale endpoint is not idempotent, because the design and requirements never considered repeated delivery of the same request. Tests only checked single requests.

## Fishbone (cause and effect)

```
 People                     Process                    Requirements
   │ assumed a single          │ no review of failure      │ no requirement for
   │ click from the till       │ modes (retry, timeout,    │ repeated requests
   │                           │ double submit)            │ (A3 added by testing)
   └──────────────┬────────────┴──────────────┬────────────┘
                  │                           │
                  ▼                           ▼
 ───────────────────────────────────────────────────────────►  N4: duplicate sale,
                  ▲                           ▲                 stock reduced twice
                  │                           │
   ┌──────────────┴────────────┬──────────────┴────────────┐
   │ POST always creates a     │ tests send each request   │ real networks retry;
   │ Sale; no idempotency key  │ once; no repeat or        │ browsers resubmit;
   │ or unique constraint      │ concurrency tests         │ slow responses cause
   │                           │                           │ double clicks
 Code                        Tools                      Environment
```

| Category | Cause |
| --- | --- |
| People | Designers assumed one click per sale from the till page |
| Process | No design review of failure modes (timeouts, retries, double submits); no API design guideline for non-idempotent POSTs |
| Code | `sale_create_view` and `create_sale` create a sale on every valid POST; there is no idempotency key, no unique constraint and no duplicate window check |
| Tools | Unit and API tests send each request once; nothing repeats a request or sends requests concurrently |
| Environment | Real networks, proxies and browsers can resend requests; a slow response invites a second click |
| Requirements | No requirement says what happens when a request is repeated; A3 was added during this project |

## Corrective actions (fix this defect)

1. The till generates an idempotency key (UUID) per checkout and sends it with the sale (field or `Idempotency-Key` header).
2. Store the key on `Sale` with a unique constraint. On a repeat, return the existing sale's response (200, same `sale_id`) instead of creating a new one. Do it inside the same transaction, so concurrent duplicates cannot both succeed.
3. Disable the till's "Complete sale" button until the response arrives (defence in depth, not the fix).
4. `test_repeats.py` must then pass. Add a concurrent variant that sends two requests at the same time.

## Preventive actions (stop it happening again)

1. Add "every state-changing POST is idempotent or protected against duplicates" to the API design checklist and the requirements template.
2. Keep repeated-request and concurrent-request tests in the API suite for every state-changing endpoint, including void (already protected by its state check).
3. Review failure modes (retry, timeout, double submit) in design reviews for every workflow that changes shared records such as `Item.quantity`.
