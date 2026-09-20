# Change digest

> #6 (2026-09-09) → #7 (2026-09-18) · 6,329 changes · rendered 2026-09-20T19:32:15+00:00

## At a glance

72 findings — **4** breaking, **17** behavioural, **38** additive, **13** editorial — covering 443 of 6,329 changed pages. Anything not here is in the full feed report beside this file.

**If you read nothing else:**

1. The partner-powered AI features toggle can no longer be turned off in the settings UI where it is enabled, and the setting is removed from all workspaces and the API on 2026-11-01.
2. From 2026-09-19 Anthropic models are removed from AWS GovCloud and AWS GovCloud DoD workspaces with DoD IL5 selected; such workspaces can't create or use endpoints serving Anthropic models.
3. Lakebase scale to zero is now documented as available only for computes of 32 CU or smaller — for an autoscaling compute, the maximum size must be 32 CU or smaller.
4. The September release notes state that unused OAuth client secrets are automatically deleted after 90 days.

---

## Breaking — 4

### The partner-powered AI features toggle can no longer be turned off in the settings UI where it is enabled, and the setting is removed from all workspaces and the API on 2026-11-01.

`breaking` · setting-removal · 3 pages

Per the page: workspaces with the setting enabled already have the account and workspace toggles disabled, so you can no longer disable it in the settings page; workspaces with it disabled can still enable it. Until November 1, 2026 the Settings API can still enable or disable it. After that date the setting is removed from all workspaces and the API, each workspace keeps its current value, and changing it requires contacting your Databricks account team.

