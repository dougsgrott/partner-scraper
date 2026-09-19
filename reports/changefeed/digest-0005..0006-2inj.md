# Change digest

> #5 (2026-09-09-before) → #6 (2026-09-09) · 1,072 changes · rendered 2026-09-19T12:15:54+00:00

## At a glance

64 findings — **7** breaking, **20** behavioural, **26** additive, **11** editorial — covering 545 of 1,072 changed pages. Anything not here is in the full feed report beside this file.

**If you read nothing else:**

1. MLflow GenAI tracing docs raise the required version from `mlflow[databricks]>=3.1` to `>=3.14.0` because the examples now store traces in Unity Catalog and need a SQL warehouse.
2. Federation issuer, federation rule and service-account admin endpoints are now documented as requiring an OAuth access token carrying the `org:admin` scope, replacing the looser "an OAuth bearer or Console session".
3. The customer-managed key reference now states that on Claude Platform on AWS the `kms_arn` must be a single-Region key in your own AWS account — cross-account keys, multi-Region keys and alias ARNs are rejected.
4. C# workload-identity-federation examples construct the client as `new AnthropicClient(new ClientOptions { Credentials = credentials })` instead of `new AnthropicOidcClient(credentials)`.
5. Automatic change data feed is generally available and its runtime requirement rises from Databricks Runtime 18 LTS to Databricks Runtime 19 or above.
6. The TypeScript SDK now states TypeScript >= 5.0 is supported, up from >= 4.9.
7. In CMEK organizations, structured outputs are now listed as unavailable for all Claude Fable and Claude Mythos models, not just Claude Fable 5.

---

## Breaking — 7

### MLflow GenAI tracing docs raise the required version from `mlflow[databricks]>=3.1` to `>=3.14.0` because the examples now store traces in Unity Catalog and need a SQL warehouse.

`breaking` · version floor · 38 pages

Every tracing integration page bumps the pip line and adds `from mlflow.entities.trace_location import UnityCatalog` plus `os.environ["MLFLOW_TRACING_SQL_WAREHOUSE_ID"]`. label-existing-traces states outright that the features described require MLflow 3.14.0 or above (previously 3.1.0). The Claude Code CLI tracing bullet moves from MLflow 3.4+ to 3.14+. dev-tools/databricks-apps/mlflow adds that an experiment resource grants workspace-level permissions and that Unity Catalog trace tables must be added separately.

- [mlflow3/genai/tracing/integrations/](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/)
- [mlflow3/genai/tracing/integrations/anthropic](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/anthropic)
- [mlflow3/genai/tracing/integrations/openai](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/openai)
- [mlflow3/genai/tracing/integrations/langchain](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/langchain)
- [mlflow3/genai/tracing/integrations/langgraph](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/langgraph)
- [mlflow3/genai/tracing/integrations/llama_index](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/llama_index)
- …and 32 more

### Federation issuer, federation rule and service-account admin endpoints are now documented as requiring an OAuth access token carrying the `org:admin` scope, replacing the looser "an OAuth bearer or Console session".

`breaking` · auth scope · 32 pages

Every one of these endpoints gains a banner: "Requires an OAuth access token with the `org:admin` scope, from `ant auth login --scope org:admin` or a workload identity federation rule; Admin API keys are not accepted", linking to manage-claude/wif-admin-api. The previous text said only that an OAuth bearer or Console session was required and that Admin API keys were rejected. Tokens minted with narrower scopes are not described as sufficient.

