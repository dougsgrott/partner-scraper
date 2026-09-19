# Change digest

> #5 (2026-09-09-before) → #6 (2026-09-09) · 1,072 changes · rendered 2026-09-19T14:20:04+00:00

## At a glance

73 findings — **15** breaking, **19** behavioural, **27** additive, **12** editorial — covering 568 of 1,072 changed pages. Anything not here is in the full feed report beside this file.

**If you read nothing else:**

1. Every federation-issuer, federation-rule and service-account endpoint now carries a banner requiring an OAuth access token with the `org:admin` scope, from `ant auth login --scope org:admin` or a WIF rule; Admin API keys are not accepted.
2. MLflow tracing examples raise their floor from `mlflow[databricks]>=3.1` to `>=3.14.0` because the quick-starts now store traces in Unity Catalog and need a SQL warehouse configured.
3. On Claude Platform on AWS, a CMEK `kms_arn` must now be a single-Region key in your own AWS account — cross-account keys, multi-Region keys and alias ARNs are rejected.
4. A new "preserved thinking" model means Claude Fable 5.1 only accepts a replayed thinking block while everything before it is unchanged — edited, reordered or compacted history now needs `prefix_mismatch_behavior: "drop_block"` or the thinking blocks stripped, or the request is rejected with 400.
5. C# workload-identity-federation examples now construct `new AnthropicClient(new ClientOptions { Credentials = credentials })` instead of `new AnthropicOidcClient(credentials)`.
6. Compliance API and Access Transparency requests now take the `anthropic-version` header on every call, and all curl examples have been updated to send it.
7. Web fetch now refuses URLs that appear only in the system prompt, and the excluded-source list grows from container tools to any server-side tool result including code execution, the MCP connector and tool search.
8. In CMEK organizations, structured outputs are now listed as unavailable for all Claude Fable and Claude Mythos models, not just Claude Fable 5.
9. The TypeScript SDK now requires TypeScript 5.0 or later.
10. Change data feed now requires Databricks Runtime 19 or above, up from Databricks Runtime 18 LTS.
11. BigQuery `INTERVAL` columns are no longer supported — a foreign table containing one fails when its schema loads, so it can't be described, queried or ingested.
12. Job performance metrics now require the "Improved Lakeflow Performance Observability" workspace preview instead of access to Query performance insights.
13. Claude Fable 5.1 on Databricks retains prompts and responses for 30 days and cannot be used by customers who opt out of data retention.
14. Ingesting the affected Salesforce object now requires the `Query All Files` permission, which itself requires `View All Data`.
15. The TikTok Ads connector's BASIC-reports-only limitation is replaced by a hard cap: report data is only supported for reports with fewer than 20,000 ads.

---

## Breaking — 15

### Every federation-issuer, federation-rule and service-account endpoint now carries a banner requiring an OAuth access token with the `org:admin` scope, from `ant auth login --scope org:admin` or a WIF rule; Admin API keys are not accepted.

`breaking` · scope requirement · 32 pages

Added banner: "**Requires an OAuth access token with the `org:admin` scope**, from `ant auth login --scope org:admin` or a workload identity federation rule; Admin API keys are not accepted." The named `org:admin` scope requirement was absent before; the pages previously only said "Admin API keys are not accepted." in the body prose. The per-endpoint note that OAuth callers may only manage rules whose `oauth_scope` is `workspace:developer` or `workspace:inference` is retained.

