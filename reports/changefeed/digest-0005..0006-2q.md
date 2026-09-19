# Change digest

> #5 (2026-09-09-before) → #6 (2026-09-09) · 1,072 changes · rendered 2026-09-19T12:24:04+00:00

## At a glance

62 findings — **5** breaking, **18** behavioural, **30** additive, **9** editorial — covering 493 of 1,072 changed pages. Anything not here is in the full feed report beside this file.

**If you read nothing else:**

1. MLflow tracing examples now require `mlflow[databricks]>=3.14.0` and a SQL warehouse, because the examples store traces in Unity Catalog.
2. The change data feed Requirements section now reads "Databricks Runtime 19 or above", up from "Databricks Runtime 18 LTS or above".
3. The TypeScript SDK now documents TypeScript >= 5.0 as the supported minimum, up from "TypeScript >= 4.9 is supported."
4. Pipeline unit testing now requires Databricks Runtime 18.1 or above instead of switching the pipeline channel to Preview.
5. Job performance metrics now require the "Improved Lakeflow Performance Observability" preview to be enabled for the workspace, replacing the Query performance insights access requirement.

---

## Breaking — 5

### MLflow tracing examples now require `mlflow[databricks]>=3.14.0` and a SQL warehouse, because the examples store traces in Unity Catalog.

`breaking` · version floor · 36 pages

Install lines that read `pip install --upgrade "mlflow[databricks]>=3.1"` (and `>=3.1.0`) become `>=3.14.0`; pages add "The examples on this page access traces stored in Unity Catalog. Configure a SQL warehouse before you run them" with `MLFLOW_TRACING_SQL_WAREHOUSE_ID`, import `from mlflow.entities.trace_location import UnityCatalog`, and note "The quick-start examples on this page require MLflow 3.14 or later because they store traces in Unity Catalog." label-existing-traces raises its floor from "MLflow version 3.1.0 or above" to 3.14.0, and the Claude Code integration moves CLI tracing from MLflow 3.4+ to 3.14+.

- [mlflow3/genai/tracing/integrations/](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/)
- [mlflow3/genai/tracing/integrations/anthropic](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/anthropic)
- [mlflow3/genai/tracing/integrations/openai](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/openai)
- [mlflow3/genai/tracing/integrations/openai-agent](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/openai-agent)
- [mlflow3/genai/tracing/integrations/langchain](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/langchain)
- [mlflow3/genai/tracing/integrations/langgraph](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/langgraph)
- …and 30 more

### The change data feed Requirements section now reads "Databricks Runtime 19 or above", up from "Databricks Runtime 18 LTS or above".

`breaking` · version floor · 2 pages

Only the runtime line in that Requirements block changed; the table-format requirements (managed Delta with row tracking or Iceberg v3, external Delta with row tracking) are unchanged. The Databricks Runtime 19 notes (dated September 1, 2026) announce that automatic change data feed, which computes row-level changes at query time, is generally available.

