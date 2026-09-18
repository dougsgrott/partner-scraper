# Change digest

> #5 (2026-09-09-before) → #6 (2026-09-09) · 1,072 changes · rendered 2026-09-18T16:07:26+00:00

## At a glance

63 findings — **4** breaking, **19** behavioural, **31** additive, **9** editorial — covering 584 of 1,072 changed pages. Anything not here is in the full feed report beside this file.

**If you read nothing else:**

1. On Claude Platform on AWS, a CMEK `kms_arn` must be a single-Region key in your own AWS account: cross-account keys, multi-Region keys and alias ARNs are rejected.
2. Change data feed now requires Databricks Runtime 19 or above, where the requirement was previously Databricks Runtime 18 LTS or above.
3. The CMEK page now says structured outputs are unavailable for Claude Fable and Claude Mythos models generally in CMEK organizations, where it previously named only Claude Fable 5 and Claude Mythos models.
4. The TypeScript SDK now states TypeScript >= 5.0 is supported, up from >= 4.9.

---

## Breaking — 4

### On Claude Platform on AWS, a CMEK `kms_arn` must be a single-Region key in your own AWS account: cross-account keys, multi-Region keys and alias ARNs are rejected.

`breaking` · restriction · 12 pages

Every external-keys reference page adds this sentence to the kms_arn description. The deprecated role_arn note is reworded: Anthropic reaches the KMS key through its own intermediate role, or on Claude Platform on AWS with credentials AWS issues for the Workspace; the field is ignored. manage-claude/cmek-aws-kms adds troubleshooting for a failed attach, including finding the denied kms: event in CloudTrail in the key's account.

