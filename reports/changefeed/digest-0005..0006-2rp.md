# Change digest

> #5 (2026-09-09-before) → #6 (2026-09-09) · 1,072 changes · rendered 2026-09-19T19:00:59+00:00

## At a glance

63 findings — **7** breaking, **20** behavioural, **28** additive, **8** editorial — covering 612 of 1,072 changed pages. Anything not here is in the full feed report beside this file.

**If you read nothing else:**

1. MLflow tracing and evaluation examples now require `mlflow[databricks]>=3.14.0` (up from >=3.1) and store traces in Unity Catalog, which means setting `MLFLOW_TRACING_SQL_WAREHOUSE_ID` and configuring a SQL warehouse.
2. C# workload-identity-federation samples replace `new AnthropicOidcClient(credentials)` with `new AnthropicClient(new ClientOptions { Credentials = credentials })`.
3. The web fetch tool's allowed URL sources are narrowed: URLs that appear only in the system prompt are no longer fetchable, and results from code execution, the MCP connector and tool search are explicitly not allowed sources.
4. The TypeScript SDK now states TypeScript >= 5.0 is supported, raising the floor from 4.9.
5. Claude Fable 5 on Databricks now carries the added condition that customers who opt out of data retention cannot use it.
6. Change data feed now requires Databricks Runtime 19 or above, raised from Databricks Runtime 18 LTS or above.
7. Ingesting the affected Salesforce object now requires the `Query All Files` permission, which itself requires `View All Data`; previously only `View All Data` was stated.

---

## Breaking — 7

### MLflow tracing and evaluation examples now require `mlflow[databricks]>=3.14.0` (up from >=3.1) and store traces in Unity Catalog, which means setting `MLFLOW_TRACING_SQL_WAREHOUSE_ID` and configuring a SQL warehouse.

`breaking` · version floor · 39 pages

Quick-start cells now say they require MLflow 3.14 or later because they store traces in Unity Catalog, and the examples import `UnityCatalog` from `mlflow.entities.trace_location` instead of calling `mlflow.set_experiment`. label-existing-traces raises its stated minimum from 3.1.0 to 3.14.0, and the Claude Code integration's CLI tracing moves from MLflow 3.4+ to 3.14+. dev-tools/databricks-apps/mlflow adds that an MLflow experiment resource grants only workspace-level permissions and that UC trace tables must be added separately.

- [mlflow3/genai/tracing/integrations/](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/)
- [mlflow3/genai/tracing/integrations/anthropic](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/anthropic)
- [mlflow3/genai/tracing/integrations/openai](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/openai)
- [mlflow3/genai/tracing/integrations/bedrock](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/bedrock)
- [mlflow3/genai/tracing/integrations/langchain](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/langchain)
- [mlflow3/genai/tracing/integrations/langgraph](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/langgraph)
- …and 33 more

### C# workload-identity-federation samples replace `new AnthropicOidcClient(credentials)` with `new AnthropicClient(new ClientOptions { Credentials = credentials })`.

`breaking` · sdk api change · 7 pages

The AWS, GitHub Actions and Kubernetes samples also drop the `?? throw new InvalidOperationException("No federation credentials found in environment")` fallback and instead comment the environment variables the credentials are read from.

