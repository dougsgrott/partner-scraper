# Change digest

> #5 (2026-09-09-before) → #6 (2026-09-09) · 1,072 changes · rendered 2026-09-19T12:06:58+00:00

## At a glance

79 findings — **5** breaking, **26** behavioural, **36** additive, **12** editorial — covering 555 of 1,072 changed pages. Anything not here is in the full feed report beside this file.

**If you read nothing else:**

1. New 'Preserved thinking' rules: a thinking block is usable only by the model that produced it or a newer one, and on Claude Fable 5.1 the API also checks that nothing before the block changed — for accounts created on or after August 31, 2026, replaying an invalidated block returns a 400 error unless you opt into dropping it.
2. The change data feed requirements are raised from Databricks Runtime 18 LTS or above to Databricks Runtime 19 or above (with Unity Catalog tables and row tracking).
3. The web fetch tool now states it cannot fetch URLs that appear only in the system prompt (include the URL in a user message to make it fetchable), nor URLs from other server-side tools such as code execution, the MCP connector, or tool search.
4. The TypeScript SDK now states TypeScript >= 5.0 is supported, up from >= 4.9.
5. BigQuery INTERVAL columns are not supported: a foreign table containing one fails when its schema loads.

---

## Breaking — 5

### New 'Preserved thinking' rules: a thinking block is usable only by the model that produced it or a newer one, and on Claude Fable 5.1 the API also checks that nothing before the block changed — for accounts created on or after August 31, 2026, replaying an invalidated block returns a 400 error unless you opt into dropping it.

`breaking` · thinking blocks · 8 pages

A new Preserved thinking page documents the rule; context editing adds that server-side context management never invalidates blocks on Fable 5.1 but client-side edits to earlier turns do, and that Fable and Mythos models default to keeping all prior thinking turns. The `thinking-binding-controls-2026-08-01` beta header reports dropped blocks in an `input_transformations` response field and adds `thinking.block_binding.prefix_mismatch_behavior` to choose between rejecting and dropping (`drop_block`) mismatched blocks; the computer-use and troubleshooting pages point at that setting when pruning history.