- [api/admin/federation_issuers](https://platform.claude.com/docs/en/api/admin/federation_issuers)
- [api/admin/federation_issuers/archive](https://platform.claude.com/docs/en/api/admin/federation_issuers/archive)
- [api/admin/federation_issuers/create](https://platform.claude.com/docs/en/api/admin/federation_issuers/create)
- [api/admin/federation_issuers/list](https://platform.claude.com/docs/en/api/admin/federation_issuers/list)
- [api/admin/federation_issuers/retrieve](https://platform.claude.com/docs/en/api/admin/federation_issuers/retrieve)
- [api/admin/federation_issuers/update](https://platform.claude.com/docs/en/api/admin/federation_issuers/update)
- …and 26 more

### MLflow tracing examples raise their floor from `mlflow[databricks]>=3.1` to `>=3.14.0` because the quick-starts now store traces in Unity Catalog and need a SQL warehouse configured.

`breaking` · version floor · 31 pages

Install lines change from `pip install --upgrade "mlflow[databricks]>=3.1" <pkg>` to `>=3.14.0`, and pages add "The quick-start examples on this page require MLflow 3.14 or later because they store traces in Unity Catalog" plus `os.environ["MLFLOW_TRACING_SQL_WAREHOUSE_ID"]` setup and `from mlflow.entities.trace_location import UnityCatalog`. The Claude Code integration note changes from "(MLflow 3.4+)" to "(MLflow 3.14+)".

- [mlflow3/genai/tracing/integrations/](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/)
- [mlflow3/genai/tracing/integrations/anthropic](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/anthropic)
- [mlflow3/genai/tracing/integrations/autogen](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/autogen)
- [mlflow3/genai/tracing/integrations/ag2](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/ag2)
- [mlflow3/genai/tracing/integrations/crewai](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/crewai)
- [mlflow3/genai/tracing/integrations/deepseek](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/deepseek)
- …and 25 more

### On Claude Platform on AWS, a CMEK `kms_arn` must now be a single-Region key in your own AWS account — cross-account keys, multi-Region keys and alias ARNs are rejected.

`breaking` · key requirements · 20 pages

The `kms_arn` field description was just "Full ARN of the AWS KMS key." and now continues "On Claude Platform on AWS the key must be a single-Region key in your organization's own AWS account; cross-account keys, multi-Region keys, and alias ARNs are rejected." manage-claude/cmek-aws-kms repeats the single-region/same-account requirement and adds CloudTrail troubleshooting guidance for distinguishing a source-ARN mismatch from an encryption-context mismatch.

- [api/admin/external_keys](https://platform.claude.com/docs/en/api/admin/external_keys)
- [api/admin/external_keys/create](https://platform.claude.com/docs/en/api/admin/external_keys/create)
- [api/admin/external_keys/list](https://platform.claude.com/docs/en/api/admin/external_keys/list)
- [api/admin/external_keys/retrieve](https://platform.claude.com/docs/en/api/admin/external_keys/retrieve)
- [api/admin/external_keys/update](https://platform.claude.com/docs/en/api/admin/external_keys/update)
- [api/beta/organization/external_keys](https://platform.claude.com/docs/en/api/beta/organization/external_keys)
- …and 14 more

### A new "preserved thinking" model means Claude Fable 5.1 only accepts a replayed thinking block while everything before it is unchanged — edited, reordered or compacted history now needs `prefix_mismatch_behavior: "drop_block"` or the thinking blocks stripped, or the request is rejected with 400.

`breaking` · thinking block validity · 8 pages

New page build-with-claude/preserved-thinking. build-with-claude/compaction adds: "On Claude Fable 5.1, remove the `thinking` and `redacted_thinking` blocks from any assistant turn you re-insert after the compaction block, or send `thinking.block_binding.prefix_mismatch_behavior: \"drop_block\"` with the `thinking-binding-controls-2026-08-01` beta header... Where the check is enforced, the continuation request is rejected with a 400 error." build-with-claude/context-editing adds: "For new accounts created on or after August 31, 2026, a request that replays an invalidated block is rejected unless you opt into dropping it," and notes server-side context editing never invalidates blocks while client-side edits to earlier turns can. thinking-troubleshooting and api/errors document the resulting error messages; computer-use-tool advises keeping `prefix_mismatch_behavior: "drop_block"` if you must prune.

- [build-with-claude/preserved-thinking](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking)
- [build-with-claude/compaction](https://platform.claude.com/docs/en/build-with-claude/compaction)
- [build-with-claude/context-editing](https://platform.claude.com/docs/en/build-with-claude/context-editing)
- [build-with-claude/thinking](https://platform.claude.com/docs/en/build-with-claude/thinking)
- [build-with-claude/thinking-troubleshooting](https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting)
- [api/errors](https://platform.claude.com/docs/en/api/errors)
- …and 2 more

### C# workload-identity-federation examples now construct `new AnthropicClient(new ClientOptions { Credentials = credentials })` instead of `new AnthropicOidcClient(credentials)`.

`breaking` · sdk api · 7 pages

Old line: "using var client = new AnthropicOidcClient(credentials);" New line: "using var client = new AnthropicClient(new ClientOptions { Credentials = credentials });" The AWS, GitHub Actions and Kubernetes samples also replace the `?? throw new InvalidOperationException("No federation credentials found in environment");` fallback with comments naming the expected environment variables.

- [manage-claude/wif-providers/gcp](https://platform.claude.com/docs/en/manage-claude/wif-providers/gcp)
- [manage-claude/wif-providers/okta](https://platform.claude.com/docs/en/manage-claude/wif-providers/okta)
- [manage-claude/workload-identity-federation](https://platform.claude.com/docs/en/manage-claude/workload-identity-federation)
- [manage-claude/wif-providers/azure](https://platform.claude.com/docs/en/manage-claude/wif-providers/azure)
- [manage-claude/wif-providers/aws](https://platform.claude.com/docs/en/manage-claude/wif-providers/aws)
- [manage-claude/wif-providers/github-actions](https://platform.claude.com/docs/en/manage-claude/wif-providers/github-actions)
- …and 1 more

### Compliance API and Access Transparency requests now take the `anthropic-version` header on every call, and all curl examples have been updated to send it.

`breaking` · required header · 6 pages

manage-claude/compliance-api previously read "Every endpoint lives under `/v1/compliance/*` on `https://api.anthropic.com` and authenticates through the `x-api-key` header." It now reads "...authenticates through the `x-api-key` header, and takes the [`anthropic-version`] header on every request," and the page gains a "Versioning" section: "Send the `anthropic-version` header on every request." Every example across the compliance and access-transparency pages adds `--header "anthropic-version: 2023-06-01"`.

- [manage-claude/compliance-api](https://platform.claude.com/docs/en/manage-claude/compliance-api)
- [manage-claude/compliance-activity-feed](https://platform.claude.com/docs/en/manage-claude/compliance-activity-feed)
- [manage-claude/compliance-sessions](https://platform.claude.com/docs/en/manage-claude/compliance-sessions)
- [manage-claude/compliance-content-data](https://platform.claude.com/docs/en/manage-claude/compliance-content-data)
- [manage-claude/compliance-org-data](https://platform.claude.com/docs/en/manage-claude/compliance-org-data)
- [manage-claude/access-transparency](https://platform.claude.com/docs/en/manage-claude/access-transparency)

### Web fetch now refuses URLs that appear only in the system prompt, and the excluded-source list grows from container tools to any server-side tool result including code execution, the MCP connector and tool search.

`breaking` · tool restriction · 1 page

Old text: "The tool cannot fetch arbitrary URLs that Claude generates or URLs from container-based server tools (such as Code Execution and Bash)." New text: "The tool cannot fetch URLs that appear only in Claude's own output or only in the system prompt. To make a URL from the system prompt fetchable, also include it in a user message. Results of other server-side tools, such as code execution, the MCP connector, or tool search, are not an allowed source either." The page also clarifies that client-side tool results remain an allowed source even when they echo text Claude produced.

- [agents-and-tools/tool-use/web-fetch-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-fetch-tool)

### In CMEK organizations, structured outputs are now listed as unavailable for all Claude Fable and Claude Mythos models, not just Claude Fable 5.

`breaking` · feature restriction · 1 page

Old: "Structured outputs (not available for Claude Fable 5 or Claude Mythos models in CMEK organizations)". New: "Structured outputs (not available for Claude Fable or Claude Mythos models in CMEK organizations)".

- [manage-claude/cmek](https://platform.claude.com/docs/en/manage-claude/cmek)

### The TypeScript SDK now requires TypeScript 5.0 or later.

`breaking` · version floor · 1 page

Old: "TypeScript >= 4.9 is supported." New: "TypeScript >= 5.0 is supported."

- [cli-sdks-libraries/sdks/typescript](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/typescript)

### Change data feed now requires Databricks Runtime 19 or above, up from Databricks Runtime 18 LTS.

`breaking` · version floor · 1 page

The Requirements bullet "Databricks Runtime 18 LTS or above" becomes "Databricks Runtime 19 or above".

- [tables/features/change-data-feed](https://docs.databricks.com/aws/en/tables/features/change-data-feed)

### BigQuery `INTERVAL` columns are no longer supported — a foreign table containing one fails when its schema loads, so it can't be described, queried or ingested.

`breaking` · unsupported type · 1 page

The type-mapping rows change from "`ARRAY`, `GEOGRAPHY`, `INTERVAL`, `JSON`, `STRING`, `STRUCT` | `VarcharType`" to the same list without `INTERVAL`, and a new note states: "BigQuery `INTERVAL` columns are not currently supported. A foreign table that contains an `INTERVAL` column fails when its schema loads, so you can't describe, query, or ingest the table. Tables without an `INTERVAL` column are unaffected."

- [query-federation/bigquery](https://docs.databricks.com/aws/en/query-federation/bigquery)

### Job performance metrics now require the "Improved Lakeflow Performance Observability" workspace preview instead of access to Query performance insights.

`breaking` · requirement change · 1 page

Old: "Your workspace must have access to [Query performance insights](https://docs.databricks.com/aws/en/sql/user/queries/performance-insights)." New: "Before you can view these metrics, the **Improved Lakeflow Performance Observability** preview must be enabled for your workspace."

- [jobs/diagnose-job-performance](https://docs.databricks.com/aws/en/jobs/diagnose-job-performance)

### Claude Fable 5.1 on Databricks retains prompts and responses for 30 days and cannot be used by customers who opt out of data retention.

`breaking` · data retention · 1 page

New text: "For Claude Fable 5.1, prompts and responses are retained for 30 days for trust and safety purposes. Customers who opt out of data retention cannot use Claude Fable 5.1." The same note already existed for Claude Fable 5. The page also states that `minimal`, `medium` or `xhigh` effort values map to `max` and that `none` is rejected.

- [machine-learning/foundation-model-apis/supported-models](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/supported-models)

### Ingesting the affected Salesforce object now requires the `Query All Files` permission, which itself requires `View All Data`.

`breaking` · permission requirement · 1 page

Old: "To ingest this object, you must have the `View All Data` permission." New: "To ingest this object, you must have the `Query All Files` permission, which requires `View All Data`."

- [ingestion/lakeflow-connect/salesforce-limits](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/salesforce-limits)

### The TikTok Ads connector's BASIC-reports-only limitation is replaced by a hard cap: report data is only supported for reports with fewer than 20,000 ads.

`breaking` · limit · 1 page

Old: "The connector only supports ingestion of BASIC reports." New: "Report data is only supported for reports with fewer than 20,000 ads. If a report includes 20,000 or more ads, TikTok's synchronous report[ing]..."

- [ingestion/lakeflow-connect/tiktok-ads-limits](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/tiktok-ads-limits)

## Behavioural — 19

### A new declarative `ant apply` command lets you keep agents, environments, skills, memory stores and deployments in sync with files in your repo, and the managed-agents guides now use it instead of piping YAML into `ant beta:<resource> create`.

`behavioural` · cli · 13 pages

New page cli-sdks-libraries/cli/apply. Examples change from `ant beta:environments create < environment.yaml` to `ant apply environment.yaml`, and from `ant beta:agents create < agent.yaml` / `$(ant beta:agents create --transform id --raw-output < ...)` to the apply form. cli-sdks-libraries/cli/scripting also documents `ant beta:sessions:events stream --session-id ... --format jsonl` for watching a session as it runs.

- [cli-sdks-libraries/cli/apply](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/apply)
- [managed-agents/self-hosted-sandboxes](https://platform.claude.com/docs/en/managed-agents/self-hosted-sandboxes)
- [managed-agents/environments](https://platform.claude.com/docs/en/managed-agents/environments)
- [managed-agents/quickstart](https://platform.claude.com/docs/en/managed-agents/quickstart)
- [managed-agents/permission-policies](https://platform.claude.com/docs/en/managed-agents/permission-policies)
- [managed-agents/tools](https://platform.claude.com/docs/en/managed-agents/tools)
- …and 7 more

### MLflow evaluation and labeling examples now read traces from Unity Catalog and require a SQL warehouse to be configured first.

`behavioural` · prerequisite · 11 pages

Pages add "The examples on this page access traces stored in Unity Catalog. Configure a SQL warehouse before you run them:" followed by `os.environ["MLFLOW_TRACING_SQL_WAREHOUSE_ID"] = "<SQL_WAREHOUSE_ID>"`, replacing guidance such as "# In Databricks notebooks, the experiment defaults to the notebook experiment." dev-tools/databricks-apps/mlflow notes that an MLflow experiment resource grants workspace-level permissions and that Unity Catalog trace tables must be added as app resources separately.

- [mlflow3/genai/eval-monitor/code-based-scorer-examples](https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/code-based-scorer-examples)
- [mlflow3/genai/eval-monitor/custom-scorer-dev-workflow](https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/custom-scorer-dev-workflow)
- [mlflow3/genai/eval-monitor/align-judges](https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/align-judges)
- [mlflow3/genai/eval-monitor/evaluate-app](https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/evaluate-app)
- [mlflow3/genai/eval-monitor/custom-judge/create-custom-judge](https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/custom-judge/create-custom-judge)
- [mlflow3/genai/eval-monitor/concepts/judges/is_context_sufficient](https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/concepts/judges/is_context_sufficient)
- …and 5 more

### ABAC GRANT policies leave Beta, SQL now works for every supported securable type rather than models only, and GRANT policies appear in `INFORMATION_SCHEMA`.

`behavioural` · ga · 6 pages

The page heading changes from "ABAC GRANT policies (Beta)" to "ABAC GRANT policies" and the Beta callout is removed. Removed limitations include "Creating a GRANT policy in SQL is currently available for models only.", "`INFORMATION_SCHEMA` does not include GRANT policies." and "System tags are available on models, but not yet on model services." The SQL grammar changes from `GRANT privilege [, ...] FOR MODELS` to `FOR securable_type`, with plural, space-or-underscore forms required (`MODEL SERVICES` or `MODEL_SERVICES`; singular forms are not accepted). sql-ref-syntax-ddl-create-policy adds that creating, modifying or dropping an ABAC GRANT policy with SQL requires Databricks Runtime 18 LTS or above.

- [data-governance/unity-catalog/abac/grant-policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/grant-policies)
- [data-governance/unity-catalog/abac/common-patterns](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/common-patterns)
- [data-governance/unity-catalog/abac/requirements](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/requirements)
- [release-notes/product/2026/june](https://docs.databricks.com/aws/en/release-notes/product/2026/june)
- [sql/language-manual/sql-ref-syntax-ddl-create-policy](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-ddl-create-policy)
- [ai-gateway/govern-access-to-models-with-grant-policies](https://docs.databricks.com/aws/en/ai-gateway/govern-access-to-models-with-grant-policies)

### The Covered Models ZDR rule is now qualified: Fable and Mythos models still require 30-day retention and are "not available under ZDR unless expressly authorized by Anthropic", and the rule now names Fable 5.1 and Mythos 5.1 too.

`behavioural` · data retention · 5 pages

manage-claude/api-and-data-retention previously ended "ZDR is therefore not available for either model." and now reads "ZDR is therefore not available for any of them unless expressly authorized by Anthropic", listing "Claude Fable 5.1, Claude Mythos 5.1, Claude Fable 5, and Claude Mythos 5". The introducing-* pages previously said "not available under zero data retention: both are designated [Co..." and now say "not available under zero data retention unless expressly authorized by Anthropic". build-with-claude/overview changes "both handle refusals from Claude Fable 5, which [is not available under ZDR]" to "they handle refusals from the Claude Fable models, which [are not available under ZDR]".

- [manage-claude/api-and-data-retention](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention)
- [models/fable-5/migration-guide](https://platform.claude.com/docs/en/models/fable-5/migration-guide)
- [about-claude/models/introducing-claude-fable-5-and-claude-mythos-5](https://platform.claude.com/docs/en/about-claude/models/introducing-claude-fable-5-and-claude-mythos-5)
- [models/fable-5/introducing-claude-fable-5-and-claude-mythos-5](https://platform.claude.com/docs/en/models/fable-5/introducing-claude-fable-5-and-claude-mythos-5)
- [build-with-claude/overview](https://platform.claude.com/docs/en/build-with-claude/overview)

### Remote Cowork session retention is now qualified as "6 years, unless a user deletes the session sooner", the session endpoints are documented as read-only, and legal-hold guidance now covers remote session transcripts.

`behavioural` · retention · 3 pages

compliance-sessions changes the remote-session Retention cell from "6 years, held by Anthropic" to "6 years, unless a user deletes the session sooner; held by Anthropic", and adds "The session endpoints are read-only; local and remote sessions cannot be deleted through the Compliance API." compliance-integration-patterns changes "If you must retain chat content after users delete it in claude.ai" to "If you must retain chat content or remote session transcripts after users delete them in claude.ai".

- [manage-claude/compliance-sessions](https://platform.claude.com/docs/en/manage-claude/compliance-sessions)
- [manage-claude/compliance-integration-patterns](https://platform.claude.com/docs/en/manage-claude/compliance-integration-patterns)
- [manage-claude/compliance-errors](https://platform.claude.com/docs/en/manage-claude/compliance-errors)

### The `ucode` CLI is now called the Unity Gateway CLI, and is the recommended path for pointing Claude Code at the gateway.

`behavioural` · rename · 3 pages

Old: "- `ucode` routes among models within a harness. Routing across harnesses requires Omnigent v0.8.0 or later." and "The `ucode` CLI. Requires Python 3.12 or later". New text substitutes "The Unity Gateway CLI". claude-max-anthropic-enterprise-support now recommends it for obtaining and refreshing the Databricks OAuth token.

- [ai-gateway/smart-routing](https://docs.databricks.com/aws/en/ai-gateway/smart-routing)
- [ai-gateway/coding-agent-integration-model-provider-services](https://docs.databricks.com/aws/en/ai-gateway/coding-agent-integration-model-provider-services)
- [ai-gateway/claude-max-anthropic-enterprise-support](https://docs.databricks.com/aws/en/ai-gateway/claude-max-anthropic-enterprise-support)

### Previewing a `FILE`-typed value reads the file's contents, so it now requires access to the file itself in addition to the table — `READ VOLUME` on the underlying volume for `FILE EXTERNAL`.

`behavioural` · permission requirement · 3 pages

file-type adds "Previewing reads the file's contents, which requires access to the file in addition to the table." unstructured/file adds "File contents stay in storage. Reading them requires access to the file: `READ VOLUME` on the underlying volume for `FILE EXTERNAL`, or ac[cess...]".

- [sql/language-manual/data-types/file-type](https://docs.databricks.com/aws/en/sql/language-manual/data-types/file-type)
- [sql/user/sql-editor/results](https://docs.databricks.com/aws/en/sql/user/sql-editor/results)
- [unstructured/file](https://docs.databricks.com/aws/en/unstructured/file)

### After an inference-hook circuit breaker trips, Anthropic now probes your server for recovery starting 10 minutes later at roughly one request per minute — but rotating the signing secret stops the testing and the breaker no longer resets on its own.

`behavioural` · failure handling · 2 pages

inference-hooks-endpoint adds "Starting 10 minutes after the trip, Anthropic tests whether your server has recovered: at most about once per minute, one request...", replacing text that began "Sustained webhook failures attributable to your AI security server trip a circuit breaker that stops enforcement: Anthropic stops conta...". inference-hooks-configuration adds that after rotating the signing secret "testing stops and the breaker no longer resets on its own; turn **Enforce verdicts** back on when your server" is ready.

- [manage-claude/inference-hooks-endpoint](https://platform.claude.com/docs/en/manage-claude/inference-hooks-endpoint)
- [manage-claude/inference-hooks-configuration](https://platform.claude.com/docs/en/manage-claude/inference-hooks-configuration)

### Lakebase's direct-write path for synced tables is documented as off by default, requiring a workspace admin to turn it on.

`behavioural` · default change · 2 pages

The pages now read "It's off by default and a workspace admin must turn it on. When enabled, it writes data directly into the storage layer backing your Lakeba[se instance]", replacing prose that described it as a feature "that reduces the time required for initial loads and full refreshes".

- [oltp/instances/sync-data/sync-table](https://docs.databricks.com/aws/en/oltp/instances/sync-data/sync-table)
- [oltp/projects/sync-tables](https://docs.databricks.com/aws/en/oltp/projects/sync-tables)

### The stated 32 TB per-branch database storage quota for Lakebase has been removed; the docs now describe an unspecified operational quota.

`behavioural` · limit removed · 2 pages

Old: "Each branch has a 32 TB database storage quota." New: "Each branch has a database storage quota." The following sentence, that this is an operational rather than architectural limit because data lives in cloud object storage, is unchanged.

- [oltp/instances/create/](https://docs.databricks.com/aws/en/oltp/instances/create/)
- [oltp/projects/manage-projects](https://docs.databricks.com/aws/en/oltp/projects/manage-projects)

### External-engine Spark configuration examples now set `spark.sql.catalog.spark_catalog` to `org.apache.spark.sql.delta.catalog.DeltaCatalog` instead of `io.unitycatalog.spark.UCSingleCatalog`.

`behavioural` · configuration change · 2 pages

Old: `"spark.sql.catalog.spark_catalog": "io.unitycatalog.spark.UCSingleCatalog",` New: `"spark.sql.catalog.spark_catalog": "org.apache.spark.sql.delta.catalog.DeltaCatalog",`

- [external-access/cross-engine-abac](https://docs.databricks.com/aws/en/external-access/cross-engine-abac)
- [external-access/unity-rest](https://docs.databricks.com/aws/en/external-access/unity-rest)

### On Claude Fable 5.1 and Claude Mythos 5.1, `tool_choice` values `any` and `tool` return a 400 error; the docs tell you to leave it at `auto` and set `"strict": true` on the tool instead.

`behavioural` · model limitation · 1 page

Added to claude_api_primer: "On Claude Fable 5.1 and Claude Mythos 5.1, `any` and `tool` return a 400 error. Leave `tool_choice` at `auto` and set `"strict": true` on the tool definition to guarantee that any call Claude makes matches the tool's `input_schema`." This is a property of the new models, not a change to existing ones.

- [claude_api_primer](https://platform.claude.com/docs/en/claude_api_primer)

### `Authorization: Bearer <token>` is now the documented primary auth header and accepts your API key directly; `x-api-key` is relabelled a "Legacy fallback for `Authorization`, still supported".

`behavioural` · authentication · 1 page

Both header rows previously had Required = "One of `x-api-key` or `Authorization`". `Authorization` is now "Yes, unless `x-api-key` is set" and its value is "your API key or a short-lived access token obtained from `POST /v1/oauth/token`"; `x-api-key` is now Required = "No". The SDK benefits bullet changes from "Automatic header management (`x-api-key`, `anthropic-version`, `content-type`)" to "(authentication, `anthropic-version`, `content-type`)".

- [api/overview](https://platform.claude.com/docs/en/api/overview)

### The C# SDK's beta notices are gone — the page no longer warns that APIs may change between versions or that breaking changes may land in minor or patch releases.

`behavioural` · stability · 1 page

Removed: "The C# SDK is currently in beta. APIs may change between versions." and the warning beginning "Although this package is versioned as 10+, it's currently in beta." The SemVer section now stands on its own.

- [cli-sdks-libraries/sdks/csharp](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/csharp)

### The top-level `effort` parameter is now described as available on all supported models with no beta header, while per-message effort stays in beta behind a `mid-conversation-output-...` header.

`behavioural` · ga · 1 page

The page now states "The top-level effort parameter is available on all supported models with no beta header required" and "Per-message effort is in beta and requires the beta header `mid-conversation-ou...`".

- [build-with-claude/effort](https://platform.claude.com/docs/en/build-with-claude/effort)

### Pipeline unit testing no longer requires the PREVIEW channel; it now requires Databricks Runtime 18.1 or above, and the setup steps drop the channel setting.

`behavioural` · requirement change · 1 page

Old requirement: "Pipeline must be on the **PREVIEW** channel. Unit testing is in Beta and is only available on PREVIEW." New: "Pipeline must run on Databricks Runtime 18.1 or above. Earlier runtimes do not include the unit testing module." The JSON snippet drops `"channel": "PREVIEW"`, leaving only `"continuous": false`.

- [ldp/unit-testing](https://docs.databricks.com/aws/en/ldp/unit-testing)

### The deprecation of `limit`, `offset`, `total_count` and `next_page` in `/api/2.1/clusters/events` moves from October 20, 2026 to November 30, 2026.

`behavioural` · deprecation date · 1 page

Old: "On October 20, 2026, Databricks will deprecate the `limit`, `offset`, `total_count`, and `next_page` fields..." New: "On November 30, 2026, ..."

- [compute/events-api-updates](https://docs.databricks.com/aws/en/compute/events-api-updates)

### A job running continuously for more than 30 days loses access to files under `/Workspace`, including source code checked out from a remote Git repository — restart it at least every 30 days.

`behavioural` · limit · 1 page

New text added under "File access permission limit": "A job that runs continuously for more than 30 days loses access to files under `/Workspace`. To retain access, restart the job at least once every 30 days. This also applies to jobs that use source code from a remote Git repository, because the job reads the checked-out repository from a path under `/Workspace`." The existing 36-hour interactive / 30-day job sentence is unchanged apart from a typo fix.

- [files/workspace](https://docs.databricks.com/aws/en/files/workspace)

### Databricks Runtime 18 LTS documents that the Apache Avro fast reader, on by default in Avro 1.12.1, can exhaust executor memory in long-running jobs; the workaround is `-Dorg.apache.avro.fastread=false`.

`behavioural` · known issue · 1 page

New known-issue entry: "**Apache Avro fast reader can exhaust executor memory in long-running jobs**: In Databricks Runtime 18 LTS, Apache Avro 1.12.1 turns on th[e fast reader]..." with the JVM option to be added for both driver and executors.

- [release-notes/runtime/18](https://docs.databricks.com/aws/en/release-notes/runtime/18)

## Additive — 27

### Lakeflow Connect gains managed connectors for Anysphere Audit Logs (Cursor), Verkada and Glean, plus a OneDrive file-ingestion guide.

`additive` · new connectors · 28 pages

Each connector ships a full page set (overview, connection, source setup, pipeline, reference, limits, FAQ, troubleshooting) and is linked from saas-overview, faq and file-connectors-overview.

- [ingestion/lakeflow-connect/anysphere-audit-logs](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs)
- [ingestion/lakeflow-connect/anysphere-audit-logs-connection](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-connection)
- [ingestion/lakeflow-connect/anysphere-audit-logs-faq](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-faq)
- [ingestion/lakeflow-connect/anysphere-audit-logs-limits](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-limits)
- [ingestion/lakeflow-connect/anysphere-audit-logs-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-pipeline)
- [ingestion/lakeflow-connect/anysphere-audit-logs-reference](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-reference)
- …and 22 more

### Claude Fable 5.1 (`claude-fable-5-1`) and the invitation-only Claude Mythos 5.1 have shipped, with their own overview, migration and prompting pages, and Claude Fable 5 is now labelled legacy.

`additive` · new model · 19 pages

New pages: models/fable-5-1/overview, models/fable-5-1/migration-guide, models/fable-5-1/whats-new-fable-5-1, models/mythos-5-1/overview, build-with-claude/prompt-engineering/prompting-claude-fable-5-1, release-notes/system-prompts/claude-fable-5-1. The primer positions it as a "Step up for the hardest long-running agentic and research tasks, at 2x Claude Opus 5 pricing" and now calls Claude Opus 5 the "Recommended default for most work". models/fable-5/overview changes its Status row from "Active (latest)" to "Active (legacy)". about-claude/model-deprecations adds a row for `claude-fable-5-1` with retirement "Not sooner than September 1, 2027".

- [models/fable-5-1/overview](https://platform.claude.com/docs/en/models/fable-5-1/overview)
- [models/fable-5-1/migration-guide](https://platform.claude.com/docs/en/models/fable-5-1/migration-guide)
- [models/fable-5-1/whats-new-fable-5-1](https://platform.claude.com/docs/en/models/fable-5-1/whats-new-fable-5-1)
- [models/mythos-5-1/overview](https://platform.claude.com/docs/en/models/mythos-5-1/overview)
- [release-notes/system-prompts/claude-fable-5-1](https://platform.claude.com/docs/en/release-notes/system-prompts/claude-fable-5-1)
- [build-with-claude/prompt-engineering/prompting-claude-fable-5-1](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1)
- …and 13 more

### Feature support lists across the platform add `claude-fable-5-1` and `claude-mythos-5-1` — structured outputs, browser use, compaction, web-fetch dynamic filtering, task budgets, refusal fallback, mid-conversation system injection and the managed-agents model enum.

`additive` · model support · 14 pages

Examples: structured outputs "Supported models" goes from "`claude-fable-5`, `claude-mythos-5`, ..." to "`claude-fable-5-1`, `claude-mythos-5-1`, `claude-fable-5`, ..."; `BetaManagedAgentsModel` goes from "\"claude-sonnet-5\" or \"claude-fable-5\" or \"claude-opus-5\" or 10 more" to "\"claude-fable-5-1\" or \"claude-sonnet-5\" or \"claude-fable-5\" or 11 more". token-counting now says Fable 5.1, Mythos 5.1, Fable 5 and Mythos 5 "share the tokenizer introduced with Claude Opus 4.7". parallel-tool-use adds a note that "Claude Fable 5.1 may issue fewer parallel tool calls than earlier models".

- [agents-and-tools/tool-use/web-fetch-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-fetch-tool)
- [build-with-claude/structured-outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)
- [agents-and-tools/tool-use/browser-use-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/browser-use-tool)
- [build-with-claude/compaction](https://platform.claude.com/docs/en/build-with-claude/compaction)
- [managed-agents/reference](https://platform.claude.com/docs/en/managed-agents/reference)
- [build-with-claude/handling-stop-reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons)
- …and 8 more

### Unity Catalog adds ABAC DENY policies (Beta), which explicitly deny `MANAGE ACCESS CONTROL` on tag-matched securables and take precedence over grants.

`additive` · new feature · 13 pages

New page data-governance/unity-catalog/abac/deny-policies. Existing ABAC pages now scope themselves away from it — abac/performance changes "GRANT policies (Beta) are not su..." to "GRANT policies and DENY policies (Bet...", and privileges-reference adds "`MANAGE ACCESS CONTROL` can be *denied*, through an ABAC DENY policy". sql/language-manual/security-deny adds a pointer distinguishing the `hive_metastore` DENY statement from ABAC DENY policies.

- [data-governance/unity-catalog/abac/deny-policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/deny-policies)
- [data-governance/unity-catalog/abac/](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/)
- [data-governance/unity-catalog/abac/core-concepts](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/core-concepts)
- [data-governance/unity-catalog/abac/best-practices](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/best-practices)
- [data-governance/unity-catalog/abac/performance](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/performance)
- [data-governance/unity-catalog/abac/policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/policies)
- …and 7 more

### Databricks Foundation Model APIs add `databricks-claude-fable-5-1`, `databricks-gemini-3-8-flash` and `databricks-gpt-6-astra`, with limits, vision, function-calling and reasoning support tables updated.

`additive` · new models · 13 pages

New model IDs appear in the query pages; limits adds "Gemini 3.8 Flash | 200,000 | 20,000 | 360,000"; priority-mode and acceptable-use-models add GPT-6 Astra and Gemini 3.8 Flash rows. query-reason-models records that Claude Fable 5.1 "always uses adaptive thinking, and reasoning cannot be disabled" and accepts `low`, `medium`, `high`, `xhigh` and `max`.

- [machine-learning/model-serving/query-anthropic-messages](https://docs.databricks.com/aws/en/machine-learning/model-serving/query-anthropic-messages)
- [machine-learning/model-serving/query-gemini-api](https://docs.databricks.com/aws/en/machine-learning/model-serving/query-gemini-api)
- [machine-learning/model-serving/query-openai-responses](https://docs.databricks.com/aws/en/machine-learning/model-serving/query-openai-responses)
- [machine-learning/foundation-model-apis/limits](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/limits)
- [machine-learning/foundation-model-apis/priority-mode](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/priority-mode)
- [machine-learning/foundation-model-apis/supported-models](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/supported-models)
- …and 7 more

### Databricks SQL adds the `time_bucket` function and the `ai_enrich` AI function (Beta), and the AI Functions page is retitled "Transform unstructured data using AI Functions".

`additive` · new functions · 13 pages

New reference pages for both functions, listed in sql-ref-functions-builtin and the alphabetical index. ai-functions adds "| [ai_enrich](...) (Beta) | Generate new columns for each row from a ...". Links elsewhere change from "Enrich data using AI Functions" to "Transform unstructured data using AI Functions".

- [sql/language-manual/functions/time_bucket](https://docs.databricks.com/aws/en/sql/language-manual/functions/time_bucket)
- [sql/language-manual/functions/ai_enrich](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_enrich)
- [sql/language-manual/sql-ref-functions-builtin](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-functions-builtin)
- [sql/language-manual/sql-ref-functions-builtin-alpha](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-functions-builtin-alpha)
- [sql/language-manual/functions/date_trunc](https://docs.databricks.com/aws/en/sql/language-manual/functions/date_trunc)
- [sql/language-manual/functions/ai_extract](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_extract)
- …and 7 more

### Mid-conversation system messages gain a `clear_at` field: with `"next_user_message"` the message stays in the array but stops being shown to the model after the turn it follows.

`additive` · new field · 9 pages

New reference text: "How long this system message's text stays in front of the model. `\"never\"` (the default) renders it on every request that includes it. `\"next_user_message\"` renders it only for the user turn it follows," and "the message stays in the array (send it unchanged) but is no longer shown to the model. Only permitted on `role: \"system\"` messages." The feature is listed as beta on Claude Fable 5.1, Claude Mythos 5.1, Claude Fable 5, Claude Mythos 5, Claude Opus 4.8 and Claude Opus 5, and placement rules are spelled out: a content-carrying `system` message must immediately follow a `user` turn and cannot be first in `messages`.

- [build-with-claude/mid-conversation-system-messages](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages)
- [build-with-claude/prompt-caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [build-with-claude/working-with-messages](https://platform.claude.com/docs/en/build-with-claude/working-with-messages)
- [api/beta/messages](https://platform.claude.com/docs/en/api/beta/messages)
- [api/beta](https://platform.claude.com/docs/en/api/beta)
- [api/beta/messages/batches](https://platform.claude.com/docs/en/api/beta/messages/batches)
- …and 3 more

### Lakebase adds HIPAA support with its own enablement, audit-logging and compliance pages, and Lakebase is available by default in compliance-security-profile workspaces.

`additive` · compliance · 9 pages

Three new pages cover enabling HIPAA for Lakebase projects, HIPAA audit log capture and delivery, and shared responsibility for PHI including the BAA. release-notes/lakebase/ notes "You no longer need to enable Lakebase in these workspaces." The HITRUST and IRAP pages are reworded from "the workspace must have the compliance security profile enabled" to "you must enable the compliance security profile".

- [oltp/projects/enable-hipaa-compliance](https://docs.databricks.com/aws/en/oltp/projects/enable-hipaa-compliance)
- [oltp/projects/hipaa-audit-logging](https://docs.databricks.com/aws/en/oltp/projects/hipaa-audit-logging)
- [oltp/projects/hipaa-compliance](https://docs.databricks.com/aws/en/oltp/projects/hipaa-compliance)
- [oltp/projects/data-protection](https://docs.databricks.com/aws/en/oltp/projects/data-protection)
- [oltp/projects/private-link](https://docs.databricks.com/aws/en/oltp/projects/private-link)
- [release-notes/lakebase/](https://docs.databricks.com/aws/en/release-notes/lakebase/)
- …and 3 more

### Databricks adds built-in MCP Services — platform-managed tools for workspace and common SaaS applications that need no server registration or OAuth app.

`additive` · new feature · 8 pages

New page agents/mcp-tools/built-in-mcp-services. mcp-services notes built-in services ship with platform-managed tools and a built-in service policy and "handle OAuth for you, with no app registration required". agents/mcp-tools/databricks-sql now recommends the `system.ai.dbsql` MCP Service.

- [agents/mcp-tools/built-in-mcp-services](https://docs.databricks.com/aws/en/agents/mcp-tools/built-in-mcp-services)
- [agents/mcp-tools/mcp-services](https://docs.databricks.com/aws/en/agents/mcp-tools/mcp-services)
- [agents/mcp-tools/databricks-sql](https://docs.databricks.com/aws/en/agents/mcp-tools/databricks-sql)
- [agents/mcp-tools/use-mcp-in-agents](https://docs.databricks.com/aws/en/agents/mcp-tools/use-mcp-in-agents)
- [agents/mcp-tools/managed-mcp](https://docs.databricks.com/aws/en/agents/mcp-tools/managed-mcp)
- [agents/mcp-tools/connect-external](https://docs.databricks.com/aws/en/agents/mcp-tools/connect-external)
- …and 2 more

### The block on editing SCIM-provisioned RBAC groups through the API is now conditional — it applies only "while an organization in the tenant uses SCIM provisioning".

`additive` · restriction narrowed · 7 pages

Old: "Groups provisioned by an identity provider (source type `\"scim\"`) cannot be modified via the API." and "...cannot be deleted via the API." New text appends "while an organization in the tenant uses SCIM provisioning" to both.

- [api/admin/rbac_groups](https://platform.claude.com/docs/en/api/admin/rbac_groups)
- [api/admin/rbac_groups/delete](https://platform.claude.com/docs/en/api/admin/rbac_groups/delete)
- [api/admin/rbac_groups/update](https://platform.claude.com/docs/en/api/admin/rbac_groups/update)
- [api/admin/rbac_groups/members](https://platform.claude.com/docs/en/api/admin/rbac_groups/members)
- [api/admin/rbac_groups/members/create](https://platform.claude.com/docs/en/api/admin/rbac_groups/members/create)
- [api/admin/rbac_groups/members/delete](https://platform.claude.com/docs/en/api/admin/rbac_groups/members/delete)
- …and 1 more

### Serverless environment version 6 ships for both CPU and GPU, selectable as "Standard v6", and a new top-level `ray_init()` enables the Ray dashboard on GPU notebooks.

`additive` · new version · 7 pages

New release-notes pages for environment version 6 and GPU environment 6. machine-learning/ai-runtime/environment adds "choose **Standard v6**, **Standard v5**, or **Standard v4**". five-gpu documents "A new top-level `ray_init()` function (a drop-in for `ray.init()`) enables the Ray dashboard"; ai-runtime/ray notes "`ray_init()` requires environment version 5 or later."

- [release-notes/serverless/environment-version/six](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/six)
- [release-notes/serverless/environment-version/six-gpu](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/six-gpu)
- [release-notes/serverless/environment-version/](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/)
- [machine-learning/ai-runtime/environment](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/environment)
- [machine-learning/ai-runtime/examples/tutorials/sgc-xgboost](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-xgboost)
- [machine-learning/ai-runtime/ray](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/ray)
- …and 1 more

### Zerobus Ingest can now write to tables backed by default storage (Public Preview), and the previous blanket restriction has been dropped.

`additive` · preview stage · 6 pages

ingestion/zerobus-concepts previously read "Zerobus Ingest writes only to managed Delta tables. Writing to default storage is not supported." and now reads "Zerobus Ingest writes only to managed Delta tables." zerobus-release-stages adds the row "Ingesting into tables backed by default storage | Public Preview".

- [ingestion/zerobus-release-stages](https://docs.databricks.com/aws/en/ingestion/zerobus-release-stages)
- [ingestion/zerobus-concepts](https://docs.databricks.com/aws/en/ingestion/zerobus-concepts)
- [ingestion/zerobus-overview](https://docs.databricks.com/aws/en/ingestion/zerobus-overview)
- [ingestion/zerobus-arrow-flight](https://docs.databricks.com/aws/en/ingestion/zerobus-arrow-flight)
- [ingestion/zerobus-message-types](https://docs.databricks.com/aws/en/ingestion/zerobus-message-types)
- [ingestion/zerobus-ingest](https://docs.databricks.com/aws/en/ingestion/zerobus-ingest)

### Integrated CDC pipelines can now run in continuous (always-on) mode; triggered remains the default and a new page documents scale-optimized and speed-optimized run modes.

`additive` · new capability · 5 pages

mysql-integrated-pipeline previously said "Integrated CDC pipelines run on a schedule; continuous (always-on) execution is not supported." All three source pages now say "**Triggered by default.** By default, integrated CDC pipelines run in triggered mode; schedule them using a Lakeflow Jobs task" and link to the new ingestion/lakeflow-connect/continuous-integrated-cdc page.

- [ingestion/lakeflow-connect/continuous-integrated-cdc](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/continuous-integrated-cdc)
- [ingestion/lakeflow-connect/mysql-integrated-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/mysql-integrated-pipeline)
- [ingestion/lakeflow-connect/oracle-integrated-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/oracle-integrated-pipeline)
- [ingestion/lakeflow-connect/sql-server-integrated-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/sql-server-integrated-pipeline)
- [ingestion/lakeflow-connect/common-patterns](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/common-patterns)

### HubSpot CRM Hub ingestion is now in Beta and requires the `hubspot_connector_crm_objects` workspace preview; the connector was previously limited to Marketing Hub.

`additive` · beta feature · 5 pages

hubspot-limits previously read "The HubSpot connector only supports ingestion from HubSpot Marketing Hub. If you are interested in ingesting from other hubs, contact y[our account team]." The pages now say ingestion from HubSpot CRM Hub is in Beta and "requires the `hubspot_connector_crm_objects` workspace preview", and the pipeline example ingests both `marketing_emails` (Marketing Hub) and `contacts` (CRM Hub).

- [ingestion/lakeflow-connect/hubspot-limits](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-limits)
- [ingestion/lakeflow-connect/hubspot-overview](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-overview)
- [ingestion/lakeflow-connect/hubspot-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-pipeline)
- [ingestion/lakeflow-connect/hubspot-reference](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-reference)
- [ingestion/lakeflow-connect/hubspot-source-setup](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-source-setup)

### Databricks adds cross-workspace access (Beta) to control which source workspaces can reach a workspace over serverless traffic, configured on ingress and network policies.

`additive` · new feature · 5 pages

New page security/network/front-end/cross-workspace-access. context-based-ingress adds "**Cross-workspace access (Beta):** Controls which source workspaces can reach this workspace over serverless traffic" and notes that leaving the policy in compatibility mode means it does not govern cross-workspace ingress. network-policies documents listing specific workspaces as allowed egress destinations.

- [security/network/front-end/cross-workspace-access](https://docs.databricks.com/aws/en/security/network/front-end/cross-workspace-access)
- [security/network/front-end/context-based-ingress](https://docs.databricks.com/aws/en/security/network/front-end/context-based-ingress)
- [security/network/front-end/manage-ingress-policies](https://docs.databricks.com/aws/en/security/network/front-end/manage-ingress-policies)
- [security/network/serverless-network-security/](https://docs.databricks.com/aws/en/security/network/serverless-network-security/)
- [security/network/serverless-network-security/network-policies](https://docs.databricks.com/aws/en/security/network/serverless-network-security/network-policies)

### Unity Gateway Skills let you publish governed SKILL.md instruction files to a Unity Catalog schema and have agents download them or load them live over MCP.

`additive` · new feature · 5 pages

New pages cover the concept, publishing and sharing a skill, connecting a coding agent via the Unity Gateway CLI, and governing skills with grants and audit.

- [agents/uc-skills/](https://docs.databricks.com/aws/en/agents/uc-skills/)
- [agents/uc-skills/create-share-uc-skills](https://docs.databricks.com/aws/en/agents/uc-skills/create-share-uc-skills)
- [agents/uc-skills/use-uc-skills](https://docs.databricks.com/aws/en/agents/uc-skills/use-uc-skills)
- [ai-gateway/govern-skills](https://docs.databricks.com/aws/en/ai-gateway/govern-skills)
- [agent-skills/](https://docs.databricks.com/aws/en/agent-skills/)

### Git Folder Serverless (Beta) lets notebooks and files in a Git folder share one compute resource and an environment managed by `pyproject.toml`.

`additive` · new feature · 4 pages

New page compute/serverless/notebooks/git-folder-serverless, listed as "(Beta)" on the serverless index; dependencies and notebooks pages point multi-file authoring at it.

- [compute/serverless/notebooks/git-folder-serverless](https://docs.databricks.com/aws/en/compute/serverless/notebooks/git-folder-serverless)
- [compute/serverless/](https://docs.databricks.com/aws/en/compute/serverless/)
- [compute/serverless/notebooks](https://docs.databricks.com/aws/en/compute/serverless/notebooks)
- [compute/serverless/dependencies](https://docs.databricks.com/aws/en/compute/serverless/dependencies)

### New Okta-specific SCIM-to-automatic-identity-management migration guidance and a readiness report that finds external ID and group membership divergences between Databricks and your IdP.

`additive` · new guidance · 4 pages

Two new pages; migrate-to-aim reformats its prerequisites into bullets, including "**Identity federation enabled on at least one workspace**".

- [admin/users-groups/automatic-identity-management/migrate-to-aim-okta](https://docs.databricks.com/aws/en/admin/users-groups/automatic-identity-management/migrate-to-aim-okta)
- [admin/users-groups/automatic-identity-management/readiness-report](https://docs.databricks.com/aws/en/admin/users-groups/automatic-identity-management/readiness-report)
- [admin/users-groups/automatic-identity-management/](https://docs.databricks.com/aws/en/admin/users-groups/automatic-identity-management/)
- [admin/users-groups/automatic-identity-management/migrate-to-aim](https://docs.databricks.com/aws/en/admin/users-groups/automatic-identity-management/migrate-to-aim)

### New beta Admin endpoints for reading and updating organization compliance settings have been added to the API reference.

`additive` · new endpoints · 3 pages

Three new reference pages under api/beta/organization/compliance_settings (retrieve and update).

- [api/beta/organization/compliance_settings](https://platform.claude.com/docs/en/api/beta/organization/compliance_settings)
- [api/beta/organization/compliance_settings/retrieve](https://platform.claude.com/docs/en/api/beta/organization/compliance_settings/retrieve)
- [api/beta/organization/compliance_settings/update](https://platform.claude.com/docs/en/api/beta/organization/compliance_settings/update)

### Unity Catalog schemas can now be backed by an external secret manager (AWS Secrets Manager or Azure Key Vault) so secret values stay in your cloud account.

`additive` · new feature · 3 pages

Two new pages plus updated guidance on unity-catalog-secrets: "Instead of Databricks storing secret values, you can back a schema with an external secret manager so the values stay in your cloud secret m[anager]".

- [security/secrets/external-secrets](https://docs.databricks.com/aws/en/security/secrets/external-secrets)
- [security/secrets/configure-external-secrets](https://docs.databricks.com/aws/en/security/secrets/configure-external-secrets)
- [security/secrets/unity-catalog-secrets](https://docs.databricks.com/aws/en/security/secrets/unity-catalog-secrets)

### A new Agent SDK cookbook shows how to build a scheduled, read-only repository reviewer that resumes its session and returns schema-validated verdicts.

`additive` · new guide · 2 pages

New page listed on the cookbook index as "Build a scheduled repository reviewer" under the Claude Agent SDK category.

- [platform.claude.com/cookbook/claude-agent-sdk-scheduled-repository-reviewer-scheduled-repository-reviewer](https://platform.claude.com/cookbook/claude-agent-sdk-scheduled-repository-reviewer-scheduled-repository-reviewer)
- [platform.claude.com/cookbook/](https://platform.claude.com/cookbook/)

### You can now add, drop or rename columns and widen column types on a streaming table with `ALTER TABLE` as metadata-only changes, without a full refresh.

`additive` · new capability · 2 pages

New page ldp/streaming-table-schema-evolution; data-engineering/schema-evolution adds "you can add, drop, or rename columns and widen column types on a streaming table with `ALTER TABLE` as metadata-only changes" alongside the existing column-renaming behaviour note.

- [ldp/streaming-table-schema-evolution](https://docs.databricks.com/aws/en/ldp/streaming-table-schema-evolution)
- [data-engineering/schema-evolution](https://docs.databricks.com/aws/en/data-engineering/schema-evolution)

### The `clear_thinking_20251015` default table adds a "Fable and Mythos" row that keeps all prior thinking for every model in those families.

`additive` · default behaviour · 1 page

New row: "| Fable and Mythos | All models | (none) |", and the `keep` option description now reads "Fable and Mythos models: all turns." Previously the table listed only Opus, Sonnet and Haiku rows.

- [build-with-claude/context-editing](https://platform.claude.com/docs/en/build-with-claude/context-editing)

### Under the `thinking-binding-controls-2026-08-01` beta header, `message_start` now carries an `input_transformations` array, repeated in the final `message_delta` after a mid-stream server-side fallback.

`additive` · streaming shape · 1 page

Also added: with `display: "updates"` (beta), reasoning blocks stream like `display: "omitted"` and only the progress updates written between tool calls emit `thinking_delta` events. The `display: "omitted"` sentence itself is unchanged.

- [build-with-claude/streaming](https://platform.claude.com/docs/en/build-with-claude/streaming)

### The Message Batches unsupported-parameter list shrinks to `stream`, `speed` and `max_tokens: 0` — the Threads, routing-hint and research-preview rows are gone.

`additive` · parameter support · 1 page

Removed table rows: "`store` / `previous_thread_event_id` (Threads)", "`cache_hint` / `context_hint`" and "`research_preview_2026_02: \"active\"`". The FAQ previously read "(`stream`, `speed`, `store`, `previous_thread_event_id`, `cache_hint`, `context_hint`, `max_tokens: 0`, and `research_preview_2026_02`) are not supported" and now reads "(`stream`, `speed`, and `max_tokens: 0`) are not supported". Batch pricing rows for Claude Fable 5.1 and Claude Mythos 5.1 ($5/$25 per MTok) were also added.

- [build-with-claude/batch-processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing)

### Priority Tier's exclusion list grows to cover Claude Fable 5.1 and Claude Mythos 5.1 alongside Claude Mythos 5 and Claude Mythos Preview.

`additive` · availability · 1 page

Old: "Priority Tier is supported on all available Claude models except Claude Mythos 5, [Claude Mythos Preview...". New: "Priority Tier is supported on all available Claude models except Claude Fable 5.1, Claude Mythos 5.1, Claude Mythos 5, [Claude Mythos Preview...". Both new models are excluded from the start.

- [api/service-tiers](https://platform.claude.com/docs/en/api/service-tiers)

### The Outlook connector's `User.Read.All` / `Directory.Read.All` scopes are now only needed when discovering all mailboxes in the tenant, not in every setup.

`additive` · permission relaxed · 1 page

Old: "`User.Read.All` or `Directory.Read.All` — required to discover and list all mailboxes in the tenant." New: "...required only to discover and list all mailboxes in the tenant. If you set the `include_mailboxe[s]`..."

- [ingestion/lakeflow-connect/outlook-source-setup](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/outlook-source-setup)

## Editorial — 12

### Databricks renamed "Unity AI Gateway" to "Unity Gateway" throughout the docs, including preview toggle names such as "Enhanced Unity Gateway" and "Consumer access to Unity Gateway".

`editorial` · rename · 43 pages

Every occurrence of "Unity AI Gateway" in prose, headings, preview names and release notes becomes "Unity Gateway" — for example "An account admin must turn on the **Unity AI Gateway** beta features" becomes "...the **Unity Gateway** beta features", and release-notes/product/ retitles "Databricks-managed MCP connectors are now integrated with Unity AI Gateway (Beta)" to "...with Unity Gateway (Beta)". The product itself is unchanged.

- [ai-gateway/](https://docs.databricks.com/aws/en/ai-gateway/)
- [ai-gateway/agent-services](https://docs.databricks.com/aws/en/ai-gateway/agent-services)
- [ai-gateway/moderate-tutorial](https://docs.databricks.com/aws/en/ai-gateway/moderate-tutorial)
- [ai-gateway/govern-model-provider-services](https://docs.databricks.com/aws/en/ai-gateway/govern-model-provider-services)
- [ai-gateway/govern-model-services](https://docs.databricks.com/aws/en/ai-gateway/govern-model-services)
- [ai-gateway/govern-mcp-service](https://docs.databricks.com/aws/en/ai-gateway/govern-mcp-service)
- …and 37 more

### Admin API curl examples switch the bearer-token environment variable from `$ANTHROPIC_OAUTH_TOKEN` to `$ANTHROPIC_AUTH_TOKEN` across the whole Admin reference.

`editorial` · example update · 28 pages

Every affected example changes `-H "Authorization: Bearer $ANTHROPIC_OAUTH_TOKEN"` to `-H "Authorization: Bearer $ANTHROPIC_AUTH_TOKEN"`. Only the sample variable name changes; no endpoint or header semantics in these examples change. This covers roughly seventy Admin reference pages beyond those cited.

- [api/admin/api_keys](https://platform.claude.com/docs/en/api/admin/api_keys)
- [api/admin/api_keys/list](https://platform.claude.com/docs/en/api/admin/api_keys/list)
- [api/admin/api_keys/retrieve](https://platform.claude.com/docs/en/api/admin/api_keys/retrieve)
- [api/admin/api_keys/update](https://platform.claude.com/docs/en/api/admin/api_keys/update)
- [api/admin/cost_report](https://platform.claude.com/docs/en/api/admin/cost_report)
- [api/admin/cost_report/retrieve](https://platform.claude.com/docs/en/api/admin/cost_report/retrieve)
- …and 22 more

### A broad copy-edit pass fixes typos, malformed SQL examples and mislabelled code fences across the Databricks SQL and data-engineering reference.

`editorial` · copy edit · 28 pages

Examples: `[{'item':'c','count',4}` becomes `[{'item':'c','count':4}`; `cast(struct('hello')) AS STRUCT<...>).name)` becomes `cast(struct('hello') AS STRUCT<...>).name)`; curly quotes in `INTERVAL “1” DAY` become `INTERVAL '1' DAY`; "To prevent userse from creating" becomes "To prevent users from creating"; `cleanSourceMoveDestination` becomes `` `cleanSource.moveDestination` ``; a ```bash fence becomes ```json. No documented behaviour changes.

- [sql/language-manual/functions/approx_top_k](https://docs.databricks.com/aws/en/sql/language-manual/functions/approx_top_k)
- [sql/language-manual/data-types/struct-type](https://docs.databricks.com/aws/en/sql/language-manual/data-types/struct-type)
- [sql/language-manual/delta-merge-into](https://docs.databricks.com/aws/en/sql/language-manual/delta-merge-into)
- [sql/language-manual/functions/posexplode_outer](https://docs.databricks.com/aws/en/sql/language-manual/functions/posexplode_outer)
- [sql/language-manual/sql-ref-names](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-names)
- [sql/language-manual/functions/http_request](https://docs.databricks.com/aws/en/sql/language-manual/functions/http_request)
- …and 22 more

### "Databricks Data Intelligence Platform" is renamed "Databricks Data + AI Platform" (and "Lakehouse Platform" to "lakehouse platform") across conceptual and architecture pages.

`editorial` · rename · 24 pages

Example: "To get the most out of the Databricks Data Intelligence Platform, you must use Delta Lake as your storage framework" becomes "To get the most out of the Databricks Data + AI Platform...". Some pages render the token unsubstituted as "platform-name".

- [lakehouse-architecture/cost-optimization/best-practices](https://docs.databricks.com/aws/en/lakehouse-architecture/cost-optimization/best-practices)
- [lakehouse-architecture/interoperability-and-usability/best-practices](https://docs.databricks.com/aws/en/lakehouse-architecture/interoperability-and-usability/best-practices)
- [lakehouse-architecture/reference](https://docs.databricks.com/aws/en/lakehouse-architecture/reference)
- [lakehouse-architecture/](https://docs.databricks.com/aws/en/lakehouse-architecture/)
- [lakehouse-architecture/scope](https://docs.databricks.com/aws/en/lakehouse-architecture/scope)
- [lakehouse-architecture/data-governance/best-practices](https://docs.databricks.com/aws/en/lakehouse-architecture/data-governance/best-practices)
- …and 18 more

### The single "Use Genie Code" page was split into features-capabilities, agent-mode, navigate-genie-code, web-search and full-page, and links across the corpus were repointed.

`editorial` · restructure · 21 pages

For example, genie-code/sample-data-explorer changes "See [Use Genie Code](.../genie-code/use-genie-code)" to "See [Genie Code features and capabilities](.../genie-code/features-capabilities)", and machine-learning/ai-runtime/genie-code repoints requirements to .../genie-code/agent-mode#requirements. Genie Code also gains a documented web search capability that a workspace admin must enable from the Previews page.

- [genie-code/features-capabilities](https://docs.databricks.com/aws/en/genie-code/features-capabilities)
- [genie-code/agent-mode](https://docs.databricks.com/aws/en/genie-code/agent-mode)
- [genie-code/navigate-genie-code](https://docs.databricks.com/aws/en/genie-code/navigate-genie-code)
- [genie-code/web-search](https://docs.databricks.com/aws/en/genie-code/web-search)
- [genie-code/full-page](https://docs.databricks.com/aws/en/genie-code/full-page)
- [genie-code/use-genie-code](https://docs.databricks.com/aws/en/genie-code/use-genie-code)
- …and 15 more

### The API reference was regenerated: the beta-header enum grows from "38 more" to "41 more", model blurbs and field descriptions are re-rendered, and plain field names are wrapped in backticks.

`editorial` · bulk regeneration · 20 pages

Recurring mechanical edits include `- "message-batches-2024-09-24" or "prompt-caching-2024-07-31" or "computer-use-2024-10-22" or 38 more` becoming `...or 41 more`; model descriptions such as "Frontier intelligence for ambitious tasks across coding, scientific discovery, and enterprise workflows" reflowing between entries; and prose like "use include_archived instead" becoming "use `include_archived` instead". This accounts for the bulk of the roughly 200 changed api/beta/* pages.

- [api/beta](https://platform.claude.com/docs/en/api/beta)
- [api/beta/agents](https://platform.claude.com/docs/en/api/beta/agents)
- [api/beta/deployments](https://platform.claude.com/docs/en/api/beta/deployments)
- [api/beta/environments](https://platform.claude.com/docs/en/api/beta/environments)
- [api/beta/files](https://platform.claude.com/docs/en/api/beta/files)
- [api/beta/memory_stores](https://platform.claude.com/docs/en/api/beta/memory_stores)
- …and 14 more

### A house-style pass rewrites "For how X, see..." as "To learn how X, see..." across the Anthropic docs and repoints the Courses link to academy.claude.com.

`editorial` · copy edit · 19 pages

Example: "For how zero data retention (ZDR) applies to this feature, see API and data retention" becomes "To learn how zero data retention (ZDR) applies to this feature, see...". about-claude/additional-resources changes the Courses link from https://anthropic.skilljar.com/ to https://academy.claude.com/courses.

- [agents-and-tools/agent-skills/overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [agents-and-tools/tool-use/bash-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/bash-tool)
- [agents-and-tools/tool-use/fine-grained-tool-streaming](https://platform.claude.com/docs/en/agents-and-tools/tool-use/fine-grained-tool-streaming)
- [agents-and-tools/tool-use/memory-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)
- [agents-and-tools/tool-use/text-editor-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/text-editor-tool)
- [agents-and-tools/tool-use/overview](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)
- …and 13 more

### Cookbook notebooks bump their model from `claude-opus-4-1` to `claude-opus-4-8` throughout.

`editorial` · example update · 18 pages

`MODEL_NAME = "claude-opus-4-1"` becomes `MODEL_NAME = "claude-opus-4-8"`, and equivalents in `client.messages.create(model=...)` and `Anthropic(temperature=0.0, model=...)` calls. The MongoDB notebook also rewrites its prose from "Load the Anthropic Claude 3, specifically the ‘claude-opus-4-1’ model" to "Load Anthropic's Claude, specifically the `claude-opus-4-8` model".

- [platform.claude.com/cookbook/misc-building-evals](https://platform.claude.com/cookbook/misc-building-evals)
- [platform.claude.com/cookbook/misc-how-to-enable-json-mode](https://platform.claude.com/cookbook/misc-how-to-enable-json-mode)
- [platform.claude.com/cookbook/misc-how-to-make-sql-queries](https://platform.claude.com/cookbook/misc-how-to-make-sql-queries)
- [platform.claude.com/cookbook/multimodal-best-practices-for-vision](https://platform.claude.com/cookbook/multimodal-best-practices-for-vision)
- [platform.claude.com/cookbook/multimodal-getting-started-with-vision](https://platform.claude.com/cookbook/multimodal-getting-started-with-vision)
- [platform.claude.com/cookbook/multimodal-how-to-transcribe-text](https://platform.claude.com/cookbook/multimodal-how-to-transcribe-text)
- …and 12 more

### Cookbook install cells switch from the shell escape `!pip install` to the notebook magic `%pip install`.

`editorial` · example update · 8 pages

For example `!pip install -U anthropic voyageai pandas numpy matplotlib scikit-learn` becomes `%pip install -U ...`.

- [platform.claude.com/cookbook/capabilities-classification-guide](https://platform.claude.com/cookbook/capabilities-classification-guide)
- [platform.claude.com/cookbook/capabilities-contextual-embeddings-guide](https://platform.claude.com/cookbook/capabilities-contextual-embeddings-guide)
- [platform.claude.com/cookbook/capabilities-summarization-guide](https://platform.claude.com/cookbook/capabilities-summarization-guide)
- [platform.claude.com/cookbook/capabilities-retrieval-augmented-generation-guide](https://platform.claude.com/cookbook/capabilities-retrieval-augmented-generation-guide)
- [platform.claude.com/cookbook/finetuning-finetuning-on-bedrock](https://platform.claude.com/cookbook/finetuning-finetuning-on-bedrock)
- [platform.claude.com/cookbook/misc-sampling-past-max-tokens](https://platform.claude.com/cookbook/misc-sampling-past-max-tokens)
- …and 2 more

### Documented SDK and CLI versions move up: the Java SDK from 2.58.0 to 2.60.0 and the `ant` CLI installer from 1.27.0 to 1.30.0.

`editorial` · version bump · 4 pages

`implementation("com.anthropic:anthropic-java:2.58.0")` becomes 2.60.0 (and `anthropic-java-aws` likewise); `VERSION=1.27.0` becomes `VERSION=1.30.0`.

- [cli-sdks-libraries/sdks/java](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/java)
- [get-started](https://platform.claude.com/docs/en/get-started)
- [build-with-claude/claude-platform-on-aws](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws)
- [cli-sdks-libraries/cli/quickstart](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/quickstart)

### SQL examples switch the served model name from `databricks-llama-4-maverick` to `system.ai.llama-4-maverick`.

`editorial` · example update · 3 pages

Old: `'databricks-llama-4-maverick',` New: `'system.ai.llama-4-maverick',`

- [sql/language-manual/functions/ai_query](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_query)
- [sql/language-manual/functions/read_files](https://docs.databricks.com/aws/en/sql/language-manual/functions/read_files)
- [volumes/volume-files](https://docs.databricks.com/aws/en/volumes/volume-files)

### The Genie One desktop app download link moves from version 0.1.4 to 0.2.2.

`editorial` · version bump · 1 page

`Genie%20One-0.1.4-arm64.dmg` becomes `Genie%20One-0.2.2-arm64.dmg`.

- [genie-one/desktop](https://docs.databricks.com/aws/en/genie-one/desktop)