- [manage-claude/workload-identity-federation](https://platform.claude.com/docs/en/manage-claude/workload-identity-federation)
- [manage-claude/wif-providers/gcp](https://platform.claude.com/docs/en/manage-claude/wif-providers/gcp)
- [manage-claude/wif-providers/okta](https://platform.claude.com/docs/en/manage-claude/wif-providers/okta)
- [manage-claude/wif-providers/azure](https://platform.claude.com/docs/en/manage-claude/wif-providers/azure)
- [manage-claude/wif-providers/aws](https://platform.claude.com/docs/en/manage-claude/wif-providers/aws)
- [manage-claude/wif-providers/github-actions](https://platform.claude.com/docs/en/manage-claude/wif-providers/github-actions)
- …and 1 more

### The web fetch tool's allowed URL sources are narrowed: URLs that appear only in the system prompt are no longer fetchable, and results from code execution, the MCP connector and tool search are explicitly not allowed sources.

`breaking` · restriction · 1 page

The old text said Claude 'is not allowed to dynamically construct URLs' and could not fetch 'URLs from container-based server tools (such as Code Execution and Bash)'. The page now states the tool cannot fetch URLs that appear only in Claude's own output or only in the system prompt, and that results of other server-side tools — code execution, the MCP connector, tool search — are not an allowed source either. To make a system-prompt URL fetchable you must also include it in a user message. Client-side tool results remain allowed even when they echo text Claude produced.

- [agents-and-tools/tool-use/web-fetch-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-fetch-tool)

### The TypeScript SDK now states TypeScript >= 5.0 is supported, raising the floor from 4.9.

`breaking` · version floor · 1 page

- [cli-sdks-libraries/sdks/typescript](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/typescript)

### Claude Fable 5 on Databricks now carries the added condition that customers who opt out of data retention cannot use it.

`breaking` · restriction · 1 page

The 30-day trust-and-safety retention callout for Claude Fable 5 previously did not include the sentence 'Customers who opt out of data retention cannot use Claude Fable 5.' The same sentence appears on the newly added Claude Fable 5.1 entry.

- [machine-learning/foundation-model-apis/supported-models](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/supported-models)

### Change data feed now requires Databricks Runtime 19 or above, raised from Databricks Runtime 18 LTS or above.

`breaking` · version floor · 1 page

The other requirements (Unity Catalog registration, row tracking or Iceberg v3) are unchanged.

- [tables/features/change-data-feed](https://docs.databricks.com/aws/en/tables/features/change-data-feed)

### Ingesting the affected Salesforce object now requires the `Query All Files` permission, which itself requires `View All Data`; previously only `View All Data` was stated.

`breaking` · requirement change · 1 page

Read the page for which object the requirement attaches to before changing your Salesforce profile.

- [ingestion/lakeflow-connect/salesforce-limits](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/salesforce-limits)

## Behavioural — 20

### Federation and service-account admin endpoints now state they require an OAuth access token with the `org:admin` scope, obtained from `ant auth login --scope org:admin` or a workload identity federation rule, replacing the older 'OAuth bearer or Console session' wording.

`behavioural` · authentication · 32 pages

The previous text on these pages read variously 'Requires an OAuth bearer or Console session; Admin API keys are not accepted' or 'other scopes require a Console session'. The replacement is a single bolded requirement naming the `org:admin` scope and how to get it.

- [api/admin/federation_issuers](https://platform.claude.com/docs/en/api/admin/federation_issuers)
- [api/admin/federation_issuers/create](https://platform.claude.com/docs/en/api/admin/federation_issuers/create)
- [api/admin/federation_issuers/update](https://platform.claude.com/docs/en/api/admin/federation_issuers/update)
- [api/admin/federation_issuers/archive](https://platform.claude.com/docs/en/api/admin/federation_issuers/archive)
- [api/admin/federation_issuers/list](https://platform.claude.com/docs/en/api/admin/federation_issuers/list)
- [api/admin/federation_issuers/retrieve](https://platform.claude.com/docs/en/api/admin/federation_issuers/retrieve)
- …and 26 more

### Customer-managed key docs now state that on Claude Platform on AWS the KMS key must be a single-Region key in your own AWS account with no cross-account keys, and the IAM role ARN field is marked Deprecated.

`behavioural` · deprecation · 25 pages

The reference says Anthropic reaches the KMS key through its own intermediate role (or, on Claude Platform on AWS, with credentials from your account), so the role ARN is no longer needed. cmek-aws-kms adds troubleshooting for telling a source-ARN mismatch apart from an encryption-context mismatch by temporarily removing the `aws:SourceArn` condition.

- [api/admin/external_keys](https://platform.claude.com/docs/en/api/admin/external_keys)
- [api/admin/external_keys/create](https://platform.claude.com/docs/en/api/admin/external_keys/create)
- [api/admin/external_keys/update](https://platform.claude.com/docs/en/api/admin/external_keys/update)
- [api/admin/external_keys/list](https://platform.claude.com/docs/en/api/admin/external_keys/list)
- [api/admin/external_keys/retrieve](https://platform.claude.com/docs/en/api/admin/external_keys/retrieve)
- [api/admin/external_keys/delete](https://platform.claude.com/docs/en/api/admin/external_keys/delete)
- …and 19 more

### A new `ant apply` declarative workflow replaces the `ant beta:environments create < file.yaml` / `ant beta:agents create < file.yaml` form throughout the managed-agents docs.

`behavioural` · cli change · 13 pages

The new cli/apply page describes declaring agents, environments, skills, memory stores and deployments as files in your repository and syncing the API's resources to them. Every managed-agents walkthrough was rewritten to use it (for example `ant apply environment.yaml`). self-hosted-sandboxes also bumps its pinned `ANT_VERSION` from 1.27.0 to 1.29.0.

- [cli-sdks-libraries/cli/apply](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/apply)
- [managed-agents/self-hosted-sandboxes](https://platform.claude.com/docs/en/managed-agents/self-hosted-sandboxes)
- [managed-agents/environments](https://platform.claude.com/docs/en/managed-agents/environments)
- [managed-agents/quickstart](https://platform.claude.com/docs/en/managed-agents/quickstart)
- [managed-agents/agent-setup](https://platform.claude.com/docs/en/managed-agents/agent-setup)
- [managed-agents/permission-policies](https://platform.claude.com/docs/en/managed-agents/permission-policies)
- …and 7 more

### A new 'Preserved thinking' page defines when a replayed thinking block is still valid, and says that for accounts created on or after August 31, 2026 a request that replays an invalidated block is rejected unless you opt into `prefix_mismatch_behavior: "drop_block"`.

`behavioural` · thinking blocks · 12 pages

Preserved thinking lets a model use an earlier thinking block only if that model or an earlier one produced it and nothing before the block has changed; client-side edits to earlier turns (an edited, reordered or removed turn, an injected-then-removed reminder, a rebuilt history) invalidate the thinking blocks in every later assistant turn. context-editing adds that on Claude Fable 5.1 server-side context management never invalidates thinking blocks, and that the `clear_thinking_20251015` default for Fable and Mythos models is to keep all turns. computer-use-tool, prompt-caching, compaction, api/errors and thinking-troubleshooting were updated to point at the same rules.

- [build-with-claude/preserved-thinking](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking)
- [build-with-claude/thinking](https://platform.claude.com/docs/en/build-with-claude/thinking)
- [build-with-claude/thinking-troubleshooting](https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting)
- [build-with-claude/context-editing](https://platform.claude.com/docs/en/build-with-claude/context-editing)
- [build-with-claude/context-windows](https://platform.claude.com/docs/en/build-with-claude/context-windows)
- [build-with-claude/prompt-caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- …and 6 more

### Databricks Runtime 19 gets a September 1, 2026 release-notes section, DBR 13.3 LTS is marked end-of-support, and DBR 18 LTS documents an Apache Avro fast-reader bug that can exhaust executor memory.

`behavioural` · runtime lifecycle · 8 pages

The DBR 18 workaround is to turn off the fast reader with `-Dorg.apache.avro.fastread=false` in the JVM options for both driver and executors. DBR 16.4 LTS adds support for reading `.gzip`-extension files as gzip, with a warning to apply `PassthroughCodec` only to uncompressed `.gzip` files. DBR 19 also documents a feature requiring DBR 19 LTS or above with row tracking.

- [release-notes/runtime/19](https://docs.databricks.com/aws/en/release-notes/runtime/19)
- [release-notes/runtime/13.3lts](https://docs.databricks.com/aws/en/release-notes/runtime/13.3lts)
- [release-notes/runtime/13.3lts-ml](https://docs.databricks.com/aws/en/release-notes/runtime/13.3lts-ml)
- [release-notes/runtime/14.0](https://docs.databricks.com/aws/en/release-notes/runtime/14.0)
- [release-notes/product/2023/august](https://docs.databricks.com/aws/en/release-notes/product/2023/august)
- [release-notes/runtime/18](https://docs.databricks.com/aws/en/release-notes/runtime/18)
- …and 2 more

### The flat statement that SCIM-provisioned RBAC groups cannot be modified or deleted via the API is now conditional — it applies only while an organization is in a particular state.

`behavioural` · api behaviour · 6 pages

Old text: 'Groups provisioned by an identity provider (source type "scim") cannot be modified via the API.' New text adds a qualifying clause beginning 'while an organization in the …'. Read the page for the exact condition before relying on it.

- [api/admin/rbac_groups](https://platform.claude.com/docs/en/api/admin/rbac_groups)
- [api/admin/rbac_groups/update](https://platform.claude.com/docs/en/api/admin/rbac_groups/update)
- [api/admin/rbac_groups/delete](https://platform.claude.com/docs/en/api/admin/rbac_groups/delete)
- [api/admin/rbac_groups/members](https://platform.claude.com/docs/en/api/admin/rbac_groups/members)
- [api/admin/rbac_groups/members/create](https://platform.claude.com/docs/en/api/admin/rbac_groups/members/create)
- [api/admin/rbac_groups/members/delete](https://platform.claude.com/docs/en/api/admin/rbac_groups/members/delete)

### ABAC GRANT policies leave Beta, SQL `CREATE POLICY ... GRANT ... FOR <securable_type>` now works for all supported securable types rather than models only, and GRANT policies appear in `INFORMATION_SCHEMA.ABAC_POLICY_DEFINITIONS`.

`behavioural` · ga · 6 pages

The Beta callout and the '(Beta)' suffix are removed. Previously SQL creation was limited to models and you had to use Catalog Explorer or the REST API for model services, model provider services, MCP services and agent services. Two earlier limitations — 'INFORMATION_SCHEMA does not include GRANT policies' and 'System tags are available on models, but not yet on model services' — are gone. Creating, modifying or dropping a GRANT policy with SQL requires Databricks Runtime 18 LTS or above. `SHOW GRANTS` still does not return privileges granted by a GRANT policy.

- [data-governance/unity-catalog/abac/grant-policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/grant-policies)
- [data-governance/unity-catalog/abac/common-patterns](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/common-patterns)
- [data-governance/unity-catalog/abac/requirements](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/requirements)
- [release-notes/product/2026/june](https://docs.databricks.com/aws/en/release-notes/product/2026/june)
- [sql/language-manual/sql-ref-syntax-ddl-create-policy](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-ddl-create-policy)
- [ai-gateway/govern-access-to-models-with-grant-policies](https://docs.databricks.com/aws/en/ai-gateway/govern-access-to-models-with-grant-policies)

### ZDR wording for the Fable and Mythos families softens from a flat exclusion to 'not available … unless expressly authorized by Anthropic', and now covers the models as a family rather than naming Fable 5 and Mythos 5.

`behavioural` · data retention · 5 pages

The pages still state the models require 30-day data retention. build-with-claude/overview changes from 'Claude Fable 5, which is not available under ZDR' to 'the Claude Fable models, which are not available under ZDR'.

- [manage-claude/api-and-data-retention](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention)
- [models/fable-5/migration-guide](https://platform.claude.com/docs/en/models/fable-5/migration-guide)
- [about-claude/models/introducing-claude-fable-5-and-claude-mythos-5](https://platform.claude.com/docs/en/about-claude/models/introducing-claude-fable-5-and-claude-mythos-5)
- [models/fable-5/introducing-claude-fable-5-and-claude-mythos-5](https://platform.claude.com/docs/en/models/fable-5/introducing-claude-fable-5-and-claude-mythos-5)
- [build-with-claude/overview](https://platform.claude.com/docs/en/build-with-claude/overview)

### Feature Store now documents an enforced lower bound: `window_duration` must be greater than two days, with `RollingWindow` recommended for shorter windows, and `CustomUDF` applies only to `RequestSource` request-time features.

`behavioural` · new limit · 4 pages

`transformation_sql` now also requires a `dataframe_schema` giving the Spark `StructType` JSON of the projected output. Streams docs add that the run-as identity needs `READ` on the secret scope and the creator needs `USE CONNECTION`.

- [machine-learning/feature-store/feature-views-api-reference](https://docs.databricks.com/aws/en/machine-learning/feature-store/feature-views-api-reference)
- [machine-learning/feature-store/feature-views](https://docs.databricks.com/aws/en/machine-learning/feature-store/feature-views)
- [release-notes/feature-store/databricks-feature-store](https://docs.databricks.com/aws/en/release-notes/feature-store/databricks-feature-store)
- [machine-learning/feature-store/streams](https://docs.databricks.com/aws/en/machine-learning/feature-store/streams)

### Inference hooks docs now describe the circuit breaker's recovery probing: starting 10 minutes after a trip, Anthropic sends at most about one test request per minute, and rotating the signing secret or turning off Enforce verdicts stops the breaker resetting on its own.

`behavioural` · documented behaviour · 3 pages

The endpoint page previously only said sustained failures trip a breaker that stops enforcement. inference-hooks still states the feature is not available on Amazon Bedrock or Google Cloud.

- [manage-claude/inference-hooks-configuration](https://platform.claude.com/docs/en/manage-claude/inference-hooks-configuration)
- [manage-claude/inference-hooks-endpoint](https://platform.claude.com/docs/en/manage-claude/inference-hooks-endpoint)
- [manage-claude/inference-hooks](https://platform.claude.com/docs/en/manage-claude/inference-hooks)

### SQL AI-function examples now pass `system.ai.llama-4-maverick` instead of the `databricks-llama-4-maverick` endpoint name.

`behavioural` · endpoint rename · 3 pages

Affects `ai_query` examples on the function reference, in `read_files`, and in the volume-files walkthrough.

- [sql/language-manual/functions/ai_query](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_query)
- [sql/language-manual/functions/read_files](https://docs.databricks.com/aws/en/sql/language-manual/functions/read_files)
- [volumes/volume-files](https://docs.databricks.com/aws/en/volumes/volume-files)

### The Outlook connector's `User.Read.All`/`Directory.Read.All` scopes are now required only when discovering all mailboxes in the tenant, and the TikTok Ads connector's BASIC-reports-only limit is replaced by a cap on reports with 20,000 or more ads.

`behavioural` · requirement change · 2 pages

Outlook previously stated the scopes were 'required to discover and list all mailboxes'; they are now tied to leaving `include_mailboxes` unset. TikTok Ads previously said 'The connector only supports ingestion of BASIC reports'; it now supports reports with fewer than 20,000 ads, above which TikTok's synchronous report path is involved.

- [ingestion/lakeflow-connect/outlook-source-setup](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/outlook-source-setup)
- [ingestion/lakeflow-connect/tiktok-ads-limits](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/tiktok-ads-limits)

### Claude Fable 5.1, Mythos 5.1, Fable 5 and Mythos 5 are now all documented as sharing the tokenizer introduced with Claude Opus 4.7.

`behavioural` · tokenization · 1 page

The earlier wording said Fable 5 and Mythos 5 use that tokenizer and that it produces roughly 30 percent more tokens than other models; the replacement covers the 5.1 models as well and restates the effect in terms of a prompt rather than a flat percentage.

- [build-with-claude/token-counting](https://platform.claude.com/docs/en/build-with-claude/token-counting)

### The CMEK page now says structured outputs are unavailable for Claude Fable or Claude Mythos models in CMEK organizations, widening a note that previously named Claude Fable 5 specifically.

`behavioural` · restriction · 1 page

Old text: 'not available for Claude Fable 5 or Claude Mythos models in CMEK organizations'. New text drops the version, covering the whole Fable family.

- [manage-claude/cmek](https://platform.claude.com/docs/en/manage-claude/cmek)

### `Authorization: Bearer <token>` is now the documented primary auth header and accepts your API key directly; `x-api-key` is relabelled a 'legacy fallback … still supported' and marked not required.

`behavioural` · authentication · 1 page

Previously the table listed both headers as 'One of `x-api-key` or `Authorization`', and `Authorization` accepted only a short-lived WIF token. The SDK benefits list changes from 'Automatic header management (`x-api-key`, …)' to 'Automatic header management (authentication, …)'.

- [api/overview](https://platform.claude.com/docs/en/api/overview)

### The Anthropic C# SDK is no longer described as beta: both the 'currently in beta' info callout and the semantic-versioning beta warning are removed.

`behavioural` · ga · 1 page

The removed warning had said breaking changes may occur in minor or patch releases during the beta period. The page now says the package generally follows SemVer.

- [cli-sdks-libraries/sdks/csharp](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/csharp)

### Lakeflow pipeline unit testing no longer requires the PREVIEW channel; it now requires Databricks Runtime 18.1 or above, because earlier runtimes do not include the unit testing module.

`behavioural` · requirement change · 1 page

Step 1 drops the channel configuration entirely — the settings JSON is now just `"continuous": false` — and points at the pipeline event log for checking which runtime an update ran on. Triggered mode is still required and Spark Connect is still unsupported.

- [ldp/unit-testing](https://docs.databricks.com/aws/en/ldp/unit-testing)

### A job that runs continuously for more than 30 days loses access to files under `/Workspace`; restart it at least every 30 days, including jobs that use source from a remote Git repository.

`behavioural` · documented limit · 1 page

The page already documented 36-hour expiry for interactive compute and 30 days for jobs; the consequence for long-running jobs and the Git-source case are newly spelled out.

- [files/workspace](https://docs.databricks.com/aws/en/files/workspace)

### The deprecation of the `limit`, `offset`, `total_count` and `next_page` fields in `/api/2.1/clusters/events` moves from October 20, 2026 to November 30, 2026.

`behavioural` · deprecation · 1 page

- [compute/events-api-updates](https://docs.databricks.com/aws/en/compute/events-api-updates)

### If you set `delta.deletedFileRetentionDuration` to less than 7 days, predictive optimization still retains data files for a minimum of 7 days.

`behavioural` · documented behaviour · 1 page

- [optimizations/predictive-optimization](https://docs.databricks.com/aws/en/optimizations/predictive-optimization)

## Additive — 28

### Lakeflow Connect adds managed connectors for Anysphere Audit Logs (Cursor), Verkada and Glean, plus a OneDrive file-ingestion guide.

`additive` · new connectors · 28 pages

Each connector ships the full set of overview, connection, source-setup, pipeline, reference, limits, FAQ and troubleshooting pages, and is listed on the SaaS/file connector overviews and the connector FAQ index. The Glean connector is full-refresh only and does not support SCD Type 2.

- [ingestion/lakeflow-connect/anysphere-audit-logs](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs)
- [ingestion/lakeflow-connect/anysphere-audit-logs-connection](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-connection)
- [ingestion/lakeflow-connect/anysphere-audit-logs-faq](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-faq)
- [ingestion/lakeflow-connect/anysphere-audit-logs-limits](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-limits)
- [ingestion/lakeflow-connect/anysphere-audit-logs-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-pipeline)
- [ingestion/lakeflow-connect/anysphere-audit-logs-reference](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-audit-logs-reference)
- …and 22 more

### Claude Fable 5.1 (`claude-fable-5-1`) and Claude Mythos 5.1 ship, with overview, migration, what's-new, prompting and system-prompt pages, and Fable 5 is re-labelled Active (legacy).

`additive` · new model · 18 pages

New pages: models/fable-5-1/{overview,migration-guide,whats-new-fable-5-1}, models/mythos-5-1/overview, a Fable 5.1 prompting guide, and a Fable 5.1 system-prompt release-note page. Mythos 5.1 is the same model offered by invitation only through Project Glasswing. model-deprecations lists claude-fable-5-1 as Active with retirement not sooner than September 1, 2027. The Fable 5 overview status changes from 'Active (latest)' to 'Active (legacy)'. home/intro mark Fable 5.1 as New.

- [models/fable-5-1/overview](https://platform.claude.com/docs/en/models/fable-5-1/overview)
- [models/fable-5-1/migration-guide](https://platform.claude.com/docs/en/models/fable-5-1/migration-guide)
- [models/fable-5-1/whats-new-fable-5-1](https://platform.claude.com/docs/en/models/fable-5-1/whats-new-fable-5-1)
- [models/mythos-5-1/overview](https://platform.claude.com/docs/en/models/mythos-5-1/overview)
- [release-notes/system-prompts/claude-fable-5-1](https://platform.claude.com/docs/en/release-notes/system-prompts/claude-fable-5-1)
- [release-notes/system-prompts](https://platform.claude.com/docs/en/release-notes/system-prompts)
- …and 12 more

### New organization compliance-settings endpoints (retrieve/update) appear, and the Compliance API docs extend to remote session transcripts alongside chats, files and artifacts.

`additive` · api addition · 13 pages

compliance-sessions states the session endpoints are read-only — local and remote sessions cannot be deleted through the Compliance API — and compliance-integration-patterns extends legal-hold guidance from 'chat content' to 'chat content or remote session transcripts'. compliance-api now also documents the `x-api-key` header and required version header on every `/v1/compliance/*` endpoint.

- [api/beta/organization/compliance_settings](https://platform.claude.com/docs/en/api/beta/organization/compliance_settings)
- [api/beta/organization/compliance_settings/retrieve](https://platform.claude.com/docs/en/api/beta/organization/compliance_settings/retrieve)
- [api/beta/organization/compliance_settings/update](https://platform.claude.com/docs/en/api/beta/organization/compliance_settings/update)
- [manage-claude/compliance-sessions](https://platform.claude.com/docs/en/manage-claude/compliance-sessions)
- [manage-claude/compliance-integration-patterns](https://platform.claude.com/docs/en/manage-claude/compliance-integration-patterns)
- [manage-claude/compliance-content-data](https://platform.claude.com/docs/en/manage-claude/compliance-content-data)
- …and 7 more

### Unity Catalog gains ABAC DENY policies (Beta), which explicitly deny `MANAGE ACCESS CONTROL` on securables by governed tag and take precedence over grants.

`additive` · new feature · 13 pages

A new deny-policies page documents the feature; the ABAC index, core concepts, best practices, performance, policies and policy-evaluation pages were updated to distinguish DENY from row-filter/column-mask policies. privileges-reference notes `MANAGE ACCESS CONTROL` can be denied, and the hive_metastore `DENY` SQL statement now cross-links to ABAC DENY policies to avoid confusion.

- [data-governance/unity-catalog/abac/deny-policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/deny-policies)
- [data-governance/unity-catalog/abac/](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/)
- [data-governance/unity-catalog/abac/core-concepts](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/core-concepts)
- [data-governance/unity-catalog/abac/best-practices](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/best-practices)
- [data-governance/unity-catalog/abac/performance](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/performance)
- [data-governance/unity-catalog/abac/policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/policies)
- …and 7 more

### Databricks Foundation Model APIs add OpenAI GPT-6 Astra, Google Gemini 3.8 Flash, Zhipu GLM 5.3 and Anthropic Claude Fable 5.1, with endpoints `databricks-gpt-6-astra`, `databricks-gemini-3-8-flash`, `databricks-glm-5-3` and `databricks-claude-fable-5-1`.

`additive` · new models · 11 pages

Gemini 3.8 Flash is on a global endpoint and requires cross-geography routing to be enabled; it rejects `reasoning_effort: "minimal"`. GLM 5.3 always reasons, accepts `low`/`high`/`max`, silently maps other values to `max`, and rejects `none`. Claude Fable 5.1 accepts `low` through `max` and cannot disable reasoning. Rate limits, priority mode and acceptable-use tables were updated to match.

- [machine-learning/foundation-model-apis/supported-models](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/supported-models)
- [machine-learning/foundation-model-apis/limits](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/limits)
- [machine-learning/foundation-model-apis/priority-mode](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/priority-mode)
- [machine-learning/foundation-model-apis/compliance](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/compliance)
- [machine-learning/model-serving/acceptable-use-models](https://docs.databricks.com/aws/en/machine-learning/model-serving/acceptable-use-models)
- [machine-learning/model-serving/query-gemini-api](https://docs.databricks.com/aws/en/machine-learning/model-serving/query-gemini-api)
- …and 5 more

### Feature support lists add `claude-fable-5-1` and `claude-mythos-5-1`: structured outputs, the browser-use tool, refusal-retry guidance and the managed-agents model enum.

`additive` · model support · 10 pages

Structured outputs now lists `claude-fable-5-1` and `claude-mythos-5-1` ahead of the existing entries; browser-use adds `claude-fable-5-1` and `claude-mythos-5-1`; handling-stop-reasons adds Fable 5.1 to the models whose refusals can usually be served by retrying elsewhere; `BetaManagedAgentsModel` grows from '10 more' to '11 more' with `claude-fable-5-1` first.

- [build-with-claude/structured-outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)
- [agents-and-tools/tool-use/browser-use-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/browser-use-tool)
- [build-with-claude/handling-stop-reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons)
- [api/beta/agents/create](https://platform.claude.com/docs/en/api/beta/agents/create)
- [api/beta/agents/update](https://platform.claude.com/docs/en/api/beta/agents/update)
- [api/beta/sessions/create](https://platform.claude.com/docs/en/api/beta/sessions/create)
- …and 4 more

### Mid-conversation system messages are documented in beta on Claude Fable 5.1, Mythos 5.1 and Opus 5 behind a `mid-conversation-output-…` beta header, with a `display` option that keeps a system message in the array but hides it from the model.

`additive` · beta feature · 10 pages

Content blocks (`text`, `tool_addition`, `tool_removal`) must immediately follow a `user` turn, and a `system` message cannot be the first entry in `messages`. The hide-from-model `display` setting is only permitted on `role: "system"` messages. managed-agents/reference no longer lists the specific supported primary models and now only says an unsupported primary model rejects the event with `model_does_not_support_mid_conversation_system`.

- [build-with-claude/mid-conversation-system-messages](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages)
- [api/beta/messages](https://platform.claude.com/docs/en/api/beta/messages)
- [api/beta/messages/create](https://platform.claude.com/docs/en/api/beta/messages/create)
- [api/beta/messages/batches](https://platform.claude.com/docs/en/api/beta/messages/batches)
- [api/beta/messages/batches/create](https://platform.claude.com/docs/en/api/beta/messages/batches/create)
- [api/beta/messages/count_tokens](https://platform.claude.com/docs/en/api/beta/messages/count_tokens)
- …and 4 more

### Databricks adds built-in MCP Services — platform-managed tools with a built-in service policy and no server registration or OAuth app setup — and now recommends the `system.ai.dbsql` MCP Service over the older Databricks SQL MCP server.

`additive` · new feature · 10 pages

The AI Search, Genie Agent and Unity Catalog functions pages are retitled '… MCP server' to distinguish them from the new services.

- [agents/mcp-tools/built-in-mcp-services](https://docs.databricks.com/aws/en/agents/mcp-tools/built-in-mcp-services)
- [agents/mcp-tools/databricks-sql](https://docs.databricks.com/aws/en/agents/mcp-tools/databricks-sql)
- [agents/mcp-tools/mcp-services](https://docs.databricks.com/aws/en/agents/mcp-tools/mcp-services)
- [agents/mcp-tools/ai-search](https://docs.databricks.com/aws/en/agents/mcp-tools/ai-search)
- [agents/mcp-tools/genie-agent](https://docs.databricks.com/aws/en/agents/mcp-tools/genie-agent)
- [agents/mcp-tools/uc-functions](https://docs.databricks.com/aws/en/agents/mcp-tools/uc-functions)
- …and 4 more

### Two new SQL functions are documented: `ai_enrich` (Beta), which generates new columns per row, and `time_bucket`, which returns the start of a fixed-width time bucket for a timestamp.

`additive` · new functions · 10 pages

Both are added to the builtin function lists and cross-linked from related AI and date functions. The AI Functions overview page is also retitled from 'Enrich data using AI Functions' to 'Transform unstructured data using AI Functions', which repointed link text across the docs.

- [sql/language-manual/functions/ai_enrich](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_enrich)
- [sql/language-manual/functions/time_bucket](https://docs.databricks.com/aws/en/sql/language-manual/functions/time_bucket)
- [sql/language-manual/sql-ref-functions-builtin](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-functions-builtin)
- [sql/language-manual/sql-ref-functions-builtin-alpha](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-functions-builtin-alpha)
- [sql/language-manual/functions/ai_extract](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_extract)
- [sql/language-manual/functions/ai_parse_document](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_parse_document)
- …and 4 more

### Genie Ontology is introduced as a unified context layer combining Unity Catalog semantics with inferred context for Genie One and Genie Code, alongside Genie Agents and Genie One updates.

`additive` · new feature · 10 pages

Genie Agents file upload changes from 'CSV and Excel uploads are not available in Agent mode' to stating PDF uploads require Agent mode. The Genie Agents API 429 description broadens from a fixed five-requests-per-minute workspace limit to non-organic usage patterns or resource limitations. Genie One chat gains an admin-enabled web search preview, and the desktop app download moves from 0.1.4 to 0.2.2.

- [genie/genie-ontology](https://docs.databricks.com/aws/en/genie/genie-ontology)
- [genie-agents/concepts](https://docs.databricks.com/aws/en/genie-agents/concepts)
- [genie-agents/file-upload](https://docs.databricks.com/aws/en/genie-agents/file-upload)
- [genie-agents/api](https://docs.databricks.com/aws/en/genie-agents/api)
- [genie-agents/tune-quality](https://docs.databricks.com/aws/en/genie-agents/tune-quality)
- [genie-one/chat](https://docs.databricks.com/aws/en/genie-one/chat)
- …and 4 more

### Serverless environment version 6 ships, including a GPU variant, and Standard v6 is selectable as an AI Runtime base environment.

`additive` · new version · 8 pages

The Serverless GPU Python API adds a top-level `ray_init()` (drop-in for `ray.init()`) that enables the Ray dashboard; `ray_init()` requires environment version 5 or later. Environment version 5 notes that the Py4J gateway is off, replacing `dbutils.entry_point` and `dbutils.notebook.entry_point`.

- [release-notes/serverless/environment-version/six](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/six)
- [release-notes/serverless/environment-version/six-gpu](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/six-gpu)
- [release-notes/serverless/environment-version/](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/)
- [release-notes/serverless/environment-version/five-gpu](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/five-gpu)
- [release-notes/serverless/environment-version/five](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/five)
- [machine-learning/ai-runtime/environment](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/environment)
- …and 2 more

### Lakebase adds HIPAA support: new pages on HIPAA compliance, enabling it per project, and HIPAA audit logging, and Lakebase is available by default in compliance security profile workspaces without a separate enablement step.

`additive` · compliance · 7 pages

The Lakebase release notes previously said Lakebase 'is now available by default for workspaces with the compliance security profile'; the text now says you no longer need to enable Lakebase in those workspaces. security/privacy/hipaa adds an explicit step to enable the compliance security profile on every workspace that processes PHI.

- [oltp/projects/hipaa-compliance](https://docs.databricks.com/aws/en/oltp/projects/hipaa-compliance)
- [oltp/projects/enable-hipaa-compliance](https://docs.databricks.com/aws/en/oltp/projects/enable-hipaa-compliance)
- [oltp/projects/hipaa-audit-logging](https://docs.databricks.com/aws/en/oltp/projects/hipaa-audit-logging)
- [release-notes/lakebase/](https://docs.databricks.com/aws/en/release-notes/lakebase/)
- [oltp/projects/data-protection](https://docs.databricks.com/aws/en/oltp/projects/data-protection)
- [oltp/projects/private-link](https://docs.databricks.com/aws/en/oltp/projects/private-link)
- …and 1 more

### Zerobus Ingest can now write into tables backed by default storage (Public Preview), and the concepts page drops the statement that writing to default storage is not supported.

`additive` · preview promotion · 6 pages

The Arrow Flight ingestion page also drops its Beta callout.

- [ingestion/zerobus-release-stages](https://docs.databricks.com/aws/en/ingestion/zerobus-release-stages)
- [ingestion/zerobus-concepts](https://docs.databricks.com/aws/en/ingestion/zerobus-concepts)
- [ingestion/zerobus-overview](https://docs.databricks.com/aws/en/ingestion/zerobus-overview)
- [ingestion/zerobus-arrow-flight](https://docs.databricks.com/aws/en/ingestion/zerobus-arrow-flight)
- [ingestion/zerobus-message-types](https://docs.databricks.com/aws/en/ingestion/zerobus-message-types)
- [ingestion/zerobus-ingest](https://docs.databricks.com/aws/en/ingestion/zerobus-ingest)

### The HubSpot connector can now ingest CRM Hub objects in Beta, gated on the `hubspot_connector_crm_objects` workspace preview; it previously supported Marketing Hub only.

`additive` · beta feature · 5 pages

The old limit read 'The HubSpot connector only supports ingestion from HubSpot Marketing Hub.' Extra `auth.requiredScopes` entries are required when the preview is enabled.

- [ingestion/lakeflow-connect/hubspot-overview](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-overview)
- [ingestion/lakeflow-connect/hubspot-limits](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-limits)
- [ingestion/lakeflow-connect/hubspot-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-pipeline)
- [ingestion/lakeflow-connect/hubspot-reference](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-reference)
- [ingestion/lakeflow-connect/hubspot-source-setup](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/hubspot-source-setup)

### Integrated CDC pipelines can now run in continuous (always-on) mode, with a new page covering scale-optimized and speed-optimized run modes; triggered remains the default.

`additive` · new feature · 5 pages

The MySQL page previously said 'Integrated CDC pipelines run on a schedule; continuous (always-on) execution is not supported.' All three source pages now say pipelines are triggered by default and link to the continuous mode page.

- [ingestion/lakeflow-connect/continuous-integrated-cdc](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/continuous-integrated-cdc)
- [ingestion/lakeflow-connect/mysql-integrated-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/mysql-integrated-pipeline)
- [ingestion/lakeflow-connect/oracle-integrated-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/oracle-integrated-pipeline)
- [ingestion/lakeflow-connect/sql-server-integrated-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/sql-server-integrated-pipeline)
- [ingestion/lakeflow-connect/common-patterns](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/common-patterns)

### Cross-workspace access (Beta) lets you control which source workspaces can reach a workspace over serverless traffic, via ingress policy rules and matching network-policy egress destinations.

`additive` · new feature · 5 pages

An ingress policy can be left in compatibility mode, in which case it does not govern cross-workspace ingress and the workspace's pre-existing behaviour applies.

- [security/network/front-end/cross-workspace-access](https://docs.databricks.com/aws/en/security/network/front-end/cross-workspace-access)
- [security/network/front-end/context-based-ingress](https://docs.databricks.com/aws/en/security/network/front-end/context-based-ingress)
- [security/network/front-end/manage-ingress-policies](https://docs.databricks.com/aws/en/security/network/front-end/manage-ingress-policies)
- [security/network/serverless-network-security/network-policies](https://docs.databricks.com/aws/en/security/network/serverless-network-security/network-policies)
- [security/network/serverless-network-security/](https://docs.databricks.com/aws/en/security/network/serverless-network-security/)

### Unity Gateway Skills arrive: governed SKILL.md instruction files published to a Unity Catalog schema, shared under normal grants and audit, and consumed by agents over MCP or via the Unity Gateway CLI.

`additive` · new feature · 5 pages

ai-gateway/govern-skills covers enabling the feature, setting up a governed schema, and the create/write/read privileges.

- [agents/uc-skills/](https://docs.databricks.com/aws/en/agents/uc-skills/)
- [agents/uc-skills/create-share-uc-skills](https://docs.databricks.com/aws/en/agents/uc-skills/create-share-uc-skills)
- [agents/uc-skills/use-uc-skills](https://docs.databricks.com/aws/en/agents/uc-skills/use-uc-skills)
- [ai-gateway/govern-skills](https://docs.databricks.com/aws/en/ai-gateway/govern-skills)
- [agent-skills/](https://docs.databricks.com/aws/en/agent-skills/)

### A new page documents adding, dropping or renaming columns and widening column types on a streaming table with `ALTER TABLE` as metadata-only changes, without a full refresh or checkpoint reset.

`additive` · new feature · 5 pages

Separately, the dlt-meta metaprogramming guide is joined by an `sdp-meta` page and its onboarding files can now be written in JSON or YAML.

- [ldp/streaming-table-schema-evolution](https://docs.databricks.com/aws/en/ldp/streaming-table-schema-evolution)
- [data-engineering/schema-evolution](https://docs.databricks.com/aws/en/data-engineering/schema-evolution)
- [ldp/developer/sdp-meta](https://docs.databricks.com/aws/en/ldp/developer/sdp-meta)
- [ldp/developer/dlt-meta](https://docs.databricks.com/aws/en/ldp/developer/dlt-meta)
- [ldp/developer/](https://docs.databricks.com/aws/en/ldp/developer/)

### Automatic identity management adds an Okta migration guide and a readiness report that finds external ID and group membership divergences between Databricks and your identity provider.

`additive` · new guide · 4 pages

The general migration page reformats its prerequisites as a list, still requiring identity federation on at least one workspace.

- [admin/users-groups/automatic-identity-management/migrate-to-aim-okta](https://docs.databricks.com/aws/en/admin/users-groups/automatic-identity-management/migrate-to-aim-okta)
- [admin/users-groups/automatic-identity-management/readiness-report](https://docs.databricks.com/aws/en/admin/users-groups/automatic-identity-management/readiness-report)
- [admin/users-groups/automatic-identity-management/migrate-to-aim](https://docs.databricks.com/aws/en/admin/users-groups/automatic-identity-management/migrate-to-aim)
- [admin/users-groups/automatic-identity-management/](https://docs.databricks.com/aws/en/admin/users-groups/automatic-identity-management/)

### Git Folder Serverless (Beta) lets notebooks and files in a Git folder share one compute resource and an environment managed by `pyproject.toml`.

`additive` · beta feature · 4 pages

- [compute/serverless/notebooks/git-folder-serverless](https://docs.databricks.com/aws/en/compute/serverless/notebooks/git-folder-serverless)
- [compute/serverless/](https://docs.databricks.com/aws/en/compute/serverless/)
- [compute/serverless/notebooks](https://docs.databricks.com/aws/en/compute/serverless/notebooks)
- [compute/serverless/dependencies](https://docs.databricks.com/aws/en/compute/serverless/dependencies)

### Unity Catalog schemas can now be backed by an external secret manager — AWS Secrets Manager or Azure Key Vault — so secret values stay in your cloud while remaining governable in Unity Catalog.

`additive` · new feature · 3 pages

- [security/secrets/external-secrets](https://docs.databricks.com/aws/en/security/secrets/external-secrets)
- [security/secrets/configure-external-secrets](https://docs.databricks.com/aws/en/security/secrets/configure-external-secrets)
- [security/secrets/unity-catalog-secrets](https://docs.databricks.com/aws/en/security/secrets/unity-catalog-secrets)

### A new cookbook recipe builds a scheduled, read-only repository reviewer with the Claude Agent SDK that resumes its session and returns schema-validated verdicts.

`additive` · new guide · 2 pages

It is listed on the cookbook index under Claude Agent SDK, dated Aug 2026.

- [platform.claude.com/cookbook/claude-agent-sdk-scheduled-repository-reviewer-scheduled-repository-reviewer](https://platform.claude.com/cookbook/claude-agent-sdk-scheduled-repository-reviewer-scheduled-repository-reviewer)
- [platform.claude.com/cookbook/](https://platform.claude.com/cookbook/)

### Priority Tier does not support Claude Fable 5.1 or Claude Mythos 5.1, which join Mythos 5, Mythos Preview, Opus 5 and Sonnet 5 on the exclusion list.

`additive` · availability · 1 page

The supported-models line changes from 'all available Claude models except Claude Mythos 5, Claude Mythos Preview, Claude Opus 5, and Claude Sonnet 5' to the same list with Claude Fable 5.1 and Claude Mythos 5.1 added. Claude Fable 5 remains absent from the exclusion list.

- [api/service-tiers](https://platform.claude.com/docs/en/api/service-tiers)

### On Claude Fable 5.1 and Claude Mythos 5.1, `tool_choice` values `any` and `tool` return a 400 error; the primer tells you to leave `tool_choice` at `auto` and set `"strict": true` on the tool instead.

`additive` · model behaviour · 1 page

The primer also positions Fable 5.1 as the step up for the hardest long-running agentic and research tasks at 2x Claude Opus 5 pricing.

- [claude_api_primer](https://platform.claude.com/docs/en/claude_api_primer)

### Claude Fable 5.1 may issue fewer parallel tool calls than earlier models, most noticeably in long agent loops.

`additive` · model behaviour · 1 page

A new note warns about reduced parallelism; the page also restates that with `tool_choice` `any` or `tool`, `disable_parallel_tool_use: true` means exactly one tool call.

- [agents-and-tools/tool-use/parallel-tool-use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/parallel-tool-use)

### The top-level `effort` parameter is now available on all supported models with no beta header, while per-message effort is in beta behind the `mid-conversation-o…` beta header.

`additive` · beta feature · 1 page

The effort page was substantially rewritten around this split.

- [build-with-claude/effort](https://platform.claude.com/docs/en/build-with-claude/effort)

### The Batch API's unsupported-parameter list is now `stream`, `speed` and `max_tokens: 0`; `research_preview_2026_02` and the effort hint are no longer listed as unbatchable.

`additive` · api behaviour · 1 page

Old text listed '…hint`, `max_tokens: 0`, and `research_preview_2026_02`' among unsupported parameters.

- [build-with-claude/batch-processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing)

### Task budgets add Claude Fable 5.1 as a beta model behind the `task-budgets-2026-03-13` header, with guidance that pre-compaction tokens count as the usage of the messages you removed.

`additive` · beta feature · 1 page

- [build-with-claude/task-budgets](https://platform.claude.com/docs/en/build-with-claude/task-budgets)

## Editorial — 8

### Admin API curl samples across the reference now use `$ANTHROPIC_AUTH_TOKEN` instead of `$ANTHROPIC_OAUTH_TOKEN` in the `Authorization: Bearer` header.

`editorial` · docs sample change · 58 pages

A mechanical rename of the placeholder environment variable in the copy-paste examples; the header itself is unchanged.

- [api/admin/api_keys](https://platform.claude.com/docs/en/api/admin/api_keys)
- [api/admin/api_keys/list](https://platform.claude.com/docs/en/api/admin/api_keys/list)
- [api/admin/api_keys/retrieve](https://platform.claude.com/docs/en/api/admin/api_keys/retrieve)
- [api/admin/api_keys/update](https://platform.claude.com/docs/en/api/admin/api_keys/update)
- [api/admin/cost_report](https://platform.claude.com/docs/en/api/admin/cost_report)
- [api/admin/cost_report/retrieve](https://platform.claude.com/docs/en/api/admin/cost_report/retrieve)
- …and 52 more

### The API reference was regenerated: the anthropic-beta enum grows from '38 more' to '41 more' on every endpoint, model description strings are refreshed, and prose fields gain backticks around identifiers.

`editorial` · bulk regeneration · 51 pages

Hundreds of api/* pages changed only in these mechanical ways — enum counts, the 'Frontier intelligence for ambitious tasks…' model blurb, and formatting of names such as `deployment_id`, `include_archived`, `satisfied` and `needs_revision`. No endpoint or field semantics are stated to have changed on these pages.

- [api/beta](https://platform.claude.com/docs/en/api/beta)
- [api/beta/deployments](https://platform.claude.com/docs/en/api/beta/deployments)
- [api/beta/deployments/create](https://platform.claude.com/docs/en/api/beta/deployments/create)
- [api/beta/deployments/list](https://platform.claude.com/docs/en/api/beta/deployments/list)
- [api/beta/deployments/retrieve](https://platform.claude.com/docs/en/api/beta/deployments/retrieve)
- [api/beta/deployments/update](https://platform.claude.com/docs/en/api/beta/deployments/update)
- …and 45 more

### Databricks renames 'Unity AI Gateway' to 'Unity Gateway' across the docs, and the `ucode` CLI is now called the Unity Gateway CLI.

`editorial` · rename · 47 pages

A new release-notes/unity-gateway/ index appears. The rename touches product pages, release notes, governance, budgets and entitlement text; the underlying URLs stay under /ai-gateway/.

- [ai-gateway/](https://docs.databricks.com/aws/en/ai-gateway/)
- [ai-gateway/ai-governance](https://docs.databricks.com/aws/en/ai-gateway/ai-governance)
- [ai-gateway/agent-services](https://docs.databricks.com/aws/en/ai-gateway/agent-services)
- [ai-gateway/moderate-tutorial](https://docs.databricks.com/aws/en/ai-gateway/moderate-tutorial)
- [ai-gateway/govern-model-services](https://docs.databricks.com/aws/en/ai-gateway/govern-model-services)
- [ai-gateway/govern-model-provider-services](https://docs.databricks.com/aws/en/ai-gateway/govern-model-provider-services)
- …and 41 more

### 'Databricks Data Intelligence Platform' is renamed 'Databricks Data + AI Platform' throughout the docs.

`editorial` · rename · 27 pages

Some pages picked up an unrendered `platform-name` placeholder in the process (for example machine-learning/mlops/mlops-workflow and repos/repos-setup image alt text).

- [lakehouse-architecture/cost-optimization/best-practices](https://docs.databricks.com/aws/en/lakehouse-architecture/cost-optimization/best-practices)
- [lakehouse-architecture/interoperability-and-usability/best-practices](https://docs.databricks.com/aws/en/lakehouse-architecture/interoperability-and-usability/best-practices)
- [lakehouse-architecture/reference](https://docs.databricks.com/aws/en/lakehouse-architecture/reference)
- [lakehouse-architecture/](https://docs.databricks.com/aws/en/lakehouse-architecture/)
- [lakehouse-architecture/scope](https://docs.databricks.com/aws/en/lakehouse-architecture/scope)
- [lakehouse-architecture/data-governance/best-practices](https://docs.databricks.com/aws/en/lakehouse-architecture/data-governance/best-practices)
- …and 21 more

### The single 'Use Genie Code' page is split into new features-capabilities, agent-mode, navigate-genie-code, web-search and full-page pages, and dozens of links across the docs are repointed.

`editorial` · restructure · 25 pages

Genie Code web search is documented as a preview a workspace admin must turn on from the Previews page; agent mode gets its own requirements section that other pages now link to.

- [genie-code/features-capabilities](https://docs.databricks.com/aws/en/genie-code/features-capabilities)
- [genie-code/agent-mode](https://docs.databricks.com/aws/en/genie-code/agent-mode)
- [genie-code/navigate-genie-code](https://docs.databricks.com/aws/en/genie-code/navigate-genie-code)
- [genie-code/web-search](https://docs.databricks.com/aws/en/genie-code/web-search)
- [genie-code/full-page](https://docs.databricks.com/aws/en/genie-code/full-page)
- [genie-code/use-genie-code](https://docs.databricks.com/aws/en/genie-code/use-genie-code)
- …and 19 more

### Cookbook notebooks move their hard-coded model from `claude-opus-4-1` to `claude-opus-4-8`.

`editorial` · docs sample change · 18 pages

A mechanical `MODEL_NAME` / `model=` swap across misc, multimodal, tool-use and third-party recipes.

- [platform.claude.com/cookbook/misc-building-evals](https://platform.claude.com/cookbook/misc-building-evals)
- [platform.claude.com/cookbook/misc-how-to-enable-json-mode](https://platform.claude.com/cookbook/misc-how-to-enable-json-mode)
- [platform.claude.com/cookbook/misc-how-to-make-sql-queries](https://platform.claude.com/cookbook/misc-how-to-make-sql-queries)
- [platform.claude.com/cookbook/multimodal-best-practices-for-vision](https://platform.claude.com/cookbook/multimodal-best-practices-for-vision)
- [platform.claude.com/cookbook/multimodal-getting-started-with-vision](https://platform.claude.com/cookbook/multimodal-getting-started-with-vision)
- [platform.claude.com/cookbook/multimodal-how-to-transcribe-text](https://platform.claude.com/cookbook/multimodal-how-to-transcribe-text)
- …and 12 more

### Cookbook install cells switch from the shell escape `!pip install` to the notebook magic `%pip install`.

`editorial` · docs sample change · 8 pages

- [platform.claude.com/cookbook/capabilities-classification-guide](https://platform.claude.com/cookbook/capabilities-classification-guide)
- [platform.claude.com/cookbook/capabilities-contextual-embeddings-guide](https://platform.claude.com/cookbook/capabilities-contextual-embeddings-guide)
- [platform.claude.com/cookbook/capabilities-summarization-guide](https://platform.claude.com/cookbook/capabilities-summarization-guide)
- [platform.claude.com/cookbook/capabilities-retrieval-augmented-generation-guide](https://platform.claude.com/cookbook/capabilities-retrieval-augmented-generation-guide)
- [platform.claude.com/cookbook/finetuning-finetuning-on-bedrock](https://platform.claude.com/cookbook/finetuning-finetuning-on-bedrock)
- [platform.claude.com/cookbook/misc-sampling-past-max-tokens](https://platform.claude.com/cookbook/misc-sampling-past-max-tokens)
- …and 2 more

### Pinned dependency versions bump: the Java SDK (and anthropic-java-aws) to 2.60.0 from 2.58.0, and the `ant` CLI install snippet to 1.30.0 from 1.27.0.

`editorial` · version bump · 4 pages

- [cli-sdks-libraries/sdks/java](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/java)
- [get-started](https://platform.claude.com/docs/en/get-started)
- [build-with-claude/claude-platform-on-aws](https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws)
- [cli-sdks-libraries/cli/quickstart](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/quickstart)