- [build-with-claude/preserved-thinking](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking)
- [build-with-claude/thinking](https://platform.claude.com/docs/en/build-with-claude/thinking)
- [build-with-claude/thinking-troubleshooting](https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting)
- [build-with-claude/context-editing](https://platform.claude.com/docs/en/build-with-claude/context-editing)
- [build-with-claude/context-windows](https://platform.claude.com/docs/en/build-with-claude/context-windows)
- [agents-and-tools/tool-use/computer-use-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool)
- …and 2 more

### The change data feed requirements are raised from Databricks Runtime 18 LTS or above to Databricks Runtime 19 or above (with Unity Catalog tables and row tracking).

`breaking` · version floor · 3 pages

The September release notes list 'Automatic change data feed is now generally available', and the DBR 19 notes add a feature that works with batch queries, Structured Streaming and Delta Sharing requiring DBR 19 LTS or above with row tracking.

- [tables/features/change-data-feed](https://docs.databricks.com/aws/en/tables/features/change-data-feed)
- [release-notes/runtime/19](https://docs.databricks.com/aws/en/release-notes/runtime/19)
- [release-notes/product/2026/september](https://docs.databricks.com/aws/en/release-notes/product/2026/september)

### The web fetch tool now states it cannot fetch URLs that appear only in the system prompt (include the URL in a user message to make it fetchable), nor URLs from other server-side tools such as code execution, the MCP connector, or tool search.

`breaking` · tool restriction · 1 page

Client-side tool results remain an allowed source even when they echo text Claude produced. The earlier wording only said Claude may not dynamically construct URLs and may fetch URLs provided by the user or from previous web search/fetch results. Dynamic filtering with `web_fetch_20260318` now also lists Fable 5.1 and Mythos 5.1.

- [agents-and-tools/tool-use/web-fetch-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-fetch-tool)

### The TypeScript SDK now states TypeScript >= 5.0 is supported, up from >= 4.9.

`breaking` · version floor · 1 page

- [cli-sdks-libraries/sdks/typescript](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/typescript)

### BigQuery INTERVAL columns are not supported: a foreign table containing one fails when its schema loads.

`breaking` · limitation · 1 page

The type-mapping table previously mapped INTERVAL alongside ARRAY, GEOGRAPHY, JSON, STRING and STRUCT to VarcharType.

- [query-federation/bigquery](https://docs.databricks.com/aws/en/query-federation/bigquery)

## Behavioural — 26

### MLflow GenAI tracing examples now store traces in Unity Catalog, which requires `mlflow[databricks]>=3.14.0` (up from >=3.1) and a SQL warehouse configured via `MLFLOW_TRACING_SQL_WAREHOUSE_ID`.

`behavioural` · version floor · 34 pages

The integrations index states the quick-start examples require MLflow 3.14 or later for that reason; examples import `UnityCatalog` from `mlflow.entities.trace_location` instead of calling `mlflow.set_experiment` with a workspace path. Claude Code CLI tracing moves from MLflow 3.4+ to 3.14+.

- [mlflow3/genai/tracing/integrations/](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/)
- [mlflow3/genai/tracing/integrations/openai](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/openai)
- [mlflow3/genai/tracing/integrations/anthropic](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/anthropic)
- [mlflow3/genai/tracing/integrations/bedrock](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/bedrock)
- [mlflow3/genai/tracing/integrations/langchain](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/langchain)
- [mlflow3/genai/tracing/integrations/langgraph](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/langgraph)
- …and 28 more

### Admin API pages for federation issuers, federation rules and service accounts now state a single requirement: an OAuth access token with the `org:admin` scope, from `ant auth login --scope org:admin` or a workload identity federation rule.

`behavioural` · authentication · 32 pages

The previous per-endpoint wording ('Requires an OAuth bearer or Console session; Admin API keys are not accepted', with scope varying by endpoint) is replaced by this uniform statement.

- [api/admin/federation_issuers](https://platform.claude.com/docs/en/api/admin/federation_issuers)
- [api/admin/federation_issuers/create](https://platform.claude.com/docs/en/api/admin/federation_issuers/create)
- [api/admin/federation_issuers/update](https://platform.claude.com/docs/en/api/admin/federation_issuers/update)
- [api/admin/federation_issuers/archive](https://platform.claude.com/docs/en/api/admin/federation_issuers/archive)
- [api/admin/federation_issuers/list](https://platform.claude.com/docs/en/api/admin/federation_issuers/list)
- [api/admin/federation_issuers/retrieve](https://platform.claude.com/docs/en/api/admin/federation_issuers/retrieve)
- …and 26 more

### AI Runtime GPU tutorials now state a minimum environment version (mostly v5, v6 for the XGBoost example) instead of UI click-paths, and the new `ray_init()` helper requires environment version 5 or later.

`behavioural` · requirement · 21 pages

A new Ray Data + vLLM multilingual batch-inference tutorial across 8 H100s is added; `ray_init()` is a drop-in for `ray.init()` that enables the Ray dashboard.

- [machine-learning/ai-runtime/ray](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/ray)
- [release-notes/serverless/environment-version/five-gpu](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/five-gpu)
- [machine-learning/ai-runtime/examples/tutorials/sgc-xgboost](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-xgboost)
- [machine-learning/ai-runtime/examples/tutorials/sgc-api-h100-starter](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-api-h100-starter)
- [machine-learning/ai-runtime/examples/tutorials/sgc-cnn-mnist](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-cnn-mnist)
- [machine-learning/ai-runtime/examples/tutorials/sgc-distributed-finetune-qwen2-0.5b](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-distributed-finetune-qwen2-0.5b)
- …and 15 more

### CMEK docs now state that on Claude Platform on AWS the KMS key must be a single-Region key in your organization's own AWS account and that cross-account keys are not supported.

`behavioural` · cmek · 15 pages

The cmek-aws-kms guide adds troubleshooting advice: retry with the `aws:SourceArn` condition temporarily removed to tell a source-ARN mismatch apart from an encryption-context mismatch, and notes the picker only lists enabled, compatible keys.

- [api/admin/external_keys](https://platform.claude.com/docs/en/api/admin/external_keys)
- [api/admin/external_keys/create](https://platform.claude.com/docs/en/api/admin/external_keys/create)
- [api/admin/external_keys/update](https://platform.claude.com/docs/en/api/admin/external_keys/update)
- [api/admin/external_keys/list](https://platform.claude.com/docs/en/api/admin/external_keys/list)
- [api/admin/external_keys/retrieve](https://platform.claude.com/docs/en/api/admin/external_keys/retrieve)
- [api/beta/organization/external_keys](https://platform.claude.com/docs/en/api/beta/organization/external_keys)
- …and 9 more

### The Claude Enterprise Admin, Analytics and Compliance API guides now show the `anthropic-version` header and say to send it on every request to those endpoints.

`behavioural` · api requirement · 8 pages

Per the September 1 release-notes entry, this brings these endpoints in line with the rest of the Claude API; the curl examples on the compliance and access-transparency pages were updated accordingly.

- [manage-claude/compliance-api](https://platform.claude.com/docs/en/manage-claude/compliance-api)
- [manage-claude/compliance-activity-feed](https://platform.claude.com/docs/en/manage-claude/compliance-activity-feed)
- [manage-claude/compliance-org-data](https://platform.claude.com/docs/en/manage-claude/compliance-org-data)
- [manage-claude/compliance-content-data](https://platform.claude.com/docs/en/manage-claude/compliance-content-data)
- [manage-claude/access-transparency](https://platform.claude.com/docs/en/manage-claude/access-transparency)
- [manage-claude/user-management](https://platform.claude.com/docs/en/manage-claude/user-management)
- …and 2 more

### C# workload-identity examples replace `new AnthropicOidcClient(credentials)` with `new AnthropicClient(new ClientOptions { Credentials = credentials })`.

`behavioural` · sdk · 7 pages

The GitHub Actions and Kubernetes samples also drop the explicit throw on missing federation credentials in favour of reading ANTHROPIC_SERVICE_ACCOUNT_ID / ANTHROPIC_WORKSPACE_ID / ANTHROPIC_IDENTITY_TOKEN_FILE from the environment.

- [manage-claude/wif-providers/azure](https://platform.claude.com/docs/en/manage-claude/wif-providers/azure)
- [manage-claude/wif-providers/gcp](https://platform.claude.com/docs/en/manage-claude/wif-providers/gcp)
- [manage-claude/wif-providers/okta](https://platform.claude.com/docs/en/manage-claude/wif-providers/okta)
- [manage-claude/wif-providers/aws](https://platform.claude.com/docs/en/manage-claude/wif-providers/aws)
- [manage-claude/wif-providers/github-actions](https://platform.claude.com/docs/en/manage-claude/wif-providers/github-actions)
- [manage-claude/wif-providers/kubernetes](https://platform.claude.com/docs/en/manage-claude/wif-providers/kubernetes)
- …and 1 more

### The 30-day retention requirement is now stated for the whole Claude Fable and Mythos family (including 5.1), with a new carve-out: they are unavailable under zero data retention unless expressly authorized by Anthropic.

`behavioural` · data retention · 6 pages

Previously the pages named Claude Fable 5 / Mythos 5 specifically and said ZDR was simply not available. The CMEK page likewise widens its structured-outputs exception from 'Claude Fable 5 or Claude Mythos models' to 'Claude Fable or Claude Mythos models'.

- [manage-claude/api-and-data-retention](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention)
- [build-with-claude/overview](https://platform.claude.com/docs/en/build-with-claude/overview)
- [models/fable-5/migration-guide](https://platform.claude.com/docs/en/models/fable-5/migration-guide)
- [about-claude/models/introducing-claude-fable-5-and-claude-mythos-5](https://platform.claude.com/docs/en/about-claude/models/introducing-claude-fable-5-and-claude-mythos-5)
- [models/fable-5/introducing-claude-fable-5-and-claude-mythos-5](https://platform.claude.com/docs/en/models/fable-5/introducing-claude-fable-5-and-claude-mythos-5)
- [manage-claude/cmek](https://platform.claude.com/docs/en/manage-claude/cmek)

### The IAM role ARN field on external keys is marked deprecated — Anthropic now reaches the KMS key through its own intermediate role (or, on Claude Platform on AWS, with credentials described in the integration guide).

`behavioural` · deprecation · 4 pages

Recorded separately from the single-Region/own-account key requirement because it retires a field rather than constraining the key.

- [api/admin/external_keys/list](https://platform.claude.com/docs/en/api/admin/external_keys/list)
- [api/admin/external_keys/retrieve](https://platform.claude.com/docs/en/api/admin/external_keys/retrieve)
- [api/beta/organization/external_keys/list](https://platform.claude.com/docs/en/api/beta/organization/external_keys/list)
- [api/beta/organization/external_keys/retrieve](https://platform.claude.com/docs/en/api/beta/organization/external_keys/retrieve)

### ABAC GRANT policies drop their Beta label, and a new page shows using GRANT policies to govern access to models and AI services in `system.ai` via governed tags.

`behavioural` · ga · 4 pages

Cross-references across the ABAC set now say 'ABAC GRANT policies' without the (Beta) qualifier, while DENY policies carry it instead.

- [data-governance/unity-catalog/abac/grant-policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/grant-policies)
- [data-governance/unity-catalog/abac/common-patterns](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/common-patterns)
- [data-governance/unity-catalog/abac/requirements](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/requirements)
- [ai-gateway/govern-access-to-models-with-grant-policies](https://docs.databricks.com/aws/en/ai-gateway/govern-access-to-models-with-grant-policies)

### Feature views enforce a lower bound on `window_duration` of more than two days (use RollingWindow for shorter windows), and CustomUDF applies only to RequestSource request-time features.

`behavioural` · limitation · 4 pages

Streams docs add that the run-as identity needs READ on the secret scope because the ingestion pipeline reads the secret at runtime, and the creator needs USE CONNECTION.

- [machine-learning/feature-store/feature-views-api-reference](https://docs.databricks.com/aws/en/machine-learning/feature-store/feature-views-api-reference)
- [machine-learning/feature-store/feature-views](https://docs.databricks.com/aws/en/machine-learning/feature-store/feature-views)
- [machine-learning/feature-store/streams](https://docs.databricks.com/aws/en/machine-learning/feature-store/streams)
- [release-notes/feature-store/databricks-feature-store](https://docs.databricks.com/aws/en/release-notes/feature-store/databricks-feature-store)

### SQL examples now reference foundation models as `system.ai.llama-4-maverick` rather than `databricks-llama-4-maverick`.

`behavioural` · naming · 3 pages

- [sql/language-manual/functions/ai_query](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_query)
- [sql/language-manual/functions/read_files](https://docs.databricks.com/aws/en/sql/language-manual/functions/read_files)
- [volumes/volume-files](https://docs.databricks.com/aws/en/volumes/volume-files)

### Previewing a FILE-typed value reads the file's contents, so it requires access to the file as well as the table — READ VOLUME on the underlying volume for FILE EXTERNAL columns.

`behavioural` · permissions · 3 pages

The same applies to casting a FILE value to BINARY or STRING and to passing it to an AI function or UDF.

- [sql/language-manual/data-types/file-type](https://docs.databricks.com/aws/en/sql/language-manual/data-types/file-type)
- [sql/user/sql-editor/results](https://docs.databricks.com/aws/en/sql/user/sql-editor/results)
- [unstructured/file](https://docs.databricks.com/aws/en/unstructured/file)

### On Claude Fable 5.1 and Claude Mythos 5.1, tool_choice types `any` and `tool` are not supported and return a 400 error; use `auto` with strict tool use or structured outputs instead.

`behavioural` · tool use · 2 pages

define-tools replaces the two prose notes with a table of models and settings where forced tool use fails: manual extended thinking (`thinking: {type: "enabled"}`) and Fable 5.1 / Mythos 5.1. `auto` (default) and `none` continue to work. The page also drops its old 'Choosing a model' section.

- [agents-and-tools/tool-use/define-tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools)
- [claude_api_primer](https://platform.claude.com/docs/en/claude_api_primer)

### Inference hooks now describe automatic recovery from a tripped circuit breaker: starting ten minutes after the trip Anthropic probes your server at most about once a minute, but rotating the signing secret stops the testing so the breaker no longer resets on its own.

`behavioural` · reliability · 2 pages

While the breaker is open your server is not contacted and your Failure handling choice applies to every request; turn Enforce verdicts back on manually after rotating the secret.

- [manage-claude/inference-hooks-configuration](https://platform.claude.com/docs/en/manage-claude/inference-hooks-configuration)
- [manage-claude/inference-hooks-endpoint](https://platform.claude.com/docs/en/manage-claude/inference-hooks-endpoint)

### Creating, modifying or dropping an ABAC GRANT policy with SQL requires Databricks Runtime 18 LTS or above (SQL warehouse support depends on the warehouse channel).

`behavioural` · version requirement · 2 pages

DESCRIBE POLICY output is now documented as policy-type dependent, with GRANT policies reporting the target securable type and granted privileges.

- [sql/language-manual/sql-ref-syntax-ddl-create-policy](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-ddl-create-policy)
- [sql/language-manual/sql-ref-syntax-aux-describe-policy](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-aux-describe-policy)

### External-access Spark configuration examples now set `spark.sql.catalog.spark_catalog` to `org.apache.spark.sql.delta.catalog.DeltaCatalog` instead of `io.unitycatalog.spark.UCSingleCatalog`.

`behavioural` · configuration · 2 pages

- [external-access/cross-engine-abac](https://docs.databricks.com/aws/en/external-access/cross-engine-abac)
- [external-access/unity-rest](https://docs.databricks.com/aws/en/external-access/unity-rest)

### The parallel tool use page notes Claude Fable 5.1 may issue fewer parallel tool calls than earlier models, most noticeably in long agent loops.

`behavioural` · model behaviour · 1 page

Guidance on disable_parallel_tool_use with tool_choice `any`/`tool` is unchanged.

- [agents-and-tools/tool-use/parallel-tool-use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/parallel-tool-use)

### Priority Tier's exclusion list now also names Claude Fable 5.1 and Claude Mythos 5.1, alongside Mythos 5 and Mythos Preview.

`behavioural` · availability · 1 page

The page says Priority Tier is supported on all available Claude models except those listed; the new 5.1 models are added to that list.

- [api/service-tiers](https://platform.claude.com/docs/en/api/service-tiers)

### Pipeline unit testing no longer requires the PREVIEW channel; it now requires Databricks Runtime 18.1 or above, since earlier runtimes do not include the unit testing module.

`behavioural` · requirement change · 1 page

- [ldp/unit-testing](https://docs.databricks.com/aws/en/ldp/unit-testing)

### Databricks Runtime 18 LTS documents that the Apache Avro 1.12.1 fast reader can exhaust executor memory in long-running jobs; the workaround is `-Dorg.apache.avro.fastread=false` in the driver and executor JVM options.

`behavioural` · known issue · 1 page

- [release-notes/runtime/18](https://docs.databricks.com/aws/en/release-notes/runtime/18)

### Deprecation of the `limit`, `offset`, `total_count` and `next_page` fields in /api/2.1/clusters/events moves from October 20, 2026 to November 30, 2026.

`behavioural` · deprecation schedule · 1 page

- [compute/events-api-updates](https://docs.databricks.com/aws/en/compute/events-api-updates)

### Customers who opt out of data retention cannot use Claude Fable 5.1 on Databricks; its data is processed by automated safety systems.

`behavioural` · restriction · 1 page

The same table also notes that for reasoning, `minimal`, `medium` and `xhigh` map to `max` while `none` is rejected.

- [machine-learning/foundation-model-apis/supported-models](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/supported-models)

### A job running continuously for more than 30 days loses access to files under /Workspace; restart the job at least once within that window to retain access.

`behavioural` · limitation · 1 page

Permission to access /Workspace files expires after 36 hours for interactive compute and 30 days for jobs.

- [files/workspace](https://docs.databricks.com/aws/en/files/workspace)

### Job performance metrics now require the 'Improved Lakeflow Performance Observability' preview to be enabled for the workspace, replacing the previous requirement of access to Query performance insights.

`behavioural` · requirement · 1 page

- [jobs/diagnose-job-performance](https://docs.databricks.com/aws/en/jobs/diagnose-job-performance)

### Databricks announces that when incremental formula field ingestion goes generally available, full snapshots will no longer be the default.

`behavioural` · upcoming change · 1 page

- [release-notes/whats-coming](https://docs.databricks.com/aws/en/release-notes/whats-coming)

### A Databricks App that writes MLflow traces to Unity Catalog must add the trace tables as app resources; an MLflow experiment resource only grants workspace-level permissions on the experiment.

`behavioural` · permissions · 1 page

The page now points at creating an experiment with a Unity Catalog trace location first.

- [dev-tools/databricks-apps/mlflow](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/mlflow)

## Additive — 36

### Three managed Lakeflow Connect connectors arrive in Beta — Anysphere Audit Logs (Cursor), Verkada, and Glean — each with a full setup, pipeline, reference, limits, FAQ and troubleshooting set.

`additive` · connector · 26 pages

Glean ingests usage insights and shortcuts (go links) and is full-refresh only with no SCD Type 2; Verkada ingests organization audit logs and access users.

- [ingestion/lakeflow-connect/anysphere-audit-logs](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs)
- [ingestion/lakeflow-connect/anysphere-audit-logs-connection](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-connection)
- [ingestion/lakeflow-connect/anysphere-audit-logs-source-setup](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-source-setup)
- [ingestion/lakeflow-connect/anysphere-audit-logs-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-pipeline)
- [ingestion/lakeflow-connect/anysphere-audit-logs-reference](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-reference)
- [ingestion/lakeflow-connect/anysphere-audit-logs-limits](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-limits)
- …and 20 more

### Claude Fable 5.1 (claude-fable-5-1) and Claude Mythos 5.1 launched on September 1, 2026, with a 1M-token context window, 128k max output, always-on adaptive thinking, and Fable 5 pricing ($10/$50 per MTok).

`additive` · model launch · 19 pages

Per the release notes, Fable 5.1 is available on the Claude API, Claude in Amazon Bedrock, Claude Platform on AWS, Claude on Google Cloud, and Claude in Microsoft Foundry; Mythos 5.1 remains invitation-only through Project Glasswing. New pages: overview, what's-new, migration guide, a Mythos 5.1 overview, a Fable 5.1 prompting guide, and a Fable 5.1 system-prompt page. The deprecations table lists claude-fable-5-1 as Active with retirement not sooner than September 1, 2027; the Fable 5 overview status changed from 'Active (latest)' to 'Active (legacy)'. The rate-limit tables relabel the Fable row 'Claude Fable 5.x' (limits themselves unchanged: 1,000 RPM / 500,000 ITPM / 100,000 OTPM on the first tier).

- [models/fable-5-1/overview](https://platform.claude.com/docs/en/models/fable-5-1/overview)
- [models/fable-5-1/whats-new-fable-5-1](https://platform.claude.com/docs/en/models/fable-5-1/whats-new-fable-5-1)
- [models/fable-5-1/migration-guide](https://platform.claude.com/docs/en/models/fable-5-1/migration-guide)
- [models/mythos-5-1/overview](https://platform.claude.com/docs/en/models/mythos-5-1/overview)
- [release-notes/overview](https://platform.claude.com/docs/en/release-notes/overview)
- [home](https://platform.claude.com/docs/en/home)
- …and 13 more

### `ant` CLI 1.30.0 adds `ant apply`, which creates and updates agents, environments, skills, memory stores and deployments from files and writes a `claude-lock.json` lockfile; managed-agents examples switch from `ant beta:<resource> create < file.yaml` to `ant apply`.

`additive` · tooling · 14 pages

A new 'Manage resources as code with ant apply' page documents the workflow, including approving the printed plan and committing the lockfile so later runs update the same resources. The quickstart's pinned VERSION moves from 1.27.0 to 1.30.0.

- [cli-sdks-libraries/cli/apply](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/apply)
- [cli-sdks-libraries/cli/quickstart](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/quickstart)
- [cli-sdks-libraries/cli/scripting](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/scripting)
- [managed-agents/self-hosted-sandboxes](https://platform.claude.com/docs/en/managed-agents/self-hosted-sandboxes)
- [managed-agents/environments](https://platform.claude.com/docs/en/managed-agents/environments)
- [managed-agents/quickstart](https://platform.claude.com/docs/en/managed-agents/quickstart)
- …and 8 more

### ABAC DENY policies are in Beta: they explicitly deny the MANAGE ACCESS CONTROL privilege on securables whose governed tags match a condition, and take precedence over grants.

`additive` · governance · 12 pages

The ABAC pages split their scope notes: row filter and column mask policies (UDF-based, evaluated at query time) versus GRANT and the new DENY policies. The SQL DENY statement page adds a pointer distinguishing hive_metastore DENY from Unity Catalog ABAC DENY policies.

- [data-governance/unity-catalog/abac/deny-policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/deny-policies)
- [data-governance/unity-catalog/abac/](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/)
- [data-governance/unity-catalog/abac/core-concepts](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/core-concepts)
- [data-governance/unity-catalog/abac/best-practices](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/best-practices)
- [data-governance/unity-catalog/abac/performance](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/performance)
- [data-governance/unity-catalog/abac/policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/policies)
- …and 6 more

### Databricks adds `databricks-claude-fable-5-1`, `databricks-gemini-3-8-flash` and `databricks-gpt-6-astra` as hosted models, with limits, priority-mode, region and acceptable-use tables updated.

`additive` · model availability · 11 pages

Gemini 3.8 Flash is listed at 200,000 / 20,000 / 360,000 in the limits table.

- [machine-learning/model-serving/query-anthropic-messages](https://docs.databricks.com/aws/en/machine-learning/model-serving/query-anthropic-messages)
- [machine-learning/model-serving/query-gemini-api](https://docs.databricks.com/aws/en/machine-learning/model-serving/query-gemini-api)
- [machine-learning/model-serving/query-openai-responses](https://docs.databricks.com/aws/en/machine-learning/model-serving/query-openai-responses)
- [machine-learning/foundation-model-apis/limits](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/limits)
- [machine-learning/foundation-model-apis/priority-mode](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/priority-mode)
- [machine-learning/foundation-model-apis/supported-models](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/supported-models)
- …and 5 more

### Existing features add Claude Fable 5.1 and Mythos 5.1 to their supported-model lists: structured outputs, the browser-use tool, task budgets (beta header), refusal fallback, and the managed-agents model enum.

`additive` · model support · 10 pages

Structured outputs and browser use now list claude-fable-5-1 and claude-mythos-5-1; task budgets lists Fable 5.1 as beta behind the task-budgets-2026-03-13 header; token counting says Fable 5.1, Mythos 5.1, Fable 5 and Mythos 5 share the tokenizer introduced with Opus 4.7; BetaManagedAgentsModel grows from 10 to 11 'more' entries starting with claude-fable-5-1.

- [build-with-claude/structured-outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)
- [agents-and-tools/tool-use/browser-use-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/browser-use-tool)
- [build-with-claude/task-budgets](https://platform.claude.com/docs/en/build-with-claude/task-budgets)
- [build-with-claude/token-counting](https://platform.claude.com/docs/en/build-with-claude/token-counting)
- [build-with-claude/handling-stop-reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons)
- [api/beta/agents/create](https://platform.claude.com/docs/en/api/beta/agents/create)
- …and 4 more

### Admin analytics endpoints document a Claude Tag (Claude in Slack) spend category with values such as `engaged` and `proactive`, and note that some filters cannot be combined with `group_by[]=rbac_group_id` or the `rbac_group_ids[]` filter.

`additive` · analytics · 9 pages

The skills analytics endpoints also extend the display-name field to plugin-delivered skills as well as user and organization skills.

- [api/admin/analytics](https://platform.claude.com/docs/en/api/admin/analytics)
- [api/admin/analytics/cost](https://platform.claude.com/docs/en/api/admin/analytics/cost)
- [api/admin/analytics/usage](https://platform.claude.com/docs/en/api/admin/analytics/usage)
- [api/admin/analytics/cost/list](https://platform.claude.com/docs/en/api/admin/analytics/cost/list)
- [api/admin/analytics/cost/list_by_user](https://platform.claude.com/docs/en/api/admin/analytics/cost/list_by_user)
- [api/admin/analytics/usage/list](https://platform.claude.com/docs/en/api/admin/analytics/usage/list)
- …and 3 more

### Databricks-provided built-in MCP services ship with platform-managed tools and a built-in service policy and need no server registration or OAuth app; the Databricks SQL page now recommends the `system.ai.dbsql` MCP service.

`additive` · mcp · 9 pages

The AI Search, Genie Agent and Unity Catalog functions pages are retitled '… MCP server'.

- [agents/mcp-tools/built-in-mcp-services](https://docs.databricks.com/aws/en/agents/mcp-tools/built-in-mcp-services)
- [agents/mcp-tools/mcp-services](https://docs.databricks.com/aws/en/agents/mcp-tools/mcp-services)
- [agents/mcp-tools/databricks-sql](https://docs.databricks.com/aws/en/agents/mcp-tools/databricks-sql)
- [agents/mcp-tools/use-mcp-in-agents](https://docs.databricks.com/aws/en/agents/mcp-tools/use-mcp-in-agents)
- [agents/mcp-tools/managed-mcp](https://docs.databricks.com/aws/en/agents/mcp-tools/managed-mcp)
- [agents/mcp-tools/ai-search](https://docs.databricks.com/aws/en/agents/mcp-tools/ai-search)
- …and 3 more

### New organization compliance-settings endpoints appear in the beta API reference, and the Compliance API docs extend to remote and local session transcripts, which are read-only and cannot be deleted through the API.

`additive` · compliance api · 8 pages

The integration-patterns page now tells organizations under legal hold to export chat content and remote session transcripts; the sessions page adds that local session transcripts are handled differently and that the messages endpoint behaves differently while an external key cannot be reached.

- [api/beta/organization/compliance_settings](https://platform.claude.com/docs/en/api/beta/organization/compliance_settings)
- [api/beta/organization/compliance_settings/retrieve](https://platform.claude.com/docs/en/api/beta/organization/compliance_settings/retrieve)
- [api/beta/organization/compliance_settings/update](https://platform.claude.com/docs/en/api/beta/organization/compliance_settings/update)
- [manage-claude/compliance-sessions](https://platform.claude.com/docs/en/manage-claude/compliance-sessions)
- [manage-claude/compliance-integration-patterns](https://platform.claude.com/docs/en/manage-claude/compliance-integration-patterns)
- [manage-claude/compliance-errors](https://platform.claude.com/docs/en/manage-claude/compliance-errors)
- …and 2 more

### Lakebase adds HIPAA support: new pages on the compliance security profile, enabling HIPAA on projects, and HIPAA audit logging, and Lakebase is now available by default in workspaces with the compliance security profile.

`additive` · compliance · 6 pages

Other compliance standards remain unsupported; the release notes say you no longer need to enable Lakebase in those workspaces.

- [oltp/projects/hipaa-compliance](https://docs.databricks.com/aws/en/oltp/projects/hipaa-compliance)
- [oltp/projects/enable-hipaa-compliance](https://docs.databricks.com/aws/en/oltp/projects/enable-hipaa-compliance)
- [oltp/projects/hipaa-audit-logging](https://docs.databricks.com/aws/en/oltp/projects/hipaa-audit-logging)
- [release-notes/lakebase/](https://docs.databricks.com/aws/en/release-notes/lakebase/)
- [oltp/projects/data-protection](https://docs.databricks.com/aws/en/oltp/projects/data-protection)
- [oltp/projects/private-link](https://docs.databricks.com/aws/en/oltp/projects/private-link)

### A new `ai_enrich` SQL function (Beta) generates new columns for each row and is cross-linked from the other AI functions.

`additive` · sql function · 6 pages

- [sql/language-manual/functions/ai_enrich](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_enrich)
- [large-language-models/ai-functions](https://docs.databricks.com/aws/en/large-language-models/ai-functions)
- [sql/language-manual/functions/ai_extract](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_extract)
- [sql/language-manual/functions/ai_parse_document](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_parse_document)
- [sql/language-manual/functions/ai_search](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_search)
- [sql/language-manual/sql-ref-functions-builtin-alpha](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-functions-builtin-alpha)

### Integrated CDC pipelines can now run in continuous (always-on) mode; the docs previously said continuous execution was not supported and now describe triggered mode only as the default.

`additive` · ingestion · 5 pages

A new page covers scale-optimized and speed-optimized run modes for always-on streams; the MySQL, Oracle and SQL Server pages point to it.

- [ingestion/lakeflow-connect/continuous-integrated-cdc](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/continuous-integrated-cdc)
- [ingestion/lakeflow-connect/mysql-integrated-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/mysql-integrated-pipeline)
- [ingestion/lakeflow-connect/oracle-integrated-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/oracle-integrated-pipeline)
- [ingestion/lakeflow-connect/sql-server-integrated-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/sql-server-integrated-pipeline)
- [ingestion/lakeflow-connect/common-patterns](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/common-patterns)

### The HubSpot connector adds CRM Hub ingestion in Beta, gated on the `hubspot_connector_crm_objects` workspace preview; previously it supported Marketing Hub only.

`additive` · connector · 5 pages

Additional `auth.requiredScopes` entries are needed for CRM Hub objects.

- [ingestion/lakeflow-connect/hubspot-overview](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-overview)
- [ingestion/lakeflow-connect/hubspot-limits](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-limits)
- [ingestion/lakeflow-connect/hubspot-source-setup](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-source-setup)
- [ingestion/lakeflow-connect/hubspot-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-pipeline)
- [ingestion/lakeflow-connect/hubspot-reference](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-reference)

### Unity Gateway Skills arrive: SKILL.md instruction files published to a Unity Catalog schema, shared under Unity Catalog grants and audit, and loaded by agents over MCP or downloaded.

`additive` · governance · 5 pages

A governance page covers enabling the feature, setting up a governed schema, and granting create/write/read privileges.

- [agents/uc-skills/](https://docs.databricks.com/aws/en/agents/uc-skills/)
- [agents/uc-skills/create-share-uc-skills](https://docs.databricks.com/aws/en/agents/uc-skills/create-share-uc-skills)
- [agents/uc-skills/use-uc-skills](https://docs.databricks.com/aws/en/agents/uc-skills/use-uc-skills)
- [ai-gateway/govern-skills](https://docs.databricks.com/aws/en/ai-gateway/govern-skills)
- [agent-skills/](https://docs.databricks.com/aws/en/agent-skills/)

### Cross-workspace access (Beta) lets you control which source workspaces can reach a workspace over serverless traffic, with matching egress entries in network policies.

`additive` · networking · 5 pages

A policy left in compatibility mode does not govern cross-workspace ingress.

- [security/network/front-end/cross-workspace-access](https://docs.databricks.com/aws/en/security/network/front-end/cross-workspace-access)
- [security/network/front-end/context-based-ingress](https://docs.databricks.com/aws/en/security/network/front-end/context-based-ingress)
- [security/network/front-end/manage-ingress-policies](https://docs.databricks.com/aws/en/security/network/front-end/manage-ingress-policies)
- [security/network/serverless-network-security/](https://docs.databricks.com/aws/en/security/network/serverless-network-security/)
- [security/network/serverless-network-security/network-policies](https://docs.databricks.com/aws/en/security/network/serverless-network-security/network-policies)

### Serverless environment version 6 (CPU and GPU) is available and selectable as Standard v6 in the AI Runtime environment panel.

`additive` · runtime · 5 pages

- [release-notes/serverless/environment-version/six](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/six)
- [release-notes/serverless/environment-version/six-gpu](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/six-gpu)
- [release-notes/serverless/environment-version/](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/)
- [machine-learning/ai-runtime/environment](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/environment)
- [release-notes/product/2026/september](https://docs.databricks.com/aws/en/release-notes/product/2026/september)

### Turn-scoped system messages are in beta behind the `mid-conversation-system-clear-at-2026-08-21` header: `clear_at: "next_user_message"` renders a mid-conversation system message for the current turn only, after which it stays in the array at no token cost.

`additive` · beta feature · 4 pages

The API reference adds that with this set the message stays in the array (send it unchanged) but is no longer shown to the model, and that it is only permitted on `role: "system"` messages. Per-turn reminders therefore don't accumulate or invalidate the prompt cache or later thinking blocks.

- [build-with-claude/mid-conversation-system-messages](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages)
- [api/beta/messages/create](https://platform.claude.com/docs/en/api/beta/messages/create)
- [api/beta/messages](https://platform.claude.com/docs/en/api/beta/messages)
- [api/beta/messages/batches](https://platform.claude.com/docs/en/api/beta/messages/batches)

### Zerobus Ingest can now write into tables backed by default storage (Public Preview); the statement that writing to default storage is not supported has been removed.

`additive` · preview · 4 pages

- [ingestion/zerobus-release-stages](https://docs.databricks.com/aws/en/ingestion/zerobus-release-stages)
- [ingestion/zerobus-concepts](https://docs.databricks.com/aws/en/ingestion/zerobus-concepts)
- [ingestion/zerobus-overview](https://docs.databricks.com/aws/en/ingestion/zerobus-overview)
- [release-notes/product/2026/september](https://docs.databricks.com/aws/en/release-notes/product/2026/september)

### A new `time_bucket(bucketSize, ts [, origin])` SQL function returns the start of a fixed-width time bucket for a timestamp.

`additive` · sql function · 4 pages

- [sql/language-manual/functions/time_bucket](https://docs.databricks.com/aws/en/sql/language-manual/functions/time_bucket)
- [sql/language-manual/functions/date_trunc](https://docs.databricks.com/aws/en/sql/language-manual/functions/date_trunc)
- [sql/language-manual/sql-ref-functions-builtin](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-functions-builtin)
- [release-notes/product/2026/september](https://docs.databricks.com/aws/en/release-notes/product/2026/september)

### Git Folder Serverless (Beta) shares one serverless compute and a `pyproject.toml`-managed environment across the notebooks and files in a Git folder.

`additive` · beta feature · 4 pages

- [compute/serverless/notebooks/git-folder-serverless](https://docs.databricks.com/aws/en/compute/serverless/notebooks/git-folder-serverless)
- [compute/serverless/](https://docs.databricks.com/aws/en/compute/serverless/)
- [compute/serverless/notebooks](https://docs.databricks.com/aws/en/compute/serverless/notebooks)
- [compute/serverless/dependencies](https://docs.databricks.com/aws/en/compute/serverless/dependencies)

### Metric views can be shared through OpenSharing (Beta), though you cannot query a shared metric view that references tables governed by ABAC policies, and metric views cannot be shared in a clean room.

`additive` · sharing · 4 pages

The earlier limitation was worded as metric views referencing tables with row filters or column masks.

- [opensharing/read-data-databricks](https://docs.databricks.com/aws/en/opensharing/read-data-databricks)
- [uc-semantics/metric-views/manage](https://docs.databricks.com/aws/en/uc-semantics/metric-views/manage)
- [clean-rooms/create-clean-room](https://docs.databricks.com/aws/en/clean-rooms/create-clean-room)
- [release-notes/product/2026/september](https://docs.databricks.com/aws/en/release-notes/product/2026/september)

### Dashboard themes gain colour mappings that pin a colour to a value by name across widgets, plus theme export to JSON; table visualizations can apply a colour scale to cell background or text.

`additive` · dashboards · 4 pages

Widgets share colours only when they colour by the same field from the same dataset; dashboard variable field options now show their source dataset.

- [dashboards/manage/settings](https://docs.databricks.com/aws/en/dashboards/manage/settings)
- [dashboards/manage/visualizations/](https://docs.databricks.com/aws/en/dashboards/manage/visualizations/)
- [dashboards/manage/visualizations/tables](https://docs.databricks.com/aws/en/dashboards/manage/visualizations/tables)
- [dashboards/manage/filters/dashboard-variables](https://docs.databricks.com/aws/en/dashboards/manage/filters/dashboard-variables)

### Apache Arrow support for Zerobus Ingest reaches general availability — the Arrow Flight page drops its Beta note.

`additive` · ga · 3 pages

The SDK still needs the `[arrow]` extra: pip install "databricks-zerobus-ingest-sdk[arrow]" pyarrow.

- [ingestion/zerobus-arrow-flight](https://docs.databricks.com/aws/en/ingestion/zerobus-arrow-flight)
- [ingestion/zerobus-message-types](https://docs.databricks.com/aws/en/ingestion/zerobus-message-types)
- [ingestion/zerobus-ingest](https://docs.databricks.com/aws/en/ingestion/zerobus-ingest)

### A Unity Catalog schema can be backed by AWS Secrets Manager or Azure Key Vault so secret values stay in your cloud secret manager while remaining governable in Unity Catalog.

`additive` · secrets · 3 pages

- [security/secrets/external-secrets](https://docs.databricks.com/aws/en/security/secrets/external-secrets)
- [security/secrets/configure-external-secrets](https://docs.databricks.com/aws/en/security/secrets/configure-external-secrets)
- [security/secrets/unity-catalog-secrets](https://docs.databricks.com/aws/en/security/secrets/unity-catalog-secrets)

### AI Search adds struct and map column support — maps must be top-level columns with string keys and primitive values, struct fields must resolve to primitives — alongside the full-text search beta on storage-optimized endpoints.

`additive` · search · 3 pages

- [ai-search/ai-search](https://docs.databricks.com/aws/en/ai-search/ai-search)
- [ai-search/create-ai-search](https://docs.databricks.com/aws/en/ai-search/create-ai-search)
- [ai-search/query-ai-search](https://docs.databricks.com/aws/en/ai-search/query-ai-search)

### New guidance for moving from SCIM to automatic identity management: an Okta-specific migration guide and a readiness report that finds external ID and group membership divergences.

`additive` · identity · 3 pages

The general migration page restates prerequisites as bullets, including identity federation on at least one workspace.

- [admin/users-groups/automatic-identity-management/migrate-to-aim](https://docs.databricks.com/aws/en/admin/users-groups/automatic-identity-management/migrate-to-aim)
- [admin/users-groups/automatic-identity-management/migrate-to-aim-okta](https://docs.databricks.com/aws/en/admin/users-groups/automatic-identity-management/migrate-to-aim-okta)
- [admin/users-groups/automatic-identity-management/readiness-report](https://docs.databricks.com/aws/en/admin/users-groups/automatic-identity-management/readiness-report)

### Web search in Genie One and Genie Code is in Beta and must be turned on by a workspace admin from the Previews page.

`additive` · beta feature · 2 pages

Genie Code can search the public web for current information such as release notes, third-party documentation and news, and cites its sources.

- [genie-one/chat](https://docs.databricks.com/aws/en/genie-one/chat)
- [genie-code/web-search](https://docs.databricks.com/aws/en/genie-code/web-search)

### A new page documents ingesting files from a user's OneDrive for Business into Delta tables with Auto Loader, `spark.read`, or COPY INTO.

`additive` · ingestion · 2 pages

- [ingestion/onedrive](https://docs.databricks.com/aws/en/ingestion/onedrive)
- [ingestion/lakeflow-connect/file-connectors-overview](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/file-connectors-overview)

### Service principal OAuth secrets can be scoped to specific API scopes; by default a secret still gets `all-apis`.

`additive` · security · 2 pages

- [dev-tools/auth/oauth-m2m](https://docs.databricks.com/aws/en/dev-tools/auth/oauth-m2m)
- [admin/users-groups/manage-service-principals](https://docs.databricks.com/aws/en/admin/users-groups/manage-service-principals)

### Path maps can draw a line by connecting a sequence of Point geometries, not only from a single geometry column.

`additive` · dashboards · 2 pages

- [dashboards/manage/visualizations/maps](https://docs.databricks.com/aws/en/dashboards/manage/visualizations/maps)
- [dashboards/manage/visualizations/types](https://docs.databricks.com/aws/en/dashboards/manage/visualizations/types)

### Prompt cache reads on Claude Fable 5.1 and Mythos 5.1 cost $0.25 per MTok — 0.025x the base input price, versus 0.1x on other models; cache writes are unchanged.

`additive` · pricing · 1 page

Stated in the September 1 release-notes entry and reflected in the pricing page tables.

- [about-claude/pricing](https://platform.claude.com/docs/en/about-claude/pricing)

### Per-message effort is in beta on Claude Fable 5.1, Mythos 5.1, and Opus 5 behind the `mid-conversation-output-config-2026-07-01` header, while the top-level effort parameter needs no beta header on any supported model.

`additive` · beta feature · 1 page

A `role: "system"` message carrying `output_config.effort` inside `messages` changes effort for later turns while preserving the prompt cache.

- [build-with-claude/effort](https://platform.claude.com/docs/en/build-with-claude/effort)

### `thinking.display` accepts a third value, `"updates"`, in beta behind `thinking-display-updates-2026-08-18`, returning the short progress updates Fable 5.1, Mythos 5.1 and Fable 5 write between tool calls as text.

`additive` · beta feature · 1 page

The streaming page also spells out that with `display: "omitted"` no `thinking_delta` events are sent — the block opens, receives a signature, and closes.

- [build-with-claude/streaming](https://platform.claude.com/docs/en/build-with-claude/streaming)

### Text from Claude Fable 5.1 and Mythos 5.1 carries Anthropic's text watermark, and image, video and audio files produced through the code execution tool carry C2PA Content Credentials when retrieved through the Files API.

`additive` · provenance · 1 page

The docs state marking requires no changes to requests or response handling and that the manifest records nothing about you, your organization, or your request.

- [agents-and-tools/tool-use/code-execution-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool)

### The Batch API's unsupported-parameter list shrinks to `stream`, `speed` and `max_tokens: 0` — `effort_hint` and `research_preview_2026_02` are no longer listed as unbatchable.

`additive` · api · 1 page

- [build-with-claude/batch-processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing)

### A pipeline events system table (Beta) records event log entries for Lakeflow pipelines.

`additive` · system table · 1 page

- [admin/system-tables/](https://docs.databricks.com/aws/en/admin/system-tables/)

## Editorial — 12

### 'Unity AI Gateway' is renamed 'Unity Gateway' throughout the Databricks docs, including preview toggles, entitlements, budget scopes and release-note headings.

`editorial` · product rename · 30 pages

A Unity Gateway release-notes section is added. Preview names change accordingly: 'Unity Gateway beta features', 'Consumer access to Unity Gateway', 'Enhanced Unity Gateway'.

- [release-notes/product/](https://docs.databricks.com/aws/en/release-notes/product/)
- [release-notes/product/2026/september](https://docs.databricks.com/aws/en/release-notes/product/2026/september)
- [machine-learning/model-serving/foundation-model-overview](https://docs.databricks.com/aws/en/machine-learning/model-serving/foundation-model-overview)
- [ai-gateway/](https://docs.databricks.com/aws/en/ai-gateway/)
- [ai-gateway/ai-governance](https://docs.databricks.com/aws/en/ai-gateway/ai-governance)
- [ai-gateway/agent-services](https://docs.databricks.com/aws/en/ai-gateway/agent-services)
- …and 24 more

### The single 'Use Genie Code' page is split into new pages — features and capabilities, agent mode, navigating Genie Code, and web search — and roughly twenty pages repoint their links.

`editorial` · restructure · 24 pages

Requirements that used to live under use-genie-code#requirements now live on the agent-mode page; the full-page command centre page is reworked alongside.

- [genie-code/features-capabilities](https://docs.databricks.com/aws/en/genie-code/features-capabilities)
- [genie-code/agent-mode](https://docs.databricks.com/aws/en/genie-code/agent-mode)
- [genie-code/navigate-genie-code](https://docs.databricks.com/aws/en/genie-code/navigate-genie-code)
- [genie-code/web-search](https://docs.databricks.com/aws/en/genie-code/web-search)
- [genie-code/full-page](https://docs.databricks.com/aws/en/genie-code/full-page)
- [genie-code/use-genie-code](https://docs.databricks.com/aws/en/genie-code/use-genie-code)
- …and 18 more

### A sweep of syntax and typo fixes lands across SQL reference, sharing and tutorial pages — unbalanced parentheses, smart quotes in INTERVAL literals, a stray `>` prompt, `DROP STREAMING TABLE` changed to `DROP TABLE`, and several misspellings.

`editorial` · corrections · 24 pages

These are example corrections, not behaviour changes.

- [sql/language-manual/functions/posexplode_outer](https://docs.databricks.com/aws/en/sql/language-manual/functions/posexplode_outer)
- [sql/language-manual/sql-ref-names](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-names)
- [sql/language-manual/data-types/struct-type](https://docs.databricks.com/aws/en/sql/language-manual/data-types/struct-type)
- [sql/language-manual/delta-merge-into](https://docs.databricks.com/aws/en/sql/language-manual/delta-merge-into)
- [sql/language-manual/functions/approx_top_k](https://docs.databricks.com/aws/en/sql/language-manual/functions/approx_top_k)
- [sql/language-manual/functions/http_request](https://docs.databricks.com/aws/en/sql/language-manual/functions/http_request)
- …and 18 more

### 'Databricks Data Intelligence Platform' is renamed 'Databricks Data + AI Platform' across architecture, migration and overview pages.

`editorial` · product rename · 20 pages

- [lakehouse-architecture/cost-optimization/best-practices](https://docs.databricks.com/aws/en/lakehouse-architecture/cost-optimization/best-practices)
- [lakehouse-architecture/interoperability-and-usability/best-practices](https://docs.databricks.com/aws/en/lakehouse-architecture/interoperability-and-usability/best-practices)
- [lakehouse-architecture/reference](https://docs.databricks.com/aws/en/lakehouse-architecture/reference)
- [lakehouse-architecture/](https://docs.databricks.com/aws/en/lakehouse-architecture/)
- [migration/warehouse-to-lakehouse](https://docs.databricks.com/aws/en/migration/warehouse-to-lakehouse)
- [migration/etl](https://docs.databricks.com/aws/en/migration/etl)
- …and 14 more

### Admin API curl examples switch the bearer-token environment variable from `$ANTHROPIC_OAUTH_TOKEN` to `$ANTHROPIC_AUTH_TOKEN` across roughly sixty endpoint pages.

`editorial` · docs example · 18 pages

Example text only; the header itself is still `Authorization: Bearer <token>`.

- [api/admin/api_keys](https://platform.claude.com/docs/en/api/admin/api_keys)
- [api/admin/api_keys/list](https://platform.claude.com/docs/en/api/admin/api_keys/list)
- [api/admin/users](https://platform.claude.com/docs/en/api/admin/users)
- [api/admin/users/list](https://platform.claude.com/docs/en/api/admin/users/list)
- [api/admin/invites](https://platform.claude.com/docs/en/api/admin/invites)
- [api/admin/invites/create](https://platform.claude.com/docs/en/api/admin/invites/create)
- …and 12 more

### The API reference was regenerated: the beta-header enum grows from '38 more' to '41 more' values on ~150 endpoint pages, model descriptions are inlined, and field prose is reformatted with backticks.

`editorial` · bulk regeneration · 18 pages

Mostly cosmetic, but the collapsed enum means three new beta header values exist without being named on these pages; individual behaviour changes (mid-conversation system messages, memory path constraints, new dream error types) are described in their own findings.

- [api/beta](https://platform.claude.com/docs/en/api/beta)
- [api/beta/messages](https://platform.claude.com/docs/en/api/beta/messages)
- [api/beta/deployments](https://platform.claude.com/docs/en/api/beta/deployments)
- [api/beta/environments](https://platform.claude.com/docs/en/api/beta/environments)
- [api/beta/files](https://platform.claude.com/docs/en/api/beta/files)
- [api/beta/memory_stores](https://platform.claude.com/docs/en/api/beta/memory_stores)
- …and 12 more

### Cookbook notebooks bump their hard-coded model from `claude-opus-4-1` to `claude-opus-4-8`.

`editorial` · docs example · 18 pages

- [platform.claude.com/cookbook/misc-building-evals](https://platform.claude.com/cookbook/misc-building-evals)
- [platform.claude.com/cookbook/misc-how-to-enable-json-mode](https://platform.claude.com/cookbook/misc-how-to-enable-json-mode)
- [platform.claude.com/cookbook/misc-how-to-make-sql-queries](https://platform.claude.com/cookbook/misc-how-to-make-sql-queries)
- [platform.claude.com/cookbook/multimodal-best-practices-for-vision](https://platform.claude.com/cookbook/multimodal-best-practices-for-vision)
- [platform.claude.com/cookbook/multimodal-getting-started-with-vision](https://platform.claude.com/cookbook/multimodal-getting-started-with-vision)
- [platform.claude.com/cookbook/multimodal-how-to-transcribe-text](https://platform.claude.com/cookbook/multimodal-how-to-transcribe-text)
- …and 12 more

### A phrasing sweep rewrites cross-reference sentences ('For how X…' becomes 'To learn how X…') across tool, thinking and ZDR notes with no change in substance.

`editorial` · copy edit · 18 pages

- [agents-and-tools/agent-skills/overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [agents-and-tools/tool-use/bash-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/bash-tool)
- [agents-and-tools/tool-use/fine-grained-tool-streaming](https://platform.claude.com/docs/en/agents-and-tools/tool-use/fine-grained-tool-streaming)
- [agents-and-tools/tool-use/memory-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)
- [agents-and-tools/tool-use/text-editor-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/text-editor-tool)
- [agents-and-tools/tool-use/web-search-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool)
- …and 12 more

### Cookbook install cells switch from `!pip install` to `%pip install`, and a new Claude Agent SDK recipe builds a scheduled, read-only repository reviewer.

`editorial` · docs example · 10 pages

The cookbook index adds the 'Build a scheduled repository reviewer' entry (Aug 2026).

- [platform.claude.com/cookbook/capabilities-classification-guide](https://platform.claude.com/cookbook/capabilities-classification-guide)
- [platform.claude.com/cookbook/capabilities-contextual-embeddings-guide](https://platform.claude.com/cookbook/capabilities-contextual-embeddings-guide)
- [platform.claude.com/cookbook/capabilities-summarization-guide](https://platform.claude.com/cookbook/capabilities-summarization-guide)
- [platform.claude.com/cookbook/capabilities-retrieval-augmented-generation-guide](https://platform.claude.com/cookbook/capabilities-retrieval-augmented-generation-guide)
- [platform.claude.com/cookbook/finetuning-finetuning-on-bedrock](https://platform.claude.com/cookbook/finetuning-finetuning-on-bedrock)
- [platform.claude.com/cookbook/misc-sampling-past-max-tokens](https://platform.claude.com/cookbook/misc-sampling-past-max-tokens)
- …and 4 more

### 'Enrich data using AI Functions' is retitled 'Transform unstructured data using AI Functions' and links are repointed.

`editorial` · page rename · 8 pages

- [large-language-models/batch-inference-pipelines](https://docs.databricks.com/aws/en/large-language-models/batch-inference-pipelines)
- [large-language-models/ai-functions-uc-permissions](https://docs.databricks.com/aws/en/large-language-models/ai-functions-uc-permissions)
- [designer/built-in-operators](https://docs.databricks.com/aws/en/designer/built-in-operators)
- [volumes/unstructured-data-tutorial](https://docs.databricks.com/aws/en/volumes/unstructured-data-tutorial)
- [machine-learning/foundation-model-apis/](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/)
- [mlflow3/genai/tracing/redact-pii-otel-traces](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/redact-pii-otel-traces)
- …and 2 more

### The Java SDK coordinates in the docs move from com.anthropic:anthropic-java(-aws):2.58.0 to 2.60.0.

`editorial` · version bump · 3 pages

- [cli-sdks-libraries/sdks/java](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/java)
- [get-started](https://platform.claude.com/docs/en/get-started)
- [build-with-claude/claude-platform-on-aws](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws)

### The `ucode` CLI is now called the Unity Gateway CLI; requirements (Python 3.12+, uv) and routing behaviour are unchanged.

`editorial` · product rename · 2 pages

- [ai-gateway/coding-agent-integration-model-provider-services](https://docs.databricks.com/aws/en/ai-gateway/coding-agent-integration-model-provider-services)
- [ai-gateway/smart-routing](https://docs.databricks.com/aws/en/ai-gateway/smart-routing)
