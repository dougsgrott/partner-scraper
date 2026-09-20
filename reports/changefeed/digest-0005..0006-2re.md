# Change digest

> #5 (2026-09-09-before) → #6 (2026-09-09) · 1,072 changes · rendered 2026-09-19T19:10:37+00:00

## At a glance

92 findings — **7** breaking, **26** behavioural, **44** additive, **15** editorial — covering 698 of 1,072 changed pages. Anything not here is in the full feed report beside this file.

**If you read nothing else:**

1. A new "Preserved thinking" model: on Claude Fable 5.1 a replayed thinking block is only valid while the system prompt, tools and preceding messages are unchanged, and for accounts created on or after August 31, 2026 (or any request setting `prefix_mismatch_behavior: "error"`) a mismatched block is rejected with a 400.
2. Web fetch's URL-source rules are restated: a URL that appears only in the system prompt is not fetchable (include it in a user message), and results from other server-side tools — code execution, MCP connector, tool search — are not an allowed source either.
3. The TypeScript SDK now states TypeScript >= 5.0 is supported, up from >= 4.9.
4. Salesforce ingestion of one object now requires the `Query All Files` permission (which itself requires `View All Data`), where the page previously required only `View All Data`.
5. Change data feed's stated requirement rises from Databricks Runtime 18 LTS or above to Databricks Runtime 19 or above.
6. Workspace files docs now state that permission to access files under `/Workspace` expires after 36 hours for interactive compute and 30 days for jobs, so a job running continuously for more than 30 days loses access unless it is restarted.
7. BigQuery federation now states `INTERVAL` columns are not supported and that a foreign table containing one fails when its schema loads; the previous type-mapping row listing `INTERVAL` is gone.

---

## Breaking — 7

### A new "Preserved thinking" model: on Claude Fable 5.1 a replayed thinking block is only valid while the system prompt, tools and preceding messages are unchanged, and for accounts created on or after August 31, 2026 (or any request setting `prefix_mismatch_behavior: "error"`) a mismatched block is rejected with a 400.

`breaking` · thinking block binding · 13 pages

New page build-with-claude/preserved-thinking. api/errors adds "Thinking block no longer matches the conversation": the error names the first failing block and tells you to remove it or set `thinking.block_binding.prefix_mismatch_behavior` to `"drop_block"`, which requires the `thinking-binding-controls-2026-08-01` beta header (sending `block_binding` without the header is itself a 400 `block_binding: Extra inputs are not permitted`). A block from a model the target model cannot read is dropped rather than rejected. Batch results and the beta Messages pages now report which request block was removed (`messages.{i}.content.{j}`); streaming documents that with `display: "omitted"` no `thinking_delta` events are sent.