- [databricks-ai/partner-powered](https://docs.databricks.com/aws/en/databricks-ai/partner-powered)
- [release-notes/product/](https://docs.databricks.com/aws/en/release-notes/product/)
- [release-notes/product/2026/september](https://docs.databricks.com/aws/en/release-notes/product/2026/september)

### From 2026-09-19 Anthropic models are removed from AWS GovCloud and AWS GovCloud DoD workspaces with DoD IL5 selected; such workspaces can't create or use endpoints serving Anthropic models.

`breaking` · model-removal · 1 page

The page tells affected customers to migrate endpoints to another supported model before September 19, 2026.

- [security/privacy/il5](https://docs.databricks.com/aws/en/security/privacy/il5)

### Lakebase scale to zero is now documented as available only for computes of 32 CU or smaller — for an autoscaling compute, the maximum size must be 32 CU or smaller.

`breaking` · restriction · 3 pages

The API section adds that setting a suspend timeout on a larger compute returns an error, and the autoscaling page says you can't enable scale to zero if you set a maximum larger than 32 CU.

- [oltp/projects/manage-computes](https://docs.databricks.com/aws/en/oltp/projects/manage-computes)
- [oltp/projects/autoscaling](https://docs.databricks.com/aws/en/oltp/projects/autoscaling)
- [oltp/projects/scale-to-zero](https://docs.databricks.com/aws/en/oltp/projects/scale-to-zero)

### The September release notes state that unused OAuth client secrets are automatically deleted after 90 days.

`breaking` · credential-lifecycle · 2 pages

Recorded from the release-notes index entry; check the September page for the exact scope and start date before acting.

- [release-notes/product/](https://docs.databricks.com/aws/en/release-notes/product/)
- [release-notes/product/2026/september](https://docs.databricks.com/aws/en/release-notes/product/2026/september)

## Behavioural — 17

### Claude Platform on AWS now states that Anthropic processes requests and stores workspace content on AWS infrastructure, except for workspaces created before 2026-09-18 00:00 UTC.

`behavioural` · data-residency · 1 page

The page previously said data might not reside in AWS and inference might route to Anthropic's primary cloud. It now says AWS infrastructure is used for request processing, inference and storage of workspace content (prompts, outputs, files, Skills, batches), and that for workspaces created before September 18, 2026, 00:00 UTC Anthropic might still process and store that content outside AWS. Subservices may still change without notice.

- [build-with-claude/claude-platform-on-aws](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws)

### Claude Platform on AWS organizations can now advance usage tiers automatically as they build a history of paid AWS Marketplace invoices; both pages previously said tier advancement did not apply.

`behavioural` · rate-limits · 2 pages

The self-service **Request rate limit increase** flow in the Console is still unavailable; the Rate limits page still directs you to your Anthropic account representative. Per-workspace rate limit configuration and fast mode remain unavailable on Claude Platform on AWS.

- [build-with-claude/claude-platform-on-aws](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws)
- [api/rate-limits](https://platform.claude.com/docs/en/api/rate-limits)

### The Java cloud-platform artifacts are now documented as add-ons to the base `com.anthropic:anthropic-java` dependency — install both, not just the platform artifact.

`behavioural` · sdk-packaging · 2 pages

The Java SDK page now says the platform artifacts are add-ons to the base dependency, which provides `AnthropicOkHttpClient`, "so install both". The Claude Platform on AWS install snippet correspondingly lists both `anthropic-java` and `anthropic-java-aws` in Gradle and Maven, where before it listed only the `-aws` artifact.

- [cli-sdks-libraries/sdks/java](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/java)
- [build-with-claude/claude-platform-on-aws](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws)

### The Compliance API's 403 scope error message changed wording from `Needed: [...]` to `Needed one of: [...]`.

`behavioural` · error-message · 1 page

Clients that match on the literal error string will need updating; the status code and the Got/Needed structure are otherwise unchanged.

- [manage-claude/compliance-api-access](https://platform.claude.com/docs/en/manage-claude/compliance-api-access)

### The SQL Server integrated CDC connector leaves Beta: `"channel": "PREVIEW"` is no longer required in the pipeline spec and workspace-level enablement is no longer listed.

`behavioural` · ga · 2 pages

`channel` is now documented as optional, defaulting to `CURRENT`, with `PREVIEW` available for early access. The Beta callout, the workspace-enablement limitation, the "channel must be PREVIEW" limitation and the related troubleshooting step were all removed, and PREVIEW was dropped from every example spec.

- [ingestion/lakeflow-connect/sql-server-integrated-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/sql-server-integrated-pipeline)
- [ingestion/lakeflow-connect/sql-server-overview](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/sql-server-overview)

### Databricks Apps is now on by default for workspaces with the compliance security profile enabled, instead of requiring a workspace admin to enable it from the Previews page.

`behavioural` · default-change · 4 pages

The docs say this applies in all regions where the selected compliance standards are supported.

- [dev-tools/databricks-apps/](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/)
- [security/privacy/security-profile](https://docs.databricks.com/aws/en/security/privacy/security-profile)
- [release-notes/product/](https://docs.databricks.com/aws/en/release-notes/product/)
- [release-notes/product/2026/september](https://docs.databricks.com/aws/en/release-notes/product/2026/september)

### The Unity Catalog thread-pool limitation is rewritten: it is now scoped to dedicated compute and explicitly names `ForkJoinPool` and Scala parallel collections (`.par`) as unsupported.

`behavioural` · restriction · 2 pages

Supported pools are given as `ThreadUtils.newDaemonFixedThreadPool` and `ThreadUtils.newDaemonCachedThreadPool`; unsupported ones now include `ForkJoinPool`, `.par`, `ThreadUtils.newForkJoinPool` and any `ScheduledExecutorService` pool. The previous text banned "standard Scala thread pools" without naming parallel collections and without scoping to dedicated compute.

- [data-governance/unity-catalog/requirements](https://docs.databricks.com/aws/en/data-governance/unity-catalog/requirements)
- [jobs/tasks/jar-create](https://docs.databricks.com/aws/en/jobs/tasks/jar-create)

### The `2.0/jobs/list` endpoint is now marked deprecated, with Databricks recommending Jobs API 2.2 for new and existing clients.

`behavioural` · deprecation · 1 page

The page links the 2.0→2.1 and 2.1→2.2 update guides.

- [reference/jobs-2.0-api](https://docs.databricks.com/aws/en/reference/jobs-2.0-api)

### Moonshot AI Kimi K2.7 is scheduled for retirement on pay-per-token from 2026-10-30, with Kimi K3 named as the replacement.

`behavioural` · deprecation · 3 pages

- [machine-learning/retired-models-policy](https://docs.databricks.com/aws/en/machine-learning/retired-models-policy)
- [release-notes/product/](https://docs.databricks.com/aws/en/release-notes/product/)
- [release-notes/product/2026/september](https://docs.databricks.com/aws/en/release-notes/product/2026/september)

### AI Runtime tutorials now target the Databricks AI v6 environment instead of AI v5, and several state they require environment version 6 or above.

`behavioural` · version-bump · 15 pages

The Ray page now says AI v6 includes Ray and that on Standard v6 you must install Ray before calling `ray_init()`. The GPU environment version 6 notes bump the Serverless GPU Python API from 0.5.24 to 0.5.25.

- [machine-learning/ai-runtime/environment](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/environment)
- [machine-learning/ai-runtime/examples/tutorials/sgc-distributed-pytorch-fsdp](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-distributed-pytorch-fsdp)
- [machine-learning/ai-runtime/examples/tutorials/sgc-sft-trl-deepspeed-llama-1b](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-sft-trl-deepspeed-llama-1b)
- [machine-learning/ai-runtime/examples/tutorials/sgc-recommender-system-lightning](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-recommender-system-lightning)
- [machine-learning/ai-runtime/examples/tutorials/sgc-api-h100-starter](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-api-h100-starter)
- [machine-learning/ai-runtime/examples/tutorials/sgc-distributed-gpt-oss-20b](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-distributed-gpt-oss-20b)
- …and 9 more

### Managed tables in Lakeflow pipelines (Beta): `create_table` and `CREATE TABLE ... FLOW` cannot adopt an existing managed table — the target must be a new managed table.

`behavioural` · restriction · 4 pages

- [ldp/developer/ldp-python-ref-create-table](https://docs.databricks.com/aws/en/ldp/developer/ldp-python-ref-create-table)
- [ldp/developer/ldp-sql-ref-create-table-flow](https://docs.databricks.com/aws/en/ldp/developer/ldp-sql-ref-create-table-flow)
- [release-notes/product/](https://docs.databricks.com/aws/en/release-notes/product/)
- [release-notes/product/2026/september](https://docs.databricks.com/aws/en/release-notes/product/2026/september)

### Databricks Runtime 18.1 (and 18.1 ML) and Databricks Runtime 13.3 LTS (and 13.3 LTS ML) are now marked end-of-support, with titles renamed "(EoS)" and maintenance-update links repointed to the archive.

`behavioural` · end-of-support · 14 pages

Pages carry a banner saying support for this Databricks Runtime version has ended and pointing to the end-of-support and end-of-life history.

- [release-notes/runtime/18.1](https://docs.databricks.com/aws/en/release-notes/runtime/18.1)
- [release-notes/runtime/18.1ml](https://docs.databricks.com/aws/en/release-notes/runtime/18.1ml)
- [release-notes/runtime/13.3lts](https://docs.databricks.com/aws/en/release-notes/runtime/13.3lts)
- [release-notes/runtime/13.3lts-ml](https://docs.databricks.com/aws/en/release-notes/runtime/13.3lts-ml)
- [release-notes/product/2026/march](https://docs.databricks.com/aws/en/release-notes/product/2026/march)
- [release-notes/product/2025/december](https://docs.databricks.com/aws/en/release-notes/product/2025/december)
- …and 8 more

### The row-tracking-based feature requirement is relaxed from "Databricks Runtime 19 LTS or above" to "Databricks Runtime 19 or above", and "Delta Lake Sharing" is renamed "Delta Sharing".

`behavioural` · requirement-change · 3 pages

The feature still requires row tracking enabled and works with batch queries, Structured Streaming and Delta Sharing.

- [release-notes/runtime/19](https://docs.databricks.com/aws/en/release-notes/runtime/19)
- [release-notes/product/2026/september](https://docs.databricks.com/aws/en/release-notes/product/2026/september)
- [release-notes/whats-coming](https://docs.databricks.com/aws/en/release-notes/whats-coming)

### The private-connectivity Beta callouts now name the previews you must enable: Front-end Private Link for Custom URLs and Account for account-level resources and Context-Based Ingress: Workspace Private Access Policies for workspace private access.

`behavioural` · preview-enablement · 4 pages

Previously the notes said only that the capability was in Beta. The service-direct page adds that you should enable it only after registration completes, because requests are rejected until then.

- [security/network/classic/privatelink-dns](https://docs.databricks.com/aws/en/security/network/classic/privatelink-dns)
- [security/network/front-end/front-end-private-connect-account](https://docs.databricks.com/aws/en/security/network/front-end/front-end-private-connect-account)
- [security/network/front-end/front-end-private-connect](https://docs.databricks.com/aws/en/security/network/front-end/front-end-private-connect)
- [security/network/front-end/service-direct-privatelink](https://docs.databricks.com/aws/en/security/network/front-end/service-direct-privatelink)

### Dropping a base table referenced by a shallow clone can now fail with `CANNOT_DROP_BASE_TABLE_REFERENCED_BY_SHALLOW_CLONE` where the workspace enforces drop-time protection, and `FORCE` is required in that case.

`behavioural` · restriction · 5 pages

The docs say `FORCE` is required only where the workspace enforces drop-time protection for shallow clones, and that shallow clones can keep reading for a time after the base table is no longer recoverable. The object-storage lifecycle page now says an asynchronous purge permanently deletes data files after the 7-day recovery window.

- [sql/language-manual/sql-ref-syntax-ddl-drop-table](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-ddl-drop-table)
- [tables/operations/clone-unity-catalog](https://docs.databricks.com/aws/en/tables/operations/clone-unity-catalog)
- [tables/operations/drop-table](https://docs.databricks.com/aws/en/tables/operations/drop-table)
- [tables/managed](https://docs.databricks.com/aws/en/tables/managed)
- [data-governance/unity-catalog/object-storage-lifecycle](https://docs.databricks.com/aws/en/data-governance/unity-catalog/object-storage-lifecycle)

### System table retention becomes configurable by account admins (Beta), and deleting a workspace now removes that workspace's audit events older than 14 days from `system.access.audit`.

`behavioural` · retention · 2 pages

Configuring retention requires account admin.

- [admin/system-tables/](https://docs.databricks.com/aws/en/admin/system-tables/)
- [admin/system-tables/audit-logs](https://docs.databricks.com/aws/en/admin/system-tables/audit-logs)

### Using a default-storage-backed catalog for AI Gateway inference tables or the unified trace table now requires a workspace admin to enable Zerobus Ingest Default Storage in Settings > Previews.

`behavioural` · preview-enablement · 2 pages

The inference tables page previously required the catalog to be an external storage catalog with `CREATE TABLE` privileges.

- [ai-gateway/inference-tables](https://docs.databricks.com/aws/en/ai-gateway/inference-tables)
- [ai-gateway/unified-trace-table](https://docs.databricks.com/aws/en/ai-gateway/unified-trace-table)

## Additive — 38

### Tool names may now be up to 128 characters: the `name` regex changed from `^[a-zA-Z0-9_-]{1,64}$` to `^[a-zA-Z0-9_-]{1,128}$`.

`additive` · limit-change · 2 pages

Both the tool-definition reference and the API primer table now document the wider bound. Names that were already valid remain valid.

- [agents-and-tools/tool-use/define-tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools)
- [claude_api_primer](https://platform.claude.com/docs/en/claude_api_primer)

### A new `compact-2026-09-04` beta adds on-demand compaction: send a top-level `compaction` parameter and the API returns a signed `compaction` block that replaces the messages it summarizes.

`additive` · beta-feature · 5 pages

The compaction page adds a full section. Key points as written: the response contains the block and no reply, with `stop_reason: "compaction"`; on later requests the signed block must be sent first, in place of the summarized messages, and leaving those messages in front of the signed block is a 400 error; `compaction` cannot be combined with `context_management` in one request. The page says on-demand compaction is available on the Claude API but not on Amazon Bedrock or Google Cloud, and lists the supported models (Fable 5.1/5, Mythos 5.1/5 and Preview, Opus 5/4.8/4.7/4.6, Sonnet 5/4.6). The Models API beta now exposes `capabilities.compaction` (`BetaCompactionCapability or null`).

- [build-with-claude/compaction](https://platform.claude.com/docs/en/build-with-claude/compaction)
- [release-notes/overview](https://platform.claude.com/docs/en/release-notes/overview)
- [api/beta/models](https://platform.claude.com/docs/en/api/beta/models)
- [api/beta/models/list](https://platform.claude.com/docs/en/api/beta/models/list)
- [api/beta/models/retrieve](https://platform.claude.com/docs/en/api/beta/models/retrieve)

### The `anthropic-workspace-id` header is now documented as an optional header on the Files, Skills and Message Batches endpoints, and Claude Platform on AWS now scopes it to inference and resource requests only.

`additive` · documentation · 21 pages

The Claude Platform on AWS page now says the header is required on inference and resource requests such as Messages, Models, Files and Managed Agents calls, and that Admin API workspace and external key endpoints don't require it (create and list act on the organization; get, update and archive take the workspace ID in the path).

- [build-with-claude/claude-platform-on-aws](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws)
- [api/files](https://platform.claude.com/docs/en/api/files)
- [api/files/list](https://platform.claude.com/docs/en/api/files/list)
- [api/files/upload](https://platform.claude.com/docs/en/api/files/upload)
- [api/files/delete](https://platform.claude.com/docs/en/api/files/delete)
- [api/files/download](https://platform.claude.com/docs/en/api/files/download)
- …and 15 more

### The Opus 5 migration guide now lists Claude Platform on AWS among the platforms where the 1M context window is the default and no context-window beta header is needed.

`additive` · availability · 1 page

The list previously read Claude API, Amazon Bedrock, Google Cloud and Microsoft Foundry.

- [models/opus-5/migration-guide](https://platform.claude.com/docs/en/models/opus-5/migration-guide)

### Per-message effort via `output_config.effort` on a mid-conversation system message is now available on Google Cloud as well as the Claude API, with the same `mid-conversation-output-config-2026-07-01` beta header.

`additive` · availability · 2 pages

Still beta and still limited to Claude Fable 5.1, Claude Mythos 5.1 and Claude Opus 5. The same page also notes that referencing an undeclared tool name in `tool_addition`/`tool_removal` returns a 400 with `error.details.error_code` set to `tool_reference_unresolved` on the Claude API, and that mid-conversation tool changes carry one extra placement restriction after a paused turn.

- [build-with-claude/mid-conversation-system-messages](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages)
- [release-notes/overview](https://platform.claude.com/docs/en/release-notes/overview)

### Claude Managed Agents permission policies gain an `auto` mode in which the server evaluates each agent or MCP tool call and runs, denies, or pauses it for approval.

`additive` · beta-feature · 12 pages

`agent.tool_use` and `agent.mcp_tool_use` events now report how each call was evaluated in an `evaluation` field alongside `evaluated_permission`. The API reference text adds that a call the server cannot reach a judgement on evaluates to `ask`. The policy page also states that when the server denies a call the session keeps running and the client cannot override the denial.

- [managed-agents/permission-policies](https://platform.claude.com/docs/en/managed-agents/permission-policies)
- [managed-agents/events-and-streaming](https://platform.claude.com/docs/en/managed-agents/events-and-streaming)
- [release-notes/overview](https://platform.claude.com/docs/en/release-notes/overview)
- [api/beta/agents](https://platform.claude.com/docs/en/api/beta/agents)
- [api/beta/agents/create](https://platform.claude.com/docs/en/api/beta/agents/create)
- [api/beta/agents/update](https://platform.claude.com/docs/en/api/beta/agents/update)
- …and 6 more

### `ant beta:sessions connect` (CLI 1.32.0) attaches your terminal to a Claude Managed Agents session to follow it live, send messages, and allow or deny pending tool calls.

`additive` · cli · 2 pages

A new page documents the command; `--web` serves the Claude Console session viewer locally and opens the session there instead.

- [cli-sdks-libraries/cli/sessions-connect](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/sessions-connect)
- [release-notes/overview](https://platform.claude.com/docs/en/release-notes/overview)

### Compliance API local-session endpoints now also return Claude in Chrome transcripts, under the `product_surface` value `claude_in_chrome`.

`additive` · compliance-api · 7 pages

In beta for Claude Enterprise organizations, using an existing Compliance Access Key with the `read:compliance_user_data` scope; the release note says no new key, scope, setting or client update is required. The local session list/retrieve schemas also document a truncation flag for sessions with more than 100,000 inference calls.

- [release-notes/overview](https://platform.claude.com/docs/en/release-notes/overview)
- [manage-claude/compliance-sessions](https://platform.claude.com/docs/en/manage-claude/compliance-sessions)
- [api/compliance/apps/sessions/local](https://platform.claude.com/docs/en/api/compliance/apps/sessions/local)
- [api/compliance/apps/sessions/local/list](https://platform.claude.com/docs/en/api/compliance/apps/sessions/local/list)
- [api/compliance/apps/sessions/local/retrieve](https://platform.claude.com/docs/en/api/compliance/apps/sessions/local/retrieve)
- [api/compliance/apps/sessions/local/messages](https://platform.claude.com/docs/en/api/compliance/apps/sessions/local/messages)
- …and 1 more

### A large set of Admin API surfaces — analytics, RBAC groups and roles, spend limits, MCP tunnels, usage and cost reports — now also appear under `api/beta/organization/*`.

`additive` · api-reference · 25 pages

These reference pages are new in this run and mirror the existing `api/admin/*` endpoints. Nothing indicates the `api/admin/*` pages were removed; they were modified in the same run.

- [api/beta/organization/analytics](https://platform.claude.com/docs/en/api/beta/organization/analytics)
- [api/beta/organization/analytics/usage](https://platform.claude.com/docs/en/api/beta/organization/analytics/usage)
- [api/beta/organization/analytics/cost](https://platform.claude.com/docs/en/api/beta/organization/analytics/cost)
- [api/beta/organization/analytics/users](https://platform.claude.com/docs/en/api/beta/organization/analytics/users)
- [api/beta/organization/analytics/skills](https://platform.claude.com/docs/en/api/beta/organization/analytics/skills)
- [api/beta/organization/analytics/connectors](https://platform.claude.com/docs/en/api/beta/organization/analytics/connectors)
- …and 19 more

### The Compliance API organization-settings enum grew from 52 to 57 additional values and now leads with `access_transparency_enabled`.

`additive` · enum-change · 3 pages

Listed as `"access_transparency_enabled" or "ai_powered_artifacts_enabled" or "api_workbench_feedback_collection_enabled" or 57 more`, up from a list starting at `ai_powered_artifacts_enabled` with 52 more.

- [api/compliance/organizations](https://platform.claude.com/docs/en/api/compliance/organizations)
- [api/compliance/organizations/settings](https://platform.claude.com/docs/en/api/compliance/organizations/settings)
- [api/compliance/organizations/settings/retrieve](https://platform.claude.com/docs/en/api/compliance/organizations/settings/retrieve)

### The Compliance API `organization_role` enum grew from "6 more" to "8 more" values beyond admin, billing and claude_code_user.

`additive` · enum-change · 2 pages

The page does not name the added roles.

- [api/compliance/organizations/users](https://platform.claude.com/docs/en/api/compliance/organizations/users)
- [api/compliance/organizations/users/list](https://platform.claude.com/docs/en/api/compliance/organizations/users/list)

### IL5 compliance controls are now available on Databricks for AWS GovCloud as well as AWS GovCloud DoD, and serverless SQL warehouses on GovCloud DoD move from Beta to Public Preview.

`additive` · availability · 1 page

The compliance security profile is enabled by default on both environments. Only AWS GovCloud DoD is connected to NIPRNet.

- [security/privacy/il5](https://docs.databricks.com/aws/en/security/privacy/il5)

### Zerobus writes to liquid clustered tables move from Beta to Generally Available.

`additive` · ga · 3 pages

The Beta markers on the liquid-clustered-tables sections were dropped and the release-stages table now shows Generally Available. The C# / .NET SDK remains in Beta.

- [ingestion/zerobus-quotas](https://docs.databricks.com/aws/en/ingestion/zerobus-quotas)
- [ingestion/zerobus-features](https://docs.databricks.com/aws/en/ingestion/zerobus-features)
- [ingestion/zerobus-release-stages](https://docs.databricks.com/aws/en/ingestion/zerobus-release-stages)

### Scheduling notebooks moves from Beta to Public Preview, and the note about workspace admins controlling access was dropped.

`additive` · ga · 1 page

- [notebooks/schedule-notebook-jobs](https://docs.databricks.com/aws/en/notebooks/schedule-notebook-jobs)

### The Databricks Excel Add-in is now generally available; the Public Preview callouts were removed from the Excel pages.

`additive` · ga · 7 pages

The setup page now says to ensure a workspace admin has enabled the Excel Connector preview rather than requiring it as a prerequisite step.

- [integrations/excel](https://docs.databricks.com/aws/en/integrations/excel)
- [integrations/excel-genie](https://docs.databricks.com/aws/en/integrations/excel-genie)
- [integrations/excel-write-back](https://docs.databricks.com/aws/en/integrations/excel-write-back)
- [integrations/excel-query](https://docs.databricks.com/aws/en/integrations/excel-query)
- [integrations/excel-setup](https://docs.databricks.com/aws/en/integrations/excel-setup)
- [release-notes/product/](https://docs.databricks.com/aws/en/release-notes/product/)
- …and 1 more

### ABAC gains metastore-level policies and DENY policies in Beta: a new page documents attaching policies `ON METASTORE`, and GRANT/DENY syntax now accepts `METASTORE | CATALOG | SCHEMA` scopes.

`additive` · beta-feature · 11 pages

Dropping a policy `ON METASTORE` (Beta) requires being a metastore admin. Creating, modifying or dropping an ABAC GRANT or DENY policy with SQL requires Databricks Runtime 18 LTS or above. The grant-policies page adds a limit of 100 policies per metastore attached directly (Beta).

- [data-governance/unity-catalog/abac/metastore-policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/metastore-policies)
- [data-governance/unity-catalog/abac/deny-policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/deny-policies)
- [data-governance/unity-catalog/abac/](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/)
- [data-governance/unity-catalog/abac/policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/policies)
- [data-governance/unity-catalog/abac/grant-policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/grant-policies)
- [data-governance/unity-catalog/abac/best-practices](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/best-practices)
- …and 5 more

### ABAC row filter and column mask policies can now apply to views via an ABAC on Views preview that an account admin enables from the account console Previews page.

`additive` · beta-feature · 2 pages

The requirements page also notes that columns with governed tags cannot be dropped until the tags are removed, as with base tables.

- [data-governance/unity-catalog/abac/requirements](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/requirements)
- [data-governance/unity-catalog/abac/core-concepts](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/core-concepts)

### Data Classification now scans Unity Catalog views (Beta) once a workspace admin turns on the Data Classification View Scanning preview, and a dedicated Data Classification release-notes page was added.

`additive` · beta-feature · 4 pages

Views whose definitions can't be handled are reported with status `UNSUPPORTED_VIEW_DEFINITION`.

- [data-governance/unity-catalog/data-classification](https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-classification)
- [release-notes/data-classification/](https://docs.databricks.com/aws/en/release-notes/data-classification/)
- [release-notes/product/](https://docs.databricks.com/aws/en/release-notes/product/)
- [release-notes/product/2026/september](https://docs.databricks.com/aws/en/release-notes/product/2026/september)

### DeepSeek V4.1 Flash is now available on Foundation Model APIs and Unity Gateway, with entries in the supported-models, limits, function-calling, vision and acceptable-use pages.

`additive` · new-model · 8 pages

Described as a multimodal mixture-of-experts model with 552 billion backbone parameters, hosted by Databricks, supporting adjustable reasoning effort; the limits table lists 200,000 context, 10,000 output tokens and 7,200 queries per minute.

- [machine-learning/foundation-model-apis/supported-models](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/supported-models)
- [machine-learning/foundation-model-apis/limits](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/limits)
- [machine-learning/foundation-model-apis/priority-mode](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/priority-mode)
- [machine-learning/model-serving/function-calling](https://docs.databricks.com/aws/en/machine-learning/model-serving/function-calling)
- [machine-learning/model-serving/query-vision-models](https://docs.databricks.com/aws/en/machine-learning/model-serving/query-vision-models)
- [machine-learning/model-serving/acceptable-use-models](https://docs.databricks.com/aws/en/machine-learning/model-serving/acceptable-use-models)
- …and 2 more

### Genie Agent limits are raised: up to 50 tables, views or metric views per agent (was 30) and a 200,000 conversation limit (was 10,000).

`additive` · limit-change · 3 pages

The best-practices guidance to prejoin tables into views now kicks in above 50 tables rather than 30.

- [genie-agents/set-up](https://docs.databricks.com/aws/en/genie-agents/set-up)
- [genie-agents/best-practices](https://docs.databricks.com/aws/en/genie-agents/best-practices)
- [genie-agents/conversation-api](https://docs.databricks.com/aws/en/genie-agents/conversation-api)

### Genie Agent PDF uploads now allow up to 100 pages (was 20) and require only CAN VIEW on the agent instead of CAN RUN.

`additive` · limit-change · 1 page

The 20 MB size cap and 15,000 character limit are unchanged, and the FAQ no longer lists missing CAN RUN permission as a reason the upload option is unavailable.

- [genie-agents/file-upload](https://docs.databricks.com/aws/en/genie-agents/file-upload)

### Sharing foreign schemas and tables — including foreign Delta and foreign Iceberg tables — with OpenSharing is now generally available, and shareable views can be defined on foreign tables.

`additive` · ga · 5 pages

The create-share page adds that foreign Iceberg tables shared with open recipients not using Iceberg clients must use default storage.

- [opensharing/create-share](https://docs.databricks.com/aws/en/opensharing/create-share)
- [opensharing/](https://docs.databricks.com/aws/en/opensharing/)
- [data-governance/unity-catalog/abac/opensharing](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/opensharing)
- [release-notes/product/](https://docs.databricks.com/aws/en/release-notes/product/)
- [release-notes/product/2026/september](https://docs.databricks.com/aws/en/release-notes/product/2026/september)

### Five new managed Lakeflow Connect connectors arrive in Beta — Anaplan, Anysphere Organization (Cursor), Atlassian Audit Logs, Celigo and Google Workspace — each with a full page set.

`additive` · new-connector · 42 pages

The SaaS overview and connector FAQ index were updated to list them. Google Workspace ingests activity events from 33 application audit logs; Celigo and Atlassian ingest audit log events; Anaplan ingests audit trail events and user account records.

- [ingestion/lakeflow-connect/anaplan](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anaplan)
- [ingestion/lakeflow-connect/anaplan-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anaplan-pipeline)
- [ingestion/lakeflow-connect/anaplan-connection](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anaplan-connection)
- [ingestion/lakeflow-connect/anaplan-source-setup](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anaplan-source-setup)
- [ingestion/lakeflow-connect/anaplan-reference](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anaplan-reference)
- [ingestion/lakeflow-connect/anaplan-limits](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anaplan-limits)
- …and 36 more

### The Google Drive connector's setup is split into three documented authentication methods, including a new Databricks-managed OAuth U2M option that needs no Google Cloud project or app registration.

`additive` · authentication · 9 pages

The other two are custom-managed OAuth U2M (bring your own Google Cloud app, for control over app ownership and API rate limiting) and an OAuth service account key. The source-setup page now routes to a new page per method, and the FAQ and troubleshooting pages were updated accordingly.

- [ingestion/lakeflow-connect/google-drive-source-setup](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/google-drive-source-setup)
- [ingestion/lakeflow-connect/google-drive-source-setup-u2m-databricks-managed](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/google-drive-source-setup-u2m-databricks-managed)
- [ingestion/lakeflow-connect/google-drive-source-setup-u2m](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/google-drive-source-setup-u2m)
- [ingestion/lakeflow-connect/google-drive-source-setup-service-account](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/google-drive-source-setup-service-account)
- [ingestion/lakeflow-connect/google-drive-connection](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/google-drive-connection)
- [ingestion/lakeflow-connect/google-drive](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/google-drive)
- …and 3 more

### The managed SharePoint connector adds list ingestion, with `LIST` requiring only `entity_type` and `url`, and documents new limits.

`additive` · connector · 5 pages

New limitations as written: ingesting SharePoint list attachments is not supported, UI-based authoring is not supported for list ingestion, and certain Microsoft 365 national cloud deployments are not supported. The connector remains in Beta with workspace-admin-controlled access.

- [ingestion/sharepoint](https://docs.databricks.com/aws/en/ingestion/sharepoint)
- [ingestion/lakeflow-connect/sharepoint-limits](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/sharepoint-limits)
- [ingestion/lakeflow-connect/sharepoint-reference](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/sharepoint-reference)
- [ingestion/lakeflow-connect/sharepoint-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/sharepoint-pipeline)
- [sql/language-manual/functions/ai_parse_document](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_parse_document)

### Continuous Lakeflow pipelines can now use a maintenance window to control when platform-initiated updates and restarts happen, configured on the job that runs the pipeline.

`additive` · new-feature · 6 pages

Jobs notifications gain maintenance start and maintenance complete events for continuous jobs with a configured maintenance window.

- [ldp/maintenance-windows](https://docs.databricks.com/aws/en/ldp/maintenance-windows)
- [ldp/concepts/pipeline-mode](https://docs.databricks.com/aws/en/ldp/concepts/pipeline-mode)
- [ldp/pipeline-mode](https://docs.databricks.com/aws/en/ldp/pipeline-mode)
- [jobs/notifications](https://docs.databricks.com/aws/en/jobs/notifications)
- [release-notes/product/](https://docs.databricks.com/aws/en/release-notes/product/)
- [release-notes/product/2026/september](https://docs.databricks.com/aws/en/release-notes/product/2026/september)

### Lakeflow pipelines gain Rewind, which restores a pipeline to an earlier point in time so you can fix a problem and reprocess only the affected data.

`additive` · beta-feature · 2 pages

Per the docs, Rewind requires a pipeline on the **Preview** channel with the `pipelines.rewind.betaEnabled` config flag set, plus supported sources and sinks.

- [ldp/rewind](https://docs.databricks.com/aws/en/ldp/rewind)
- [ldp/recover-streaming](https://docs.databricks.com/aws/en/ldp/recover-streaming)

### Lakeflow pipeline flows gain a `depends_on` option (Public Preview) that makes a flow start only after named flows complete successfully.

`additive` · new-feature · 3 pages

A new page covers ordering flows, for example draining a backfill before switching to a live stream. The Python append-flow and update-flow references document the parameter as `str` or `list`.

- [ldp/flows-depends-on](https://docs.databricks.com/aws/en/ldp/flows-depends-on)
- [ldp/developer/ldp-python-ref-append-flow](https://docs.databricks.com/aws/en/ldp/developer/ldp-python-ref-append-flow)
- [ldp/developer/ldp-python-ref-update-flow](https://docs.databricks.com/aws/en/ldp/developer/ldp-python-ref-update-flow)

### Metric views support unitless numeric `offset` and `range` on a consecutive integer index column, requiring Databricks Runtime 19 or above and YAML specification version 1.1 or above.

`additive` · new-feature · 5 pages

The advanced-techniques page warns that a dated offset such as `-12 month` steps along a date or timestamp column and that gaps in periods break the window mapping, so densify the source.

- [uc-semantics/metric-views/yaml-reference](https://docs.databricks.com/aws/en/uc-semantics/metric-views/yaml-reference)
- [uc-semantics/metric-views/feature-availability](https://docs.databricks.com/aws/en/uc-semantics/metric-views/feature-availability)
- [uc-semantics/metric-views/advanced-techniques](https://docs.databricks.com/aws/en/uc-semantics/metric-views/advanced-techniques)
- [release-notes/product/](https://docs.databricks.com/aws/en/release-notes/product/)
- [release-notes/product/2026/september](https://docs.databricks.com/aws/en/release-notes/product/2026/september)

### A new `counter_diff` analytic window function converts consecutive cumulative counter values into per-row deltas.

`additive` · new-function · 5 pages

Added to the builtin function lists as `counter_diff(value[,start_time])`.

- [sql/language-manual/functions/counter_diff](https://docs.databricks.com/aws/en/sql/language-manual/functions/counter_diff)
- [sql/language-manual/sql-ref-functions-builtin](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-functions-builtin)
- [sql/language-manual/sql-ref-functions-builtin-alpha](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-functions-builtin-alpha)
- [release-notes/product/](https://docs.databricks.com/aws/en/release-notes/product/)
- [release-notes/product/2026/september](https://docs.databricks.com/aws/en/release-notes/product/2026/september)

### A new `ai_transcribe()` SQL function (Beta) transcribes an audio file to text, returning time-stamped segments and speaker labels.

`additive` · new-function · 3 pages

Listed in the AI Functions index with a Beta marker.

- [sql/language-manual/functions/ai_transcribe](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_transcribe)
- [large-language-models/ai-functions](https://docs.databricks.com/aws/en/large-language-models/ai-functions)
- [release-notes/product/2026/august](https://docs.databricks.com/aws/en/release-notes/product/2026/august)

### A new page documents the Databricks Labs `migrate-ip-acls` CLI tool for migrating workspace IP access lists to a context-based ingress policy, and the IP access list pages now recommend migrating.

`additive` · migration-tooling · 6 pages

Context-based ingress is documented as requiring the Enterprise tier.

- [security/network/front-end/migrate-to-context-based-ingress](https://docs.databricks.com/aws/en/security/network/front-end/migrate-to-context-based-ingress)
- [security/network/front-end/ip-access-list](https://docs.databricks.com/aws/en/security/network/front-end/ip-access-list)
- [security/network/front-end/ip-access-list-workspace](https://docs.databricks.com/aws/en/security/network/front-end/ip-access-list-workspace)
- [security/network/front-end/context-based-ingress](https://docs.databricks.com/aws/en/security/network/front-end/context-based-ingress)
- [security/network/context-based-policies](https://docs.databricks.com/aws/en/security/network/context-based-policies)
- [security/network/front-end/manage-ingress-policies](https://docs.databricks.com/aws/en/security/network/front-end/manage-ingress-policies)

### The AI Gateway coding-agent integration docs now list Claude Code alongside Codex CLI, Cursor and Gemini CLI as agents you can route through a Databricks model service.

`additive` · documentation · 3 pages

- [ai-gateway/coding-agent-integration-model-services](https://docs.databricks.com/aws/en/ai-gateway/coding-agent-integration-model-services)
- [ai-gateway/ai-governance](https://docs.databricks.com/aws/en/ai-gateway/ai-governance)
- [ai-gateway/govern-coding-agent-models](https://docs.databricks.com/aws/en/ai-gateway/govern-coding-agent-models)

### Genie One adds account-only user access (Beta) for users in a registered identity provider who aren't assigned to a workspace, plus personalized starter questions on the home page.

`additive` · beta-feature · 6 pages

A new page covers what account-only users can do and how account admins manage their access, data permissions and compute.

- [genie-one/account-only-user-access](https://docs.databricks.com/aws/en/genie-one/account-only-user-access)
- [genie-one/](https://docs.databricks.com/aws/en/genie-one/)
- [genie-one/external-sources](https://docs.databricks.com/aws/en/genie-one/external-sources)
- [genie-one/customize-genie-homepage](https://docs.databricks.com/aws/en/genie-one/customize-genie-homepage)
- [release-notes/product/](https://docs.databricks.com/aws/en/release-notes/product/)
- [release-notes/product/2026/september](https://docs.databricks.com/aws/en/release-notes/product/2026/september)

### Genie Code gains conversation controls: fork a chat into a separate thread from a chosen point, ask a side question with `/btw`, or edit an earlier message to regenerate the chat.

`additive` · new-feature · 7 pages

A new Branch and edit chats page documents the behaviour, and the feature is cross-linked from the navigation and capabilities pages.

- [genie-code/branch](https://docs.databricks.com/aws/en/genie-code/branch)
- [genie-code/full-page](https://docs.databricks.com/aws/en/genie-code/full-page)
- [genie-code/navigate-genie-code](https://docs.databricks.com/aws/en/genie-code/navigate-genie-code)
- [genie-code/features-capabilities](https://docs.databricks.com/aws/en/genie-code/features-capabilities)
- [genie-code/use-genie-code](https://docs.databricks.com/aws/en/genie-code/use-genie-code)
- [release-notes/product/](https://docs.databricks.com/aws/en/release-notes/product/)
- …and 1 more

### A new guide covers creating, running commands in, and managing the lifecycle of a Databricks Sandbox with the Python SDK.

`additive` · new-guide · 2 pages

The sandbox page adds that to stop paying for storage you must delete the sandbox, and that you cannot customize the environment at startup or persist an environment outside your home directory.

- [compute/serverless/sandbox-usage-guide](https://docs.databricks.com/aws/en/compute/serverless/sandbox-usage-guide)
- [compute/serverless/sandbox](https://docs.databricks.com/aws/en/compute/serverless/sandbox)

### Lakehouse Federation adds AWS IAM authentication for Amazon Redshift, and the MySQL/PostgreSQL IAM pages clarify that only a single IAM role in the database's own AWS account is needed.

`additive` · new-feature · 3 pages

- [query-federation/redshift-iam](https://docs.databricks.com/aws/en/query-federation/redshift-iam)
- [query-federation/mysql-iam](https://docs.databricks.com/aws/en/query-federation/mysql-iam)
- [query-federation/postgresql-iam](https://docs.databricks.com/aws/en/query-federation/postgresql-iam)

### A new Genie consumption guide covers planning enterprise Genie spend with a usage discovery period, persona tiers and budgets; the budgets and cost pages link to it.

`additive` · new-guide · 3 pages

- [genie/consumption-guide](https://docs.databricks.com/aws/en/genie/consumption-guide)
- [genie/budgets](https://docs.databricks.com/aws/en/genie/budgets)
- [genie/monitor-cost](https://docs.databricks.com/aws/en/genie/monitor-cost)

## Editorial — 13

### Java SDK snippets across the platform pages move from 2.60.0 to 2.63.0.

`editorial` · version-bump · 5 pages

Applies to `anthropic-java`, `anthropic-java-vertex`, `anthropic-java-bedrock` and `anthropic-java-foundry` Gradle/Maven examples.

- [build-with-claude/claude-on-vertex-ai](https://platform.claude.com/docs/en/build-with-claude/claude-on-vertex-ai)
- [build-with-claude/claude-in-amazon-bedrock](https://platform.claude.com/docs/en/build-with-claude/claude-in-amazon-bedrock)
- [build-with-claude/claude-in-microsoft-foundry](https://platform.claude.com/docs/en/build-with-claude/claude-in-microsoft-foundry)
- [build-with-claude/claude-on-amazon-bedrock-legacy](https://platform.claude.com/docs/en/build-with-claude/claude-on-amazon-bedrock-legacy)
- [cli-sdks-libraries/sdks/java](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/java)

### The CLI quickstart's pinned install version moves from 1.30.0 to 1.33.0.

`editorial` · version-bump · 1 page

`VERSION=1.33.0` in the install snippet.

- [cli-sdks-libraries/cli/quickstart](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/quickstart)

### The MCP tunnels research-preview access request link moved from claude.com/form/claude-managed-agents to claude.com/form/mcp-tunnels across all nine tunnel pages.

`editorial` · link-change · 9 pages

The research-preview status and the note that Anthropic may modify or discontinue MCP tunnels are unchanged.

- [agents-and-tools/mcp-tunnels/concepts](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/concepts)
- [agents-and-tools/mcp-tunnels/console](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/console)
- [agents-and-tools/mcp-tunnels/deploy-compose](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/deploy-compose)
- [agents-and-tools/mcp-tunnels/deploy-helm](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/deploy-helm)
- [agents-and-tools/mcp-tunnels/overview](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/overview)
- [agents-and-tools/mcp-tunnels/quickstart](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/quickstart)
- …and 3 more

### Managed Agents pages replace the inline beta-header callout with a metadata block listing Status: Beta and the page's beta header.

`editorial` · documentation · 24 pages

Most pages list `managed-agents-2026-04-01`; the memory page lists `agent-memory-2026-07-22`. The header requirement itself is unchanged, only how it is presented.

- [managed-agents/overview](https://platform.claude.com/docs/en/managed-agents/overview)
- [managed-agents/agent-setup](https://platform.claude.com/docs/en/managed-agents/agent-setup)
- [managed-agents/onboarding](https://platform.claude.com/docs/en/managed-agents/onboarding)
- [managed-agents/quickstart](https://platform.claude.com/docs/en/managed-agents/quickstart)
- [managed-agents/sessions](https://platform.claude.com/docs/en/managed-agents/sessions)
- [managed-agents/session-operations](https://platform.claude.com/docs/en/managed-agents/session-operations)
- …and 18 more

### Most of the API reference was regenerated: inline union shapes become named schema types, the beta enum count moves from "41 more" to "43 more", and prose typos are corrected.

`editorial` · bulk-regeneration · 32 pages

Representative patterns: `array of object or object` becomes `array of Text or ToolUse or ToolResult`; `BetaOrganizationInvite`, `BetaWorkspaceRole`, `BetaCacheCreation`, `BetaJWKSDiscovery` and similar names replace expanded field lists; the `anthropic-beta` header is now described as `optional array of AnthropicBeta` instead of the old comma-separated-list prose; and the `temperature` deprecation note fixes "A value of 1.0 of will be accepted". This covers many more pages than those cited.

- [api/admin](https://platform.claude.com/docs/en/api/admin)
- [api/admin/organizations](https://platform.claude.com/docs/en/api/admin/organizations)
- [api/beta](https://platform.claude.com/docs/en/api/beta)
- [api/beta/organization](https://platform.claude.com/docs/en/api/beta/organization)
- [api/admin/analytics](https://platform.claude.com/docs/en/api/admin/analytics)
- [api/admin/users](https://platform.claude.com/docs/en/api/admin/users)
- …and 26 more

### Several Admin API curl examples switched from `Authorization: Bearer $ANTHROPIC_AUTH_TOKEN` to `X-Api-Key: $ANTHROPIC_API_KEY`.

`editorial` · documentation · 6 pages

Only the example snippets changed; the pages do not state that either authentication method stopped working.

- [api/admin/external_keys/delete](https://platform.claude.com/docs/en/api/admin/external_keys/delete)
- [api/admin/external_keys/validate](https://platform.claude.com/docs/en/api/admin/external_keys/validate)
- [api/admin/invites/delete](https://platform.claude.com/docs/en/api/admin/invites/delete)
- [api/admin/spend_limits/delete](https://platform.claude.com/docs/en/api/admin/spend_limits/delete)
- [api/admin/users/delete](https://platform.claude.com/docs/en/api/admin/users/delete)
- [api/admin/workspaces/members/delete](https://platform.claude.com/docs/en/api/admin/workspaces/members/delete)

### Compliance API example timestamps now carry a trailing `Z` (`2025-03-12T18:22:41.123456Z`).

`editorial` · documentation · 8 pages

Example payloads only; the field descriptions are unchanged.

- [api/compliance/groups](https://platform.claude.com/docs/en/api/compliance/groups)
- [api/compliance/groups/list](https://platform.claude.com/docs/en/api/compliance/groups/list)
- [api/compliance/groups/retrieve](https://platform.claude.com/docs/en/api/compliance/groups/retrieve)
- [api/compliance/groups/members](https://platform.claude.com/docs/en/api/compliance/groups/members)
- [api/compliance/groups/members/list](https://platform.claude.com/docs/en/api/compliance/groups/members/list)
- [api/compliance/organizations/roles](https://platform.claude.com/docs/en/api/compliance/organizations/roles)
- …and 2 more

### Compliance API curl examples now include the `anthropic-version: 2023-06-01` header.

`editorial` · documentation · 18 pages

Added to the request snippets across the compliance reference; the header requirement itself is not described as new.

- [api/compliance/apps/artifacts](https://platform.claude.com/docs/en/api/compliance/apps/artifacts)
- [api/compliance/apps/artifacts/retrieve](https://platform.claude.com/docs/en/api/compliance/apps/artifacts/retrieve)
- [api/compliance/apps/artifacts/download](https://platform.claude.com/docs/en/api/compliance/apps/artifacts/download)
- [api/compliance/apps/chats/files](https://platform.claude.com/docs/en/api/compliance/apps/chats/files)
- [api/compliance/apps/chats/files/retrieve](https://platform.claude.com/docs/en/api/compliance/apps/chats/files/retrieve)
- [api/compliance/apps/chats/files/download](https://platform.claude.com/docs/en/api/compliance/apps/chats/files/download)
- …and 12 more

### Cross-references to the preserved-thinking guidance were repointed from a "Preserved thinking" anchor to a "Keeping the prefix unchanged" section.

`editorial` · link-change · 7 pages

The preserved-thinking page itself was reworked in the same run, including a note that with `"drop_block"` the dropped count is no longer 0 and the response carries one entry per thinking block in the history.

- [api/errors](https://platform.claude.com/docs/en/api/errors)
- [build-with-claude/context-editing](https://platform.claude.com/docs/en/build-with-claude/context-editing)
- [build-with-claude/preserved-thinking](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking)
- [build-with-claude/thinking-troubleshooting](https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting)
- [models/fable-5-1/whats-new-fable-5-1](https://platform.claude.com/docs/en/models/fable-5-1/whats-new-fable-5-1)
- [models/fable-5-1/migration-guide](https://platform.claude.com/docs/en/models/fable-5-1/migration-guide)
- …and 1 more

### The get-started prerequisites link for an API key now points at the get-api-key doc instead of the Console settings page.

`editorial` · link-change · 1 page

- [get-started](https://platform.claude.com/docs/en/get-started)

### Account console identity configuration moved to a single Identity provider setup tab, replacing the old Authentication tab, and the SSO setup guides now describe an explicit Enable SSO step with a connection test.

`editorial` · console-reorganization · 23 pages

SCIM provisioning, automatic identity management, JIT provisioning, MFA and token regeneration instructions were all renavigated to the new tab. The SSO guides now say Databricks saves the configuration in a disabled state, runs a connection test, and that JIT provisioning is enabled afterwards.

- [security/auth/](https://docs.databricks.com/aws/en/security/auth/)
- [security/auth/jit](https://docs.databricks.com/aws/en/security/auth/jit)
- [security/auth/mfa](https://docs.databricks.com/aws/en/security/auth/mfa)
- [security/auth/single-sign-on/unified-login](https://docs.databricks.com/aws/en/security/auth/single-sign-on/unified-login)
- [security/auth/single-sign-on/emergency-access](https://docs.databricks.com/aws/en/security/auth/single-sign-on/emergency-access)
- [security/auth/single-sign-on/okta](https://docs.databricks.com/aws/en/security/auth/single-sign-on/okta)
- …and 17 more

### The MLflow GenAI docs were restructured: tracing consolidates under a new `/tracing/overview` with new automatic, manual, enrich, govern-redact, otel-export and migrate pages, and links to `/tracing/`, `/tracing/tracing-101` and `/agents/agent-evaluation/` were repointed across the corpus.

`editorial` · documentation-restructure · 30 pages

New conceptual entry points (agent observability and quality, core concepts, recipes) were added, `agents/agent-evaluation/` references now point at `mlflow3/genai/eval-monitor/`, and much wording shifts from "GenAI application" to "agent". This touches far more pages than those cited.

- [mlflow3/genai/tracing/overview](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/overview)
- [mlflow3/genai/tracing/automatic-tracing](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/automatic-tracing)
- [mlflow3/genai/tracing/manual-tracing](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/manual-tracing)
- [mlflow3/genai/tracing/enrich-traces](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/enrich-traces)
- [mlflow3/genai/tracing/govern-redact](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/govern-redact)
- [mlflow3/genai/tracing/otel-export](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/otel-export)
- …and 24 more

### The materialized-view refresh example now sets `STATEMENT_TIMEOUT` to the integer 21600 instead of the string '6h'.

`editorial` · correction · 1 page

- [ldp/dbsql/schedule-refreshes](https://docs.databricks.com/aws/en/ldp/dbsql/schedule-refreshes)