- [tables/features/change-data-feed](https://docs.databricks.com/aws/en/tables/features/change-data-feed)
- [release-notes/runtime/19](https://docs.databricks.com/aws/en/release-notes/runtime/19)

### The TypeScript SDK now documents TypeScript >= 5.0 as the supported minimum, up from "TypeScript >= 4.9 is supported."

`breaking` · version floor · 1 page

Single-line change from "TypeScript >= 4.9 is supported." to "TypeScript >= 5.0 is supported."

- [cli-sdks-libraries/sdks/typescript](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/typescript)

### Pipeline unit testing now requires Databricks Runtime 18.1 or above instead of switching the pipeline channel to Preview.

`breaking` · version floor · 1 page

New text: "Pipeline must run on Databricks Runtime 18.1 or above. Earlier runtimes do not include the unit testing module." It replaces the instruction "1. In the UI, open your pipeline and click **Settings** > **Advanced settings** > **Channel** > **Preview**".

- [ldp/unit-testing](https://docs.databricks.com/aws/en/ldp/unit-testing)

### Job performance metrics now require the "Improved Lakeflow Performance Observability" preview to be enabled for the workspace, replacing the Query performance insights access requirement.

`breaking` · preview gate · 1 page

The page previously read "- Your workspace must have access to [Query performance insights]"; it now reads "Before you can view these metrics, the **Improved Lakeflow Performance Observability** preview must be enabled for your workspace."

- [jobs/diagnose-job-performance](https://docs.databricks.com/aws/en/jobs/diagnose-job-performance)

## Behavioural — 18

### Federation-issuer, federation-rule and service-account endpoints now state a concrete requirement: an OAuth access token with the `org:admin` scope, from `ant auth login --scope org:admin` or a workload identity federation rule.

`behavioural` · auth · 32 pages

The prose replaces looser wording such as "Requires an OAuth bearer or Console session; Admin API keys are not" accepted, and per-endpoint notes about which scopes need a Console session.

- [api/admin/federation_issuers](https://platform.claude.com/docs/en/api/admin/federation_issuers)
- [api/admin/federation_issuers/create](https://platform.claude.com/docs/en/api/admin/federation_issuers/create)
- [api/admin/federation_issuers/archive](https://platform.claude.com/docs/en/api/admin/federation_issuers/archive)
- [api/admin/federation_issuers/update](https://platform.claude.com/docs/en/api/admin/federation_issuers/update)
- [api/admin/federation_issuers/list](https://platform.claude.com/docs/en/api/admin/federation_issuers/list)
- [api/admin/federation_issuers/retrieve](https://platform.claude.com/docs/en/api/admin/federation_issuers/retrieve)
- …and 26 more

### A new "preserved thinking" model: on Claude Fable 5.1 and Mythos 5.1 a replayed thinking block is only accepted if the same or a newer model produced it and nothing before it changed, and new API fields report blocks the API dropped.

`behavioural` · thinking · 15 pages

build-with-claude/preserved-thinking is a new page. release-notes/overview: "Thinking blocks produced by Claude Fable 5.1 and Claude Mythos 5.1 are preserved only for the model that produced them or a newer one". thinking-troubleshooting: "On Claude Fable 5.1, the API accepts a replayed thinking block only while the `system` prompt, `tools`, and messages that preceded it" are unchanged; the fix given is to keep history append-only. compaction: "On Claude Fable 5.1 and Claude Mythos 5.1, thinking blocks from before a `compaction` block aren't carried forward". computer-use-tool warns that removing an earlier screenshot invalidates every later thinking block. The Messages API gains `prefix_mismatch_behavior` (`BetaThinkingPrefixMismatchBehavior`) on requests and `input_transformations` (`BetaThinkingDroppedInputTransformation`) on responses, reporting the removed block's position as `messages.{i}.content.{j}`. streaming adds that with `display: "omitted"` no `thinking_delta` events are sent, under the `thinking-binding-controls-2026-08-01` beta.

- [build-with-claude/preserved-thinking](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking)
- [build-with-claude/context-windows](https://platform.claude.com/docs/en/build-with-claude/context-windows)
- [build-with-claude/thinking-troubleshooting](https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting)
- [build-with-claude/compaction](https://platform.claude.com/docs/en/build-with-claude/compaction)
- [build-with-claude/thinking](https://platform.claude.com/docs/en/build-with-claude/thinking)
- [build-with-claude/streaming](https://platform.claude.com/docs/en/build-with-claude/streaming)
- …and 9 more

### The managed-agents docs switch from piping YAML into `ant beta:<resource> create` to a declarative `ant apply <file>`, with a new page covering it.

`behavioural` · cli · 12 pages

cli-sdks-libraries/cli/apply is new: declare agents, environments, skills, memory stores and deployments as files and sync them with `ant apply`. Examples that read "ant beta:environments create < environment.yaml" and "ant beta:agents create < agent.yaml" now read `ant apply environment.yaml`. The scripting page adds `ant beta:sessions:events stream --session-id … --format jsonl` for watching a running session.

- [cli-sdks-libraries/cli/apply](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/apply)
- [managed-agents/self-hosted-sandboxes](https://platform.claude.com/docs/en/managed-agents/self-hosted-sandboxes)
- [managed-agents/environments](https://platform.claude.com/docs/en/managed-agents/environments)
- [managed-agents/quickstart](https://platform.claude.com/docs/en/managed-agents/quickstart)
- [managed-agents/agent-setup](https://platform.claude.com/docs/en/managed-agents/agent-setup)
- [managed-agents/permission-policies](https://platform.claude.com/docs/en/managed-agents/permission-policies)
- …and 6 more

### The external-key IAM role ARN field is marked deprecated, and the KMS key requirement is spelled out: on Claude Platform on AWS the key must be a single-Region key in your organization's own AWS account.

`behavioural` · deprecation · 12 pages

New field text: "IAM role ARN. Deprecated — Anthropic reaches the KMS key through its own intermediate role (or, on Claude Platform on AWS, with credent[ials])", and "Full ARN of the AWS KMS key. On Claude Platform on AWS the key must be a single-Region key in your organization's own AWS account; cross-acc[ount]" use is constrained. cmek-aws-kms adds troubleshooting for a failed attach: find the denied `kms:` event in CloudTrail in the key's account.

- [api/admin/external_keys](https://platform.claude.com/docs/en/api/admin/external_keys)
- [api/admin/external_keys/create](https://platform.claude.com/docs/en/api/admin/external_keys/create)
- [api/admin/external_keys/update](https://platform.claude.com/docs/en/api/admin/external_keys/update)
- [api/admin/external_keys/list](https://platform.claude.com/docs/en/api/admin/external_keys/list)
- [api/admin/external_keys/retrieve](https://platform.claude.com/docs/en/api/admin/external_keys/retrieve)
- [api/admin/external_keys/validate](https://platform.claude.com/docs/en/api/admin/external_keys/validate)
- …and 6 more

### ABAC GRANT policies lose their Beta label across the ABAC docs, and a new page shows using them to govern access to models and AI services in `system.ai`.

`behavioural` · ga · 8 pages

Cross-references that read "For GRANT policies (Beta), see [ABAC GRANT policies (Beta)]" now read "For GRANT policies, see [ABAC GRANT policies]", and the grant-policies page drops its "> ABAC GRANT policies are in [Beta]" admonition. The abac/performance note now excludes "GRANT policies and DENY policies (Beta)" from UDF-based evaluation.

- [data-governance/unity-catalog/abac/grant-policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/grant-policies)
- [data-governance/unity-catalog/abac/common-patterns](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/common-patterns)
- [data-governance/unity-catalog/abac/requirements](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/requirements)
- [data-governance/unity-catalog/abac/core-concepts](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/core-concepts)
- [data-governance/unity-catalog/abac/best-practices](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/best-practices)
- [data-governance/unity-catalog/abac/performance](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/performance)
- …and 2 more

### C# workload-identity examples now construct `new AnthropicClient(new ClientOptions { Credentials = credentials })` instead of `new AnthropicOidcClient(credentials)`.

`behavioural` · sdk · 7 pages

Every WIF provider page replaces the line "using var client = new AnthropicOidcClient(credentials);". The AWS, GitHub Actions and Kubernetes samples also drop the "?? throw new InvalidOperationException(\"No federation credentials found in environment\");" fallback in favour of comments naming the environment variables (ANTHROPIC_SERVICE_ACCOUNT_ID, ANTHROPIC_WORKSPACE_ID, ANTHROPIC_IDENTITY_TOKEN_FILE).

- [manage-claude/workload-identity-federation](https://platform.claude.com/docs/en/manage-claude/workload-identity-federation)
- [manage-claude/wif-providers/gcp](https://platform.claude.com/docs/en/manage-claude/wif-providers/gcp)
- [manage-claude/wif-providers/okta](https://platform.claude.com/docs/en/manage-claude/wif-providers/okta)
- [manage-claude/wif-providers/azure](https://platform.claude.com/docs/en/manage-claude/wif-providers/azure)
- [manage-claude/wif-providers/aws](https://platform.claude.com/docs/en/manage-claude/wif-providers/aws)
- [manage-claude/wif-providers/github-actions](https://platform.claude.com/docs/en/manage-claude/wif-providers/github-actions)
- …and 1 more

### Compliance API session coverage is clarified: session endpoints are read-only and local and remote sessions cannot be deleted through the API, while deletes elsewhere are immediate and unrecoverable.

`behavioural` · compliance · 4 pages

compliance-sessions: "The session endpoints are read-only; local and remote sessions cannot be deleted through the Compliance API," plus handling of local transcripts in organizations using customer-managed encryption keys. compliance-integration-patterns extends the legal-hold guidance to "chat content or remote session transcripts after users delete them in claude.ai". compliance-faq: "Deletes performed through the Compliance API are immediate, permanent, and not recoverable."

- [manage-claude/compliance-sessions](https://platform.claude.com/docs/en/manage-claude/compliance-sessions)
- [manage-claude/compliance-integration-patterns](https://platform.claude.com/docs/en/manage-claude/compliance-integration-patterns)
- [manage-claude/compliance-faq](https://platform.claude.com/docs/en/manage-claude/compliance-faq)
- [manage-claude/compliance-errors](https://platform.claude.com/docs/en/manage-claude/compliance-errors)

### Changing the top-level `effort` value between requests invalidates the prompt cache, and the effort setting is now listed in the cache-invalidation table.

`behavioural` · caching · 3 pages

effort adds: "**Hold top-level effort constant within cached conversations:** Changing the top-level effort value between requests invalidates [prompt caching]". prompt-caching adds a row "**Effort setting** | Model-specific | Model-specific". thinking adds "**Configuration changes invalidate caching.** The thinking configuration and the resolved [`effort`]".

- [build-with-claude/effort](https://platform.claude.com/docs/en/build-with-claude/effort)
- [build-with-claude/prompt-caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [build-with-claude/thinking](https://platform.claude.com/docs/en/build-with-claude/thinking)

### When the inference-hooks circuit breaker trips, enforcement stops and automatic recovery only runs while your Inference hooks settings are unchanged since the trip; recovery probes start about 10 minutes after the trip, roughly one request a minute.

`behavioural` · reliability · 3 pages

inference-hooks-configuration: "Automatic recovery runs only while your Inference hooks settings are unchanged since the trip. If you change any Inference hooks setting aft[er]" the trip. inference-hooks-endpoint: "Starting 10 minutes after the trip, Anthropic tests whether your server has recovered: at most about once per minute, one request".

- [manage-claude/inference-hooks-configuration](https://platform.claude.com/docs/en/manage-claude/inference-hooks-configuration)
- [manage-claude/inference-hooks-endpoint](https://platform.claude.com/docs/en/manage-claude/inference-hooks-endpoint)
- [manage-claude/inference-hooks](https://platform.claude.com/docs/en/manage-claude/inference-hooks)

### Claude Fable 5 and Mythos 5 can now be used under zero data retention if expressly authorized, where the docs previously stated a flat exclusion.

`behavioural` · data retention · 3 pages

Old text: "Claude Fable 5 and Claude Mythos 5 carry 30-day data retention and are not available under zero data retention: both are designated [Covered Models]". New text ends "…are not available under zero data retention unless expressly authorized b[y Anthropic]"; the migration guide makes the same change to its "(ZDR) arrangements;" sentence.

- [models/fable-5/migration-guide](https://platform.claude.com/docs/en/models/fable-5/migration-guide)
- [models/fable-5/introducing-claude-fable-5-and-claude-mythos-5](https://platform.claude.com/docs/en/models/fable-5/introducing-claude-fable-5-and-claude-mythos-5)
- [about-claude/models/introducing-claude-fable-5-and-claude-mythos-5](https://platform.claude.com/docs/en/about-claude/models/introducing-claude-fable-5-and-claude-mythos-5)

### AI function examples now name models by their Unity Catalog path, `'system.ai.llama-4-maverick'`, instead of the endpoint name `'databricks-llama-4-maverick'`.

`behavioural` · docs example · 3 pages

All three pages replace the literal `'databricks-llama-4-maverick'` in `ai_query` calls.

- [sql/language-manual/functions/ai_query](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_query)
- [sql/language-manual/functions/read_files](https://docs.databricks.com/aws/en/sql/language-manual/functions/read_files)
- [volumes/volume-files](https://docs.databricks.com/aws/en/volumes/volume-files)

### Priority Tier does not support Claude Fable 5.1 or Claude Mythos 5.1, which join the existing exclusion list.

`behavioural` · availability · 1 page

The page previously read "Priority Tier is supported on all available Claude models except Claude Mythos 5"; it now excludes Claude Fable 5.1 and Claude Mythos 5.1 as well.

- [api/service-tiers](https://platform.claude.com/docs/en/api/service-tiers)

### On Claude Fable 5.1 and Claude Mythos 5.1 the primer says `tool_choice` values `any` and `tool` return a 400 error and advises leaving `tool_choice` at `auto`.

`behavioural` · tool use · 1 page

New text: "On Claude Fable 5.1 and Claude Mythos 5.1, `any` and `tool` return a 400 error. Leave `tool_choice` at `auto` and set `\"strict\": true` on the" tool. The same page adds Fable 5.1 pricing guidance at 2x Claude Opus 5 pricing.

- [claude_api_primer](https://platform.claude.com/docs/en/claude_api_primer)

### Claude Fable 5.1 may issue fewer parallel tool calls than earlier models, most noticeably in long agent loops.

`behavioural` · tool use · 1 page

Added note: "Claude Fable 5.1 may issue fewer parallel tool calls than earlier models, most noticeably in long agent loops where the next reads are onl…". The page also restates that with `tool_choice` `any` or `tool`, `disable_parallel_tool_use: true` means exactly one tool call.

- [agents-and-tools/tool-use/parallel-tool-use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/parallel-tool-use)

### Deprecation of the `limit`, `offset`, `total_count` and `next_page` fields in the clusters events API moves from October 20, 2026 to November 30, 2026.

`behavioural` · deprecation · 1 page

The page previously read "On October 20, 2026, Databricks will deprecate the `limit`, `offset`, `total_count`, and `next_page` fields"; it now names November 30, 2026.

- [compute/events-api-updates](https://docs.databricks.com/aws/en/compute/events-api-updates)

### A job running continuously for more than 30 days loses access to files under `/Workspace` and must be restarted at least once to retain access.

`behavioural` · limits · 1 page

New text: "A job that runs continuously for more than 30 days loses access to files under `/Workspace`. To retain access, restart the job at least once". The page also states permission to access files under `/Workspace` expires after 36 hours for interactive compute and after 30 days for jobs.

- [files/workspace](https://docs.databricks.com/aws/en/files/workspace)

### The Genie Agents API `429`/`RATE_LIMIT_EXCEEDED` description no longer names a numeric limit, citing detected non-organic usage patterns or resource limitations instead.

`behavioural` · limits · 1 page

The old description read "The per-workspace rate limit of five requests per minute was exceeded."

- [genie-agents/api](https://docs.databricks.com/aws/en/genie-agents/api)

### Databricks Runtime 18 LTS documents that the Apache Avro fast reader, on by default in Avro 1.12.1, can exhaust executor memory in long-running jobs.

`behavioural` · known issue · 1 page

Workaround given: "turn off the Avro fast reader by adding `-Dorg.apache.avro.fastread=false` to the JVM options for both the driver" and executors.

- [release-notes/runtime/18](https://docs.databricks.com/aws/en/release-notes/runtime/18)

## Additive — 30

### Lakeflow Connect documents three new managed SaaS connectors — Anysphere Audit Logs (Cursor), Verkada and Glean — plus OneDrive file ingestion.

`additive` · connectors · 28 pages

Each connector ships the usual set of pages (overview, connection, source setup, pipeline, reference, limits, FAQ, troubleshooting) and is listed on the SaaS and file-connector indexes. The Glean limits page notes full-refresh-only ingestion and unsupported SCD Type 2; OneDrive ingestion uses Auto Loader, `spark.read` or `COPY INTO`.

- [ingestion/lakeflow-connect/anysphere-audit-logs](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs)
- [ingestion/lakeflow-connect/anysphere-audit-logs-connection](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-connection)
- [ingestion/lakeflow-connect/anysphere-audit-logs-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-pipeline)
- [ingestion/lakeflow-connect/anysphere-audit-logs-reference](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-reference)
- [ingestion/lakeflow-connect/anysphere-audit-logs-source-setup](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-source-setup)
- [ingestion/lakeflow-connect/anysphere-audit-logs-limits](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-limits)
- …and 22 more

### Claude Fable 5.1 (`claude-fable-5-1`) and Claude Mythos 5.1 ship with their own overview, migration, what's-new, prompting and system-prompt pages, and Fable 5 is relabelled legacy.

`additive` · model launch · 17 pages

New pages: models/fable-5-1/overview, migration-guide, whats-new-fable-5-1, models/mythos-5-1/overview, release-notes/system-prompts/claude-fable-5-1 and a Fable 5.1 prompting guide. Mythos 5.1 is described as the same model offered by invitation through Project Glasswing. The deprecation table adds `| claude-fable-5-1 | Active | N/A | Not sooner than September 1, 2027 |`. On models/fable-5/overview the Status row now reads Active (legacy) where it read "Active (latest)".

- [models/fable-5-1/overview](https://platform.claude.com/docs/en/models/fable-5-1/overview)
- [models/fable-5-1/migration-guide](https://platform.claude.com/docs/en/models/fable-5-1/migration-guide)
- [models/fable-5-1/whats-new-fable-5-1](https://platform.claude.com/docs/en/models/fable-5-1/whats-new-fable-5-1)
- [models/mythos-5-1/overview](https://platform.claude.com/docs/en/models/mythos-5-1/overview)
- [release-notes/system-prompts/claude-fable-5-1](https://platform.claude.com/docs/en/release-notes/system-prompts/claude-fable-5-1)
- [build-with-claude/prompt-engineering/prompting-claude-fable-5-1](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1)
- …and 11 more

### Feature support matrices across the platform docs now list Claude Fable 5.1 and Mythos 5.1 — structured outputs, browser use, advisor, `system.message`, 1M-token context on Vertex, Bedrock access, task budgets (beta header `task-budgets-2026-03-13`) and the managed-agents model enum ("10 more" → "11 more").

`additive` · availability · 15 pages

manage-claude/api-and-data-retention adds Fable 5.1 and Mythos 5.1 to the designated Covered Models; token-counting states the 5.1 models share the tokenizer introduced with Claude Opus 4.7.

- [build-with-claude/structured-outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)
- [agents-and-tools/tool-use/browser-use-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/browser-use-tool)
- [agents-and-tools/tool-use/advisor-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool)
- [managed-agents/events-and-streaming](https://platform.claude.com/docs/en/managed-agents/events-and-streaming)
- [managed-agents/reference](https://platform.claude.com/docs/en/managed-agents/reference)
- [build-with-claude/handling-stop-reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons)
- …and 9 more

### Model serving adds `databricks-claude-fable-5-1`, `databricks-gemini-3-8-flash`, `databricks-gpt-6-astra`, `databricks-grok-4-6` and GLM-5.3 to its supported-model, region, limits, function-calling, vision and acceptable-use tables.

`additive` · models · 13 pages

For example query-anthropic-messages adds `databricks-claude-fable-5-1`, query-gemini-api adds `databricks-gemini-3-8-flash`, query-openai-responses adds `databricks-gpt-6-astra`, and the `us-west-2` row of the region table lists `databricks-grok-4-6`. supported-models describes GLM-5.3 as a text-only MoE model from Zhipu AI for coding and agentic tool use, and adds a note that for Claude Fable 5.1 "prompts and responses are retained for 30 days for trust and safety purposes" with an opt-out reference.

- [machine-learning/model-serving/foundation-model-overview](https://docs.databricks.com/aws/en/machine-learning/model-serving/foundation-model-overview)
- [machine-learning/model-serving/function-calling](https://docs.databricks.com/aws/en/machine-learning/model-serving/function-calling)
- [machine-learning/model-serving/acceptable-use-models](https://docs.databricks.com/aws/en/machine-learning/model-serving/acceptable-use-models)
- [machine-learning/model-serving/score-foundation-models](https://docs.databricks.com/aws/en/machine-learning/model-serving/score-foundation-models)
- [machine-learning/model-serving/query-anthropic-messages](https://docs.databricks.com/aws/en/machine-learning/model-serving/query-anthropic-messages)
- [machine-learning/model-serving/query-gemini-api](https://docs.databricks.com/aws/en/machine-learning/model-serving/query-gemini-api)
- …and 7 more

### Unity Catalog gains ABAC DENY policies (Beta), which deny a privilege — documented for `MANAGE ACCESS CONTROL` — to principals on securables in scope and always take precedence over grants.

`additive` · governance · 12 pages

New page data-governance/unity-catalog/abac/deny-policies. core-concepts: "DENY policies explicitly deny a Unity Catalog privilege to principals on the securable objects in their scope, and always take precedence ov[er grants]". The hive_metastore `DENY` statement page now points readers to ABAC DENY policies for Unity Catalog, and privileges-reference notes `MANAGE ACCESS CONTROL` can be denied.

- [data-governance/unity-catalog/abac/deny-policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/deny-policies)
- [data-governance/unity-catalog/abac/core-concepts](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/core-concepts)
- [data-governance/unity-catalog/abac/best-practices](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/best-practices)
- [data-governance/unity-catalog/abac/performance](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/performance)
- [data-governance/unity-catalog/abac/policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/policies)
- [data-governance/unity-catalog/abac/policy-evaluation](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/policy-evaluation)
- …and 6 more

### A new "built-in MCP services" page collects the Databricks-provided `system.ai` MCP services, and the individual server pages are retitled (for example "AI Search MCP server").

`additive` · docs restructure · 12 pages

Links that pointed at mcp-tools/mcp-services#prebuilt now point at agents/mcp-tools/built-in-mcp-services. agents/mcp-tools/databricks-sql adds: "Databricks recommends the [`system.ai.dbsql` MCP Service] for a[gents]". Section titles change from "# AI Search", "# Genie Agent" and "# Unity Catalog functions" to "… MCP server".

- [agents/mcp-tools/built-in-mcp-services](https://docs.databricks.com/aws/en/agents/mcp-tools/built-in-mcp-services)
- [agents/mcp-tools/mcp-services](https://docs.databricks.com/aws/en/agents/mcp-tools/mcp-services)
- [agents/mcp-tools/use-mcp-in-agents](https://docs.databricks.com/aws/en/agents/mcp-tools/use-mcp-in-agents)
- [agents/mcp-tools/connect-external](https://docs.databricks.com/aws/en/agents/mcp-tools/connect-external)
- [agents/mcp-tools/databricks-sql](https://docs.databricks.com/aws/en/agents/mcp-tools/databricks-sql)
- [agents/mcp-tools/ai-search](https://docs.databricks.com/aws/en/agents/mcp-tools/ai-search)
- …and 6 more

### Analytics endpoints add Claude-in-Slack attribution: a spend category (`engaged` vs `proactive`) and a Slack user ID field that is explicitly not a claude.ai user ID.

`additive` · api surface · 10 pages

"Claude Tag (Claude in Slack) spend category: `engaged` (a person addressed Claude in a channel or thread), `proactive` (Claude responded wit[hout being addressed])" and "Slack user ID (for example `U0123ABCDEF`) of the member the Claude Tag (Claude in Slack) usage is attributed to, not a claude.ai user ID". The skills endpoints extend the display-name fallback to plugin-delivered skills. manage-claude/analytics-api restates that engagement and adoption endpoints return a per-day snapshot.

- [api/admin/analytics](https://platform.claude.com/docs/en/api/admin/analytics)
- [api/admin/analytics/cost](https://platform.claude.com/docs/en/api/admin/analytics/cost)
- [api/admin/analytics/cost/list](https://platform.claude.com/docs/en/api/admin/analytics/cost/list)
- [api/admin/analytics/cost/list_by_user](https://platform.claude.com/docs/en/api/admin/analytics/cost/list_by_user)
- [api/admin/analytics/usage](https://platform.claude.com/docs/en/api/admin/analytics/usage)
- [api/admin/analytics/usage/list](https://platform.claude.com/docs/en/api/admin/analytics/usage/list)
- …and 4 more

### The AI/BI dashboards release adds dashboard-wide color mappings, path maps drawn from point sequences, table color-scale placement, theme export to JSON, Teams subscription snapshots and cross-dataset filtering through relationships (Public Preview).

`additive` · dashboards · 9 pages

Theme settings gain "**Color mappings** in the **Color palette** tab, which assign a specific color to a value by name acro[ss the dashboard]" and JSON theme export; maps add a "**Geometry point sequence**" option alongside geometry columns; tables add "Use **Apply to** to paint the color scale on the cell **Backgro[und]**"; subscriptions add "**Microsoft Teams**: Teams channels receive a PNG image snapshot"; dashboard variables show each field's source dataset as a subtitle.

- [ai-bi/release-notes/2026](https://docs.databricks.com/aws/en/ai-bi/release-notes/2026)
- [dashboards/manage/settings](https://docs.databricks.com/aws/en/dashboards/manage/settings)
- [dashboards/manage/visualizations/](https://docs.databricks.com/aws/en/dashboards/manage/visualizations/)
- [dashboards/manage/visualizations/maps](https://docs.databricks.com/aws/en/dashboards/manage/visualizations/maps)
- [dashboards/manage/visualizations/types](https://docs.databricks.com/aws/en/dashboards/manage/visualizations/types)
- [dashboards/manage/visualizations/tables](https://docs.databricks.com/aws/en/dashboards/manage/visualizations/tables)
- …and 3 more

### Mid-conversation system messages gain a lifetime setting — `"never"` (the default) renders the text on every request that includes it — and placement rules are now spelled out.

`additive` · api surface · 7 pages

New field description: "How long this system message's text stays in front of the model. `\"never\"` (the default) renders it on every request that includes it." The guide adds: "**Placement is constrained.** A `system` message that carries content (`text`, `tool_addition`, or `tool_removal` blocks) must immediately" follow a particular turn.

- [build-with-claude/mid-conversation-system-messages](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages)
- [api/beta](https://platform.claude.com/docs/en/api/beta)
- [api/beta/messages](https://platform.claude.com/docs/en/api/beta/messages)
- [api/beta/messages/create](https://platform.claude.com/docs/en/api/beta/messages/create)
- [api/beta/messages/batches](https://platform.claude.com/docs/en/api/beta/messages/batches)
- [api/beta/messages/batches/create](https://platform.claude.com/docs/en/api/beta/messages/batches/create)
- …and 1 more

### Zerobus Ingest can write into tables backed by default storage, now listed as Public Preview, and the blanket exclusion is gone from the concepts page.

`additive` · ingestion · 6 pages

The release-stages table adds a row "| Ingesting into tables backed by [default storage] | Public Preview |". zerobus-concepts previously read "Zerobus Ingest writes only to managed Delta tables. Writing to default storage is not supported." and now stops after "managed Delta tables."

- [ingestion/zerobus-release-stages](https://docs.databricks.com/aws/en/ingestion/zerobus-release-stages)
- [ingestion/zerobus-concepts](https://docs.databricks.com/aws/en/ingestion/zerobus-concepts)
- [ingestion/zerobus-overview](https://docs.databricks.com/aws/en/ingestion/zerobus-overview)
- [ingestion/zerobus-ingest](https://docs.databricks.com/aws/en/ingestion/zerobus-ingest)
- [ingestion/zerobus-arrow-flight](https://docs.databricks.com/aws/en/ingestion/zerobus-arrow-flight)
- [ingestion/zerobus-message-types](https://docs.databricks.com/aws/en/ingestion/zerobus-message-types)

### A new `ai_enrich` function (Beta) generates new columns for each row and is listed in the AI functions table and related see-also sections.

`additive` · sql function · 6 pages

New reference page sql/language-manual/functions/ai_enrich; the AI functions index adds "| [ai_enrich](…) (Beta) | Generate new columns for each row from a…".

- [sql/language-manual/functions/ai_enrich](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_enrich)
- [large-language-models/ai-functions](https://docs.databricks.com/aws/en/large-language-models/ai-functions)
- [sql/language-manual/functions/ai_extract](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_extract)
- [sql/language-manual/functions/ai_parse_document](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_parse_document)
- [sql/language-manual/functions/ai_search](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_search)
- [sql/language-manual/sql-ref-functions-builtin-alpha](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-functions-builtin-alpha)

### New beta organization compliance-settings endpoints (retrieve and update) are documented alongside the Compliance API.

`additive` · api surface · 5 pages

api/beta/organization/compliance_settings and its retrieve/update endpoints are new pages. compliance-api restates that every endpoint lives under `/v1/compliance/*` on `https://api.anthropic.com` and authenticates through the `x-api-key` header.

- [api/beta/organization/compliance_settings](https://platform.claude.com/docs/en/api/beta/organization/compliance_settings)
- [api/beta/organization/compliance_settings/retrieve](https://platform.claude.com/docs/en/api/beta/organization/compliance_settings/retrieve)
- [api/beta/organization/compliance_settings/update](https://platform.claude.com/docs/en/api/beta/organization/compliance_settings/update)
- [manage-claude/compliance-api](https://platform.claude.com/docs/en/manage-claude/compliance-api)
- [manage-claude/compliance-api-access](https://platform.claude.com/docs/en/manage-claude/compliance-api-access)

### Unity Gateway Skills arrive: governed SKILL.md files published to a Unity Catalog schema that agents download or load live over MCP, with grants and audit.

`additive` · feature · 5 pages

Four new pages cover the concept, publishing and sharing a skill, consuming skills from a coding agent via the Unity Gateway CLI, and the admin side (enabling the feature, governed schema, create/write/read privileges, auditing).

- [agents/uc-skills/](https://docs.databricks.com/aws/en/agents/uc-skills/)
- [agents/uc-skills/create-share-uc-skills](https://docs.databricks.com/aws/en/agents/uc-skills/create-share-uc-skills)
- [agents/uc-skills/use-uc-skills](https://docs.databricks.com/aws/en/agents/uc-skills/use-uc-skills)
- [ai-gateway/govern-skills](https://docs.databricks.com/aws/en/ai-gateway/govern-skills)
- [agent-skills/](https://docs.databricks.com/aws/en/agent-skills/)

### The HubSpot connector now supports CRM Hub ingestion in Beta, alongside Marketing Hub.

`additive` · connectors · 5 pages

hubspot-limits previously read "The HubSpot connector only supports ingestion from HubSpot Marketing Hub. If you are interested in ingesting from other hubs, contact y[our account team]"; it now says both hubs are supported with CRM Hub in Beta. The pipeline example ingests `marketing_emails` and `contacts`, and the source-setup scope list is no longer conditioned on the CRM preview wording.

- [ingestion/lakeflow-connect/hubspot-limits](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-limits)
- [ingestion/lakeflow-connect/hubspot-overview](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-overview)
- [ingestion/lakeflow-connect/hubspot-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-pipeline)
- [ingestion/lakeflow-connect/hubspot-reference](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-reference)
- [ingestion/lakeflow-connect/hubspot-source-setup](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-source-setup)

### Integrated CDC pipelines can run in continuous (always-on) mode, documented on a new page, with triggered mode remaining the default.

`additive` · ingestion · 5 pages

New page ingestion/lakeflow-connect/continuous-integrated-cdc describes scale-optimized and speed-optimized run modes. The per-source pages now state "**Triggered by default.** By default, integrated CDC pipelines run in triggered mode; schedule them using a Lakeflow Jobs task. Continuous" mode is available.

- [ingestion/lakeflow-connect/continuous-integrated-cdc](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/continuous-integrated-cdc)
- [ingestion/lakeflow-connect/mysql-integrated-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/mysql-integrated-pipeline)
- [ingestion/lakeflow-connect/oracle-integrated-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/oracle-integrated-pipeline)
- [ingestion/lakeflow-connect/sql-server-integrated-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/sql-server-integrated-pipeline)
- [ingestion/lakeflow-connect/common-patterns](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/common-patterns)

### Lakebase documents HIPAA support: how to enable it on projects in compliance-security-profile workspaces, the shared responsibility for PHI and the BAA, and how HIPAA audit logs land in the Unity Catalog audit system table.

`additive` · compliance · 5 pages

Three new OLTP pages. security/privacy/hipaa adds "Enable the compliance security profile on every workspace that processes PHI data." The Lakebase release notes state Lakebase "is now enabled by default in workspaces with the [compliance security profile]", where they read "is now available by default for workspaces with the".

- [oltp/projects/hipaa-compliance](https://docs.databricks.com/aws/en/oltp/projects/hipaa-compliance)
- [oltp/projects/enable-hipaa-compliance](https://docs.databricks.com/aws/en/oltp/projects/enable-hipaa-compliance)
- [oltp/projects/hipaa-audit-logging](https://docs.databricks.com/aws/en/oltp/projects/hipaa-audit-logging)
- [security/privacy/hipaa](https://docs.databricks.com/aws/en/security/privacy/hipaa)
- [release-notes/lakebase/](https://docs.databricks.com/aws/en/release-notes/lakebase/)

### Cross-workspace access (Beta) lets you control which source workspaces can reach a workspace over serverless traffic, as ingress rules on the ingress policy and egress entries in network policies.

`additive` · networking · 5 pages

New page security/network/front-end/cross-workspace-access. context-based-ingress: "**Cross-workspace access (Beta):** Controls which source workspaces can reach this workspace over serverless traffic", and a policy left in compatibility mode does not govern cross-workspace ingress. network-policies covers allowing specific workspaces as destinations, "the egress side of cross-[workspace access]".

- [security/network/front-end/cross-workspace-access](https://docs.databricks.com/aws/en/security/network/front-end/cross-workspace-access)
- [security/network/front-end/context-based-ingress](https://docs.databricks.com/aws/en/security/network/front-end/context-based-ingress)
- [security/network/front-end/manage-ingress-policies](https://docs.databricks.com/aws/en/security/network/front-end/manage-ingress-policies)
- [security/network/serverless-network-security/network-policies](https://docs.databricks.com/aws/en/security/network/serverless-network-security/network-policies)
- [security/network/serverless-network-security/](https://docs.databricks.com/aws/en/security/network/serverless-network-security/)

### Serverless environment version 6 ships, with CPU and GPU release notes and a new Standard v6 base environment choice.

`additive` · runtime · 5 pages

New pages for environment version 6 and GPU environment 6; the version table adds a row "| 6 | - [CPU environment] | - **Operating System**: Ubu[ntu…]" and the AI Runtime environment panel now offers "**Standard v6**, **Standard v5**, or **Standard v4**". The version 5 GPU notes add a top-level `ray_init()` drop-in that enables the Ray dashboard.

- [release-notes/serverless/environment-version/six](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/six)
- [release-notes/serverless/environment-version/six-gpu](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/six-gpu)
- [release-notes/serverless/environment-version/](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/)
- [machine-learning/ai-runtime/environment](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/environment)
- [release-notes/serverless/environment-version/five-gpu](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/five-gpu)

### A new `time_bucket(bucketSize, ts [, origin])` function returns the start of a fixed-width time bucket for a timestamp, aligned to an origin.

`additive` · sql function · 4 pages

New reference page plus entries in the built-in function lists and a see-also link from `date_trunc`.

- [sql/language-manual/functions/time_bucket](https://docs.databricks.com/aws/en/sql/language-manual/functions/time_bucket)
- [sql/language-manual/sql-ref-functions-builtin](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-functions-builtin)
- [sql/language-manual/sql-ref-functions-builtin-alpha](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-functions-builtin-alpha)
- [sql/language-manual/functions/date_trunc](https://docs.databricks.com/aws/en/sql/language-manual/functions/date_trunc)

### Feature views gain a `SawtoothWindow` time-window class that keeps long aggregation windows (30, 60, 90 days) continuously fresh, plus a schema registry for streaming sources in Preview.

`additive` · feature · 4 pages

The release notes describe the new class; the API reference explains that because the historic portion is computed by the batch pipeline, a sawtooth feature is ready to serve shortly after materialization. feature-views also documents `transformation_sql` requiring `dataframe_schema`, and streams covers Kafka registry credentials supplied as options on a Unity Catalog connection with the registry API secret in a Databricks secret.

- [machine-learning/feature-store/feature-views-api-reference](https://docs.databricks.com/aws/en/machine-learning/feature-store/feature-views-api-reference)
- [machine-learning/feature-store/feature-views](https://docs.databricks.com/aws/en/machine-learning/feature-store/feature-views)
- [machine-learning/feature-store/streams](https://docs.databricks.com/aws/en/machine-learning/feature-store/streams)
- [release-notes/feature-store/databricks-feature-store](https://docs.databricks.com/aws/en/release-notes/feature-store/databricks-feature-store)

### Automatic identity management adds an Okta migration guide and a readiness report that finds external ID and group-membership divergences between Databricks and your identity provider.

`additive` · identity · 4 pages

Two new pages; the existing SCIM-to-AIM migration page and the section index were updated and moved.

- [admin/users-groups/automatic-identity-management/migrate-to-aim-okta](https://docs.databricks.com/aws/en/admin/users-groups/automatic-identity-management/migrate-to-aim-okta)
- [admin/users-groups/automatic-identity-management/readiness-report](https://docs.databricks.com/aws/en/admin/users-groups/automatic-identity-management/readiness-report)
- [admin/users-groups/automatic-identity-management/migrate-to-aim](https://docs.databricks.com/aws/en/admin/users-groups/automatic-identity-management/migrate-to-aim)
- [admin/users-groups/automatic-identity-management/](https://docs.databricks.com/aws/en/admin/users-groups/automatic-identity-management/)

### Git Folder Serverless (Beta) lets notebooks and files in a Git folder share one compute resource and an environment managed by `pyproject.toml`.

`additive` · compute · 4 pages

New page compute/serverless/notebooks/git-folder-serverless, listed under compute/serverless/ as "(Beta)"; the dependencies page notes that in this experience notebooks and files attached to the same compute use the `pyproject.toml`-managed environment, while standard serverless notebooks keep the existing flow.

- [compute/serverless/notebooks/git-folder-serverless](https://docs.databricks.com/aws/en/compute/serverless/notebooks/git-folder-serverless)
- [compute/serverless/](https://docs.databricks.com/aws/en/compute/serverless/)
- [compute/serverless/notebooks](https://docs.databricks.com/aws/en/compute/serverless/notebooks)
- [compute/serverless/dependencies](https://docs.databricks.com/aws/en/compute/serverless/dependencies)

### Values in `FILE` columns can be previewed directly in SQL editor query results, and the docs state the access needed: the file and the table, plus `READ VOLUME` for a `FILE EXTERNAL` column.

`additive` · feature · 3 pages

New cross-reference "To preview a file's contents in query results, see [Preview files in FILE columns]". The results page adds: "Previewing reads the file's contents, so you need access to both the file and the table. For a `FILE EXTERNAL` column, you need the `READ VO[LUME]`" privilege.

- [sql/language-manual/data-types/file-type](https://docs.databricks.com/aws/en/sql/language-manual/data-types/file-type)
- [sql/user/sql-editor/results](https://docs.databricks.com/aws/en/sql/user/sql-editor/results)
- [unstructured/file](https://docs.databricks.com/aws/en/unstructured/file)

### A Unity Catalog schema can be backed by AWS Secrets Manager or Azure Key Vault so secret values stay in your cloud secret manager while remaining governable in Unity Catalog.

`additive` · security · 3 pages

Two new pages (concept and configuration); unity-catalog-secrets adds "Instead of Databricks storing secret values, you can back a schema with an external secret manager so the values stay in your cloud secret m[anager]".

- [security/secrets/external-secrets](https://docs.databricks.com/aws/en/security/secrets/external-secrets)
- [security/secrets/configure-external-secrets](https://docs.databricks.com/aws/en/security/secrets/configure-external-secrets)
- [security/secrets/unity-catalog-secrets](https://docs.databricks.com/aws/en/security/secrets/unity-catalog-secrets)

### HTTP connections in Unity Catalog are generally available at the schema level — you can create an HTTP connection inside a schema.

`additive` · ga · 3 pages

August release notes: "HTTP connections in Unity Catalog are now generally available at the schema level. You can create an HTTP connection inside a schema instead" of at the catalog level. query-federation/http is rewritten around the securable object holding endpoint and credential information; the same release-notes page also announces Smart Routing (Beta) for picking a model and agent harness per task.

- [release-notes/product/2026/august](https://docs.databricks.com/aws/en/release-notes/product/2026/august)
- [query-federation/http](https://docs.databricks.com/aws/en/query-federation/http)
- [connect/uc-connections](https://docs.databricks.com/aws/en/connect/uc-connections)

### A new Claude Agent SDK cookbook recipe builds a scheduled, read-only repository reviewer that resumes its session and returns schema-validated verdicts.

`additive` · tutorial · 2 pages

Listed on the cookbook index as "Build a scheduled repository reviewer" under the Claude Agent SDK category.

- [platform.claude.com/cookbook/claude-agent-sdk-scheduled-repository-reviewer-scheduled-repository-reviewer](https://platform.claude.com/cookbook/claude-agent-sdk-scheduled-repository-reviewer-scheduled-repository-reviewer)
- [platform.claude.com/cookbook/](https://platform.claude.com/cookbook/)

### Lakebase PCI-DSS and HITRUST support extends to all AWS regions where Lakebase is available, rather than only `us-east-1`.

`additive` · availability · 2 pages

Previous text: "PCI-DSS and HITRUST are now supported in the `us-east-1` region on AWS."

- [oltp/projects/data-protection](https://docs.databricks.com/aws/en/oltp/projects/data-protection)
- [oltp/projects/private-link](https://docs.databricks.com/aws/en/oltp/projects/private-link)

### OAuth machine-to-machine secrets can be scoped: by default a secret can access every API the service principal is authorized for (`all-apis`), and a scoped secret restricts it.

`additive` · auth · 2 pages

New text: "By default, an OAuth secret can access every API the service principal is authorized for (`all-apis`). A scoped secret restricts access to a[ selection]", with a UI step "Under **Scopes**, select the API scopes the secret can use." The service principal page links to "Scoped OAuth secrets".

- [dev-tools/auth/oauth-m2m](https://docs.databricks.com/aws/en/dev-tools/auth/oauth-m2m)
- [admin/users-groups/manage-service-principals](https://docs.databricks.com/aws/en/admin/users-groups/manage-service-principals)

### You can add, drop or rename columns and widen column types on a streaming table with `ALTER TABLE` as metadata-only changes, without a full refresh or checkpoint reset.

`additive` · feature · 2 pages

New page ldp/streaming-table-schema-evolution; data-engineering/schema-evolution adds the same statement and revises its column-renaming entry, which previously read "**Column renaming**: Supported. By default, when a source column is renamed, the query restarts to resolve the schema mismatch".

- [ldp/streaming-table-schema-evolution](https://docs.databricks.com/aws/en/ldp/streaming-table-schema-evolution)
- [data-engineering/schema-evolution](https://docs.databricks.com/aws/en/data-engineering/schema-evolution)

### A new Genie Ontology page describes the unified context layer combining Unity Catalog semantics with inferred context so Genie One and Genie Code answer with business meaning.

`additive` · concept · 1 page

New page under genie/.

- [genie/genie-ontology](https://docs.databricks.com/aws/en/genie/genie-ontology)

## Editorial — 9

### "Unity AI Gateway" is renamed to "Unity Gateway" throughout the Databricks docs, including entitlement names such as "Consumer access to Unity Gateway".

`editorial` · rename · 32 pages

Mechanical replacement of the product name; for example "Unity AI Gateway is generally available" becomes "Unity Gateway is generally available" and "A new Unity AI Gateway experience is generally available" loses the "AI". A new release-notes/unity-gateway/ index was also added.

- [ai-gateway/](https://docs.databricks.com/aws/en/ai-gateway/)
- [ai-gateway/overview-serving-endpoints](https://docs.databricks.com/aws/en/ai-gateway/overview-serving-endpoints)
- [ai-gateway/agent-services](https://docs.databricks.com/aws/en/ai-gateway/agent-services)
- [ai-gateway/model-services](https://docs.databricks.com/aws/en/ai-gateway/model-services)
- [ai-gateway/govern-model-services](https://docs.databricks.com/aws/en/ai-gateway/govern-model-services)
- [ai-gateway/govern-model-provider-services](https://docs.databricks.com/aws/en/ai-gateway/govern-model-provider-services)
- …and 26 more

### The single "Use Genie Code" page is split into features-and-capabilities, agent mode, navigation, web search and full-page topics, and links across the docs are repointed.

`editorial` · docs restructure · 25 pages

New pages: genie-code/features-capabilities, agent-mode (approval prompts and multi-step automation), navigate-genie-code, web-search (public web search with citations) and full-page. Cross-references such as "See [Use Genie Code](…/genie-code/use-genie-code)" now target the new pages, and requirement links move to genie-code/agent-mode#requirements.

- [genie-code/features-capabilities](https://docs.databricks.com/aws/en/genie-code/features-capabilities)
- [genie-code/agent-mode](https://docs.databricks.com/aws/en/genie-code/agent-mode)
- [genie-code/navigate-genie-code](https://docs.databricks.com/aws/en/genie-code/navigate-genie-code)
- [genie-code/web-search](https://docs.databricks.com/aws/en/genie-code/web-search)
- [genie-code/full-page](https://docs.databricks.com/aws/en/genie-code/full-page)
- [genie-code/use-genie-code](https://docs.databricks.com/aws/en/genie-code/use-genie-code)
- …and 19 more

### Most of the API reference was regenerated: the beta-header enum grows from "or 38 more" to "or 41 more", model blurbs are rewritten, and many field descriptions gain backticks around literal values.

`editorial` · bulk regeneration · 24 pages

Hundreds of endpoint pages change only through this regeneration — e.g. `"message-batches-2024-09-24" or "prompt-caching-2024-07-31" or "computer-use-2024-10-22" or 38 more` becomes "or 41 more", descriptions such as "Filter by status: active or paused" become "Filter by status: `active` or `paused`", and model descriptions such as "Frontier intelligence for ambitious tasks across coding, scientific discovery, and enterprise workflows" are restated. Treat these pages as noise unless a specific field is named elsewhere in this digest.

- [api/beta](https://platform.claude.com/docs/en/api/beta)
- [api/beta/agents](https://platform.claude.com/docs/en/api/beta/agents)
- [api/beta/environments](https://platform.claude.com/docs/en/api/beta/environments)
- [api/beta/files](https://platform.claude.com/docs/en/api/beta/files)
- [api/beta/models](https://platform.claude.com/docs/en/api/beta/models)
- [api/beta/skills](https://platform.claude.com/docs/en/api/beta/skills)
- …and 18 more

### Admin API curl examples switch the bearer-token environment variable from `$ANTHROPIC_OAUTH_TOKEN` to `$ANTHROPIC_AUTH_TOKEN` across the admin reference.

`editorial` · docs example · 20 pages

Mechanical replacement of `-H "Authorization: Bearer $ANTHROPIC_OAUTH_TOKEN"` throughout api/admin/*; only the shell variable name in the samples changes.

- [api/admin/api_keys](https://platform.claude.com/docs/en/api/admin/api_keys)
- [api/admin/api_keys/list](https://platform.claude.com/docs/en/api/admin/api_keys/list)
- [api/admin/api_keys/retrieve](https://platform.claude.com/docs/en/api/admin/api_keys/retrieve)
- [api/admin/api_keys/update](https://platform.claude.com/docs/en/api/admin/api_keys/update)
- [api/admin/cost_report](https://platform.claude.com/docs/en/api/admin/cost_report)
- [api/admin/cost_report/retrieve](https://platform.claude.com/docs/en/api/admin/cost_report/retrieve)
- …and 14 more

### Cookbook notebooks move off `claude-opus-4-1` to `claude-opus-4-8` in their model constants.

`editorial` · docs example · 18 pages

Lines such as "MODEL_NAME = \"claude-opus-4-1\"" and "llm = Anthropic(temperature=0.0, model=\"claude-opus-4-1\")" now use `claude-opus-4-8`; the MongoDB recipe also rewrites "Load the Anthropic Claude 3, specifically the ‘claude-opus-4-1’ model" as "Load Anthropic's Claude, specifically the `claude-opus-4-8` model".

- [platform.claude.com/cookbook/misc-building-evals](https://platform.claude.com/cookbook/misc-building-evals)
- [platform.claude.com/cookbook/misc-how-to-enable-json-mode](https://platform.claude.com/cookbook/misc-how-to-enable-json-mode)
- [platform.claude.com/cookbook/misc-how-to-make-sql-queries](https://platform.claude.com/cookbook/misc-how-to-make-sql-queries)
- [platform.claude.com/cookbook/multimodal-best-practices-for-vision](https://platform.claude.com/cookbook/multimodal-best-practices-for-vision)
- [platform.claude.com/cookbook/multimodal-getting-started-with-vision](https://platform.claude.com/cookbook/multimodal-getting-started-with-vision)
- [platform.claude.com/cookbook/multimodal-how-to-transcribe-text](https://platform.claude.com/cookbook/multimodal-how-to-transcribe-text)
- …and 12 more

### "Databricks Data Intelligence Platform" is renamed to "Databricks Data + AI Platform", and two pages now render the literal placeholder "platform-name".

`editorial` · rename · 18 pages

Example: "To get the most out of the Databricks Data Intelligence Platform" becomes "the Databricks Data + AI Platform". On machine-learning/mlops/mlops-workflow and repos/repos-setup the substitution produced image alt text reading "MLOps on the Databricks platform-name." and "Databricks platform-name" — describe as the text now stands, not as intent.

- [lakehouse-architecture/cost-optimization/best-practices](https://docs.databricks.com/aws/en/lakehouse-architecture/cost-optimization/best-practices)
- [lakehouse-architecture/interoperability-and-usability/best-practices](https://docs.databricks.com/aws/en/lakehouse-architecture/interoperability-and-usability/best-practices)
- [lakehouse-architecture/reference](https://docs.databricks.com/aws/en/lakehouse-architecture/reference)
- [lakehouse-architecture/](https://docs.databricks.com/aws/en/lakehouse-architecture/)
- [migration/warehouse-to-lakehouse](https://docs.databricks.com/aws/en/migration/warehouse-to-lakehouse)
- [migration/etl](https://docs.databricks.com/aws/en/migration/etl)
- …and 12 more

### Cookbook install cells switch from the shell escape `!pip install` to the notebook magic `%pip install`.

`editorial` · docs example · 8 pages

For example "!pip install anthropic" becomes `%pip install anthropic`.

- [platform.claude.com/cookbook/capabilities-classification-guide](https://platform.claude.com/cookbook/capabilities-classification-guide)
- [platform.claude.com/cookbook/capabilities-contextual-embeddings-guide](https://platform.claude.com/cookbook/capabilities-contextual-embeddings-guide)
- [platform.claude.com/cookbook/capabilities-summarization-guide](https://platform.claude.com/cookbook/capabilities-summarization-guide)
- [platform.claude.com/cookbook/capabilities-retrieval-augmented-generation-guide](https://platform.claude.com/cookbook/capabilities-retrieval-augmented-generation-guide)
- [platform.claude.com/cookbook/finetuning-finetuning-on-bedrock](https://platform.claude.com/cookbook/finetuning-finetuning-on-bedrock)
- [platform.claude.com/cookbook/misc-sampling-past-max-tokens](https://platform.claude.com/cookbook/misc-sampling-past-max-tokens)
- …and 2 more

### Pinned install versions in the docs move to anthropic-java 2.60.0 and CLI 1.30.0.

`editorial` · version bump · 4 pages

Snippets that read "implementation(\"com.anthropic:anthropic-java:2.58.0\")" (and anthropic-java-aws 2.58.0) now pin 2.60.0; the CLI quickstart changes "VERSION=1.27.0" to 1.30.0.

- [cli-sdks-libraries/sdks/java](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/java)
- [get-started](https://platform.claude.com/docs/en/get-started)
- [build-with-claude/claude-platform-on-aws](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws)
- [cli-sdks-libraries/cli/quickstart](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/quickstart)

### The documented per-branch database storage quota no longer states a figure; the pages now say only that each branch has a quota.

`editorial` · limits · 2 pages

Both pages previously read "Each branch has a 32 TB database storage quota." and now read "Each branch has a database storage quota." The surrounding explanation that this is operational rather than architectural is unchanged.

- [oltp/instances/create/](https://docs.databricks.com/aws/en/oltp/instances/create/)
- [oltp/projects/manage-projects](https://docs.databricks.com/aws/en/oltp/projects/manage-projects)
