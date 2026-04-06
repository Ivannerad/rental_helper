 # Rental Helper Implementation Plan

  ## Summary

  Build a Python-based Telegram rental assistant composed of three services: a Telegram admin bot, a Telegram userbot worker built on Telethon, and a chatbot service connected
  through RabbitMQ. The system will support multiple Telegram accounts, bind each account to one public group, process inbound tenant conversations in Russian, and manage a four-
  stage flow: collecting needs, searching options, scheduling viewings, and upselling a similar listing.

  This plan assumes property search in v1 uses a human-managed source of listings posted in each account’s bound public Telegram group. The chatbot will not scrape external sites in
  v1; instead, it will rank and reuse listings already available from the bound group feed and escalate when matching inventory is insufficient.

  ## Key Changes

  ### Service architecture

  - Create a Python monorepo layout under src/ with three services:
      - admin_bot/ for the Telegram admin bot
      - userbot_worker/ for Telethon-based user sessions
      - chatbot_service/ for RabbitMQ consumers, conversation logic, and LLM orchestration
  - Add shared packages for domain models, queue schemas, config loading, logging, and persistence.
  - Use PostgreSQL for durable state: Telegram accounts, session status, group bindings, user conversations, extracted requirements, listing history, viewing slots, and audit logs.
  - Use RabbitMQ as the only asynchronous boundary between userbot workers and the chatbot service.

  ### Telegram admin bot

  - Implement admin-only commands to:
      - add a Telegram account and complete Telethon session authorization
      - start or stop automation per account
      - bind exactly one public group to each account
      - inspect account status, recent errors, active conversations, and viewing schedule
  - Restrict admin access through an allowlist of Telegram user IDs in configuration.
  - Persist account state changes so workers can resume safely after restart.

  ### Telegram userbot worker

  - Run one Telethon client session per managed Telegram account with supervision and reconnect handling.
  - Listen for direct user messages, normalize them into an inbound queue event, and publish to RabbitMQ with account ID, user ID, message metadata, and conversation correlation IDs.
  - Consume outbound queue events from the chatbot service and perform one of two actions:
      - send a plain text reply to the user
      - forward a message from the bound public group to the user when the chatbot requests a listing share
  - Enforce account start/stop state and reject sends for disabled accounts.

  ### Chatbot service

  - Consume inbound user messages from RabbitMQ and maintain a state machine with four explicit stages:
      - collecting: capture budget, district (center|west|east|north), room count, and missing fields
      - searching: find candidate listings from the bound group inventory, present one option at a time, and continue on rejection
      - viewing: negotiate date/time and create a pending viewing entry
      - upsell: after a viewing is accepted or completed, offer one similar option in the same area
  - Add LLM prompt orchestration in Russian with structured extraction output for requirements, intent, and next action.
  - Separate deterministic policy from LLM generation:
      - LLM extracts user intent and drafts user-facing Russian text
      - application logic decides state transitions, listing eligibility, retries, and forwarding actions
  - Define outbound queue commands such as send_text, forward_group_message, and handoff_to_human.
  - Store listing metadata from the bound group in a searchable local index keyed by group message ID, district, rooms, price, and free-text summary.
  - Add a fallback path when no suitable listing is found: apologize, record unmet demand, and mark the conversation for manual review instead of fabricating inventory.

  ### Listings and scheduling

  - Treat the bound public group as the canonical v1 listing source.
  - Add a lightweight ingestion flow that indexes relevant group posts for each account, either by backfilling recent history on startup or by indexing new posts as they appear.
  - Support viewing schedule management as appointment records attached to account, user, listing, and proposed time window.
  - Surface upcoming and pending viewings through the admin bot.

  ### Interfaces and data contracts

  - Define typed queue payloads for:
      - inbound Telegram user message event
      - outbound chatbot action event
      - optional dead-letter/error event
  - Define durable entities:
      - ManagedAccount
      - BoundGroup
      - Conversation
      - LeadRequirements
      - Listing
      - ListingOffer
      - ViewingAppointment
  - Add configuration for Telegram API credentials, admin Telegram IDs, RabbitMQ DSN, PostgreSQL DSN, LLM provider keys, and service-level concurrency.

  ### Operational and safety requirements

  - Add idempotency keys on inbound/outbound events to prevent duplicate replies during reconnects.
  - Add structured logs with correlation IDs across all three services.
  - Add dead-letter handling for malformed queue messages.
  - Add rate limiting and retry policies around Telegram sends and LLM requests.
  - Add a human-handoff flag so conversations can be paused from automation if the model is uncertain or a user asks for an agent.

  ## Test Plan

  - Unit tests for:
      - conversation state transitions across all four stages
      - requirement extraction normalization
      - listing selection and rejection loops
      - outbound action generation from policy decisions
  - Integration tests for:
      - RabbitMQ message flow between userbot and chatbot services
      - Telethon event ingestion to queue publication
      - admin bot commands for account lifecycle and group binding
      - schedule creation and retrieval
  - Manual acceptance scenarios:
      - admin adds an account, binds a group, and starts automation
      - user sends a Russian inquiry, bot collects missing criteria, offers a listing from the bound group, and forwards the original group post
      - user rejects multiple listings and receives the next best option
      - user agrees to a viewing and the appointment appears in admin schedule output
      - stopped accounts cease responding until restarted

  ## Assumptions

  - Python is the implementation language for all services.
  - Telethon is the userbot client library.
  - The admin panel is implemented as a Telegram admin bot, not a web app.
  - V1 property search uses listings from each account’s bound public Telegram group, not external listing websites.
  - Russian is the only supported user-facing language in v1.
  - One bound public group per managed account is a hard constraint in v1.