- [build-with-claude/preserved-thinking](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking)
- [api/errors](https://platform.claude.com/docs/en/api/errors)
- [build-with-claude/thinking-troubleshooting](https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting)
- [build-with-claude/thinking](https://platform.claude.com/docs/en/build-with-claude/thinking)
- [build-with-claude/context-editing](https://platform.claude.com/docs/en/build-with-claude/context-editing)
- [build-with-claude/context-windows](https://platform.claude.com/docs/en/build-with-claude/context-windows)
- …and 7 more

### Web fetch's URL-source rules are restated: a URL that appears only in the system prompt is not fetchable (include it in a user message), and results from other server-side tools — code execution, MCP connector, tool search — are not an allowed source either.

`breaking` · tool restriction · 1 page

The page previously said only that Claude cannot fetch URLs it generates or URLs from container-based server tools. It now also says client-side tool results are an allowed source even when they echo text Claude produced, and lists Fable 5.1 and Mythos 5.1 among the models supporting dynamic filtering in `web_fetch_20260318`.

- [agents-and-tools/tool-use/web-fetch-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-fetch-tool)

### The TypeScript SDK now states TypeScript >= 5.0 is supported, up from >= 4.9.

`breaking` · version floor · 1 page

Single-line change on the TypeScript SDK page.

- [cli-sdks-libraries/sdks/typescript](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/typescript)

### Salesforce ingestion of one object now requires the `Query All Files` permission (which itself requires `View All Data`), where the page previously required only `View All Data`.

`breaking` · permission requirement · 1 page

Single limits-table change on the Salesforce connector.

- [ingestion/lakeflow-connect/salesforce-limits](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/salesforce-limits)

### Change data feed's stated requirement rises from Databricks Runtime 18 LTS or above to Databricks Runtime 19 or above.

`breaking` · version floor · 1 page

Single requirement line.

- [tables/features/change-data-feed](https://docs.databricks.com/aws/en/tables/features/change-data-feed)

### Workspace files docs now state that permission to access files under `/Workspace` expires after 36 hours for interactive compute and 30 days for jobs, so a job running continuously for more than 30 days loses access unless it is restarted.

`breaking` · limit · 1 page

New text on databricks/files/workspace.

- [files/workspace](https://docs.databricks.com/aws/en/files/workspace)

### BigQuery federation now states `INTERVAL` columns are not supported and that a foreign table containing one fails when its schema loads; the previous type-mapping row listing `INTERVAL` is gone.

`breaking` · limitation · 1 page

Data-type mapping table change plus a new note.

- [query-federation/bigquery](https://docs.databricks.com/aws/en/query-federation/bigquery)

## Behavioural — 26

### MLflow GenAI examples now require `mlflow[databricks]>=3.14.0` (up from >=3.1) and set `MLFLOW_TRACING_SQL_WAREHOUSE_ID`, because the examples store traces in Unity Catalog.

`behavioural` · version floor · 38 pages

Examples import `UnityCatalog` from `mlflow.entities.trace_location` and configure a SQL warehouse; the Claude Code integration's CLI tracing now says MLflow 3.14+. Databricks Apps writing traces to Unity Catalog must add the trace tables as app resources, since an MLflow experiment resource only grants workspace-level permissions.

- [mlflow3/genai/tracing/integrations/](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/)
- [mlflow3/genai/tracing/integrations/anthropic](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/anthropic)
- [mlflow3/genai/tracing/integrations/openai](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/openai)
- [mlflow3/genai/tracing/integrations/bedrock](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/bedrock)
- [mlflow3/genai/tracing/integrations/langchain](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/langchain)
- [mlflow3/genai/tracing/integrations/langgraph](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/langgraph)
- …and 32 more

### Federation-issuer, federation-rule and service-account admin endpoints now state a single auth requirement: an OAuth access token with the `org:admin` scope (from `ant auth login --scope org:admin` or a workload identity federation rule), replacing the older mix of "OAuth bearer or Console session; Admin API keys are not accepted" notes.

`behavioural` · authentication · 32 pages

The same sentence replaces per-endpoint variations that previously mentioned Console sessions, interactive credentials and scope-specific carve-outs.

- [api/admin/federation_issuers](https://platform.claude.com/docs/en/api/admin/federation_issuers)
- [api/admin/federation_issuers/create](https://platform.claude.com/docs/en/api/admin/federation_issuers/create)
- [api/admin/federation_issuers/update](https://platform.claude.com/docs/en/api/admin/federation_issuers/update)
- [api/admin/federation_issuers/archive](https://platform.claude.com/docs/en/api/admin/federation_issuers/archive)
- [api/admin/federation_issuers/list](https://platform.claude.com/docs/en/api/admin/federation_issuers/list)
- [api/admin/federation_issuers/retrieve](https://platform.claude.com/docs/en/api/admin/federation_issuers/retrieve)
- …and 26 more

### External-key (CMEK) docs now state that on Claude Platform on AWS the KMS key must be a single-Region key in your organization's own AWS account, that cross-account keys are not supported, and that the `iam_role_arn` field is deprecated because Anthropic reaches the key through its own intermediate role.

`behavioural` · cmek requirements · 18 pages

manage-claude/cmek-aws-kms adds key requirements (symmetric, encrypt/decrypt usage, single-region, same account and region) and troubleshooting guidance for telling a source-ARN mismatch from an encryption-context mismatch. Workspace pages repeat that once a key is attached to a workspace it cannot be detached or replaced.

- [manage-claude/cmek-aws-kms](https://platform.claude.com/docs/en/manage-claude/cmek-aws-kms)
- [api/admin/external_keys](https://platform.claude.com/docs/en/api/admin/external_keys)
- [api/admin/external_keys/create](https://platform.claude.com/docs/en/api/admin/external_keys/create)
- [api/admin/external_keys/update](https://platform.claude.com/docs/en/api/admin/external_keys/update)
- [api/admin/external_keys/list](https://platform.claude.com/docs/en/api/admin/external_keys/list)
- [api/admin/external_keys/retrieve](https://platform.claude.com/docs/en/api/admin/external_keys/retrieve)
- …and 12 more

### C# workload-identity-federation examples now construct `new AnthropicClient(new ClientOptions { Credentials = credentials })` instead of `new AnthropicOidcClient(credentials)`.

`behavioural` · sdk examples · 7 pages

The AWS, GitHub Actions and Kubernetes pages also replace the "No federation credentials found in environment" throw with comments naming the expected environment variables.

- [manage-claude/workload-identity-federation](https://platform.claude.com/docs/en/manage-claude/workload-identity-federation)
- [manage-claude/wif-providers/gcp](https://platform.claude.com/docs/en/manage-claude/wif-providers/gcp)
- [manage-claude/wif-providers/okta](https://platform.claude.com/docs/en/manage-claude/wif-providers/okta)
- [manage-claude/wif-providers/azure](https://platform.claude.com/docs/en/manage-claude/wif-providers/azure)
- [manage-claude/wif-providers/aws](https://platform.claude.com/docs/en/manage-claude/wif-providers/aws)
- [manage-claude/wif-providers/github-actions](https://platform.claude.com/docs/en/manage-claude/wif-providers/github-actions)
- …and 1 more

### RBAC group docs now qualify the SCIM restriction: identity-provider-provisioned groups (source type `"scim"`) cannot be renamed, deleted, or have membership changed via the API "while an organization in the …" condition holds, rather than unconditionally.

`behavioural` · api behaviour · 6 pages

Same clause applied to the group update/delete endpoints and the membership create/delete endpoints.

- [api/admin/rbac_groups](https://platform.claude.com/docs/en/api/admin/rbac_groups)
- [api/admin/rbac_groups/update](https://platform.claude.com/docs/en/api/admin/rbac_groups/update)
- [api/admin/rbac_groups/delete](https://platform.claude.com/docs/en/api/admin/rbac_groups/delete)
- [api/admin/rbac_groups/members](https://platform.claude.com/docs/en/api/admin/rbac_groups/members)
- [api/admin/rbac_groups/members/create](https://platform.claude.com/docs/en/api/admin/rbac_groups/members/create)
- [api/admin/rbac_groups/members/delete](https://platform.claude.com/docs/en/api/admin/rbac_groups/members/delete)

### The Fable/Mythos ZDR language gains an exception: these models require 30-day retention and are "not available under ZDR unless expressly authorized by Anthropic", rather than flatly unavailable.

`behavioural` · data retention · 5 pages

The wording is applied across the retention page, the Fable 5 migration and launch pages, and the refusal discussion in build-with-claude/overview, which now speaks of "the Claude Fable models" rather than Claude Fable 5 alone.

- [manage-claude/api-and-data-retention](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention)
- [models/fable-5/migration-guide](https://platform.claude.com/docs/en/models/fable-5/migration-guide)
- [about-claude/models/introducing-claude-fable-5-and-claude-mythos-5](https://platform.claude.com/docs/en/about-claude/models/introducing-claude-fable-5-and-claude-mythos-5)
- [models/fable-5/introducing-claude-fable-5-and-claude-mythos-5](https://platform.claude.com/docs/en/models/fable-5/introducing-claude-fable-5-and-claude-mythos-5)
- [build-with-claude/overview](https://platform.claude.com/docs/en/build-with-claude/overview)

### Compliance API docs extend session coverage to remote sessions: session endpoints stay read-only, deleted remote sessions are no longer listed and the messages endpoint returns 404 for them, and content must be exported before deletion if you need to retain it.

`behavioural` · compliance api · 5 pages

compliance-integration-patterns now says to export chat, file, artifact and remote session transcript content ahead of user deletion (for example under legal hold); compliance-faq adds that a user-deleted remote session is not recoverable; compliance-errors distinguishes transient "captured content" and index-unavailable conditions; the 503 wording for an unusable customer key is reworded.

- [manage-claude/compliance-sessions](https://platform.claude.com/docs/en/manage-claude/compliance-sessions)
- [manage-claude/compliance-integration-patterns](https://platform.claude.com/docs/en/manage-claude/compliance-integration-patterns)
- [manage-claude/compliance-faq](https://platform.claude.com/docs/en/manage-claude/compliance-faq)
- [manage-claude/compliance-errors](https://platform.claude.com/docs/en/manage-claude/compliance-errors)
- [manage-claude/compliance-api-access](https://platform.claude.com/docs/en/manage-claude/compliance-api-access)

### Refusal and fallback-credit guidance is updated for the 5.1 models: Fable 5.1 joins the list of models whose refusals can be retried elsewhere, and Fable 5.1 thinking blocks are preserved only for that model, so a fallback model ignores them.

`behavioural` · refusals · 4 pages

fallback-credit restates that redemption requires the body unchanged and that the prefix already cached for the first model must be written into the new model's cache from scratch; refusals-and-fallback clarifies that the beta header must carry exactly `2026-07-01` (which supports `"default"` and the explicit list) or `2026-06-01`.

- [build-with-claude/handling-stop-reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons)
- [build-with-claude/refusals-and-fallback](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback)
- [build-with-claude/fallback-credit](https://platform.claude.com/docs/en/build-with-claude/fallback-credit)
- [agents-and-tools/agent-skills/claude-api-skill](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/claude-api-skill)

### ABAC GRANT policies lose their Beta labelling — the Beta banner is gone from the GRANT policies page and cross-references now read "ABAC GRANT policies" without "(Beta)".

`behavioural` · ga · 4 pages

The June 2026 release note entry was also reworded.

- [data-governance/unity-catalog/abac/grant-policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/grant-policies)
- [data-governance/unity-catalog/abac/common-patterns](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/common-patterns)
- [data-governance/unity-catalog/abac/requirements](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/requirements)
- [release-notes/product/2026/june](https://docs.databricks.com/aws/en/release-notes/product/2026/june)

### Runtime release notes add a Databricks Runtime 19 (September 1, 2026) section, a DBR 18 LTS known issue where the Apache Avro fast reader can exhaust executor memory, and gzip-extension read support in 16.4 LTS.

`behavioural` · runtime notes · 4 pages

The DBR 18 workaround is to add `-Dorg.apache.avro.fastread=false` to driver and executor JVM options. DBR 19 LTS with row tracking is required for a feature working across batch queries, Structured Streaming and Delta Sharing. The 13.3 LTS page gains an end-of-support banner. The 16.4 LTS note warns that applying `PassthroughCodec` to genuinely gzip-compressed `.gzip` files prevents them from being read correctly.

- [release-notes/runtime/19](https://docs.databricks.com/aws/en/release-notes/runtime/19)
- [release-notes/runtime/18](https://docs.databricks.com/aws/en/release-notes/runtime/18)
- [release-notes/runtime/16.4lts](https://docs.databricks.com/aws/en/release-notes/runtime/16.4lts)
- [release-notes/runtime/13.3lts](https://docs.databricks.com/aws/en/release-notes/runtime/13.3lts)

### Feature Store documents a sawtooth window option and an enforced lower bound: `window_duration` must be greater than two days, with `RollingWindow` for shorter windows, and `CustomUDF` applies only to request-time `RequestSource` features.

`behavioural` · constraint · 4 pages

Sawtooth windows rely on history already present, so the Stream's ingestion table must cover the full window. `transformation_sql` now requires a `dataframe_schema` (Spark StructType JSON) and has a documented list of supported expressions; Streams document secret-scope `READ` and `USE CONNECTION` requirements for the run-as identity.

- [machine-learning/feature-store/feature-views-api-reference](https://docs.databricks.com/aws/en/machine-learning/feature-store/feature-views-api-reference)
- [machine-learning/feature-store/feature-views](https://docs.databricks.com/aws/en/machine-learning/feature-store/feature-views)
- [machine-learning/feature-store/streams](https://docs.databricks.com/aws/en/machine-learning/feature-store/streams)
- [release-notes/feature-store/databricks-feature-store](https://docs.databricks.com/aws/en/release-notes/feature-store/databricks-feature-store)

### Inference hooks now document circuit-breaker recovery probing: starting 10 minutes after a trip, Anthropic sends at most about one test request per minute, and with "Enforce verdicts" off the breaker no longer resets on its own.

`behavioural` · failure handling · 3 pages

The pages also restate that while the breaker is open your server is not contacted and your Failure handling choice applies to every inspection, and that turning off "Allow for your organization" in Data and privacy settings stops prompt inspection entirely. Inference hooks remain unavailable on Amazon Bedrock and Google Cloud.

- [manage-claude/inference-hooks-configuration](https://platform.claude.com/docs/en/manage-claude/inference-hooks-configuration)
- [manage-claude/inference-hooks-endpoint](https://platform.claude.com/docs/en/manage-claude/inference-hooks-endpoint)
- [manage-claude/inference-hooks](https://platform.claude.com/docs/en/manage-claude/inference-hooks)

### The managed-agents reference drops its explicit model list for mid-conversation system injection and now simply says the event is rejected with `model_does_not_support_mid_conversation_system` on an unsupported primary model.

`behavioural` · api reference · 3 pages

managed-agents/dreams also rewords how dreaming inputs and the selected model are described.

- [managed-agents/reference](https://platform.claude.com/docs/en/managed-agents/reference)
- [managed-agents/events-and-streaming](https://platform.claude.com/docs/en/managed-agents/events-and-streaming)
- [managed-agents/dreams](https://platform.claude.com/docs/en/managed-agents/dreams)

### SQL AI-function examples now reference the model as `system.ai.llama-4-maverick` instead of the `databricks-llama-4-maverick` endpoint name.

`behavioural` · endpoint naming · 3 pages

Applies to ai_query, read_files and the volume-files tutorial examples.

- [sql/language-manual/functions/ai_query](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_query)
- [sql/language-manual/functions/read_files](https://docs.databricks.com/aws/en/sql/language-manual/functions/read_files)
- [volumes/volume-files](https://docs.databricks.com/aws/en/volumes/volume-files)

### `FILE` type docs now state that previewing or reading a file's contents requires access to the file itself in addition to the table — `READ VOLUME` on the underlying volume for `FILE EXTERNAL`.

`behavioural` · permissions · 3 pages

Applies to casting to BINARY/STRING, passing a FILE to an AI function or UDF, and previewing values in the SQL editor results table.

- [sql/language-manual/data-types/file-type](https://docs.databricks.com/aws/en/sql/language-manual/data-types/file-type)
- [sql/user/sql-editor/results](https://docs.databricks.com/aws/en/sql/user/sql-editor/results)
- [unstructured/file](https://docs.databricks.com/aws/en/unstructured/file)

### Metric view sharing gains stated limits: recipients cannot query a metric view that references tables governed by ABAC policies or carrying row filters or column masks, must use Databricks Runtime 16.4 LTS or above, and metric views cannot be shared in a clean room.

`behavioural` · limitation · 3 pages

The metric views management page also carries a Beta notice stating workspace admins can control access to the feature.

- [opensharing/read-data-databricks](https://docs.databricks.com/aws/en/opensharing/read-data-databricks)
- [clean-rooms/create-clean-room](https://docs.databricks.com/aws/en/clean-rooms/create-clean-room)
- [uc-semantics/metric-views/manage](https://docs.databricks.com/aws/en/uc-semantics/metric-views/manage)

### LTAP Direct Writes is documented as off by default with a workspace admin required to turn on the preview, and it requires a Lakebase project running Postgres 17.

`behavioural` · default change · 2 pages

When enabled it writes data directly into the storage layer backing your Lakebase instance.

- [oltp/instances/sync-data/sync-table](https://docs.databricks.com/aws/en/oltp/instances/sync-data/sync-table)
- [oltp/projects/sync-tables](https://docs.databricks.com/aws/en/oltp/projects/sync-tables)

### The documented per-branch Lakebase storage quota drops its 32 TB figure — the pages now say only that each branch has a database storage quota.

`behavioural` · limit · 2 pages

Both pages keep the explanation that this is an operational quota rather than an architectural limit.

- [oltp/instances/create/](https://docs.databricks.com/aws/en/oltp/instances/create/)
- [oltp/projects/manage-projects](https://docs.databricks.com/aws/en/oltp/projects/manage-projects)

### External-access Spark examples change `spark.sql.catalog.spark_catalog` from `io.unitycatalog.spark.UCSingleCatalog` to `org.apache.spark.sql.delta.catalog.DeltaCatalog`.

`behavioural` · configuration fix · 2 pages

Same configuration line in both the cross-engine ABAC and Unity REST pages.

- [external-access/cross-engine-abac](https://docs.databricks.com/aws/en/external-access/cross-engine-abac)
- [external-access/unity-rest](https://docs.databricks.com/aws/en/external-access/unity-rest)

### Query profile and query performance insights drop their Beta banners and the note that workspace admins control access to the feature.

`behavioural` · ga · 2 pages

Banner removal only.

- [sql/user/queries/query-profile](https://docs.databricks.com/aws/en/sql/user/queries/query-profile)
- [sql/user/queries/performance-insights](https://docs.databricks.com/aws/en/sql/user/queries/performance-insights)

### The CMEK page now says structured outputs are unavailable for Claude Fable or Claude Mythos models in CMEK organizations, widening the note from Fable 5 and Mythos models specifically.

`behavioural` · restriction · 1 page

Single table-cell change on manage-claude/cmek.

- [manage-claude/cmek](https://platform.claude.com/docs/en/manage-claude/cmek)

### The C# SDK page drops both beta notices — the "versioned as 10+ but currently in beta" warning and the "APIs may change between versions" note.

`behavioural` · status · 1 page

No replacement status language appears in the excerpt.

- [cli-sdks-libraries/sdks/csharp](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/csharp)

### The TikTok Ads connector's report limitation changes: report data is supported only for reports with fewer than 20,000 ads (TikTok's synchronous report path), replacing the earlier "BASIC reports only" restriction.

`behavioural` · limit · 1 page

Limits page rewrite.

- [ingestion/lakeflow-connect/tiktok-ads-limits](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/tiktok-ads-limits)

### Pipeline unit testing now requires Databricks Runtime 18.1 or above instead of the PREVIEW channel; earlier runtimes do not include the unit testing module.

`behavioural` · requirement change · 1 page

The Beta/PREVIEW-channel requirement was replaced with a runtime version floor.

- [ldp/unit-testing](https://docs.databricks.com/aws/en/ldp/unit-testing)

### The deprecation of the `limit`, `offset`, `total_count` and `next_page` fields in `/api/2.1/clusters/events` moves from October 20, 2026 to November 30, 2026.

`behavioural` · deprecation date · 1 page

The "before" date for required migration moves with it.

- [compute/events-api-updates](https://docs.databricks.com/aws/en/compute/events-api-updates)

### Predictive optimization now states it retains data files for a minimum of 7 days even when `delta.deletedFileRetentionDuration` is set lower.

`behavioural` · retention · 1 page

Added note on the predictive optimization page.

- [optimizations/predictive-optimization](https://docs.databricks.com/aws/en/optimizations/predictive-optimization)

## Additive — 44

### Lakeflow Connect gains managed connectors for Anysphere (Cursor) Audit Logs, Verkada and Glean, each with connection, pipeline, reference, limits, FAQ and troubleshooting pages.

`additive` · new connectors · 26 pages

Glean ingests usage insights and go-links and is full-refresh-only with no SCD Type 2; Verkada ingests organization audit logs and access users. The connector index and FAQ hub list all three.

- [ingestion/lakeflow-connect/anysphere-audit-logs](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs)
- [ingestion/lakeflow-connect/anysphere-audit-logs-connection](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-connection)
- [ingestion/lakeflow-connect/anysphere-audit-logs-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-pipeline)
- [ingestion/lakeflow-connect/anysphere-audit-logs-reference](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-reference)
- [ingestion/lakeflow-connect/anysphere-audit-logs-source-setup](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-source-setup)
- [ingestion/lakeflow-connect/anysphere-audit-logs-limits](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-limits)
- …and 20 more

### Claude Fable 5.1 (`claude-fable-5-1`) and the invitation-only Claude Mythos 5.1 ship with their own overview, migration and "what's new" pages, and Fable 5's status changes from "Active (latest)" to "Active (legacy)".

`additive` · model launch · 17 pages

New pages: models/fable-5-1/overview, models/fable-5-1/migration-guide, models/fable-5-1/whats-new-fable-5-1, models/mythos-5-1/overview and a Fable 5.1 system-prompt release note. Fable 5.1 is listed as the most capable widely released model on home, intro and choosing-a-model; model-deprecations adds a `claude-fable-5-1` row (Active, retirement not sooner than September 1, 2027); Mythos 5.1 is described as the same model offered by invitation through Project Glasswing. Token counting now says Fable 5.1, Mythos 5.1, Fable 5 and Mythos 5 share the tokenizer introduced with Claude Opus 4.7.

- [models/fable-5-1/overview](https://platform.claude.com/docs/en/models/fable-5-1/overview)
- [models/fable-5-1/migration-guide](https://platform.claude.com/docs/en/models/fable-5-1/migration-guide)
- [models/fable-5-1/whats-new-fable-5-1](https://platform.claude.com/docs/en/models/fable-5-1/whats-new-fable-5-1)
- [models/mythos-5-1/overview](https://platform.claude.com/docs/en/models/mythos-5-1/overview)
- [release-notes/system-prompts/claude-fable-5-1](https://platform.claude.com/docs/en/release-notes/system-prompts/claude-fable-5-1)
- [release-notes/system-prompts](https://platform.claude.com/docs/en/release-notes/system-prompts)
- …and 11 more

### Databricks-provided (built-in) MCP Services land as a new page: platform-managed tools with a built-in service policy and no connection setup or app registration, with `system.ai.dbsql` now recommended over the standalone Databricks SQL MCP server.

`additive` · new feature · 14 pages

MCP tool pages are retitled "… MCP server"; the Glean entry in managed OAuth drops the "MCP" suffix; connect-clients documents per-request OAuth tokens with no OAuth application or stored token.

- [agents/mcp-tools/built-in-mcp-services](https://docs.databricks.com/aws/en/agents/mcp-tools/built-in-mcp-services)
- [agents/mcp-tools/mcp-services](https://docs.databricks.com/aws/en/agents/mcp-tools/mcp-services)
- [agents/mcp-tools/databricks-sql](https://docs.databricks.com/aws/en/agents/mcp-tools/databricks-sql)
- [agents/mcp-tools/connect-clients](https://docs.databricks.com/aws/en/agents/mcp-tools/connect-clients)
- [agents/mcp-tools/use-mcp-in-agents](https://docs.databricks.com/aws/en/agents/mcp-tools/use-mcp-in-agents)
- [agents/mcp-tools/managed-mcp](https://docs.databricks.com/aws/en/agents/mcp-tools/managed-mcp)
- …and 8 more

### A new `ant apply` workflow declares agents, environments, skills, memory stores and deployments as files and syncs them, and the managed-agents guides replace `ant beta:<resource> create < file.yaml` examples with it.

`additive` · cli · 13 pages

New page cli-sdks-libraries/cli/apply; self-hosted-sandboxes now shows `ant apply environment.yaml`. cli/scripting adds `ant beta:sessions:events stream --format jsonl` for watching a session as it runs.

- [cli-sdks-libraries/cli/apply](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/apply)
- [managed-agents/self-hosted-sandboxes](https://platform.claude.com/docs/en/managed-agents/self-hosted-sandboxes)
- [managed-agents/environments](https://platform.claude.com/docs/en/managed-agents/environments)
- [managed-agents/quickstart](https://platform.claude.com/docs/en/managed-agents/quickstart)
- [managed-agents/agent-setup](https://platform.claude.com/docs/en/managed-agents/agent-setup)
- [managed-agents/permission-policies](https://platform.claude.com/docs/en/managed-agents/permission-policies)
- …and 7 more

### Unity Catalog adds ABAC DENY policies (Beta), which explicitly deny `MANAGE ACCESS CONTROL` on securables by governed tag and take precedence over grants.

`additive` · new feature · 13 pages

A new deny-policies page joins the ABAC set; performance, policies and policy-evaluation pages scope themselves to row filter and column mask policies and say GRANT and DENY policies are not subject to the UDF-based query-time behaviour. `DESCRIBE POLICY` reports fields per policy type, and `CREATE POLICY` with GRANT semantics requires Databricks Runtime 18 LTS or above.

- [data-governance/unity-catalog/abac/deny-policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/deny-policies)
- [data-governance/unity-catalog/abac/](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/)
- [data-governance/unity-catalog/abac/core-concepts](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/core-concepts)
- [data-governance/unity-catalog/abac/best-practices](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/best-practices)
- [data-governance/unity-catalog/abac/performance](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/performance)
- [data-governance/unity-catalog/abac/policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/policies)
- …and 7 more

### Databricks foundation model APIs add `databricks-claude-fable-5-1`, `databricks-gemini-3-8-flash` and `databricks-gpt-6-astra`, with rate limits, priority mode, acceptable-use and reasoning-effort entries for each.

`additive` · model availability · 12 pages

supported-models says Claude Fable 5.1 accepts `low`, `medium`, `high`, `xhigh` and `max` effort, reasoning cannot be disabled, `minimal`/`medium`/`xhigh` map to `max` and `none` is rejected, and that customers who opt out of data retention cannot use Claude Fable 5.1 (as already stated for Fable 5).

- [machine-learning/model-serving/foundation-model-overview](https://docs.databricks.com/aws/en/machine-learning/model-serving/foundation-model-overview)
- [machine-learning/foundation-model-apis/supported-models](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/supported-models)
- [machine-learning/foundation-model-apis/priority-mode](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/priority-mode)
- [machine-learning/foundation-model-apis/limits](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/limits)
- [machine-learning/foundation-model-apis/compliance](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/compliance)
- [machine-learning/model-serving/acceptable-use-models](https://docs.databricks.com/aws/en/machine-learning/model-serving/acceptable-use-models)
- …and 6 more

### Cost and usage analytics gain a Claude Tag (Claude in Slack) spend category (`engaged`, `proactive`, …) and state that it cannot be combined with `group_by[]=rbac_group_id` or the `rbac_group_ids[]` filter; skills analytics extend display names to plugin-delivered skills.

`additive` · api reference · 9 pages

Previously the skills display-name note covered only user/organization skill types.

- [api/admin/analytics](https://platform.claude.com/docs/en/api/admin/analytics)
- [api/admin/analytics/cost](https://platform.claude.com/docs/en/api/admin/analytics/cost)
- [api/admin/analytics/cost/list](https://platform.claude.com/docs/en/api/admin/analytics/cost/list)
- [api/admin/analytics/cost/list_by_user](https://platform.claude.com/docs/en/api/admin/analytics/cost/list_by_user)
- [api/admin/analytics/usage](https://platform.claude.com/docs/en/api/admin/analytics/usage)
- [api/admin/analytics/usage/list](https://platform.claude.com/docs/en/api/admin/analytics/usage/list)
- …and 3 more

### Fable 5.1 and Mythos 5.1 are added to feature support lists: structured outputs, the browser use tool, task budgets (beta header `task-budgets-2026-03-13`) and the managed-agents model enum.

`additive` · availability · 8 pages

`BetaManagedAgentsModel` now leads with `"claude-fable-5-1"` and lists 11 more values (previously 10).

- [build-with-claude/structured-outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)
- [agents-and-tools/tool-use/browser-use-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/browser-use-tool)
- [build-with-claude/task-budgets](https://platform.claude.com/docs/en/build-with-claude/task-budgets)
- [api/beta/agents](https://platform.claude.com/docs/en/api/beta/agents)
- [api/beta/agents/create](https://platform.claude.com/docs/en/api/beta/agents/create)
- [api/beta/agents/update](https://platform.claude.com/docs/en/api/beta/agents/update)
- …and 2 more

### A new `ai_enrich` SQL function (Beta) generates new columns for each row and is listed in the AI functions tables and related function pages.

`additive` · new function · 7 pages

New reference page sql/language-manual/functions/ai_enrich plus "see also" links from ai_extract, ai_parse_document and ai_search.

- [sql/language-manual/functions/ai_enrich](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_enrich)
- [large-language-models/ai-functions](https://docs.databricks.com/aws/en/large-language-models/ai-functions)
- [sql/language-manual/sql-ref-functions-builtin](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-functions-builtin)
- [sql/language-manual/sql-ref-functions-builtin-alpha](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-functions-builtin-alpha)
- [sql/language-manual/functions/ai_extract](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_extract)
- [sql/language-manual/functions/ai_parse_document](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_parse_document)
- …and 1 more

### Lakebase adds HIPAA support: new pages cover enabling HIPAA compliance, the shared-responsibility model and BAA, and HIPAA audit logging in the Unity Catalog audit log system table.

`additive` · compliance · 7 pages

Lakebase is now available by default in workspaces with the compliance security profile, so you no longer need to enable it there; other compliance standards remain unsupported. security/privacy/hipaa adds the requirement to enable the compliance security profile on every workspace that processes PHI.

- [oltp/projects/hipaa-compliance](https://docs.databricks.com/aws/en/oltp/projects/hipaa-compliance)
- [oltp/projects/enable-hipaa-compliance](https://docs.databricks.com/aws/en/oltp/projects/enable-hipaa-compliance)
- [oltp/projects/hipaa-audit-logging](https://docs.databricks.com/aws/en/oltp/projects/hipaa-audit-logging)
- [security/privacy/hipaa](https://docs.databricks.com/aws/en/security/privacy/hipaa)
- [release-notes/lakebase/](https://docs.databricks.com/aws/en/release-notes/lakebase/)
- [oltp/projects/data-protection](https://docs.databricks.com/aws/en/oltp/projects/data-protection)
- …and 1 more

### Mid-conversation system messages gain a per-message output config and a `visibility` control — a message can stay in the array but stop being shown to the model — in beta on Fable 5.1, Mythos 5.1 and Opus 5 behind the `mid-conversation-output-config` header.

`additive` · beta feature · 6 pages

The docs restate placement rules (turn-scoped content must follow a user turn, or an assistant turn ending in a server tool result) and say a message with neither content nor output_config fields is rejected. `visibility` is only permitted on `role: "system"` messages.

- [build-with-claude/mid-conversation-system-messages](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages)
- [api/beta/messages](https://platform.claude.com/docs/en/api/beta/messages)
- [api/beta/messages/create](https://platform.claude.com/docs/en/api/beta/messages/create)
- [api/beta/messages/batches](https://platform.claude.com/docs/en/api/beta/messages/batches)
- [api/beta/messages/batches/create](https://platform.claude.com/docs/en/api/beta/messages/batches/create)
- [api/beta](https://platform.claude.com/docs/en/api/beta)

### Unity Gateway Skills arrive: SKILL.md instruction files published to a Unity Catalog schema, shared under Unity Catalog grants and audit, and loaded by agents over MCP or the Unity Gateway CLI.

`additive` · new feature · 5 pages

Three new agents/uc-skills pages plus a governance page covering enabling the feature, schema setup, create/write/read privileges and auditing.

- [agents/uc-skills/](https://docs.databricks.com/aws/en/agents/uc-skills/)
- [agents/uc-skills/create-share-uc-skills](https://docs.databricks.com/aws/en/agents/uc-skills/create-share-uc-skills)
- [agents/uc-skills/use-uc-skills](https://docs.databricks.com/aws/en/agents/uc-skills/use-uc-skills)
- [ai-gateway/govern-skills](https://docs.databricks.com/aws/en/ai-gateway/govern-skills)
- [agent-skills/](https://docs.databricks.com/aws/en/agent-skills/)

### Integrated CDC pipelines can now run continuously: a new page documents always-on mode with scale- or speed-optimized run modes, and the MySQL page's "continuous execution is not supported" limitation is replaced by "triggered by default".

`additive` · new capability · 5 pages

The Oracle and SQL Server integrated-pipeline pages and the common-patterns index point to the new continuous mode page.

- [ingestion/lakeflow-connect/continuous-integrated-cdc](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/continuous-integrated-cdc)
- [ingestion/lakeflow-connect/mysql-integrated-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/mysql-integrated-pipeline)
- [ingestion/lakeflow-connect/oracle-integrated-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/oracle-integrated-pipeline)
- [ingestion/lakeflow-connect/sql-server-integrated-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/sql-server-integrated-pipeline)
- [ingestion/lakeflow-connect/common-patterns](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/common-patterns)

### The HubSpot connector adds CRM Hub ingestion in Beta, gated on the `hubspot_connector_crm_objects` workspace preview and extra `auth.requiredScopes` entries; previously the connector supported Marketing Hub only.

`additive` · beta feature · 5 pages

Pipeline examples now ingest both `marketing_emails` (Marketing Hub) and `contacts` (CRM Hub).

- [ingestion/lakeflow-connect/hubspot-overview](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-overview)
- [ingestion/lakeflow-connect/hubspot-limits](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-limits)
- [ingestion/lakeflow-connect/hubspot-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-pipeline)
- [ingestion/lakeflow-connect/hubspot-reference](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-reference)
- [ingestion/lakeflow-connect/hubspot-source-setup](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-source-setup)

### Cross-workspace access (Beta) lets network policies control which source workspaces can reach a workspace over serverless traffic, with matching egress rules that allow specific workspaces as destinations.

`additive` · new feature · 5 pages

New page security/network/front-end/cross-workspace-access; a policy left in compatibility mode does not govern cross-workspace ingress and existing behaviour continues.

- [security/network/front-end/cross-workspace-access](https://docs.databricks.com/aws/en/security/network/front-end/cross-workspace-access)
- [security/network/front-end/context-based-ingress](https://docs.databricks.com/aws/en/security/network/front-end/context-based-ingress)
- [security/network/front-end/manage-ingress-policies](https://docs.databricks.com/aws/en/security/network/front-end/manage-ingress-policies)
- [security/network/serverless-network-security/](https://docs.databricks.com/aws/en/security/network/serverless-network-security/)
- [security/network/serverless-network-security/network-policies](https://docs.databricks.com/aws/en/security/network/serverless-network-security/network-policies)

### Serverless environment version 6 ships, with CPU and GPU release notes, an entry in the version table, and Standard v6 selectable in the AI Runtime environment panel.

`additive` · new version · 5 pages

The environment version 5 notes restate that the Py4J gateway is off, replacing `dbutils.entry_point` and `dbutils.notebook.entry_point`, and list APIs no longer supported.

- [release-notes/serverless/environment-version/six](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/six)
- [release-notes/serverless/environment-version/six-gpu](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/six-gpu)
- [release-notes/serverless/environment-version/](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/)
- [release-notes/serverless/environment-version/five](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/five)
- [machine-learning/ai-runtime/environment](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/environment)

### A new top-level `ray_init()` (drop-in for `ray.init()`) enables the Ray dashboard on serverless GPU compute and requires environment version 5 or later; a new Ray Data + vLLM batch inference tutorial uses 8 H100 GPUs.

`additive` · new capability · 5 pages

The Ray page notes Databricks AI v5 includes Ray but Standard v5 needs Ray installed before calling `ray_init()`; the examples index now covers inference as well as training and fine-tuning.

- [machine-learning/ai-runtime/ray](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/ray)
- [machine-learning/ai-runtime/examples/](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/)
- [machine-learning/ai-runtime/examples/gpu-llms](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/gpu-llms)
- [machine-learning/ai-runtime/examples/tutorials/sgc-raydata-vllm-batch-inference](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-raydata-vllm-batch-inference)
- [release-notes/serverless/environment-version/five-gpu](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/five-gpu)

### Dashboard theme settings gain color mappings that pin a color to a value by name across the dashboard, plus JSON theme export/import without editing dashboard JSON.

`additive` · new capability · 5 pages

Widgets share colors only when they color by the same field from the same dataset; dashboard variable field options now show their source dataset; table visualizations can apply a color scale to the cell background or other targets.

- [dashboards/manage/settings](https://docs.databricks.com/aws/en/dashboards/manage/settings)
- [dashboards/manage/visualizations/](https://docs.databricks.com/aws/en/dashboards/manage/visualizations/)
- [dashboards/manage/visualizations/tables](https://docs.databricks.com/aws/en/dashboards/manage/visualizations/tables)
- [dashboards/manage/filters/dashboard-variables](https://docs.databricks.com/aws/en/dashboards/manage/filters/dashboard-variables)
- [ai-bi/admin/themes](https://docs.databricks.com/aws/en/ai-bi/admin/themes)

### Claude Fable 5.1 and Mythos 5.1 reject forced tool use: `tool_choice` `any` or `tool` returns a 400 `invalid_request_error`, including on the token-counting endpoint.

`additive` · model limitation · 4 pages

api/errors adds a "Forced tool use not supported" section: the message is `tool_choice: type "tool" and "any" are not supported for this model.` Only `auto` (default) and `none` are accepted; the docs point to strict tool use or structured outputs instead. api/errors also extends "Thinking cannot be disabled" to Fable 5.1 and Mythos 5.1 — `thinking: {"type":"disabled"}` and the suggested `"enabled"` are both rejected.

- [api/errors](https://platform.claude.com/docs/en/api/errors)
- [claude_api_primer](https://platform.claude.com/docs/en/claude_api_primer)
- [build-with-claude/thinking](https://platform.claude.com/docs/en/build-with-claude/thinking)
- [agents-and-tools/tool-use/define-tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools)

### The rate-limit listing endpoints document cursor pagination: `next_page` is an opaque cursor, `null` when no entries remain, and omitting the page size returns every remaining entry in one page.

`additive` · api reference · 4 pages

The `model_group` description for rate-limit entry kinds was also reworded.

- [api/admin/rate_limits](https://platform.claude.com/docs/en/api/admin/rate_limits)
- [api/admin/rate_limits/list](https://platform.claude.com/docs/en/api/admin/rate_limits/list)
- [api/admin/workspaces/rate_limits](https://platform.claude.com/docs/en/api/admin/workspaces/rate_limits)
- [api/admin/workspaces/rate_limits/list](https://platform.claude.com/docs/en/api/admin/workspaces/rate_limits/list)

### New beta endpoints let you retrieve and update organization compliance settings, and the Compliance API overview now states every endpoint lives under `/v1/compliance/*` and authenticates with `x-api-key`.

`additive` · new endpoints · 4 pages

Three new reference pages under api/beta/organization/compliance_settings.

- [api/beta/organization/compliance_settings](https://platform.claude.com/docs/en/api/beta/organization/compliance_settings)
- [api/beta/organization/compliance_settings/retrieve](https://platform.claude.com/docs/en/api/beta/organization/compliance_settings/retrieve)
- [api/beta/organization/compliance_settings/update](https://platform.claude.com/docs/en/api/beta/organization/compliance_settings/update)
- [manage-claude/compliance-api](https://platform.claude.com/docs/en/manage-claude/compliance-api)

### A new `time_bucket(bucketSize, ts [, origin])` SQL function returns the start of a fixed-width time bucket for a timestamp.

`additive` · new function · 4 pages

Cross-linked from date_trunc and added to the built-in function lists.

- [sql/language-manual/functions/time_bucket](https://docs.databricks.com/aws/en/sql/language-manual/functions/time_bucket)
- [sql/language-manual/functions/date_trunc](https://docs.databricks.com/aws/en/sql/language-manual/functions/date_trunc)
- [sql/language-manual/sql-ref-functions-builtin](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-functions-builtin)
- [sql/language-manual/sql-ref-functions-builtin-alpha](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-functions-builtin-alpha)

### Automatic identity management gains an Okta migration guide and a readiness report that finds external ID and group membership divergences between Databricks and your identity provider.

`additive` · new guidance · 4 pages

The generic SCIM migration page was restructured into prerequisite bullets, including identity federation enabled on at least one workspace.

- [admin/users-groups/automatic-identity-management/](https://docs.databricks.com/aws/en/admin/users-groups/automatic-identity-management/)
- [admin/users-groups/automatic-identity-management/migrate-to-aim](https://docs.databricks.com/aws/en/admin/users-groups/automatic-identity-management/migrate-to-aim)
- [admin/users-groups/automatic-identity-management/migrate-to-aim-okta](https://docs.databricks.com/aws/en/admin/users-groups/automatic-identity-management/migrate-to-aim-okta)
- [admin/users-groups/automatic-identity-management/readiness-report](https://docs.databricks.com/aws/en/admin/users-groups/automatic-identity-management/readiness-report)

### Git Folder Serverless (Beta) lets notebooks and files in a Git folder share one compute resource and an environment managed by `pyproject.toml`.

`additive` · beta feature · 4 pages

Listed on the serverless index as Beta and cross-linked from the notebooks and dependencies pages.

- [compute/serverless/notebooks/git-folder-serverless](https://docs.databricks.com/aws/en/compute/serverless/notebooks/git-folder-serverless)
- [compute/serverless/](https://docs.databricks.com/aws/en/compute/serverless/)
- [compute/serverless/notebooks](https://docs.databricks.com/aws/en/compute/serverless/notebooks)
- [compute/serverless/dependencies](https://docs.databricks.com/aws/en/compute/serverless/dependencies)

### The GitHub connector documents repository selection: it ingests all organization repositories by default, and `repository_id_selection` restricts ingestion to specific repositories for repository-scoped tables.

`additive` · configuration · 3 pages

Limits note that batch-only tables such as `pull_requests`, `pull_request_commits` and `pull_request_reviews` can hold millions of records in large organizations.

- [ingestion/lakeflow-connect/github-reference](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/github-reference)
- [ingestion/lakeflow-connect/github-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/github-pipeline)
- [ingestion/lakeflow-connect/github-limits](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/github-limits)

### Zerobus Ingest now lists ingesting into default-storage-backed tables as Public Preview, and the "writing to default storage is not supported" limitation is dropped.

`additive` · preview · 3 pages

The concepts page now says only that Zerobus writes to managed Delta tables; the overview drops its region-pairing bullet.

- [ingestion/zerobus-release-stages](https://docs.databricks.com/aws/en/ingestion/zerobus-release-stages)
- [ingestion/zerobus-concepts](https://docs.databricks.com/aws/en/ingestion/zerobus-concepts)
- [ingestion/zerobus-overview](https://docs.databricks.com/aws/en/ingestion/zerobus-overview)

### Unity Catalog schemas can be backed by AWS Secrets Manager or Azure Key Vault so secret values stay in your cloud secret manager while remaining governable in Unity Catalog.

`additive` · new feature · 3 pages

Two new pages plus an example retrieving a secret and passing it to `dbutils.credentials.getServiceCredentialsProvider` for a boto3 session.

- [security/secrets/external-secrets](https://docs.databricks.com/aws/en/security/secrets/external-secrets)
- [security/secrets/configure-external-secrets](https://docs.databricks.com/aws/en/security/secrets/configure-external-secrets)
- [security/secrets/unity-catalog-secrets](https://docs.databricks.com/aws/en/security/secrets/unity-catalog-secrets)

### New release-notes pages appear for September 2026 and for Unity Gateway, and route optimization on model serving endpoints becomes available on AWS GovCloud and GovCloud DoD.

`additive` · release notes · 3 pages

The GovCloud 2026 page adds the route-optimization section.

- [release-notes/product/2026/september](https://docs.databricks.com/aws/en/release-notes/product/2026/september)
- [release-notes/unity-gateway/](https://docs.databricks.com/aws/en/release-notes/unity-gateway/)
- [release-notes/gov-cloud/2026](https://docs.databricks.com/aws/en/release-notes/gov-cloud/2026)

### On the Claude API, image, video and audio files Claude produces in the code execution sandbox now carry C2PA Content Credentials when downloaded through the Files API.

`additive` · content provenance · 2 pages

A signed manifest identifies Anthropic as issuer, carries a timestamp and an action description; it records nothing about you or your request and needs no changes to requests or response handling, but adds a few kilobytes so the downloaded file's size and checksum differ from the in-container file. Text files, PDFs and office documents are not signed. The page also replaces its model-compatibility and platform-availability tables with a single Compatibility block (ZDR: not eligible; Microsoft Foundry requires a Hosted on Anthropic deployment).

- [agents-and-tools/tool-use/code-execution-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool)
- [release-notes/overview](https://platform.claude.com/docs/en/release-notes/overview)

### A new prompting guide for Fable 5.1 and Mythos 5.1 lands, and parallel tool use notes that Fable 5.1 may issue fewer parallel tool calls than earlier models, most noticeably in long agent loops.

`additive` · prompting guidance · 2 pages

The guide covers effort, progress updates, tool-call batching, conversation history, formatting, task completion, compaction summaries and search triggering.

- [build-with-claude/prompt-engineering/prompting-claude-fable-5-1](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1)
- [agents-and-tools/tool-use/parallel-tool-use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/parallel-tool-use)

### A new Agent SDK cookbook builds a scheduled, read-only repository reviewer that resumes its session and returns schema-validated verdicts, and it is listed on the cookbook index.

`additive` · new guide · 2 pages

Indexed under Claude Agent SDK / Agents, dated Aug 2026.

- [platform.claude.com/cookbook/claude-agent-sdk-scheduled-repository-reviewer-scheduled-repository-reviewer](https://platform.claude.com/cookbook/claude-agent-sdk-scheduled-repository-reviewer-scheduled-repository-reviewer)
- [platform.claude.com/cookbook/](https://platform.claude.com/cookbook/)

### You can now govern access to models and AI services in `system.ai` with ABAC GRANT policies, using a new `ai.*` family of system governed tags that Databricks applies to hosted models.

`additive` · new feature · 2 pages

New page ai-gateway/govern-access-to-models-with-grant-policies; the governed-tags overview documents the `ai.*` prefix alongside `system.`, `class.` and `sap.`.

- [ai-gateway/govern-access-to-models-with-grant-policies](https://docs.databricks.com/aws/en/ai-gateway/govern-access-to-models-with-grant-policies)
- [admin/governed-tags/](https://docs.databricks.com/aws/en/admin/governed-tags/)

### Genie Code and Genie One can search the public web and cite sources, behind a "Web search in Genie Code and Genie One" workspace preview an admin must turn on.

`additive` · new feature · 2 pages

genie-one/chat also restates its eligibility requirements: eligible geo (Americas or Europe) or cross-geography processing, and partner-powered AI features enabled.

- [genie-code/web-search](https://docs.databricks.com/aws/en/genie-code/web-search)
- [genie-one/chat](https://docs.databricks.com/aws/en/genie-one/chat)

### A new page documents ingesting files from OneDrive for Business into Delta tables with Auto Loader, `spark.read` or `COPY INTO`, and the file-connectors index lists it.

`additive` · new connector · 2 pages

Covers structured, semi-structured and unstructured files.

- [ingestion/onedrive](https://docs.databricks.com/aws/en/ingestion/onedrive)
- [ingestion/lakeflow-connect/file-connectors-overview](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/file-connectors-overview)

### Service principal OAuth secrets can now be scoped: by default a secret can access every API the principal is authorized for (`all-apis`), and you can restrict it to selected API scopes when creating it.

`additive` · new feature · 2 pages

The service principal page links to the new Scoped OAuth secrets section.

- [dev-tools/auth/oauth-m2m](https://docs.databricks.com/aws/en/dev-tools/auth/oauth-m2m)
- [admin/users-groups/manage-service-principals](https://docs.databricks.com/aws/en/admin/users-groups/manage-service-principals)

### Unity Catalog adds UDF lineage you can view in the UI to see which workloads and tables reference a UDF, but it is not available in the lineage system tables and cannot be queried there.

`additive` · new capability · 2 pages

The data-lineage page adds a limitation note and a View UDF lineage section.

- [data-governance/unity-catalog/data-lineage](https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-lineage)
- [udf/unity-catalog](https://docs.databricks.com/aws/en/udf/unity-catalog)

### Path maps can now draw a line by connecting a sequence of `Point` GEOMETRY values, in addition to drawing from a geometry column.

`additive` · new capability · 2 pages

Both the maps reference and the visualization types list were updated.

- [dashboards/manage/visualizations/maps](https://docs.databricks.com/aws/en/dashboards/manage/visualizations/maps)
- [dashboards/manage/visualizations/types](https://docs.databricks.com/aws/en/dashboards/manage/visualizations/types)

### Databricks Marketplace listings can use SecureConnect with no Marketplace-specific configuration: enable SecureConnect on the provider metastore that hosts your shares and Marketplace creates a recipient per consumer.

`additive` · new capability · 2 pages

SecureConnect cannot be used with recipients that read shared data using SAP HANA, which does not support the Databricks pre-signed URL flow.

- [marketplace/create-listing](https://docs.databricks.com/aws/en/marketplace/create-listing)
- [opensharing/secureconnect-provider](https://docs.databricks.com/aws/en/opensharing/secureconnect-provider)

### A new page documents adding, dropping or renaming columns and widening column types on a streaming table with `ALTER TABLE` as metadata-only changes, without a full refresh or checkpoint reset.

`additive` · new capability · 2 pages

The schema-evolution page adds that a renamed source column restarts the query by default to resolve the mismatch.

- [ldp/streaming-table-schema-evolution](https://docs.databricks.com/aws/en/ldp/streaming-table-schema-evolution)
- [data-engineering/schema-evolution](https://docs.databricks.com/aws/en/data-engineering/schema-evolution)

### The Message Batches API's unsupported-parameter list shrinks to `stream`, `speed` and `max_tokens: 0` — `store`/`previous_thread_event_id`, `cache_hint`/`context_hint` and `research_preview_2026_02` are no longer listed as unsupported — and Fable 5.1/Mythos 5.1 batch pricing ($5/$25 per MTok) is added.

`additive` · batch support · 1 page

Both the "What can be batched" table and the FAQ answer were trimmed to the three remaining parameters.

- [build-with-claude/batch-processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing)

### Priority Tier is documented as supported on all available Claude models except Claude Fable 5.1, Claude Mythos 5.1, Claude Mythos 5 and Claude Mythos Preview.

`additive` · availability · 1 page

The exclusion list grew to name the two new 5.1 models.

- [api/service-tiers](https://platform.claude.com/docs/en/api/service-tiers)

### Per-message effort is in beta behind the `mid-conversation-output-config` beta header, while the top-level `effort` parameter remains available on all supported models with no header.

`additive` · beta feature · 1 page

The page splits the former single statement about effort availability into top-level and per-message forms.

- [build-with-claude/effort](https://platform.claude.com/docs/en/build-with-claude/effort)

### A new page documents Genie Ontology, a unified context layer combining Unity Catalog semantics with inferred business context for Genie One and Genie Code.

`additive` · new feature · 1 page

Single new page under genie/.

- [genie/genie-ontology](https://docs.databricks.com/aws/en/genie/genie-ontology)

### A Pipeline events system table (Beta) is listed, recording event log entries for Lakeflow pipelines.

`additive` · system table · 1 page

Row added to the system tables index.

- [admin/system-tables/](https://docs.databricks.com/aws/en/admin/system-tables/)

## Editorial — 15

### Admin API curl examples switch the bearer-token environment variable from `$ANTHROPIC_OAUTH_TOKEN` to `$ANTHROPIC_AUTH_TOKEN` across the whole Admin API reference.

`editorial` · examples · 60 pages

Example-only change; no described change to the endpoints themselves.

- [api/admin/api_keys](https://platform.claude.com/docs/en/api/admin/api_keys)
- [api/admin/api_keys/list](https://platform.claude.com/docs/en/api/admin/api_keys/list)
- [api/admin/api_keys/retrieve](https://platform.claude.com/docs/en/api/admin/api_keys/retrieve)
- [api/admin/api_keys/update](https://platform.claude.com/docs/en/api/admin/api_keys/update)
- [api/admin/cost_report](https://platform.claude.com/docs/en/api/admin/cost_report)
- [api/admin/cost_report/retrieve](https://platform.claude.com/docs/en/api/admin/cost_report/retrieve)
- …and 54 more

### Databricks renames "Unity AI Gateway" to "Unity Gateway" throughout the docs, including preview names ("Consumer access to Unity Gateway", "Enhanced Unity Gateway") and the `ucode` CLI, now called the Unity Gateway CLI.

`editorial` · rename · 37 pages

Release-notes entries and MCP-connector headlines were retitled to match; a new release-notes/unity-gateway/ landing page also appears.

- [ai-gateway/](https://docs.databricks.com/aws/en/ai-gateway/)
- [ai-gateway/ai-governance](https://docs.databricks.com/aws/en/ai-gateway/ai-governance)
- [ai-gateway/agent-services](https://docs.databricks.com/aws/en/ai-gateway/agent-services)
- [ai-gateway/model-services](https://docs.databricks.com/aws/en/ai-gateway/model-services)
- [ai-gateway/govern-model-services](https://docs.databricks.com/aws/en/ai-gateway/govern-model-services)
- [ai-gateway/govern-model-provider-services](https://docs.databricks.com/aws/en/ai-gateway/govern-model-provider-services)
- …and 31 more

### A broad copy-editing pass fixes SQL and shell examples (unbalanced parentheses, smart quotes, wrong fence languages, `DROP STREAMING TABLE` → `DROP TABLE`), repoints external links such as `.netrc`, and bumps the Genie One desktop download to 0.2.2.

`editorial` · copy and example fixes · 30 pages

resources/support adds a GovCloud/FedRAMP Moderate support portal pointer; excel-setup attributes the add-in failure to a known Microsoft Edge WebView2 issue (office-js #6771); sparkr examples move from DBFS paths to Unity Catalog volumes.

- [resources/support](https://docs.databricks.com/aws/en/resources/support)
- [integrations/excel-setup](https://docs.databricks.com/aws/en/integrations/excel-setup)
- [genie-one/desktop](https://docs.databricks.com/aws/en/genie-one/desktop)
- [dev-tools/cli/profiles](https://docs.databricks.com/aws/en/dev-tools/cli/profiles)
- [partner-connect/admin](https://docs.databricks.com/aws/en/partner-connect/admin)
- [reference/jobs-2.0-api](https://docs.databricks.com/aws/en/reference/jobs-2.0-api)
- …and 24 more

### The beta API reference was regenerated wholesale: the beta-header enum grows from "38 more" to "41 more", model descriptions and enum orderings are refreshed, and prose fields gain backticks — no endpoint or field semantics change in these lines.

`editorial` · bulk regeneration · 27 pages

Around 150 reference pages carry only these regenerated enum/description lines; the memory-store path constraints, deployment `include_archived` note and session grader-verdict text are the same statements with formatting fixes.

- [api/beta](https://platform.claude.com/docs/en/api/beta)
- [api/beta/messages](https://platform.claude.com/docs/en/api/beta/messages)
- [api/beta/files](https://platform.claude.com/docs/en/api/beta/files)
- [api/beta/skills](https://platform.claude.com/docs/en/api/beta/skills)
- [api/beta/skills/versions](https://platform.claude.com/docs/en/api/beta/skills/versions)
- [api/beta/vaults](https://platform.claude.com/docs/en/api/beta/vaults)
- …and 21 more

### The Genie Code docs are split up: use-genie-code's content moves into new features-capabilities, agent-mode, navigate-genie-code and full-page pages, and links across the corpus are repointed.

`editorial` · restructure · 24 pages

Requirements (region eligibility, compliance standards, geo, partner-powered AI features) now live on the new pages; the `use-genie-code#requirements` anchor becomes `agent-mode#requirements`.

- [genie-code/features-capabilities](https://docs.databricks.com/aws/en/genie-code/features-capabilities)
- [genie-code/agent-mode](https://docs.databricks.com/aws/en/genie-code/agent-mode)
- [genie-code/navigate-genie-code](https://docs.databricks.com/aws/en/genie-code/navigate-genie-code)
- [genie-code/full-page](https://docs.databricks.com/aws/en/genie-code/full-page)
- [genie-code/use-genie-code](https://docs.databricks.com/aws/en/genie-code/use-genie-code)
- [genie-code/](https://docs.databricks.com/aws/en/genie-code/)
- …and 18 more

### Serverless GPU tutorials replace their generic notes with an explicit environment-version requirement (version 4, 5 or 6 depending on the example), and the AI Runtime CLI docs spell out YAML constraints.

`editorial` · requirements notes · 21 pages

CLI docs state that `mlflow_artifact_location` must match an existing experiment's artifact location or be omitted, that `environment.version` requires an inline `environment.dependencies` list, and that `compute.num_accelerators` must be a multiple of the GPUs per node; a CUDA 13 devel image row replaces the Azure devel rows.

- [machine-learning/ai-runtime/examples/tutorials/sgc-xgboost](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-xgboost)
- [machine-learning/ai-runtime/examples/tutorials/sgc-cnn-mnist](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-cnn-mnist)
- [machine-learning/ai-runtime/examples/tutorials/sgc-api-h100-starter](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-api-h100-starter)
- [machine-learning/ai-runtime/examples/tutorials/sgc-distributed-finetune-qwen2-0.5b](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-distributed-finetune-qwen2-0.5b)
- [machine-learning/ai-runtime/examples/tutorials/sgc-distributed-gpt-oss-20b](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-distributed-gpt-oss-20b)
- [machine-learning/ai-runtime/examples/tutorials/sgc-distributed-pytorch-fsdp](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-distributed-pytorch-fsdp)
- …and 15 more

### A house-style pass rewrites "For how X, see…" as "To learn how X, see…" across dozens of pages and repoints the courses link to academy.claude.com.

`editorial` · copy edit · 20 pages

No statements of behaviour change in these lines.

- [agents-and-tools/agent-skills/overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [agents-and-tools/tool-use/bash-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/bash-tool)
- [agents-and-tools/tool-use/fine-grained-tool-streaming](https://platform.claude.com/docs/en/agents-and-tools/tool-use/fine-grained-tool-streaming)
- [agents-and-tools/tool-use/memory-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)
- [agents-and-tools/tool-use/text-editor-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/text-editor-tool)
- [agents-and-tools/tool-use/web-search-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool)
- …and 14 more

### "Databricks Data Intelligence Platform" becomes "Databricks Data + AI Platform" (and "Lakehouse Platform" becomes "Data + AI Platform") across architecture, migration and getting-started pages.

`editorial` · rename · 19 pages

Branding-only edits; the surrounding guidance is unchanged.

- [lakehouse-architecture/cost-optimization/best-practices](https://docs.databricks.com/aws/en/lakehouse-architecture/cost-optimization/best-practices)
- [lakehouse-architecture/interoperability-and-usability/best-practices](https://docs.databricks.com/aws/en/lakehouse-architecture/interoperability-and-usability/best-practices)
- [lakehouse-architecture/reference](https://docs.databricks.com/aws/en/lakehouse-architecture/reference)
- [lakehouse-architecture/](https://docs.databricks.com/aws/en/lakehouse-architecture/)
- [migration/warehouse-to-lakehouse](https://docs.databricks.com/aws/en/migration/warehouse-to-lakehouse)
- [migration/etl](https://docs.databricks.com/aws/en/migration/etl)
- …and 13 more

### Cookbook notebooks bump their model constant from `claude-opus-4-1` to `claude-opus-4-8`.

`editorial` · examples · 18 pages

The MongoDB RAG notebook also drops the "Claude 3" phrasing in favour of "Anthropic's Claude".

- [platform.claude.com/cookbook/misc-building-evals](https://platform.claude.com/cookbook/misc-building-evals)
- [platform.claude.com/cookbook/misc-how-to-enable-json-mode](https://platform.claude.com/cookbook/misc-how-to-enable-json-mode)
- [platform.claude.com/cookbook/misc-how-to-make-sql-queries](https://platform.claude.com/cookbook/misc-how-to-make-sql-queries)
- [platform.claude.com/cookbook/multimodal-best-practices-for-vision](https://platform.claude.com/cookbook/multimodal-best-practices-for-vision)
- [platform.claude.com/cookbook/multimodal-getting-started-with-vision](https://platform.claude.com/cookbook/multimodal-getting-started-with-vision)
- [platform.claude.com/cookbook/multimodal-how-to-transcribe-text](https://platform.claude.com/cookbook/multimodal-how-to-transcribe-text)
- …and 12 more

### Model pricing, rate-limit and comparison tables were regenerated — footnotes about batch discounts and cache-read pricing, deprecation links and per-model migration prompts — with no price or limit values changed in the excerpts.

`editorial` · regeneration · 14 pages

The migration guides' `/claude-api migrate this project to …` examples now name their own model.

- [about-claude/pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- [api/rate-limits](https://platform.claude.com/docs/en/api/rate-limits)
- [models/opus-5/overview](https://platform.claude.com/docs/en/models/opus-5/overview)
- [models/opus-4-8/overview](https://platform.claude.com/docs/en/models/opus-4-8/overview)
- [models/opus-4-7/overview](https://platform.claude.com/docs/en/models/opus-4-7/overview)
- [models/opus-4-6/overview](https://platform.claude.com/docs/en/models/opus-4-6/overview)
- …and 8 more

### Install snippets move to CLI 1.30.0 and `anthropic-java`/`anthropic-java-aws` 2.60.0, and the third-party platform guides were reflowed (Mythos Preview access wording, context-window notes, Sonnet 5 system-field note).

`editorial` · version bumps · 8 pages

Bedrock legacy and Vertex pages keep the same statements — code execution's system-field limitation on Claude Sonnet 5, 200k context for Sonnet 4.5/4 — split into shorter sentences.

- [cli-sdks-libraries/cli/quickstart](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/quickstart)
- [cli-sdks-libraries/sdks/java](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/java)
- [get-started](https://platform.claude.com/docs/en/get-started)
- [build-with-claude/claude-platform-on-aws](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws)
- [build-with-claude/claude-in-microsoft-foundry](https://platform.claude.com/docs/en/build-with-claude/claude-in-microsoft-foundry)
- [build-with-claude/claude-on-vertex-ai](https://platform.claude.com/docs/en/build-with-claude/claude-on-vertex-ai)
- …and 2 more

### Cookbook install cells switch from shell `!pip install` to the `%pip` magic.

`editorial` · examples · 8 pages

No dependency versions change in these lines.

- [platform.claude.com/cookbook/capabilities-classification-guide](https://platform.claude.com/cookbook/capabilities-classification-guide)
- [platform.claude.com/cookbook/capabilities-contextual-embeddings-guide](https://platform.claude.com/cookbook/capabilities-contextual-embeddings-guide)
- [platform.claude.com/cookbook/capabilities-summarization-guide](https://platform.claude.com/cookbook/capabilities-summarization-guide)
- [platform.claude.com/cookbook/capabilities-retrieval-augmented-generation-guide](https://platform.claude.com/cookbook/capabilities-retrieval-augmented-generation-guide)
- [platform.claude.com/cookbook/finetuning-finetuning-on-bedrock](https://platform.claude.com/cookbook/finetuning-finetuning-on-bedrock)
- [platform.claude.com/cookbook/misc-sampling-past-max-tokens](https://platform.claude.com/cookbook/misc-sampling-past-max-tokens)
- …and 2 more

### The "Enrich data using AI Functions" page is retitled "Transform unstructured data using AI Functions", and inbound links were updated.

`editorial` · rename · 8 pages

Link-text-only change on the citing pages.

- [large-language-models/batch-inference-pipelines](https://docs.databricks.com/aws/en/large-language-models/batch-inference-pipelines)
- [designer/built-in-operators](https://docs.databricks.com/aws/en/designer/built-in-operators)
- [large-language-models/ai-functions-uc-permissions](https://docs.databricks.com/aws/en/large-language-models/ai-functions-uc-permissions)
- [mlflow3/genai/tracing/redact-pii-otel-traces](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/redact-pii-otel-traces)
- [release-notes/product/2024/october](https://docs.databricks.com/aws/en/release-notes/product/2024/october)
- [release-notes/product/2025/october](https://docs.databricks.com/aws/en/release-notes/product/2025/october)
- …and 2 more

### Compliance and access-transparency curl examples were regenerated (header ordering, `anthropic-version` and `$ANTHROPIC_COMPLIANCE_ACCESS_KEY` usage) without changing the documented endpoints.

`editorial` · examples · 4 pages

compliance-content-data also rewords its Enterprise-only scope note.

- [manage-claude/compliance-content-data](https://platform.claude.com/docs/en/manage-claude/compliance-content-data)
- [manage-claude/compliance-org-data](https://platform.claude.com/docs/en/manage-claude/compliance-org-data)
- [manage-claude/compliance-activity-feed](https://platform.claude.com/docs/en/manage-claude/compliance-activity-feed)
- [manage-claude/access-transparency](https://platform.claude.com/docs/en/manage-claude/access-transparency)

### The dlt-meta metaprogramming project is documented as `sdp-meta` on a new page, with onboarding files now allowed in JSON or YAML.

`editorial` · rename · 3 pages

The existing dlt-meta page's prerequisites now read "To use sdp-meta, you must".

- [ldp/developer/sdp-meta](https://docs.databricks.com/aws/en/ldp/developer/sdp-meta)
- [ldp/developer/dlt-meta](https://docs.databricks.com/aws/en/ldp/developer/dlt-meta)
- [ldp/developer/](https://docs.databricks.com/aws/en/ldp/developer/)