- [api/admin/external_keys](https://platform.claude.com/docs/en/api/admin/external_keys)
- [api/admin/external_keys/create](https://platform.claude.com/docs/en/api/admin/external_keys/create)
- [api/admin/external_keys/list](https://platform.claude.com/docs/en/api/admin/external_keys/list)
- [api/admin/external_keys/retrieve](https://platform.claude.com/docs/en/api/admin/external_keys/retrieve)
- [api/admin/external_keys/update](https://platform.claude.com/docs/en/api/admin/external_keys/update)
- [api/admin/external_keys/validate](https://platform.claude.com/docs/en/api/admin/external_keys/validate)
- …and 6 more

### Change data feed now requires Databricks Runtime 19 or above, where the requirement was previously Databricks Runtime 18 LTS or above.

`breaking` · version floor · 2 pages

The requirements list changed to "Databricks Runtime 19 or above". The Databricks Runtime 19 release notes (September 1, 2026) announce automatic change data feed (Auto CDF), which computes row-level changes at query time, as generally available.

- [tables/features/change-data-feed](https://docs.databricks.com/aws/en/tables/features/change-data-feed)
- [release-notes/runtime/19](https://docs.databricks.com/aws/en/release-notes/runtime/19)

### The CMEK page now says structured outputs are unavailable for Claude Fable and Claude Mythos models generally in CMEK organizations, where it previously named only Claude Fable 5 and Claude Mythos models.

`breaking` · restriction · 1 page

The table entry changed from "not available for Claude Fable 5 or Claude Mythos models in CMEK organizations" to "not available for Claude Fable or Claude Mythos models in CMEK organizations", widening the stated exclusion to the whole families.

- [manage-claude/cmek](https://platform.claude.com/docs/en/manage-claude/cmek)

### The TypeScript SDK now states TypeScript >= 5.0 is supported, up from >= 4.9.

`breaking` · version floor · 1 page

One-line change to the supported-TypeScript statement.

- [cli-sdks-libraries/sdks/typescript](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/typescript)

## Behavioural — 19

### MLflow tracing examples now require mlflow[databricks]>=3.14.0 and store traces in Unity Catalog, which means setting MLFLOW_TRACING_SQL_WAREHOUSE_ID before running them.

`behavioural` · version floor · 42 pages

Install lines move from >=3.1 to >=3.14.0; pages add "the examples on this page access traces stored in Unity Catalog. Configure a SQL warehouse before you run them" and import mlflow.entities.trace_location.UnityCatalog. label-existing-traces raises its stated requirement from MLflow 3.1.0 to 3.14.0, Claude Code CLI tracing from MLflow 3.4+ to 3.14+, and the Databricks Apps page notes an MLflow experiment resource grants only workspace-level permissions, so UC trace tables must be added separately.

- [mlflow3/genai/tracing/integrations/](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/)
- [mlflow3/genai/tracing/integrations/anthropic](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/anthropic)
- [mlflow3/genai/tracing/integrations/autogen](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/autogen)
- [mlflow3/genai/tracing/integrations/ag2](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/ag2)
- [mlflow3/genai/tracing/integrations/crewai](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/crewai)
- [mlflow3/genai/tracing/integrations/databricks-foundation-models](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/databricks-foundation-models)
- …and 36 more

### Federation-issuer, federation-rule and service-account endpoints are now documented as requiring an OAuth access token with the `org:admin` scope, from `ant auth login --scope org:admin` or a workload identity federation rule.

`behavioural` · authentication · 31 pages

These pages previously said the endpoints required an OAuth bearer or Console session and that Admin API keys were not accepted, with some scopes Console-only. The new boilerplate names the specific scope and the two ways to obtain a token.

- [api/admin/federation_issuers](https://platform.claude.com/docs/en/api/admin/federation_issuers)
- [api/admin/federation_issuers/archive](https://platform.claude.com/docs/en/api/admin/federation_issuers/archive)
- [api/admin/federation_issuers/create](https://platform.claude.com/docs/en/api/admin/federation_issuers/create)
- [api/admin/federation_issuers/list](https://platform.claude.com/docs/en/api/admin/federation_issuers/list)
- [api/admin/federation_issuers/retrieve](https://platform.claude.com/docs/en/api/admin/federation_issuers/retrieve)
- [api/admin/federation_issuers/update](https://platform.claude.com/docs/en/api/admin/federation_issuers/update)
- …and 25 more

### Managed-agent examples now use a declarative `ant apply <file>` instead of piping YAML into `ant beta:environments create` / `ant beta:agents create`, and a new cli/apply page documents the workflow.

`behavioural` · cli · 12 pages

cli-sdks-libraries/cli/apply is new: declare agents, environments, skills, memory stores and deployments as files in your repository and keep the API's resources in sync with them. The managed-agents guides were rewritten to that form.

- [cli-sdks-libraries/cli/apply](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/apply)
- [managed-agents/self-hosted-sandboxes](https://platform.claude.com/docs/en/managed-agents/self-hosted-sandboxes)
- [managed-agents/environments](https://platform.claude.com/docs/en/managed-agents/environments)
- [managed-agents/quickstart](https://platform.claude.com/docs/en/managed-agents/quickstart)
- [managed-agents/agent-setup](https://platform.claude.com/docs/en/managed-agents/agent-setup)
- [managed-agents/permission-policies](https://platform.claude.com/docs/en/managed-agents/permission-policies)
- …and 6 more

### A new "preserved thinking" page states that thinking blocks from Claude Fable 5.1 and Claude Mythos 5.1 are usable only by the model that produced them or a newer one, and only while the system prompt, tools and preceding messages are unchanged.

`behavioural` · thinking · 11 pages

build-with-claude/preserved-thinking is new. Release notes say thinking blocks produced by Fable 5.1 / Mythos 5.1 are preserved only for that model or a newer one. thinking-troubleshooting says the API accepts a replayed thinking block only while the system prompt, tools and the messages that preceded it are unchanged, and advises keeping history append-only. compaction says thinking blocks before a compaction block aren't carried forward on 5.1; the computer-use page warns that pruning an earlier screenshot client-side invalidates every later thinking block. The beta Messages and Batches references gain input_transformations (BetaThinkingDroppedInputTransformation) and prefix_mismatch_behavior fields that report where a block was removed.

- [build-with-claude/preserved-thinking](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking)
- [build-with-claude/context-windows](https://platform.claude.com/docs/en/build-with-claude/context-windows)
- [build-with-claude/compaction](https://platform.claude.com/docs/en/build-with-claude/compaction)
- [build-with-claude/thinking-troubleshooting](https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting)
- [api/errors](https://platform.claude.com/docs/en/api/errors)
- [release-notes/overview](https://platform.claude.com/docs/en/release-notes/overview)
- …and 5 more

### Compliance API session endpoints are documented as read-only — local and remote sessions cannot be deleted through the API — and deletes that the API does perform are immediate, permanent and unrecoverable.

`behavioural` · compliance api · 10 pages

compliance-sessions adds the read-only statement and notes that in organizations using customer-managed encryption keys local session transcripts behave differently; integration patterns now cover exporting remote session transcripts as well as chat content before user deletion; the FAQ states deletes are not recoverable. The API overview adds that every /v1/compliance/* endpoint takes the anthropic-version header, and the curl examples were updated accordingly.

- [manage-claude/compliance-sessions](https://platform.claude.com/docs/en/manage-claude/compliance-sessions)
- [manage-claude/compliance-integration-patterns](https://platform.claude.com/docs/en/manage-claude/compliance-integration-patterns)
- [manage-claude/compliance-faq](https://platform.claude.com/docs/en/manage-claude/compliance-faq)
- [manage-claude/compliance-api](https://platform.claude.com/docs/en/manage-claude/compliance-api)
- [manage-claude/compliance-errors](https://platform.claude.com/docs/en/manage-claude/compliance-errors)
- [manage-claude/compliance-activity-feed](https://platform.claude.com/docs/en/manage-claude/compliance-activity-feed)
- …and 4 more

### ABAC GRANT policies lose their Beta label across the Unity Catalog ABAC pages, and a new page covers using GRANT policies to govern access to models and AI services in system.ai.

`behavioural` · ga · 7 pages

Cross-references now read "ABAC GRANT policies" rather than "ABAC GRANT policies (Beta)". ai-gateway/govern-access-to-models-with-grant-policies is new and uses system or custom governed tags.

- [data-governance/unity-catalog/abac/grant-policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/grant-policies)
- [data-governance/unity-catalog/abac/](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/)
- [data-governance/unity-catalog/abac/common-patterns](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/common-patterns)
- [data-governance/unity-catalog/abac/requirements](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/requirements)
- [data-governance/unity-catalog/abac/best-practices](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/best-practices)
- [release-notes/product/2026/june](https://docs.databricks.com/aws/en/release-notes/product/2026/june)
- …and 1 more

### Fable and Mythos models still require 30-day retention, but the docs now say they are unavailable under zero data retention "unless expressly authorized by Anthropic" rather than flatly unavailable, and 5.1 joins the Covered Models list.

`behavioural` · data retention · 4 pages

api-and-data-retention now designates Claude Fable 5.1, Claude Mythos 5.1, Claude Fable 5 and Claude Mythos 5 as Covered Models. The Fable 5 migration and announcement pages soften the ZDR statement to allow express authorization by Anthropic.

- [manage-claude/api-and-data-retention](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention)
- [models/fable-5/migration-guide](https://platform.claude.com/docs/en/models/fable-5/migration-guide)
- [about-claude/models/introducing-claude-fable-5-and-claude-mythos-5](https://platform.claude.com/docs/en/about-claude/models/introducing-claude-fable-5-and-claude-mythos-5)
- [models/fable-5/introducing-claude-fable-5-and-claude-mythos-5](https://platform.claude.com/docs/en/models/fable-5/introducing-claude-fable-5-and-claude-mythos-5)

### On Claude Fable 5.1 and Claude Mythos 5.1, tool_choice values `any` and `tool` return a 400 error; leave tool_choice at `auto` and set "strict": true instead.

`behavioural` · tool use · 3 pages

claude_api_primer states the 400 explicitly and gives the replacement. define-tools reworks its guidance table for manual extended thinking. parallel-tool-use adds that Fable 5.1 may issue fewer parallel tool calls than earlier models, most noticeably in long agent loops.

- [claude_api_primer](https://platform.claude.com/docs/en/claude_api_primer)
- [agents-and-tools/tool-use/define-tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools)
- [agents-and-tools/tool-use/parallel-tool-use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/parallel-tool-use)

### Changing the top-level effort value or the thinking configuration between requests invalidates the prompt cache.

`behavioural` · prompt caching · 3 pages

The effort guide adds "hold top-level effort constant within cached conversations"; the prompt-caching table gains an "Effort setting" row marked model-specific; the thinking page adds "Configuration changes invalidate caching" covering the thinking configuration and the resolved effort.

- [build-with-claude/effort](https://platform.claude.com/docs/en/build-with-claude/effort)
- [build-with-claude/prompt-caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [build-with-claude/thinking](https://platform.claude.com/docs/en/build-with-claude/thinking)

### After the inference-hooks circuit breaker trips, automatic recovery runs only while your Inference hooks settings are unchanged, and Anthropic retests the server about once a minute starting 10 minutes after the trip.

`behavioural` · reliability · 3 pages

The configuration page says changing any Inference hooks setting after a trip stops automatic recovery; the endpoint page describes the probe cadence. The hooks overview restates that one hook governs claude.ai, Cowork and Claude Code sessions.

- [manage-claude/inference-hooks-configuration](https://platform.claude.com/docs/en/manage-claude/inference-hooks-configuration)
- [manage-claude/inference-hooks-endpoint](https://platform.claude.com/docs/en/manage-claude/inference-hooks-endpoint)
- [manage-claude/inference-hooks](https://platform.claude.com/docs/en/manage-claude/inference-hooks)

### ai_query examples now name the Llama model as `system.ai.llama-4-maverick` instead of the endpoint `databricks-llama-4-maverick`.

`behavioural` · identifier change · 3 pages

The substitution appears in the ai_query reference, read_files and the volume-files tutorial.

- [sql/language-manual/functions/ai_query](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_query)
- [sql/language-manual/functions/read_files](https://docs.databricks.com/aws/en/sql/language-manual/functions/read_files)
- [volumes/volume-files](https://docs.databricks.com/aws/en/volumes/volume-files)

### Lakeflow pipeline unit testing now requires Databricks Runtime 18.1 or above; earlier runtimes do not include the unit testing module.

`behavioural` · requirement · 1 page

The instructions to switch the pipeline channel to Preview in Settings > Advanced settings were replaced by the runtime requirement.

- [ldp/unit-testing](https://docs.databricks.com/aws/en/ldp/unit-testing)

### The deprecation of the `limit`, `offset`, `total_count` and `next_page` fields in /api/2.1/clusters/events moved from October 20, 2026 to November 30, 2026.

`behavioural` · deprecation · 1 page

Only the date changed; the field list is the same.

- [compute/events-api-updates](https://docs.databricks.com/aws/en/compute/events-api-updates)

### The TikTok Ads connector limit changed from "BASIC reports only" to "report data is only supported for reports with fewer than 20,000 ads".

`behavioural` · limits · 1 page

The page attributes the new ceiling to TikTok's synchronous report behaviour.

- [ingestion/lakeflow-connect/tiktok-ads-limits](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/tiktok-ads-limits)

### The Outlook connector's `User.Read.All` / `Directory.Read.All` permission is now described as required only to discover and list all mailboxes in the tenant, when you do not set `include_mailboxes`.

`behavioural` · permissions · 1 page

Previously the permission was listed as required for mailbox discovery unconditionally.

- [ingestion/lakeflow-connect/outlook-source-setup](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/outlook-source-setup)

### A job running continuously for more than 30 days loses access to files under /Workspace and must be restarted at least once to retain access.

`behavioural` · limits · 1 page

This replaces the earlier statement that permission to access files under /Workspace expires after 36 hours for interactive compute and 30 days for jobs.

- [files/workspace](https://docs.databricks.com/aws/en/files/workspace)

### Job performance metrics now require the "Improved Lakeflow Performance Observability" preview to be enabled for the workspace, replacing the earlier Query performance insights access requirement.

`behavioural` · requirement · 1 page

The prerequisite line was rewritten around the new preview.

- [jobs/diagnose-job-performance](https://docs.databricks.com/aws/en/jobs/diagnose-job-performance)

### Databricks Runtime 18 LTS documents a known issue where the Apache Avro fast reader can exhaust executor memory in long-running jobs; the workaround is -Dorg.apache.avro.fastread=false on driver and executors.

`behavioural` · known issue · 1 page

Avro 1.12.1 turns the fast reader on by default in DBR 18 LTS.

- [release-notes/runtime/18](https://docs.databricks.com/aws/en/release-notes/runtime/18)

### Setting delta.deletedFileRetentionDuration below 7 days no longer shortens retention under predictive optimization: data files are still kept for a minimum of 7 days.

`behavioural` · limits · 1 page

A new admonition on the predictive optimization page.

- [optimizations/predictive-optimization](https://docs.databricks.com/aws/en/optimizations/predictive-optimization)

## Additive — 31

### Lakeflow Connect gains managed connectors for Anysphere (Cursor) Audit Logs, Verkada and Glean, plus a page on ingesting files from OneDrive for Business.

`additive` · new connectors · 28 pages

Each connector ships the full set: overview, connection, source setup, pipeline, reference, limits, FAQ and troubleshooting. The SaaS and file connector indexes and the connector FAQ list them.

- [ingestion/lakeflow-connect/anysphere-audit-logs](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs)
- [ingestion/lakeflow-connect/anysphere-audit-logs-connection](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-connection)
- [ingestion/lakeflow-connect/anysphere-audit-logs-faq](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-faq)
- [ingestion/lakeflow-connect/anysphere-audit-logs-limits](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-limits)
- [ingestion/lakeflow-connect/anysphere-audit-logs-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-pipeline)
- [ingestion/lakeflow-connect/anysphere-audit-logs-reference](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-reference)
- …and 22 more

### Claude Fable 5.1 (claude-fable-5-1) and Claude Mythos 5.1 ship with their own overview, migration, prompting and system-prompt pages, and Claude Fable 5 is now listed as "Active (legacy)".

`additive` · new model · 18 pages

A full page set is new: models/fable-5-1/overview, its migration guide and "what's new", models/mythos-5-1/overview (invitation-only through Project Glasswing), a prompting guide, and a published system prompt. The model index, home page, intro, choosing-a-model and the deprecation table all add claude-fable-5-1 (retirement not sooner than September 1, 2027); claude_api_primer prices it at 2x Claude Opus 5 for the hardest long-running agentic and research tasks. models/fable-5/overview now shows status "Active (legacy)".

- [models/fable-5-1/overview](https://platform.claude.com/docs/en/models/fable-5-1/overview)
- [models/fable-5-1/migration-guide](https://platform.claude.com/docs/en/models/fable-5-1/migration-guide)
- [models/fable-5-1/whats-new-fable-5-1](https://platform.claude.com/docs/en/models/fable-5-1/whats-new-fable-5-1)
- [models/mythos-5-1/overview](https://platform.claude.com/docs/en/models/mythos-5-1/overview)
- [home](https://platform.claude.com/docs/en/home)
- [intro](https://platform.claude.com/docs/en/intro)
- …and 12 more

### Databricks Foundation Model APIs add databricks-claude-fable-5-1, Gemini 3.8 Flash, GPT-6 Astra, GLM-5.3 and grok-4-6, with region, rate-limit, vision, reasoning and acceptable-use entries for each.

`additive` · new models · 13 pages

foundation-model-overview lists databricks-grok-4-6 under us-west-2; the supported-models page describes GLM-5.3 as a text-only MoE model from Zhipu AI for coding and agentic tool use and notes that for Claude Fable 5.1 prompts and responses are retained for 30 days for trust and safety, with an opt-out path for customers who opt out of data retention.

- [machine-learning/model-serving/foundation-model-overview](https://docs.databricks.com/aws/en/machine-learning/model-serving/foundation-model-overview)
- [machine-learning/model-serving/function-calling](https://docs.databricks.com/aws/en/machine-learning/model-serving/function-calling)
- [machine-learning/model-serving/acceptable-use-models](https://docs.databricks.com/aws/en/machine-learning/model-serving/acceptable-use-models)
- [machine-learning/model-serving/score-foundation-models](https://docs.databricks.com/aws/en/machine-learning/model-serving/score-foundation-models)
- [machine-learning/model-serving/query-anthropic-messages](https://docs.databricks.com/aws/en/machine-learning/model-serving/query-anthropic-messages)
- [machine-learning/model-serving/query-gemini-api](https://docs.databricks.com/aws/en/machine-learning/model-serving/query-gemini-api)
- …and 7 more

### A new "built-in MCP services" page documents Databricks-provided MCP Services for workspace tools and SaaS apps, and existing MCP server pages were retitled and repointed to it.

`additive` · restructure · 12 pages

The AI Search, Genie Agent and Unity Catalog functions pages are now titled "… MCP server"; the Databricks SQL page recommends the system.ai.dbsql MCP Service; links that pointed at mcp-services#prebuilt now go to built-in-mcp-services.

- [agents/mcp-tools/built-in-mcp-services](https://docs.databricks.com/aws/en/agents/mcp-tools/built-in-mcp-services)
- [agents/mcp-tools/mcp-services](https://docs.databricks.com/aws/en/agents/mcp-tools/mcp-services)
- [agents/mcp-tools/use-mcp-in-agents](https://docs.databricks.com/aws/en/agents/mcp-tools/use-mcp-in-agents)
- [agents/mcp-tools/connect-clients](https://docs.databricks.com/aws/en/agents/mcp-tools/connect-clients)
- [agents/mcp-tools/managed-mcp](https://docs.databricks.com/aws/en/agents/mcp-tools/managed-mcp)
- [agents/mcp-tools/ai-search](https://docs.databricks.com/aws/en/agents/mcp-tools/ai-search)
- …and 6 more

### A new `ai_enrich` SQL function (Beta) generates new columns for each row, and the AI Functions guide is retitled "Transform unstructured data using AI Functions".

`additive` · new function · 12 pages

ai_enrich has its own reference page and is listed in the AI functions table and the alphabetical builtin index; the many pages that linked to "Enrich data using AI Functions" now use the new title.

- [sql/language-manual/functions/ai_enrich](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_enrich)
- [large-language-models/ai-functions](https://docs.databricks.com/aws/en/large-language-models/ai-functions)
- [sql/language-manual/functions/ai_extract](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_extract)
- [sql/language-manual/functions/ai_parse_document](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_parse_document)
- [sql/language-manual/functions/ai_search](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_search)
- [sql/language-manual/sql-ref-functions-builtin-alpha](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-functions-builtin-alpha)
- …and 6 more

### Unity Catalog adds ABAC DENY policies (Beta), which deny the MANAGE ACCESS CONTROL privilege on securable objects and always take precedence over grants.

`additive` · new feature · 11 pages

data-governance/unity-catalog/abac/deny-policies is new. Core concepts explain precedence; the privileges reference notes MANAGE ACCESS CONTROL can be denied through a DENY policy; the hive_metastore DENY statement page now points readers to ABAC DENY policies for Unity Catalog; row filter and column mask pages clarify that they cover UDF-based policies only, with GRANT and DENY handled elsewhere.

- [data-governance/unity-catalog/abac/deny-policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/deny-policies)
- [data-governance/unity-catalog/abac/core-concepts](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/core-concepts)
- [data-governance/unity-catalog/abac/best-practices](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/best-practices)
- [data-governance/unity-catalog/abac/performance](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/performance)
- [data-governance/unity-catalog/abac/policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/policies)
- [data-governance/unity-catalog/abac/policy-evaluation](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/policy-evaluation)
- …and 5 more

### Analytics cost and usage endpoints add Claude Tag (Claude in Slack) fields — a spend category of `engaged` or `proactive` and a Slack user ID attribution field.

`additive` · api field · 10 pages

The Slack user ID (for example U0123ABCDEF) identifies the member the usage is attributed to and is not a claude.ai user ID. The skills analytics display-name field now also covers plugin-delivered skills.

- [api/admin/analytics](https://platform.claude.com/docs/en/api/admin/analytics)
- [api/admin/analytics/cost](https://platform.claude.com/docs/en/api/admin/analytics/cost)
- [api/admin/analytics/cost/list](https://platform.claude.com/docs/en/api/admin/analytics/cost/list)
- [api/admin/analytics/cost/list_by_user](https://platform.claude.com/docs/en/api/admin/analytics/cost/list_by_user)
- [api/admin/analytics/usage](https://platform.claude.com/docs/en/api/admin/analytics/usage)
- [api/admin/analytics/usage/list](https://platform.claude.com/docs/en/api/admin/analytics/usage/list)
- …and 4 more

### Lakebase adds HIPAA support — enablement, audit logging and shared-responsibility pages — and PCI-DSS and HITRUST now cover all AWS regions where Lakebase is available rather than us-east-1 only.

`additive` · compliance · 7 pages

New pages cover enabling HIPAA on workspaces with the compliance security profile, the Business Associate Agreement and shared responsibility for PHI, and how HIPAA audit logs are captured, delivered and queried in the Unity Catalog audit log system table. Release notes state Lakebase is now enabled by default in workspaces with the compliance security profile.

- [oltp/projects/hipaa-compliance](https://docs.databricks.com/aws/en/oltp/projects/hipaa-compliance)
- [oltp/projects/enable-hipaa-compliance](https://docs.databricks.com/aws/en/oltp/projects/enable-hipaa-compliance)
- [oltp/projects/hipaa-audit-logging](https://docs.databricks.com/aws/en/oltp/projects/hipaa-audit-logging)
- [security/privacy/hipaa](https://docs.databricks.com/aws/en/security/privacy/hipaa)
- [oltp/projects/data-protection](https://docs.databricks.com/aws/en/oltp/projects/data-protection)
- [oltp/projects/private-link](https://docs.databricks.com/aws/en/oltp/projects/private-link)
- …and 1 more

### Zerobus Ingest can now write into tables backed by default storage (Public Preview) — the "writing to default storage is not supported" line is gone — and Arrow Flight ingestion loses its Beta admonition wording.

`additive` · preview · 6 pages

The release-stages table adds the default-storage row at Public Preview; zerobus-concepts now says only that Zerobus Ingest writes to managed Delta tables.

- [ingestion/zerobus-concepts](https://docs.databricks.com/aws/en/ingestion/zerobus-concepts)
- [ingestion/zerobus-release-stages](https://docs.databricks.com/aws/en/ingestion/zerobus-release-stages)
- [ingestion/zerobus-overview](https://docs.databricks.com/aws/en/ingestion/zerobus-overview)
- [ingestion/zerobus-ingest](https://docs.databricks.com/aws/en/ingestion/zerobus-ingest)
- [ingestion/zerobus-arrow-flight](https://docs.databricks.com/aws/en/ingestion/zerobus-arrow-flight)
- [ingestion/zerobus-message-types](https://docs.databricks.com/aws/en/ingestion/zerobus-message-types)

### Serverless environment version 6 is documented, with CPU and GPU release notes and a new Standard v6 option in the AI Runtime environment panel.

`additive` · release · 6 pages

The environment version table adds row 6 with its operating system and library set; the version 5 notes restate that the Py4J gateway is off, replacing dbutils.entry_point, and the v5 GPU notes add a top-level ray_init() that enables the Ray dashboard.

- [release-notes/serverless/environment-version/six](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/six)
- [release-notes/serverless/environment-version/six-gpu](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/six-gpu)
- [release-notes/serverless/environment-version/](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/)
- [release-notes/serverless/environment-version/five](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/five)
- [release-notes/serverless/environment-version/five-gpu](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/five-gpu)
- [machine-learning/ai-runtime/environment](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/environment)

### The HubSpot connector now supports ingestion from CRM Hub in Beta, in addition to Marketing Hub.

`additive` · beta · 5 pages

The limits page previously said only Marketing Hub was supported. Source setup lists the extra auth.requiredScopes and the pipeline example ingests marketing_emails plus the CRM Hub contacts table.

- [ingestion/lakeflow-connect/hubspot-limits](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-limits)
- [ingestion/lakeflow-connect/hubspot-overview](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-overview)
- [ingestion/lakeflow-connect/hubspot-source-setup](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-source-setup)
- [ingestion/lakeflow-connect/hubspot-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-pipeline)
- [ingestion/lakeflow-connect/hubspot-reference](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-reference)

### Integrated CDC pipelines can now run in continuous mode; they remain triggered by default and are scheduled with a Lakeflow Jobs task.

`additive` · new feature · 5 pages

A new page covers always-on streaming with scale-optimized or speed-optimized run modes; the MySQL, Oracle and SQL Server integrated-pipeline pages add the "triggered by default" note and link to it.

- [ingestion/lakeflow-connect/continuous-integrated-cdc](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/continuous-integrated-cdc)
- [ingestion/lakeflow-connect/mysql-integrated-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/mysql-integrated-pipeline)
- [ingestion/lakeflow-connect/oracle-integrated-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/oracle-integrated-pipeline)
- [ingestion/lakeflow-connect/sql-server-integrated-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/sql-server-integrated-pipeline)
- [ingestion/lakeflow-connect/common-patterns](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/common-patterns)

### Cross-workspace access (Beta) lets you control which source workspaces can reach a workspace over serverless traffic, as ingress rules on the destination and egress entries in network policies.

`additive` · new feature · 5 pages

A new page documents both sides; the ingress-policy page adds a "Configure cross-workspace access" section and notes a policy left in compatibility mode does not govern cross-workspace ingress. Network policies can list Databricks workspaces as allowed destinations, and calls to external MCP servers egress through the workspace's serverless egress controls.

- [security/network/front-end/cross-workspace-access](https://docs.databricks.com/aws/en/security/network/front-end/cross-workspace-access)
- [security/network/front-end/manage-ingress-policies](https://docs.databricks.com/aws/en/security/network/front-end/manage-ingress-policies)
- [security/network/front-end/context-based-ingress](https://docs.databricks.com/aws/en/security/network/front-end/context-based-ingress)
- [security/network/serverless-network-security/network-policies](https://docs.databricks.com/aws/en/security/network/serverless-network-security/network-policies)
- [security/network/serverless-network-security/](https://docs.databricks.com/aws/en/security/network/serverless-network-security/)

### Unity Gateway Skills let you publish SKILL.md instruction files into a Unity Catalog schema, share them under Unity Catalog grants, and load them in agents via the Unity Gateway CLI or MCP.

`additive` · new feature · 4 pages

New pages cover the concept, authoring and publishing, consuming skills from a coding agent, and governing them (enabling the feature, create/write/read privileges and auditing).

- [agents/uc-skills/](https://docs.databricks.com/aws/en/agents/uc-skills/)
- [agents/uc-skills/create-share-uc-skills](https://docs.databricks.com/aws/en/agents/uc-skills/create-share-uc-skills)
- [agents/uc-skills/use-uc-skills](https://docs.databricks.com/aws/en/agents/uc-skills/use-uc-skills)
- [ai-gateway/govern-skills](https://docs.databricks.com/aws/en/ai-gateway/govern-skills)

### Feature Store adds a SawtoothWindow time-window class that keeps long aggregation windows (30, 60, 90 days) continuously fresh by computing the historic part in a batch pipeline.

`additive` · new feature · 4 pages

The API reference documents the class and notes a sawtooth feature is ready to serve shortly after materialization; the release notes also list a schema registry for streaming sources (Preview) and the streams page covers supplying registry details on the Kafka Unity Catalog connection.

- [machine-learning/feature-store/feature-views-api-reference](https://docs.databricks.com/aws/en/machine-learning/feature-store/feature-views-api-reference)
- [machine-learning/feature-store/feature-views](https://docs.databricks.com/aws/en/machine-learning/feature-store/feature-views)
- [release-notes/feature-store/databricks-feature-store](https://docs.databricks.com/aws/en/release-notes/feature-store/databricks-feature-store)
- [machine-learning/feature-store/streams](https://docs.databricks.com/aws/en/machine-learning/feature-store/streams)

### Git Folder Serverless (Beta) lets notebooks and files in a Git folder share one compute resource and an environment managed by pyproject.toml.

`additive` · beta · 4 pages

A new page under compute/serverless/notebooks documents the experience; the serverless index, notebooks and dependencies pages point to it.

- [compute/serverless/notebooks/git-folder-serverless](https://docs.databricks.com/aws/en/compute/serverless/notebooks/git-folder-serverless)
- [compute/serverless/](https://docs.databricks.com/aws/en/compute/serverless/)
- [compute/serverless/notebooks](https://docs.databricks.com/aws/en/compute/serverless/notebooks)
- [compute/serverless/dependencies](https://docs.databricks.com/aws/en/compute/serverless/dependencies)

### Automatic identity management adds an Okta migration guide and a readiness report that finds external ID and group membership divergences between Databricks and your identity provider.

`additive` · documentation · 4 pages

The existing Entra ID migration page keeps its single-tenant limitation note; the section index was moved.

- [admin/users-groups/automatic-identity-management/migrate-to-aim-okta](https://docs.databricks.com/aws/en/admin/users-groups/automatic-identity-management/migrate-to-aim-okta)
- [admin/users-groups/automatic-identity-management/readiness-report](https://docs.databricks.com/aws/en/admin/users-groups/automatic-identity-management/readiness-report)
- [admin/users-groups/automatic-identity-management/migrate-to-aim](https://docs.databricks.com/aws/en/admin/users-groups/automatic-identity-management/migrate-to-aim)
- [admin/users-groups/automatic-identity-management/](https://docs.databricks.com/aws/en/admin/users-groups/automatic-identity-management/)

### Providers whose cloud storage sits behind a firewall or private endpoint can use SecureConnect, enabled on the provider metastore, for Delta Sharing and Marketplace data products.

`additive` · new feature · 4 pages

create-listing describes enabling SecureConnect on the metastore that hosts your shares, with Marketplace creating a recipient per consumer; the provider page notes SecureConnect does not work with recipients reading through SAP HANA.

- [marketplace/create-listing](https://docs.databricks.com/aws/en/marketplace/create-listing)
- [opensharing/secureconnect-provider](https://docs.databricks.com/aws/en/opensharing/secureconnect-provider)
- [opensharing/create-share](https://docs.databricks.com/aws/en/opensharing/create-share)
- [opensharing/](https://docs.databricks.com/aws/en/opensharing/)

### Dashboard themes gain colour mappings that assign a specific colour to a value by name across widgets, and themes can be exported to JSON for reuse.

`additive` · new feature · 4 pages

Widgets share colours only when they colour by the same field from the same dataset; a field with the same name from a different dataset keeps its own. Dashboard variable field options now show their source dataset as a subtitle, and table cell colour scales gain an "Apply to" choice.

- [dashboards/manage/settings](https://docs.databricks.com/aws/en/dashboards/manage/settings)
- [dashboards/manage/visualizations/](https://docs.databricks.com/aws/en/dashboards/manage/visualizations/)
- [dashboards/manage/filters/dashboard-variables](https://docs.databricks.com/aws/en/dashboards/manage/filters/dashboard-variables)
- [dashboards/manage/visualizations/tables](https://docs.databricks.com/aws/en/dashboards/manage/visualizations/tables)

### Mid-conversation system messages gain a duration control (`"never"` by default, rendered on every request that includes it) and a documented placement constraint.

`additive` · api field · 3 pages

The guide states that a system message carrying text, tool_addition or tool_removal blocks must immediately precede the turn it applies to; the beta Messages and Batches references document the duration field.

- [build-with-claude/mid-conversation-system-messages](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages)
- [api/beta/messages](https://platform.claude.com/docs/en/api/beta/messages)
- [api/beta/messages/batches](https://platform.claude.com/docs/en/api/beta/messages/batches)

### New beta endpoints let you retrieve and update an organization's compliance settings.

`additive` · new endpoints · 3 pages

Three new reference pages under api/beta/organization/compliance_settings.

- [api/beta/organization/compliance_settings](https://platform.claude.com/docs/en/api/beta/organization/compliance_settings)
- [api/beta/organization/compliance_settings/retrieve](https://platform.claude.com/docs/en/api/beta/organization/compliance_settings/retrieve)
- [api/beta/organization/compliance_settings/update](https://platform.claude.com/docs/en/api/beta/organization/compliance_settings/update)

### A Unity Catalog schema can now be backed by AWS Secrets Manager or Azure Key Vault so secret values stay in your own cloud secret manager.

`additive` · new feature · 3 pages

Two new pages describe the concept and the configuration; the Unity Catalog secrets page adds an example passing a retrieved secret to dbutils.credentials.getServiceCredentialsProvider.

- [security/secrets/external-secrets](https://docs.databricks.com/aws/en/security/secrets/external-secrets)
- [security/secrets/configure-external-secrets](https://docs.databricks.com/aws/en/security/secrets/configure-external-secrets)
- [security/secrets/unity-catalog-secrets](https://docs.databricks.com/aws/en/security/secrets/unity-catalog-secrets)

### A new `time_bucket(bucketSize, ts [, origin])` function returns the start of a fixed-width time bucket for a timestamp, aligned to an origin.

`additive` · new function · 3 pages

It has a new reference page and is cross-linked from date_trunc and the builtin function list.

- [sql/language-manual/functions/time_bucket](https://docs.databricks.com/aws/en/sql/language-manual/functions/time_bucket)
- [sql/language-manual/functions/date_trunc](https://docs.databricks.com/aws/en/sql/language-manual/functions/date_trunc)
- [sql/language-manual/sql-ref-functions-builtin](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-functions-builtin)

### A new Agent SDK cookbook builds a scheduled, read-only repository reviewer that resumes its session and returns schema-validated verdicts.

`additive` · tutorial · 2 pages

The cookbook index gains the "Build a scheduled repository reviewer" entry (Aug 2026) under Claude Agent SDK.

- [platform.claude.com/cookbook/claude-agent-sdk-scheduled-repository-reviewer-scheduled-repository-reviewer](https://platform.claude.com/cookbook/claude-agent-sdk-scheduled-repository-reviewer-scheduled-repository-reviewer)
- [platform.claude.com/cookbook/](https://platform.claude.com/cookbook/)

### The Python, TypeScript, Go, Java, Ruby, PHP and C# SDKs now support `code_execution_20260120`.

`additive` · sdk support · 2 pages

Release notes list the new SDK support; the code execution tool page also adds that container signing requires no changes to requests or response handling and that the manifest records nothing about you, your organization or your requests.

- [release-notes/overview](https://platform.claude.com/docs/en/release-notes/overview)
- [agents-and-tools/tool-use/code-execution-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool)

### With `display: "omitted"` on the thinking configuration no thinking_delta events are sent — the thinking block opens, receives a single signature and closes — and message_start behaviour is described under the thinking-binding-controls-2026-08-01 beta.

`additive` · streaming · 2 pages

context-editing also marks the thinking-block-clearing `keep` default as model-specific.

- [build-with-claude/streaming](https://platform.claude.com/docs/en/build-with-claude/streaming)
- [build-with-claude/context-editing](https://platform.claude.com/docs/en/build-with-claude/context-editing)

### OAuth M2M secrets can now be scoped: by default a secret can access every API the service principal is authorized for (all-apis), and a scoped secret restricts it to selected API scopes.

`additive` · new feature · 2 pages

The create-secret flow gains a Scopes step; the service principal page links to the new section.

- [dev-tools/auth/oauth-m2m](https://docs.databricks.com/aws/en/dev-tools/auth/oauth-m2m)
- [admin/users-groups/manage-service-principals](https://docs.databricks.com/aws/en/admin/users-groups/manage-service-principals)

### You can now add, drop or rename columns and widen column types on a streaming table with ALTER TABLE as metadata-only changes, without a full refresh or checkpoint reset.

`additive` · new feature · 2 pages

A new page documents the supported operations; the schema evolution page adds the ALTER TABLE path alongside the existing restart-and-resolve behaviour for renamed source columns.

- [ldp/streaming-table-schema-evolution](https://docs.databricks.com/aws/en/ldp/streaming-table-schema-evolution)
- [data-engineering/schema-evolution](https://docs.databricks.com/aws/en/data-engineering/schema-evolution)

### Path maps can now draw a line by connecting a sequence of Point GEOMETRY values, not only from a single geometry column.

`additive` · new feature · 2 pages

The maps page adds the "Geometry point sequence" option and the visualization types page describes both ways of drawing a path.

- [dashboards/manage/visualizations/maps](https://docs.databricks.com/aws/en/dashboards/manage/visualizations/maps)
- [dashboards/manage/visualizations/types](https://docs.databricks.com/aws/en/dashboards/manage/visualizations/types)

### Priority Tier now lists Claude Fable 5.1 and Claude Mythos 5.1 among the models it does not support, alongside Claude Mythos 5 and Claude Mythos Preview.

`additive` · availability · 1 page

The page previously excluded only Claude Mythos 5 and Claude Mythos Preview from Priority Tier; the new sentence adds the two 5.1 models.

- [api/service-tiers](https://platform.claude.com/docs/en/api/service-tiers)

### Genie Ontology is introduced as a unified context layer combining Unity Catalog semantics with inferred context so Genie One and Genie Code answer with your business meaning.

`additive` · new feature · 1 page

New page under genie/.

- [genie/genie-ontology](https://docs.databricks.com/aws/en/genie/genie-ontology)

## Editorial — 9

### The API reference was regenerated: the anthropic-beta enum grew from "38 more" to "41 more" values, model descriptions were restated, and many field descriptions gained backticks and code formatting.

`editorial` · regeneration · 60 pages

Across roughly 150 reference pages the only change is mechanical — the collapsed beta-header enum count, model blurbs such as "Frontier intelligence for ambitious tasks…", and prose-to-code formatting of values like `satisfied`, `needs_revision`, `active`, `paused` and `deployment_id`. The BetaManagedAgentsModel union also grows from "10 more" to "11 more" entries with claude-fable-5-1 listed first.

- [api/beta](https://platform.claude.com/docs/en/api/beta)
- [api/beta/agents](https://platform.claude.com/docs/en/api/beta/agents)
- [api/beta/agents/archive](https://platform.claude.com/docs/en/api/beta/agents/archive)
- [api/beta/agents/list](https://platform.claude.com/docs/en/api/beta/agents/list)
- [api/beta/agents/retrieve](https://platform.claude.com/docs/en/api/beta/agents/retrieve)
- [api/beta/agents/versions](https://platform.claude.com/docs/en/api/beta/agents/versions)
- …and 54 more

### Admin API curl examples now use $ANTHROPIC_AUTH_TOKEN instead of $ANTHROPIC_OAUTH_TOKEN in the Authorization header.

`editorial` · examples · 53 pages

A sweep across the Admin API reference renames the environment variable used in the sample commands; the header itself is unchanged (Authorization: Bearer <token>).

- [api/admin/api_keys](https://platform.claude.com/docs/en/api/admin/api_keys)
- [api/admin/api_keys/list](https://platform.claude.com/docs/en/api/admin/api_keys/list)
- [api/admin/api_keys/retrieve](https://platform.claude.com/docs/en/api/admin/api_keys/retrieve)
- [api/admin/api_keys/update](https://platform.claude.com/docs/en/api/admin/api_keys/update)
- [api/admin/cost_report](https://platform.claude.com/docs/en/api/admin/cost_report)
- [api/admin/cost_report/retrieve](https://platform.claude.com/docs/en/api/admin/cost_report/retrieve)
- …and 47 more

### Databricks renamed "Unity AI Gateway" to "Unity Gateway" throughout the documentation, including a new release-notes/unity-gateway/ section.

`editorial` · rename · 46 pages

A terminology sweep across the AI Gateway guide, governance, budgets, entitlements and release-notes pages; the product itself and its URLs are unchanged.

- [ai-gateway/](https://docs.databricks.com/aws/en/ai-gateway/)
- [ai-gateway/overview-serving-endpoints](https://docs.databricks.com/aws/en/ai-gateway/overview-serving-endpoints)
- [ai-gateway/ai-governance](https://docs.databricks.com/aws/en/ai-gateway/ai-governance)
- [ai-gateway/agent-services](https://docs.databricks.com/aws/en/ai-gateway/agent-services)
- [ai-gateway/model-services](https://docs.databricks.com/aws/en/ai-gateway/model-services)
- [ai-gateway/govern-model-services](https://docs.databricks.com/aws/en/ai-gateway/govern-model-services)
- …and 40 more

### The single "Use Genie Code" page was split into features-capabilities, agent-mode, navigate-genie-code, web-search and full-page, and links across the corpus were repointed.

`editorial` · restructure · 26 pages

New pages document Genie Code's capabilities, its approval-gated agent mode, the chat pane and full-page command center, and public web search with citations. Dozens of pages now link to genie-code/features-capabilities or genie-code/agent-mode#requirements instead of genie-code/use-genie-code.

- [genie-code/features-capabilities](https://docs.databricks.com/aws/en/genie-code/features-capabilities)
- [genie-code/agent-mode](https://docs.databricks.com/aws/en/genie-code/agent-mode)
- [genie-code/navigate-genie-code](https://docs.databricks.com/aws/en/genie-code/navigate-genie-code)
- [genie-code/web-search](https://docs.databricks.com/aws/en/genie-code/web-search)
- [genie-code/full-page](https://docs.databricks.com/aws/en/genie-code/full-page)
- [genie-code/use-genie-code](https://docs.databricks.com/aws/en/genie-code/use-genie-code)
- …and 20 more

### Cookbook notebooks were bumped from claude-opus-4-1 to claude-opus-4-8.

`editorial` · examples · 18 pages

A mechanical MODEL_NAME / model= substitution across vision, tool-use, misc and third-party integration notebooks.

- [platform.claude.com/cookbook/misc-building-evals](https://platform.claude.com/cookbook/misc-building-evals)
- [platform.claude.com/cookbook/misc-how-to-enable-json-mode](https://platform.claude.com/cookbook/misc-how-to-enable-json-mode)
- [platform.claude.com/cookbook/misc-how-to-make-sql-queries](https://platform.claude.com/cookbook/misc-how-to-make-sql-queries)
- [platform.claude.com/cookbook/multimodal-best-practices-for-vision](https://platform.claude.com/cookbook/multimodal-best-practices-for-vision)
- [platform.claude.com/cookbook/multimodal-getting-started-with-vision](https://platform.claude.com/cookbook/multimodal-getting-started-with-vision)
- [platform.claude.com/cookbook/multimodal-how-to-transcribe-text](https://platform.claude.com/cookbook/multimodal-how-to-transcribe-text)
- …and 12 more

### A phrasing sweep rewrites cross-reference sentences from "For how X…" to "To learn how X…" with no change in content.

`editorial` · copy edit · 16 pages

Mostly the zero-data-retention cross-reference admonition and similar "see also" lines.

- [agents-and-tools/agent-skills/overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [agents-and-tools/tool-use/bash-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/bash-tool)
- [agents-and-tools/tool-use/fine-grained-tool-streaming](https://platform.claude.com/docs/en/agents-and-tools/tool-use/fine-grained-tool-streaming)
- [agents-and-tools/tool-use/memory-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)
- [agents-and-tools/tool-use/text-editor-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/text-editor-tool)
- [agents-and-tools/tool-use/tool-reference](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-reference)
- …and 10 more

### "Databricks Data Intelligence Platform" is being replaced with "Databricks Data + AI Platform" (and "Lakehouse platform") across architecture and getting-started pages.

`editorial` · rename · 14 pages

Naming-only edits; some pages show the raw placeholder "platform-name" in image alt text.

- [lakehouse-architecture/cost-optimization/best-practices](https://docs.databricks.com/aws/en/lakehouse-architecture/cost-optimization/best-practices)
- [lakehouse-architecture/interoperability-and-usability/best-practices](https://docs.databricks.com/aws/en/lakehouse-architecture/interoperability-and-usability/best-practices)
- [lakehouse-architecture/reference](https://docs.databricks.com/aws/en/lakehouse-architecture/reference)
- [migration/warehouse-to-lakehouse](https://docs.databricks.com/aws/en/migration/warehouse-to-lakehouse)
- [introduction/](https://docs.databricks.com/aws/en/introduction/)
- [getting-started/cloud-setup](https://docs.databricks.com/aws/en/getting-started/cloud-setup)
- …and 8 more

### Cookbook install cells switched from the shell escape `!pip` to the `%pip` magic.

`editorial` · examples · 8 pages

Same substitution in several notebooks; deepgram's install cells were rewritten the same way.

- [platform.claude.com/cookbook/capabilities-classification-guide](https://platform.claude.com/cookbook/capabilities-classification-guide)
- [platform.claude.com/cookbook/capabilities-contextual-embeddings-guide](https://platform.claude.com/cookbook/capabilities-contextual-embeddings-guide)
- [platform.claude.com/cookbook/capabilities-summarization-guide](https://platform.claude.com/cookbook/capabilities-summarization-guide)
- [platform.claude.com/cookbook/capabilities-retrieval-augmented-generation-guide](https://platform.claude.com/cookbook/capabilities-retrieval-augmented-generation-guide)
- [platform.claude.com/cookbook/finetuning-finetuning-on-bedrock](https://platform.claude.com/cookbook/finetuning-finetuning-on-bedrock)
- [platform.claude.com/cookbook/misc-sampling-past-max-tokens](https://platform.claude.com/cookbook/misc-sampling-past-max-tokens)
- …and 2 more

### Install snippets move to anthropic-java 2.60.0 (and anthropic-java-aws 2.60.0) and CLI VERSION=1.30.0; the C# SDK beta note is reworded to explain its 10+ version number.

`editorial` · version bump · 5 pages

The C# page now says that although the package is versioned as 10+ it is currently in beta and breaking changes may occur in minor or patch releases.

- [cli-sdks-libraries/cli/quickstart](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/quickstart)
- [cli-sdks-libraries/sdks/java](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/java)
- [get-started](https://platform.claude.com/docs/en/get-started)
- [build-with-claude/claude-platform-on-aws](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws)
- [cli-sdks-libraries/sdks/csharp](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/csharp)