- [api/admin/federation_issuers](https://platform.claude.com/docs/en/api/admin/federation_issuers)
- [api/admin/federation_issuers/archive](https://platform.claude.com/docs/en/api/admin/federation_issuers/archive)
- [api/admin/federation_issuers/create](https://platform.claude.com/docs/en/api/admin/federation_issuers/create)
- [api/admin/federation_issuers/update](https://platform.claude.com/docs/en/api/admin/federation_issuers/update)
- [api/admin/federation_issuers/list](https://platform.claude.com/docs/en/api/admin/federation_issuers/list)
- [api/admin/federation_issuers/retrieve](https://platform.claude.com/docs/en/api/admin/federation_issuers/retrieve)
- …and 26 more

### The customer-managed key reference now states that on Claude Platform on AWS the `kms_arn` must be a single-Region key in your own AWS account — cross-account keys, multi-Region keys and alias ARNs are rejected.

`breaking` · restriction · 19 pages

`kms_arn` previously read only "Full ARN of the AWS KMS key." The added sentence appears on every external-keys and workspace schema that carries the field. manage-claude/cmek-aws-kms adds matching key requirements (symmetric, encrypt/decrypt usage, single-region, same account and region as the workspace) and CloudTrail troubleshooting for a denied `kms:` event. The deprecated `iam_role_arn` field description was reworded but was already deprecated and ignored before this run.

- [api/admin/external_keys](https://platform.claude.com/docs/en/api/admin/external_keys)
- [api/admin/external_keys/create](https://platform.claude.com/docs/en/api/admin/external_keys/create)
- [api/admin/external_keys/update](https://platform.claude.com/docs/en/api/admin/external_keys/update)
- [api/admin/external_keys/list](https://platform.claude.com/docs/en/api/admin/external_keys/list)
- [api/admin/external_keys/retrieve](https://platform.claude.com/docs/en/api/admin/external_keys/retrieve)
- [api/admin/external_keys/delete](https://platform.claude.com/docs/en/api/admin/external_keys/delete)
- …and 13 more

### C# workload-identity-federation examples construct the client as `new AnthropicClient(new ClientOptions { Credentials = credentials })` instead of `new AnthropicOidcClient(credentials)`.

`breaking` · sdk api change · 7 pages

The same substitution appears in every WIF provider guide and the overview page. The GitHub Actions and Kubernetes samples also drop the `?? throw new InvalidOperationException("No federation credentials found in environment")` fallback in favour of comments listing the environment variables read (`ANTHROPIC_ORGANIZATION_ID`, `ANTHROPIC_SERVICE_ACCOUNT_ID`, `ANTHROPIC_WORKSPACE_ID`, `ANTHROPIC_IDENTITY_TOKEN_FILE`).

- [manage-claude/wif-providers/gcp](https://platform.claude.com/docs/en/manage-claude/wif-providers/gcp)
- [manage-claude/wif-providers/okta](https://platform.claude.com/docs/en/manage-claude/wif-providers/okta)
- [manage-claude/wif-providers/azure](https://platform.claude.com/docs/en/manage-claude/wif-providers/azure)
- [manage-claude/wif-providers/aws](https://platform.claude.com/docs/en/manage-claude/wif-providers/aws)
- [manage-claude/wif-providers/github-actions](https://platform.claude.com/docs/en/manage-claude/wif-providers/github-actions)
- [manage-claude/wif-providers/kubernetes](https://platform.claude.com/docs/en/manage-claude/wif-providers/kubernetes)
- …and 1 more

### Automatic change data feed is generally available and its runtime requirement rises from Databricks Runtime 18 LTS to Databricks Runtime 19 or above.

`breaking` · version floor · 2 pages

change-data-feed's Requirements list now reads "Databricks Runtime 19 or above"; the table-format prerequisites (managed Delta with row tracking or Iceberg v3, external Delta with row tracking) are unchanged. The DBR 19 release notes announce Auto CDF, which computes row-level changes at query time, as generally available, under a new "Databricks Runtime 19: September 1, 2026" heading.

- [tables/features/change-data-feed](https://docs.databricks.com/aws/en/tables/features/change-data-feed)
- [release-notes/runtime/19](https://docs.databricks.com/aws/en/release-notes/runtime/19)

### The TypeScript SDK now states TypeScript >= 5.0 is supported, up from >= 4.9.

`breaking` · version floor · 1 page

One-line change on cli-sdks-libraries/sdks/typescript: "TypeScript >= 4.9 is supported" becomes "TypeScript >= 5.0 is supported".

- [cli-sdks-libraries/sdks/typescript](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/typescript)

### In CMEK organizations, structured outputs are now listed as unavailable for all Claude Fable and Claude Mythos models, not just Claude Fable 5.

`breaking` · restriction · 1 page

The unsupported-features table entry changes from "Structured outputs (not available for Claude Fable 5 or Claude Mythos models in CMEK organizations)" to "(not available for Claude Fable or Claude Mythos models in CMEK organizations)", which brings Fable 5.1 under the same exclusion even though build-with-claude/structured-outputs lists `claude-fable-5-1` as a supported model generally.

- [manage-claude/cmek](https://platform.claude.com/docs/en/manage-claude/cmek)

## Behavioural — 20

### Serverless GPU example notebooks now state a minimum environment version (mostly "Databricks AI environment version 5 or above") in place of a generic note, and a new Ray Data + vLLM batch inference tutorial is added.

`behavioural` · requirement stated · 18 pages

Fifteen sgc-* tutorials replace an unlabelled "Note" with an explicit environment-version requirement; two state version 4 or 5 of the Standard environment specifically. New page sgc-raydata-vllm-batch-inference runs multilingual batch inference across 8 H100 GPUs and writes results to Unity Catalog. The examples index now describes AI Runtime as serverless GPU compute for inference as well as training and fine-tuning.

- [machine-learning/ai-runtime/examples/tutorials/sgc-api-h100-starter](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-api-h100-starter)
- [machine-learning/ai-runtime/examples/tutorials/sgc-cnn-mnist](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-cnn-mnist)
- [machine-learning/ai-runtime/examples/tutorials/sgc-distributed-finetune-qwen2-0.5b](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-distributed-finetune-qwen2-0.5b)
- [machine-learning/ai-runtime/examples/tutorials/sgc-distributed-gpt-oss-20b](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-distributed-gpt-oss-20b)
- [machine-learning/ai-runtime/examples/tutorials/sgc-distributed-pytorch-fsdp](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-distributed-pytorch-fsdp)
- [machine-learning/ai-runtime/examples/tutorials/sgc-finetune-llama-unsloth](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-finetune-llama-unsloth)
- …and 12 more

### A new `ant apply <file>` command declares agents, environments, skills, memory stores and deployments from files, and the managed-agents docs replace `ant beta:<resource> create < file.yaml` invocations with it.

`behavioural` · cli · 13 pages

New page cli-sdks-libraries/cli/apply describes keeping API resources in sync with files in your repository. Across the managed-agents guides the shell examples change from piped creates such as `ant beta:environments create < environment.yaml` and `ant beta:agents create < agent.yaml` to `ant apply environment.yaml`. cli-sdks-libraries/cli/scripting adds `ant beta:sessions:events stream --session-id … --format jsonl` for watching a session as it runs.

- [cli-sdks-libraries/cli/apply](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/apply)
- [managed-agents/self-hosted-sandboxes](https://platform.claude.com/docs/en/managed-agents/self-hosted-sandboxes)
- [managed-agents/environments](https://platform.claude.com/docs/en/managed-agents/environments)
- [managed-agents/quickstart](https://platform.claude.com/docs/en/managed-agents/quickstart)
- [managed-agents/permission-policies](https://platform.claude.com/docs/en/managed-agents/permission-policies)
- [managed-agents/tools](https://platform.claude.com/docs/en/managed-agents/tools)
- …and 7 more

### A new "preserved thinking" page documents that on Claude Fable 5.1 and Mythos 5.1 a replayed thinking block is only accepted by the model that produced it (or a newer one) and only while the system prompt, tools and preceding messages are unchanged.

`behavioural` · thinking blocks · 9 pages

New page build-with-claude/preserved-thinking. context-windows now makes thinking-block retention model-dependent. thinking-troubleshooting adds guidance to keep history append-only and describes the error text when the `thinking-binding-controls-2026-08-01` beta header is missing. compaction says thinking blocks before a `compaction` block are not carried forward on Fable 5.1 / Mythos 5.1, and to strip `thinking`/`redacted_thinking` from re-inserted turns or set `thinking.block_binding.prefix_mismatch_behavior: "d…"`. computer-use-tool warns that pruning an earlier screenshot client-side invalidates every later thinking block on Fable 5.1. streaming documents `display: "omitted"` suppressing `thinking_delta` events under the same beta.

- [build-with-claude/preserved-thinking](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking)
- [build-with-claude/context-windows](https://platform.claude.com/docs/en/build-with-claude/context-windows)
- [build-with-claude/thinking-troubleshooting](https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting)
- [build-with-claude/compaction](https://platform.claude.com/docs/en/build-with-claude/compaction)
- [build-with-claude/streaming](https://platform.claude.com/docs/en/build-with-claude/streaming)
- [build-with-claude/context-editing](https://platform.claude.com/docs/en/build-with-claude/context-editing)
- …and 3 more

### The block on modifying SCIM-provisioned RBAC groups through the API is now conditional — it applies only while an organization in the tenant uses SCIM provisioning.

`behavioural` · restriction scope · 6 pages

Descriptions change from "Groups provisioned by an identity provider (source type `\"scim\"`) cannot be modified via the API" to the same sentence plus "while an organization in the tenant uses SCIM provisioning". Applies to group rename, delete, and member add/remove.

- [api/admin/rbac_groups](https://platform.claude.com/docs/en/api/admin/rbac_groups)
- [api/admin/rbac_groups/update](https://platform.claude.com/docs/en/api/admin/rbac_groups/update)
- [api/admin/rbac_groups/delete](https://platform.claude.com/docs/en/api/admin/rbac_groups/delete)
- [api/admin/rbac_groups/members](https://platform.claude.com/docs/en/api/admin/rbac_groups/members)
- [api/admin/rbac_groups/members/create](https://platform.claude.com/docs/en/api/admin/rbac_groups/members/create)
- [api/admin/rbac_groups/members/delete](https://platform.claude.com/docs/en/api/admin/rbac_groups/members/delete)

### ABAC GRANT policies drop their Beta label; a new guide shows using them to govern access to models and AI services in `system.ai`.

`behavioural` · ga · 6 pages

Cross-references change from "For GRANT policies (Beta), see ABAC GRANT policies (Beta)" to "For GRANT policies, see ABAC GRANT policies", and the Beta banner is removed from the grant-policies page itself. `CREATE POLICY` documents GRANT as a policy type alongside row filters and column masks. New page ai-gateway/govern-access-to-models-with-grant-policies covers tagging models in `system.ai`.

- [data-governance/unity-catalog/abac/common-patterns](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/common-patterns)
- [data-governance/unity-catalog/abac/requirements](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/requirements)
- [data-governance/unity-catalog/abac/grant-policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/grant-policies)
- [sql/language-manual/sql-ref-syntax-aux-show-policies](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-aux-show-policies)
- [sql/language-manual/sql-ref-syntax-ddl-create-policy](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-ddl-create-policy)
- [ai-gateway/govern-access-to-models-with-grant-policies](https://docs.databricks.com/aws/en/ai-gateway/govern-access-to-models-with-grant-policies)

### Compliance API session coverage now spans local and remote sessions; the session endpoints are read-only and sessions cannot be deleted through the Compliance API.

`behavioural` · compliance · 4 pages

compliance-sessions states the endpoints are read-only, that local session transcripts are retained for 6 years by default, and that in CMEK organizations local transcripts are encrypted under your customer-managed key. compliance-integration-patterns extends its legal-hold advice from "chat content" to "chat content or remote session transcripts". compliance-faq restates that deletes are immediate, permanent and unrecoverable, and that on-device activity never reaching the Claude API is not captured. compliance-errors documents a transient "index is temporarily unavailable" body for session listings.

- [manage-claude/compliance-sessions](https://platform.claude.com/docs/en/manage-claude/compliance-sessions)
- [manage-claude/compliance-integration-patterns](https://platform.claude.com/docs/en/manage-claude/compliance-integration-patterns)
- [manage-claude/compliance-faq](https://platform.claude.com/docs/en/manage-claude/compliance-faq)
- [manage-claude/compliance-errors](https://platform.claude.com/docs/en/manage-claude/compliance-errors)

### The zero-data-retention exclusion for Fable and Mythos models is softened to "not available under ZDR unless expressly authorized by Anthropic", and Fable 5.1 and Mythos 5.1 join the Covered Models list.

`behavioural` · data retention · 4 pages

api-and-data-retention now names Claude Fable 5.1, Claude Mythos 5.1, Claude Fable 5 and Claude Mythos 5 as Covered Models requiring 30-day retention. The previous flat statement that they are "not available under zero data retention" now carries the "unless expressly authorized by Anthropic" qualifier on all four pages.

- [manage-claude/api-and-data-retention](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention)
- [models/fable-5/migration-guide](https://platform.claude.com/docs/en/models/fable-5/migration-guide)
- [about-claude/models/introducing-claude-fable-5-and-claude-mythos-5](https://platform.claude.com/docs/en/about-claude/models/introducing-claude-fable-5-and-claude-mythos-5)
- [models/fable-5/introducing-claude-fable-5-and-claude-mythos-5](https://platform.claude.com/docs/en/models/fable-5/introducing-claude-fable-5-and-claude-mythos-5)

### Inference-hook circuit-breaker recovery now runs only while your Inference hooks settings are unchanged since the trip, and recovery probes start about 10 minutes after tripping at roughly one request per minute.

`behavioural` · enforcement · 3 pages

inference-hooks-configuration: "Automatic recovery runs only while your Inference hooks settings are unchanged since the trip. If you change any Inference hooks setting after…". inference-hooks-endpoint describes the probe cadence. inference-hooks clarifies one hook governs claude.ai, Cowork and Claude Code sessions whether run on web, desktop, mobile or the CLI.

- [manage-claude/inference-hooks-configuration](https://platform.claude.com/docs/en/manage-claude/inference-hooks-configuration)
- [manage-claude/inference-hooks-endpoint](https://platform.claude.com/docs/en/manage-claude/inference-hooks-endpoint)
- [manage-claude/inference-hooks](https://platform.claude.com/docs/en/manage-claude/inference-hooks)

### SQL AI-function examples now name models as `system.ai.llama-4-maverick` instead of the endpoint name `databricks-llama-4-maverick`.

`behavioural` · naming · 3 pages

The substitution appears in the `ai_query` reference, the `read_files` examples and the volumes file-processing tutorial. The pages do not say whether the old endpoint names still resolve.

- [sql/language-manual/functions/ai_query](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_query)
- [sql/language-manual/functions/read_files](https://docs.databricks.com/aws/en/sql/language-manual/functions/read_files)
- [volumes/volume-files](https://docs.databricks.com/aws/en/volumes/volume-files)

### Forced tool use (`tool_choice` `any` or `tool`) returns a 400 error on Claude Fable 5.1 and Claude Mythos 5.1; the docs now carry a table of where forced tool use is unsupported.

`behavioural` · restriction · 2 pages

define-tools replaces two scattered notes with a table under "Forcing tool use". Rows: manual extended thinking (`thinking: {type: "enabled"}`), where `any` and `tool` error; and Claude Fable 5.1 / Mythos 5.1, where `any` and `tool` return a 400 (linked to an api/errors anchor). Recommended alternatives are `auto` with strict tool use, or structured outputs; `none` also works. The api primer repeats this and adds: leave `tool_choice` at `auto` and set `"strict": true`. The page also drops its old "Choosing a model" section.

- [agents-and-tools/tool-use/define-tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools)
- [claude_api_primer](https://platform.claude.com/docs/en/claude_api_primer)

### Changing the top-level effort value between requests invalidates the prompt cache; the caching table adds an "Effort setting" row.

`behavioural` · caching · 2 pages

build-with-claude/effort adds the guidance "Hold top-level effort constant within cached conversations". prompt-caching's what-invalidates table gains an Effort setting row (model-specific) and reworks the row for non-tool results passed to extended thinking requests.

- [build-with-claude/effort](https://platform.claude.com/docs/en/build-with-claude/effort)
- [build-with-claude/prompt-caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)

### The partner-powered and Designated Services availability tables are rewritten and now mark several Genie surfaces — including chat in Genie One, Genie Code Agent mode and both Genie Agents modes — as unavailable in some partner-powered configurations.

`behavioural` · availability · 2 pages

partner-powered lists per-feature model providers (Azure OpenAI service, OpenAI on Databricks, Anthropic on Databricks) with availability notes such as "Chat in Genie One is not available" and "Feature is not available", noting users can still access Genie One and interact with it. designated-services adds rows including the AI Search reranker and Genie Agents chat mode with per-region availability markers. The tables were regenerated whole, so check the row for your own configuration rather than assuming a change.

- [databricks-ai/partner-powered](https://docs.databricks.com/aws/en/databricks-ai/partner-powered)
- [resources/designated-services](https://docs.databricks.com/aws/en/resources/designated-services)

### Priority Tier does not support Claude Fable 5.1 or Claude Mythos 5.1, which join Mythos 5, Mythos Preview, Opus 5 and Sonnet 5 on the unsupported list.

`behavioural` · availability · 1 page

The "Supported models" line now reads: Priority Tier is supported on all available Claude models except Claude Fable 5.1, Claude Mythos 5.1, Claude Mythos 5, Claude Mythos Preview, Claude Opus 5, and Claude Sonnet 5. The page does not say what happens to a Priority Tier request naming one of these models.

- [api/service-tiers](https://platform.claude.com/docs/en/api/service-tiers)

### `Authorization: Bearer <token>` is now the primary authentication header and accepts your API key directly; `x-api-key` is relabelled a legacy fallback that is still supported.

`behavioural` · auth · 1 page

The header table reorders the two rows. `Authorization` is "Yes, unless `x-api-key` is set" and its value is now "your API key or a short-lived access token obtained from `POST /v1/oauth/token`". `x-api-key` becomes Required: No, described as "Legacy fallback for `Authorization`, still supported". The SDK benefits list changes "Automatic header management (`x-api-key`, …)" to "(authentication, …)".

- [api/overview](https://platform.claude.com/docs/en/api/overview)

### Claude Fable 5.1 may issue fewer parallel tool calls than earlier models, most noticeably in long agent loops.

`behavioural` · model behaviour · 1 page

A new note on parallel-tool-use. The page also restates that with `tool_choice` `any` or `tool`, `disable_parallel_tool_use: true` means exactly one tool is called.

- [agents-and-tools/tool-use/parallel-tool-use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/parallel-tool-use)

### Programmatic tool calling now states its platforms inline: Claude API, Claude Platform on AWS and Microsoft Foundry, and not available on Amazon Bedrock or Google Cloud.

`behavioural` · availability · 1 page

The page previously pointed readers at the code execution tool's model-compatibility table instead of listing platforms itself.

- [agents-and-tools/tool-use/programmatic-tool-calling](https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling)

### Lakeflow pipeline unit testing no longer requires the PREVIEW channel; it now requires the pipeline to run on Databricks Runtime 18.1 or above.

`behavioural` · requirement change · 1 page

The prerequisite "Pipeline must be on the PREVIEW channel. Unit testing is in Beta and is only available on PREVIEW" is replaced by "Pipeline must run on Databricks Runtime 18.1 or above. Earlier runtimes do not include the unit testing module." Step 1 drops the channel switch and the `"channel": "PREVIEW"` JSON setting, keeping only `"continuous": false`. Spark Connect is still unsupported.

- [ldp/unit-testing](https://docs.databricks.com/aws/en/ldp/unit-testing)

### The deprecation of `limit`, `offset`, `total_count` and `next_page` in `/api/2.1/clusters/events` moves from October 20, 2026 to November 30, 2026.

`behavioural` · deprecation date · 1 page

The fields are still to be replaced with token-based pagination; only the date changed.

- [compute/events-api-updates](https://docs.databricks.com/aws/en/compute/events-api-updates)

### Viewing serverless job performance metrics no longer requires workspace access to Query performance insights; only the "Improved Lakeflow Performance Observability" preview is required.

`behavioural` · requirement removed · 1 page

The two-item prerequisite list collapses to one. The removed item previously warned that without Query performance insights the lightbulb indicators would not appear, though aggregated metrics still would.

- [jobs/diagnose-job-performance](https://docs.databricks.com/aws/en/jobs/diagnose-job-performance)

### A job that runs continuously for more than 30 days loses access to files under `/Workspace`; restart it at least once every 30 days to retain access.

`behavioural` · restriction · 1 page

New paragraph under "File access permission limit", alongside the existing 36-hour interactive / 30-day job expiry. It explicitly extends to jobs that use source code from a remote Git repository, because the job reads the checked-out repository from a path under `/Workspace`.

- [files/workspace](https://docs.databricks.com/aws/en/files/workspace)

## Additive — 26

### Lakeflow Connect adds three managed SaaS connectors — Anysphere (Cursor) Audit Logs, Verkada and Glean — each with a full eight-page doc set.

`additive` · new connectors · 26 pages

Anysphere ingests Cursor audit logs; Verkada ingests organization audit logs and access users; Glean ingests company-wide usage insights and shortcuts (go links) and is documented as full-refresh-only with no SCD Type 2. The connector index and FAQ hub link the new pages.

- [ingestion/lakeflow-connect/anysphere-audit-logs](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs)
- [ingestion/lakeflow-connect/anysphere-audit-logs-connection](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-connection)
- [ingestion/lakeflow-connect/anysphere-audit-logs-faq](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-faq)
- [ingestion/lakeflow-connect/anysphere-audit-logs-limits](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-limits)
- [ingestion/lakeflow-connect/anysphere-audit-logs-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-pipeline)
- [ingestion/lakeflow-connect/anysphere-audit-logs-reference](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-reference)
- …and 20 more

### Claude Fable 5.1 (`claude-fable-5-1`) and Claude Mythos 5.1 ship with a full page set — overview, migration guide, what's-new, prompting guide and system prompt — and Claude Fable 5 is now marked "Active (legacy)".

`additive` · model launch · 18 pages

New pages: models/fable-5-1/overview, models/fable-5-1/migration-guide, models/fable-5-1/whats-new-fable-5-1, models/mythos-5-1/overview (invitation-only via Project Glasswing), release-notes/system-prompts/claude-fable-5-1 and a dedicated prompting guide. The model appears on home, intro, choosing-a-model, the models overview tables and the deprecation table (retirement not sooner than September 1, 2027). Mythos 5.1 is described as the same model offered separately by invitation. models/fable-5/overview flips its Status row from "Active (latest)" to "Active (legacy)".

- [models/fable-5-1/overview](https://platform.claude.com/docs/en/models/fable-5-1/overview)
- [models/fable-5-1/migration-guide](https://platform.claude.com/docs/en/models/fable-5-1/migration-guide)
- [models/fable-5-1/whats-new-fable-5-1](https://platform.claude.com/docs/en/models/fable-5-1/whats-new-fable-5-1)
- [models/mythos-5-1/overview](https://platform.claude.com/docs/en/models/mythos-5-1/overview)
- [release-notes/system-prompts/claude-fable-5-1](https://platform.claude.com/docs/en/release-notes/system-prompts/claude-fable-5-1)
- [build-with-claude/prompt-engineering/prompting-claude-fable-5-1](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1)
- …and 12 more

### Claude Fable 5.1 and Mythos 5.1 are added to the per-feature support lists: structured outputs, browser use, advisor, `system.message` events, 1M-token context on Vertex AI and Bedrock, task budgets beta, and the managed-agents model enum.

`additive` · model support · 15 pages

structured-outputs adds `claude-fable-5-1` and `claude-mythos-5-1`; browser-use-tool does the same. advisor-tool notes Fable 5.1 and Mythos 5.1 advisors return the encrypted `advisor_redacted_re…` field. managed-agents pages add the two models to `system.message` support. token-counting says Fable 5.1, Mythos 5.1, Fable 5 and Mythos 5 share the tokenizer introduced with Opus 4.7. task-budgets lists Fable 5.1 as Beta behind `task-budgets-2026-03-13`. `BetaManagedAgentsModel` grows to include `claude-fable-5-1`.

- [build-with-claude/structured-outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)
- [agents-and-tools/tool-use/browser-use-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/browser-use-tool)
- [agents-and-tools/tool-use/advisor-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool)
- [managed-agents/events-and-streaming](https://platform.claude.com/docs/en/managed-agents/events-and-streaming)
- [managed-agents/reference](https://platform.claude.com/docs/en/managed-agents/reference)
- [build-with-claude/working-with-messages](https://platform.claude.com/docs/en/build-with-claude/working-with-messages)
- …and 9 more

### Foundation Model APIs add `databricks-claude-fable-5-1`, `databricks-gemini-3-8-flash`, `databricks-gpt-6-astra` and GLM-5.3, with the per-region availability tables regenerated across every supported region.

`additive` · model availability · 13 pages

supported-models describes GLM-5.3 as a text-only MoE model from Zhipu AI for coding and agentic tool use, and states Claude Fable 5.1 accepts `low`, `medium`, `high`, `xhigh` and `max` effort with reasoning that cannot be disabled. It also warns that Fable 5.1 prompts and responses are retained 30 days for trust and safety and that customers who opt out of data retention cannot use Claude Fable 5.1 — the same condition already documented for Claude Fable 5. The new models appear in the rate-limit, function-calling, vision, reasoning, priority-mode and acceptable-use tables, and in the regional support matrix on foundation-model-overview.

- [machine-learning/foundation-model-apis/supported-models](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/supported-models)
- [machine-learning/foundation-model-apis/limits](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/limits)
- [machine-learning/foundation-model-apis/priority-mode](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/priority-mode)
- [machine-learning/foundation-model-apis/compliance](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/compliance)
- [machine-learning/model-serving/foundation-model-overview](https://docs.databricks.com/aws/en/machine-learning/model-serving/foundation-model-overview)
- [machine-learning/model-serving/query-anthropic-messages](https://docs.databricks.com/aws/en/machine-learning/model-serving/query-anthropic-messages)
- …and 7 more

### Unity Catalog gains ABAC DENY policies (Beta), which explicitly deny a privilege — `MANAGE ACCESS CONTROL` in particular — to principals on tagged securables and always take precedence over grants.

`additive` · new feature · 11 pages

New page data-governance/unity-catalog/abac/deny-policies. core-concepts adds the precedence rule; best-practices adds a DENY row; privileges-reference notes `MANAGE ACCESS CONTROL` can be denied through a DENY policy; the ABAC scoping banners on policies, performance and policy-evaluation now read "GRANT policies and DENY policies (Beta) are not…" where they previously named GRANT alone; and sql-ref security-deny points readers at ABAC DENY policies while restating that `DENY` applies only to `hive_metastore`.

- [data-governance/unity-catalog/abac/deny-policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/deny-policies)
- [data-governance/unity-catalog/abac/core-concepts](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/core-concepts)
- [data-governance/unity-catalog/abac/best-practices](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/best-practices)
- [data-governance/unity-catalog/abac/](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/)
- [data-governance/unity-catalog/abac/policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/policies)
- [data-governance/unity-catalog/abac/performance](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/performance)
- …and 5 more

### A new "built-in MCP services" page collects the Databricks-provided `system.ai.*` MCP services, and existing MCP tool pages are retitled "... MCP server" with links repointed from the old `mcp-services#prebuilt` anchor.

`additive` · restructure · 11 pages

New page agents/mcp-tools/built-in-mcp-services covers workspace tools and common SaaS applications with no server registration. The AI Search, Genie Agent and Unity Catalog functions pages gain "MCP server" in their titles. agents/mcp-tools/databricks-sql now recommends the `system.ai.dbsql` MCP Service.

- [agents/mcp-tools/built-in-mcp-services](https://docs.databricks.com/aws/en/agents/mcp-tools/built-in-mcp-services)
- [agents/mcp-tools/mcp-services](https://docs.databricks.com/aws/en/agents/mcp-tools/mcp-services)
- [agents/mcp-tools/use-mcp-in-agents](https://docs.databricks.com/aws/en/agents/mcp-tools/use-mcp-in-agents)
- [agents/mcp-tools/connect-clients](https://docs.databricks.com/aws/en/agents/mcp-tools/connect-clients)
- [agents/mcp-tools/ai-search](https://docs.databricks.com/aws/en/agents/mcp-tools/ai-search)
- [agents/mcp-tools/genie-agent](https://docs.databricks.com/aws/en/agents/mcp-tools/genie-agent)
- …and 5 more

### Two new SQL functions land: `ai_enrich` (Beta), which generates new columns per row, and `time_bucket`, which returns the start of a fixed-width time bucket aligned to an origin.

`additive` · new functions · 9 pages

Both get reference pages and entries in the built-in function lists; the related AI function pages and `date_trunc` add see-also links.

- [sql/language-manual/functions/ai_enrich](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_enrich)
- [sql/language-manual/functions/time_bucket](https://docs.databricks.com/aws/en/sql/language-manual/functions/time_bucket)
- [sql/language-manual/sql-ref-functions-builtin](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-functions-builtin)
- [sql/language-manual/sql-ref-functions-builtin-alpha](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-functions-builtin-alpha)
- [large-language-models/ai-functions](https://docs.databricks.com/aws/en/large-language-models/ai-functions)
- [sql/language-manual/functions/ai_extract](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_extract)
- …and 3 more

### Turn-scoped system messages arrive in beta: set `clear_at: "next_user_message"` on a `role: "system"` message (header `mid-conversation-system-clear-at-2026-08-21`) so a per-turn reminder renders once instead of accumulating.

`additive` · beta feature · 7 pages

`clear_at` defaults to `"never"` (renders on every request that includes it). The same page adds a second beta: a `role: "system"` message can carry `output_config.effort` to change effort from the next user turn on, requiring `mid-conversation-output-config-2026-07-01`, on Fable 5.1, Mythos 5.1 and Opus 5 on the Claude API. Mid-conversation system messages and tool changes are now listed as available on Fable 5.1 and Mythos 5.1 as well; they remain unavailable on Claude Sonnet 5. The `clear_at` field description appears throughout the beta Messages reference.

- [build-with-claude/mid-conversation-system-messages](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages)
- [api/beta/messages](https://platform.claude.com/docs/en/api/beta/messages)
- [api/beta/messages/create](https://platform.claude.com/docs/en/api/beta/messages/create)
- [api/beta/messages/count_tokens](https://platform.claude.com/docs/en/api/beta/messages/count_tokens)
- [api/beta/messages/batches](https://platform.claude.com/docs/en/api/beta/messages/batches)
- [api/beta/messages/batches/create](https://platform.claude.com/docs/en/api/beta/messages/batches/create)
- …and 1 more

### Serverless environment version 6 ships with CPU and GPU release notes, and the AI Runtime environment picker adds "Standard v6" alongside v5 and v4.

`additive` · new release · 6 pages

New pages for environment version 6 and GPU environment 6; the version index table adds a row 6 with its OS and library set. The version 5 notes restate that the Py4J gateway is off, replacing `dbutils.entry_point` and `dbutils.notebook.entry_point`, and the GPU 5 notes add a top-level `ray_init()` drop-in that enables the Ray dashboard.

- [release-notes/serverless/environment-version/six](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/six)
- [release-notes/serverless/environment-version/six-gpu](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/six-gpu)
- [release-notes/serverless/environment-version/](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/)
- [machine-learning/ai-runtime/environment](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/environment)
- [release-notes/serverless/environment-version/five](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/five)
- [release-notes/serverless/environment-version/five-gpu](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/five-gpu)

### The HubSpot connector can now ingest from CRM Hub in Beta, where previously it supported Marketing Hub only.

`additive` · new capability · 5 pages

hubspot-limits changes from "The HubSpot connector only supports ingestion from HubSpot Marketing Hub" to supporting both hubs with CRM Hub in Beta. The pipeline example ingests `marketing_emails` (Marketing Hub) and `contacts` (CRM Hub); source-setup drops the "to ingest HubSpot CRM Hub objects" qualifier from the extra `auth.requiredScopes`.

- [ingestion/lakeflow-connect/hubspot-limits](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-limits)
- [ingestion/lakeflow-connect/hubspot-overview](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-overview)
- [ingestion/lakeflow-connect/hubspot-source-setup](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-source-setup)
- [ingestion/lakeflow-connect/hubspot-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-pipeline)
- [ingestion/lakeflow-connect/hubspot-reference](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-reference)

### Integrated CDC pipelines can run in continuous (always-on) mode, with scale-optimized or speed-optimized run modes; triggered remains the default.

`additive` · new capability · 5 pages

New page ingestion/lakeflow-connect/continuous-integrated-cdc. The MySQL, Oracle and SQL Server integrated-pipeline pages replace "Triggered (scheduled) execution meets your needs" with "Triggered by default … schedule them using a Lakeflow Jobs task. Continuous…" and link the new page, as does the common-patterns table.

- [ingestion/lakeflow-connect/continuous-integrated-cdc](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/continuous-integrated-cdc)
- [ingestion/lakeflow-connect/mysql-integrated-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/mysql-integrated-pipeline)
- [ingestion/lakeflow-connect/oracle-integrated-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/oracle-integrated-pipeline)
- [ingestion/lakeflow-connect/sql-server-integrated-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/sql-server-integrated-pipeline)
- [ingestion/lakeflow-connect/common-patterns](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/common-patterns)

### Cross-workspace access (Beta) lets you control which source workspaces can reach a workspace over serverless traffic, as ingress rules on context-based ingress policies and matching egress entries in network policies.

`additive` · new feature · 5 pages

New page security/network/front-end/cross-workspace-access. context-based-ingress documents the new control and notes a policy can be left in compatibility mode, in which case it does not govern cross-workspace ingress. network-policies adds allowing specific Databricks workspaces as egress destinations, and notes MCP Services are subject to serverless egress control in the same way.

- [security/network/front-end/cross-workspace-access](https://docs.databricks.com/aws/en/security/network/front-end/cross-workspace-access)
- [security/network/front-end/context-based-ingress](https://docs.databricks.com/aws/en/security/network/front-end/context-based-ingress)
- [security/network/front-end/manage-ingress-policies](https://docs.databricks.com/aws/en/security/network/front-end/manage-ingress-policies)
- [security/network/serverless-network-security/network-policies](https://docs.databricks.com/aws/en/security/network/serverless-network-security/network-policies)
- [security/network/serverless-network-security/](https://docs.databricks.com/aws/en/security/network/serverless-network-security/)

### Unity Gateway Skills publish SKILL.md instruction files into a Unity Catalog schema, governed by Unity Catalog grants and audit, and loadable by agents over MCP or by download.

`additive` · new feature · 5 pages

Three new pages under agents/uc-skills/ cover the concept, publishing and sharing a skill, and connecting a coding agent with the Unity Gateway CLI. ai-gateway/govern-skills covers enabling the feature, setting up a governed schema, and the create/write/read privileges.

- [agents/uc-skills/](https://docs.databricks.com/aws/en/agents/uc-skills/)
- [agents/uc-skills/create-share-uc-skills](https://docs.databricks.com/aws/en/agents/uc-skills/create-share-uc-skills)
- [agents/uc-skills/use-uc-skills](https://docs.databricks.com/aws/en/agents/uc-skills/use-uc-skills)
- [ai-gateway/govern-skills](https://docs.databricks.com/aws/en/ai-gateway/govern-skills)
- [agent-skills/](https://docs.databricks.com/aws/en/agent-skills/)

### New beta endpoints let you retrieve and update organization compliance settings.

`additive` · new endpoints · 4 pages

Three new reference pages under api/beta/organization/compliance_settings. manage-claude/compliance-api adds that every endpoint lives under `/v1/compliance/*` on `https://api.anthropic.com` and authenticates through `x-api-key`.

- [api/beta/organization/compliance_settings](https://platform.claude.com/docs/en/api/beta/organization/compliance_settings)
- [api/beta/organization/compliance_settings/retrieve](https://platform.claude.com/docs/en/api/beta/organization/compliance_settings/retrieve)
- [api/beta/organization/compliance_settings/update](https://platform.claude.com/docs/en/api/beta/organization/compliance_settings/update)
- [manage-claude/compliance-api](https://platform.claude.com/docs/en/manage-claude/compliance-api)

### Zerobus Ingest can now write into tables backed by default storage (Public Preview); the flat "Writing to default storage is not supported" restriction is gone.

`additive` · new capability · 4 pages

zerobus-release-stages adds a Public Preview row for "Ingesting into tables backed by default storage". zerobus-concepts trims its limitation from "Zerobus Ingest writes only to managed Delta tables. Writing to default storage is not supported." to just the first sentence.

- [ingestion/zerobus-release-stages](https://docs.databricks.com/aws/en/ingestion/zerobus-release-stages)
- [ingestion/zerobus-concepts](https://docs.databricks.com/aws/en/ingestion/zerobus-concepts)
- [ingestion/zerobus-overview](https://docs.databricks.com/aws/en/ingestion/zerobus-overview)
- [ingestion/zerobus-ingest](https://docs.databricks.com/aws/en/ingestion/zerobus-ingest)

### Git Folder Serverless (Beta) lets notebooks and files in a Git folder share one serverless compute resource and an environment managed by `pyproject.toml`.

`additive` · new feature · 4 pages

New page compute/serverless/notebooks/git-folder-serverless, listed as Beta on the serverless index. compute/serverless/dependencies distinguishes the pyproject-managed Git folder environment from the standard serverless notebook environment panel.

- [compute/serverless/notebooks/git-folder-serverless](https://docs.databricks.com/aws/en/compute/serverless/notebooks/git-folder-serverless)
- [compute/serverless/](https://docs.databricks.com/aws/en/compute/serverless/)
- [compute/serverless/notebooks](https://docs.databricks.com/aws/en/compute/serverless/notebooks)
- [compute/serverless/dependencies](https://docs.databricks.com/aws/en/compute/serverless/dependencies)

### Feature Store adds a `SawtoothWindow` time-window class that keeps long aggregation windows continuously fresh, and a `CustomUDF` function type that applies a registered Unity Catalog function row-wise.

`additive` · new capability · 4 pages

The API reference documents SawtoothWindow's constraints: it requires a `StreamSource` (a `DeltaTableSource` is not supported), does not support the `delay` parameter, and supports only `Sum`, `Avg`, `Count`, `Min` and `Max`. `transformation_sql` is documented as row-wise only — aggregations such as `SUM()` or `COUNT()` are not supported there — and requires `dataframe_schema`. streams adds Kafka schema-registry options on the Unity Catalog connection.

- [machine-learning/feature-store/feature-views-api-reference](https://docs.databricks.com/aws/en/machine-learning/feature-store/feature-views-api-reference)
- [machine-learning/feature-store/feature-views](https://docs.databricks.com/aws/en/machine-learning/feature-store/feature-views)
- [release-notes/feature-store/databricks-feature-store](https://docs.databricks.com/aws/en/release-notes/feature-store/databricks-feature-store)
- [machine-learning/feature-store/streams](https://docs.databricks.com/aws/en/machine-learning/feature-store/streams)

### Automatic identity management adds an Okta migration guide and a readiness report that finds external-ID and group-membership divergences between Databricks and your identity provider before you migrate off SCIM.

`additive` · new guidance · 4 pages

Two new pages; the existing Entra ID migration page and the section index were reorganised alongside them.

- [admin/users-groups/automatic-identity-management/migrate-to-aim-okta](https://docs.databricks.com/aws/en/admin/users-groups/automatic-identity-management/migrate-to-aim-okta)
- [admin/users-groups/automatic-identity-management/readiness-report](https://docs.databricks.com/aws/en/admin/users-groups/automatic-identity-management/readiness-report)
- [admin/users-groups/automatic-identity-management/](https://docs.databricks.com/aws/en/admin/users-groups/automatic-identity-management/)
- [admin/users-groups/automatic-identity-management/migrate-to-aim](https://docs.databricks.com/aws/en/admin/users-groups/automatic-identity-management/migrate-to-aim)

### A Unity Catalog schema can now be backed by AWS Secrets Manager or Azure Key Vault so secret values stay in your cloud secret manager while remaining governable in Unity Catalog.

`additive` · new feature · 3 pages

Two new pages plus updates to unity-catalog-secrets, which adds an example retrieving a secret value and passing it to `dbutils.credentials.getServiceCredentialsProvider` to configure a boto client.

- [security/secrets/external-secrets](https://docs.databricks.com/aws/en/security/secrets/external-secrets)
- [security/secrets/configure-external-secrets](https://docs.databricks.com/aws/en/security/secrets/configure-external-secrets)
- [security/secrets/unity-catalog-secrets](https://docs.databricks.com/aws/en/security/secrets/unity-catalog-secrets)

### Lakebase documents HIPAA support: how to enable it on projects in compliance-security-profile workspaces, the shared responsibility for PHI, and how HIPAA audit logs land in the Unity Catalog audit log system table.

`additive` · compliance · 3 pages

Three new pages. security/privacy/hipaa adds a line telling you to enable the compliance security profile on every workspace that processes PHI.

- [oltp/projects/hipaa-compliance](https://docs.databricks.com/aws/en/oltp/projects/hipaa-compliance)
- [oltp/projects/enable-hipaa-compliance](https://docs.databricks.com/aws/en/oltp/projects/enable-hipaa-compliance)
- [oltp/projects/hipaa-audit-logging](https://docs.databricks.com/aws/en/oltp/projects/hipaa-audit-logging)

### Lakebase PCI-DSS and HITRUST support expands from the `us-east-1` region to all AWS regions where Lakebase is available.

`additive` · availability · 3 pages

Both pages change "PCI-DSS and HITRUST are now supported in the `us-east-1` region on AWS" to "supported in all AWS regions where Lakebase is available". The Lakebase release notes reword availability for compliance-security-profile workspaces from "available by default" to "enabled by default".

- [oltp/projects/data-protection](https://docs.databricks.com/aws/en/oltp/projects/data-protection)
- [oltp/projects/private-link](https://docs.databricks.com/aws/en/oltp/projects/private-link)
- [release-notes/lakebase/](https://docs.databricks.com/aws/en/release-notes/lakebase/)

### Values in `FILE` columns can be previewed directly in SQL editor query results, subject to access on both the file and the table.

`additive` · new capability · 3 pages

sql-editor/results describes the preview affordance and states that for a `FILE EXTERNAL` column you need the `READ VO…` privilege as well. unstructured/file notes that casting a `FILE` value to `BINARY` or `STRING`, passing it to an AI function or UDF, and previewing it all read file content.

- [sql/language-manual/data-types/file-type](https://docs.databricks.com/aws/en/sql/language-manual/data-types/file-type)
- [sql/user/sql-editor/results](https://docs.databricks.com/aws/en/sql/user/sql-editor/results)
- [unstructured/file](https://docs.databricks.com/aws/en/unstructured/file)

### A new Claude Agent SDK cookbook recipe builds a scheduled, read-only repository reviewer that resumes its session and returns schema-validated verdicts.

`additive` · new recipe · 2 pages

New page, indexed on the cookbook landing page under the Claude Agent SDK and Agents categories, dated Aug 2026.

- [platform.claude.com/cookbook/claude-agent-sdk-scheduled-repository-reviewer-scheduled-repository-reviewer](https://platform.claude.com/cookbook/claude-agent-sdk-scheduled-repository-reviewer-scheduled-repository-reviewer)
- [platform.claude.com/cookbook/](https://platform.claude.com/cookbook/)

### Marketplace providers whose backing cloud storage sits behind a firewall or private endpoint can use SecureConnect, enabled on the provider metastore that hosts the shares.

`additive` · new capability · 2 pages

create-listing adds the enablement step and notes Marketplace creates a recipient per consumer. secureconnect-provider states SecureConnect also applies to Marketplace data products, and that it can't be used with recipients reading shared data through SAP HANA, which does not support the Databricks protocol.

- [marketplace/create-listing](https://docs.databricks.com/aws/en/marketplace/create-listing)
- [opensharing/secureconnect-provider](https://docs.databricks.com/aws/en/opensharing/secureconnect-provider)

### Claude Fable 5.1 and Mythos 5.1 price prompt-cache hits at 0.025x base input ($0.25/MTok) instead of the 0.1x multiplier every other model uses.

`additive` · pricing · 1 page

The pricing table adds Fable 5.1 and Mythos 5.1 at $10/MTok input, $50/MTok output, $12.50 5m cache write, $20 1h cache write — and a footnote stating cache hits and refreshes on these two models are 0.025x the base input price, versus the standard 0.1x. The cache-multiplier table and prose were updated to match, and batch pricing rows ($5 in / $25 out) were added. The rest of the table is a header-casing rewrite.

- [about-claude/pricing](https://platform.claude.com/docs/en/about-claude/pricing)

### September 2026 Databricks product release notes are published.

`additive` · release notes · 1 page

New monthly page collecting the month's feature announcements.

- [release-notes/product/2026/september](https://docs.databricks.com/aws/en/release-notes/product/2026/september)

## Editorial — 11

### "Unity AI Gateway" is renamed "Unity Gateway" throughout the Databricks docs, including in past release-note titles, and a release-notes/unity-gateway/ hub appears.

`editorial` · product rename · 33 pages

A uniform string substitution across the AI Gateway chapter, Unity Catalog governance pages, budgets, entitlements and historical release notes. The cited pages are a representative subset of a much larger set. No behaviour changes accompany the rename.

- [ai-gateway/](https://docs.databricks.com/aws/en/ai-gateway/)
- [ai-gateway/ai-governance](https://docs.databricks.com/aws/en/ai-gateway/ai-governance)
- [ai-gateway/overview-serving-endpoints](https://docs.databricks.com/aws/en/ai-gateway/overview-serving-endpoints)
- [ai-gateway/model-services](https://docs.databricks.com/aws/en/ai-gateway/model-services)
- [ai-gateway/agent-services](https://docs.databricks.com/aws/en/ai-gateway/agent-services)
- [ai-gateway/govern-model-services](https://docs.databricks.com/aws/en/ai-gateway/govern-model-services)
- …and 27 more

### Admin API curl examples rename the shell variable `$ANTHROPIC_OAUTH_TOKEN` to `$ANTHROPIC_AUTH_TOKEN` across the whole admin reference.

`editorial` · example rename · 31 pages

A mechanical substitution in `-H "Authorization: Bearer …"` lines on roughly eighty admin and beta-admin endpoint pages; the change list above is a representative subset. No behaviour or requirement text changes with it.

- [api/admin/api_keys](https://platform.claude.com/docs/en/api/admin/api_keys)
- [api/admin/api_keys/list](https://platform.claude.com/docs/en/api/admin/api_keys/list)
- [api/admin/api_keys/retrieve](https://platform.claude.com/docs/en/api/admin/api_keys/retrieve)
- [api/admin/api_keys/update](https://platform.claude.com/docs/en/api/admin/api_keys/update)
- [api/admin/cost_report](https://platform.claude.com/docs/en/api/admin/cost_report)
- [api/admin/cost_report/retrieve](https://platform.claude.com/docs/en/api/admin/cost_report/retrieve)
- …and 25 more

### The beta API reference was regenerated: the `anthropic-beta` enum summary moves from "38 more" to "41 more", model descriptions and filter-parameter prose were re-cased and backticked across hundreds of endpoint pages.

`editorial` · bulk regeneration · 30 pages

Most of this run's page count is this regeneration. Visible shapes: the beta-header enum tail count changing from 38 to 41; model blurbs such as "Frontier intelligence for ambitious tasks…" being re-emitted; descriptions like "Filter by status: active or paused" gaining backticks; `BetaManagedAgentsModel` unions growing from "10 more" to "11 more" as Fable 5.1 is added. Treat individual entries in this set as formatting unless a specific finding above names them.

- [api/beta/deployments](https://platform.claude.com/docs/en/api/beta/deployments)
- [api/beta/deployments/create](https://platform.claude.com/docs/en/api/beta/deployments/create)
- [api/beta/deployments/list](https://platform.claude.com/docs/en/api/beta/deployments/list)
- [api/beta/environments](https://platform.claude.com/docs/en/api/beta/environments)
- [api/beta/environments/work](https://platform.claude.com/docs/en/api/beta/environments/work)
- [api/beta/files](https://platform.claude.com/docs/en/api/beta/files)
- …and 24 more

### The single "Use Genie Code" page is split into features-capabilities, agent-mode, navigate-genie-code, web-search and full-page, and every inbound link across the corpus is repointed.

`editorial` · restructure · 24 pages

New pages cover Agent mode (multi-step planning with tool-approval prompts), the full-page command centre, the chat pane and settings, and public web search with source citations. genie-code/use-genie-code itself is heavily trimmed. Most of the link churn in this run under notebooks/, machine-learning/ and getting-started/ is this repointing, not a content change.

- [genie-code/features-capabilities](https://docs.databricks.com/aws/en/genie-code/features-capabilities)
- [genie-code/agent-mode](https://docs.databricks.com/aws/en/genie-code/agent-mode)
- [genie-code/navigate-genie-code](https://docs.databricks.com/aws/en/genie-code/navigate-genie-code)
- [genie-code/web-search](https://docs.databricks.com/aws/en/genie-code/web-search)
- [genie-code/full-page](https://docs.databricks.com/aws/en/genie-code/full-page)
- [genie-code/use-genie-code](https://docs.databricks.com/aws/en/genie-code/use-genie-code)
- …and 18 more

### "Databricks Data Intelligence Platform" is renamed "Databricks Data + AI Platform" across architecture, migration and getting-started content.

`editorial` · product rename · 23 pages

Prose-only substitution, including in image alt text ("MLOps on the Databricks platform-name"). Some pages show placeholder artefacts such as "Databricks platform-name" where the token was not resolved.

- [lakehouse-architecture/cost-optimization/best-practices](https://docs.databricks.com/aws/en/lakehouse-architecture/cost-optimization/best-practices)
- [lakehouse-architecture/interoperability-and-usability/best-practices](https://docs.databricks.com/aws/en/lakehouse-architecture/interoperability-and-usability/best-practices)
- [lakehouse-architecture/reference](https://docs.databricks.com/aws/en/lakehouse-architecture/reference)
- [lakehouse-architecture/](https://docs.databricks.com/aws/en/lakehouse-architecture/)
- [lakehouse-architecture/scope](https://docs.databricks.com/aws/en/lakehouse-architecture/scope)
- [lakehouse-architecture/data-governance/best-practices](https://docs.databricks.com/aws/en/lakehouse-architecture/data-governance/best-practices)
- …and 17 more

### Cookbook recipes move off the retired `claude-opus-4-1` to `claude-opus-4-8` in their `MODEL_NAME` constants and client calls.

`editorial` · example update · 18 pages

A uniform substitution across eighteen notebooks. The pricing page lists Claude Opus 4.1 as retired except on Bedrock and Google Cloud, which is consistent with the move, though the cookbook pages themselves say nothing about retirement.

- [platform.claude.com/cookbook/misc-building-evals](https://platform.claude.com/cookbook/misc-building-evals)
- [platform.claude.com/cookbook/misc-how-to-enable-json-mode](https://platform.claude.com/cookbook/misc-how-to-enable-json-mode)
- [platform.claude.com/cookbook/misc-how-to-make-sql-queries](https://platform.claude.com/cookbook/misc-how-to-make-sql-queries)
- [platform.claude.com/cookbook/multimodal-best-practices-for-vision](https://platform.claude.com/cookbook/multimodal-best-practices-for-vision)
- [platform.claude.com/cookbook/multimodal-getting-started-with-vision](https://platform.claude.com/cookbook/multimodal-getting-started-with-vision)
- [platform.claude.com/cookbook/multimodal-how-to-transcribe-text](https://platform.claude.com/cookbook/multimodal-how-to-transcribe-text)
- …and 12 more

### Beta and Preview callouts were reformatted across many pages, replacing a bare "Beta:" marker with a full sentence linking the release-types page.

`editorial` · admonition reformat · 10 pages

Both the old marker and the new banner appear in these diffs, so a page losing the "**Beta:**" line has not necessarily changed release stage. Two pages also gain a pricing caveat: compute/serverless/sandbox and dev-tools/ssh-tunnel now say Databricks does not currently charge for the feature but that cost and pricing for Beta features are subject to change.

- [ingestion/lakeflow-connect/salesforce-connection](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/salesforce-connection)
- [sql/user/queries/query-profile](https://docs.databricks.com/aws/en/sql/user/queries/query-profile)
- [sql/user/queries/performance-insights](https://docs.databricks.com/aws/en/sql/user/queries/performance-insights)
- [genie-code/scheduled-tasks](https://docs.databricks.com/aws/en/genie-code/scheduled-tasks)
- [uc-semantics/metric-views/manage](https://docs.databricks.com/aws/en/uc-semantics/metric-views/manage)
- [ingestion/zerobus-arrow-flight](https://docs.databricks.com/aws/en/ingestion/zerobus-arrow-flight)
- …and 4 more

### Cookbook install cells switch from the shell escape `!pip install` to the notebook magic `%pip install`.

`editorial` · example update · 8 pages

Mechanical change to the dependency cells; no package or version changes accompany it.

- [platform.claude.com/cookbook/capabilities-classification-guide](https://platform.claude.com/cookbook/capabilities-classification-guide)
- [platform.claude.com/cookbook/capabilities-contextual-embeddings-guide](https://platform.claude.com/cookbook/capabilities-contextual-embeddings-guide)
- [platform.claude.com/cookbook/capabilities-summarization-guide](https://platform.claude.com/cookbook/capabilities-summarization-guide)
- [platform.claude.com/cookbook/capabilities-retrieval-augmented-generation-guide](https://platform.claude.com/cookbook/capabilities-retrieval-augmented-generation-guide)
- [platform.claude.com/cookbook/finetuning-finetuning-on-bedrock](https://platform.claude.com/cookbook/finetuning-finetuning-on-bedrock)
- [platform.claude.com/cookbook/misc-sampling-past-max-tokens](https://platform.claude.com/cookbook/misc-sampling-past-max-tokens)
- …and 2 more

### The AI Functions hub is retitled from "Enrich data using AI Functions" to "Transform unstructured data using AI Functions", and inbound links are relabelled.

`editorial` · page rename · 8 pages

Link-text-only change across the AI functions, batch inference, designer and release-note pages.

- [large-language-models/batch-inference-pipelines](https://docs.databricks.com/aws/en/large-language-models/batch-inference-pipelines)
- [large-language-models/ai-functions-uc-permissions](https://docs.databricks.com/aws/en/large-language-models/ai-functions-uc-permissions)
- [designer/built-in-operators](https://docs.databricks.com/aws/en/designer/built-in-operators)
- [mlflow3/genai/tracing/redact-pii-otel-traces](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/redact-pii-otel-traces)
- [machine-learning/foundation-model-apis/](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/)
- [volumes/unstructured-data-tutorial](https://docs.databricks.com/aws/en/volumes/unstructured-data-tutorial)
- …and 2 more

### Install snippets bump the Java SDK from 2.58.0 to 2.60.0 (including `anthropic-java-aws`) and the `ant` CLI from 1.27.0 to 1.30.0.

`editorial` · version bump · 4 pages

Dependency coordinates only; no behaviour described.

- [cli-sdks-libraries/sdks/java](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/java)
- [get-started](https://platform.claude.com/docs/en/get-started)
- [build-with-claude/claude-platform-on-aws](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws)
- [cli-sdks-libraries/cli/quickstart](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/quickstart)

### The documented 32 TB per-branch database storage quota is replaced by an unquantified "database storage quota".

`editorial` · limit removed from docs · 2 pages

Both pages now read "Each branch has a database storage quota. This is an operational quota rather than an architectural limit, because data lives in cloud object…". The pages do not say the limit changed, only that the number is no longer stated.

- [oltp/instances/create/](https://docs.databricks.com/aws/en/oltp/instances/create/)
- [oltp/projects/manage-projects](https://docs.databricks.com/aws/en/oltp/projects/manage-projects)
