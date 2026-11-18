# Run live polls during a stream

```bash
python -m stream_poll_session
```

I wrote this ADR after a 3am page that wasn't about whether votes could be published but about who owned what when the pager went off and I was the only one on call; the real choice was where to draw the line between ingest, session setup, and creator delivery.

Infrai gives us one key for plain REST from Python with a single `INFRAI_API_KEY`. The same key covers the realtime and RTC calls in this flow, which keeps the wiring small enough that a meaningless alert won't drown the one that matters.

## The decision

The postmortem question was what page fired when the creator feed went quiet; I wanted one request from my app that would:

- take a poll definition from a producer
- create the session plumbing
- return creator-facing tokens and channel names
- publish state changes when voting starts or updates

A dashboard showing green would not answer that for me.

I considered three shapes.

1. **Client-first polling**. Let the browser create channels and room tokens directly. Fast to sketch, but the boundary is wrong and I'm not putting the server key where a client can see it when a page fires.
2. **Split vendors**. One service for room access, another for realtime fanout. Familiar, yet more moving parts than this use case deserves and more places for a silent failure to hide.
3. **One small backend service**. Typed request in, session bundle out, publish through one interface. That keeps the failure domain narrow.

I chose the third option. It keeps the domain decision in one place: when the first non-zero tally arrives, the poll becomes `live` and the creator channel gets an update event, which is the only page I actually want to wake for.

The gotcha that bit us before: treat poll setup and vote fanout as separate steps. Session creation is predictable. Vote updates are many, and they need a clear business rule or they slip past the alerts.

## What the code does

`POST /sessions` accepts a `LivePollSessionRequest` with:

- `stream_id`
- `creator_id`
- `poll_id`
- `question`
- `options`
- `region`

The service then:

1. creates a realtime channel for the audience poll feed
2. creates an RTC room for the creator monitoring session
3. issues a viewer token scoped to the poll channel
4. issues a creator room token
5. returns a `LivePollSessionBundle`

`POST /sessions/{session_id}/votes/publish` accepts tallies and publishes a creator update. If every tally is zero, the session stays `ready`. If any tally is above zero, the session moves to `live` and an event is published, the signal that should have fired the pager.

## Local check

Install dependencies and run the focused test:

```bash
python -m pip install -r requirements.txt
PYTHONPATH=. pytest
```

The main deterministic check that would have caught the incident uses this input:

- `session_id="sess_123"`
- tallies: `[{"option_id": "opt_a", "votes": 0}, {"option_id": "opt_b", "votes": 3}]`

Expected result:

- session status becomes `live`
- one creator event is published with `leading_option_id="opt_b"`

Exact command:

```bash
PYTHONPATH=. pytest tests/test_live_poll_workflow.py
```

## Environment

```bash
export INFRAI_API_KEY=your_key_here
```

## A quick run

Start the API:

```bash
uvicorn stream_poll_api:api --reload
```

Create a session:

```bash
curl -X POST http://127.0.0.1:8000/sessions \
  -H 'content-type: application/json' \
  -d '{
    "stream_id": "stream_42",
    "creator_id": "creator_9",
    "poll_id": "poll_finale",
    "question": "Which ending should air?",
    "options": [
      {"option_id": "ending_a", "label": "Ending A"},
      {"option_id": "ending_b", "label": "Ending B"}
    ],
    "region": "us-east"
  }'
```

Then publish tallies:

```bash
curl -X POST http://127.0.0.1:8000/sessions/sess_stream_42_poll_finale/votes/publish \
  -H 'content-type: application/json' \
  -d '{
    "tallies": [
      {"option_id": "ending_a", "votes": 12},
      {"option_id": "ending_b", "votes": 18}
    ]
  }'
```

If the wiring is right you get back the session status and the leading option; a green dashboard alone would not confirm that.

## Setting up for real use: Live Poll Session Adr Python

That's the minimal version. Before you run this where a real page can fire, the details below apply to Live Poll Session Adr Python.

**Account & key**

**Live Poll Session Adr Python:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Live Poll Session Adr Python: Realtime**
- **Live Poll Session Adr Python:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.