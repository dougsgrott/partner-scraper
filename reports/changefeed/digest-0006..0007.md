# Change digest

> #6 (2026-09-09) → #7 (2026-09-18) · 6,329 changes · rendered 2026-09-18T20:28:03+00:00

## At a glance

79 findings — **5** breaking, **31** behavioural, **33** additive, **10** editorial — covering 437 of 6,329 changed pages. Anything not here is in the full feed report beside this file.

**If you read nothing else:**

1. The Databricks AI v6 environment does not include Unsloth; the fine-tuning tutorials now install it explicitly, where AI v5 bundled it with its dependencies.
2. Connecting directly to a Lakehouse//RT warehouse from the Power BI service is no longer supported; the docs now tell you to connect through an on-premises data gateway.
3. From serverless compute environment version 6, the `/databricks/runtime/info.json` file is no longer available.
4. Starting September 19, 2026, Anthropic models are removed from Databricks on AWS GovCloud and AWS GovCloud DoD workspaces that have DoD IL5 enabled.
5. The partner-powered AI features setting is being removed on November 1, 2026; until then the page documents only how to enable it if currently disabled.

---

## Breaking — 5

### The Databricks AI v6 environment does not include Unsloth; the fine-tuning tutorials now install it explicitly, where AI v5 bundled it with its dependencies.

`breaking` · dependency removed · 2 pages

AI v5 shipped `unsloth`, `unsloth_zoo`, `bitsandbytes`, `trl`, `xformers`, `peft` and `einops`; notebooks that relied on those being present must install Unsloth before continuing.

- [machine-learning/ai-runtime/examples/tutorials/sgc-finetune-llama-unsloth](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-finetune-llama-unsloth)
- [machine-learning/ai-runtime/examples/tutorials/sgc-finetune-llama-unsloth-distributed](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-finetune-llama-unsloth-distributed)

### Connecting directly to a Lakehouse//RT warehouse from the Power BI service is no longer supported; the docs now tell you to connect through an on-premises data gateway.

`breaking` · capability removed · 2 pages

The page previously said you can connect to a Lakehouse//RT warehouse and linked the steps; the ADBC page notes the Power BI service connector fails against it.

- [partners/bi/power-bi/service](https://docs.databricks.com/aws/en/partners/bi/power-bi/service)
- [partners/bi/power-bi/adbc](https://docs.databricks.com/aws/en/partners/bi/power-bi/adbc)

### From serverless compute environment version 6, the `/databricks/runtime/info.json` file is no longer available.

`breaking` · removal · 1 page

Recorded as a dedicated section in the environment version 6 release notes.

- [release-notes/serverless/environment-version/six](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/six)

### Starting September 19, 2026, Anthropic models are removed from Databricks on AWS GovCloud and AWS GovCloud DoD workspaces that have DoD IL5 enabled.

`breaking` · availability removal · 1 page

Stated as a dated notice on the IL5 compliance page, which also lists serverless SQL warehouses at Public Preview.

- [security/privacy/il5](https://docs.databricks.com/aws/en/security/privacy/il5)

### The partner-powered AI features setting is being removed on November 1, 2026; until then the page documents only how to enable it if currently disabled.

`breaking` · removal · 1 page

For workspaces where the setting is enabled, the account and workspace toggles are affected.

- [databricks-ai/partner-powered](https://docs.databricks.com/aws/en/databricks-ai/partner-powered)

## Behavioural — 31

### The Databricks CLI reference no longer documents `--page-token` on a long list of `list` commands, and `workspace-bindings get-bindings` now shows `--limit` instead of `--max-results`.

`behavioural` · cli reference · 24 pages

The pagination-token option descriptions and the paginated example invocations were removed from these command pages in one sweep.

- [dev-tools/cli/reference/catalogs-commands](https://docs.databricks.com/aws/en/dev-tools/cli/reference/catalogs-commands)
- [dev-tools/cli/reference/schemas-commands](https://docs.databricks.com/aws/en/dev-tools/cli/reference/schemas-commands)
- [dev-tools/cli/reference/tables-commands](https://docs.databricks.com/aws/en/dev-tools/cli/reference/tables-commands)
- [dev-tools/cli/reference/connections-commands](https://docs.databricks.com/aws/en/dev-tools/cli/reference/connections-commands)
- [dev-tools/cli/reference/external-locations-commands](https://docs.databricks.com/aws/en/dev-tools/cli/reference/external-locations-commands)
- [dev-tools/cli/reference/functions-commands](https://docs.databricks.com/aws/en/dev-tools/cli/reference/functions-commands)
- …and 18 more

### Databricks Runtime 18.1 and 18.1 ML are now marked end-of-support ("(EoS)") alongside 13.3 LTS, and maintenance-update links for those versions repoint to the maintenance-updates archive page.

`behavioural` · end of support · 17 pages

Release-notes indexes, the Databricks Connect page and the Gov Cloud notes all pick up the renamed titles and archive anchors.

- [release-notes/runtime/18.1](https://docs.databricks.com/aws/en/release-notes/runtime/18.1)
- [release-notes/runtime/18.1ml](https://docs.databricks.com/aws/en/release-notes/runtime/18.1ml)
- [release-notes/runtime/13.3lts-ml](https://docs.databricks.com/aws/en/release-notes/runtime/13.3lts-ml)
- [release-notes/runtime/13.3lts](https://docs.databricks.com/aws/en/release-notes/runtime/13.3lts)
- [release-notes/runtime/18](https://docs.databricks.com/aws/en/release-notes/runtime/18)
- [release-notes/runtime/18.2](https://docs.databricks.com/aws/en/release-notes/runtime/18.2)
- …and 11 more

### AI Runtime tutorials now tell you to select the AI v6 environment instead of AI v5, and the Serverless GPU Python API included in the GPU environment moves from 0.5.24 to 0.5.25.

`behavioural` · environment upgrade · 13 pages

Some notebooks that previously installed their own libraries now rely on AI v6 pre-bundling them (for example `mlflow>=3` skinny, `nvidia-ml-py`, `threadpoolctl`, `torch`, `ultralytics`).

- [machine-learning/ai-runtime/examples/tutorials/sgc-distributed-pytorch-fsdp](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-distributed-pytorch-fsdp)
- [machine-learning/ai-runtime/examples/tutorials/sgc-sft-trl-deepspeed-llama-1b](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-sft-trl-deepspeed-llama-1b)
- [machine-learning/ai-runtime/examples/tutorials/sgc-recommender-system-lightning](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-recommender-system-lightning)
- [machine-learning/ai-runtime/examples/tutorials/sgc-api-h100-starter](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-api-h100-starter)
- [machine-learning/ai-runtime/examples/tutorials/sgc-distributed-gpt-oss-20b](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-distributed-gpt-oss-20b)
- [machine-learning/ai-runtime/examples/tutorials/sgc-finetune-qwen3-4b](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-finetune-qwen3-4b)
- …and 7 more

### Sharing and reading foreign schemas, foreign tables and foreign Iceberg tables with OpenSharing is now generally available.

`behavioural` · GA · 5 pages

The create-share page drops its Beta banner and adds guidance that foreign Iceberg tables shared with open recipients not using Iceberg clients must use default storage.

- [release-notes/product/](https://docs.databricks.com/aws/en/release-notes/product/)
- [release-notes/product/2026/september](https://docs.databricks.com/aws/en/release-notes/product/2026/september)
- [opensharing/create-share](https://docs.databricks.com/aws/en/opensharing/create-share)
- [opensharing/](https://docs.databricks.com/aws/en/opensharing/)
- [data-governance/unity-catalog/abac/opensharing](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/opensharing)

### Automatic change data feed is generally available in Databricks Runtime 19 and is rolling out to all supported regions, and the Lakebase sync pages no longer label it Public Preview.

`behavioural` · GA · 5 pages

Auto CDF computes row-level changes at query time and uses the same `table_changes()` and `readChangeFeed` APIs as the legacy change data feed.

- [release-notes/runtime/19](https://docs.databricks.com/aws/en/release-notes/runtime/19)
- [release-notes/whats-coming](https://docs.databricks.com/aws/en/release-notes/whats-coming)
- [tables/features/change-data-feed](https://docs.databricks.com/aws/en/tables/features/change-data-feed)
- [oltp/instances/sync-data/sync-table](https://docs.databricks.com/aws/en/oltp/instances/sync-data/sync-table)
- [oltp/projects/sync-tables](https://docs.databricks.com/aws/en/oltp/projects/sync-tables)

### The top-level `workspace_id` on API key objects is marked deprecated in favour of `scope`, which reports the real workspace ID even for the default workspace.

`behavioural` · deprecation · 4 pages

The API key schema now documents `scope: BetaAPIKeyOrganizationScope or BetaAPIKeyWorkspaceScope` and notes that the deprecated `workspace_id` is `null` when the key belongs to the default workspace.

- [api/admin/api_keys](https://platform.claude.com/docs/en/api/admin/api_keys)
- [api/admin/api_keys/list](https://platform.claude.com/docs/en/api/admin/api_keys/list)
- [api/admin/api_keys/retrieve](https://platform.claude.com/docs/en/api/admin/api_keys/retrieve)
- [api/admin/api_keys/update](https://platform.claude.com/docs/en/api/admin/api_keys/update)

### Go examples for the Files API now pass an options struct — `Files.Download(ctx, fileID, anthropic.FileDownloadParams{})` and `Files.GetMetadata(ctx, fileID, anthropic.FileGetMetadataParams{})`.

`behavioural` · sdk signature · 4 pages

The previous examples called `Files.Download(ctx, fileID)` with no params argument.

- [agents-and-tools/agent-skills/quickstart](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/quickstart)
- [build-with-claude/files](https://platform.claude.com/docs/en/build-with-claude/files)
- [build-with-claude/skills-guide](https://platform.claude.com/docs/en/build-with-claude/skills-guide)
- [agents-and-tools/tool-use/code-execution-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool)

### The `FILE` type now requires serverless environment version 6 or above, and UDFs registered in Unity Catalog can read a FILE's metadata but not its contents and cannot create files.

`behavioural` · requirement change · 4 pages

The earlier note said the FILE type wasn't supported on serverless notebooks and was supported on notebooks attached to serverless SQL warehouses; that framing is replaced by the environment-version requirement. The UDF limitation is now stated on the file-type, PySpark and file-UDF pages.

- [sql/language-manual/data-types/file-type](https://docs.databricks.com/aws/en/sql/language-manual/data-types/file-type)
- [pyspark/reference/file-type](https://docs.databricks.com/aws/en/pyspark/reference/file-type)
- [unstructured/file-udfs](https://docs.databricks.com/aws/en/unstructured/file-udfs)
- [udf/python](https://docs.databricks.com/aws/en/udf/python)

### The SharePoint connector docs now list Microsoft 365 national cloud deployments as unsupported and state that ingesting SharePoint list attachments is not supported.

`behavioural` · restriction · 4 pages

The prerequisite to enable the Excel Beta feature for parsing Excel files was removed from the SharePoint prerequisites at the same time; the connector remains in Beta with workspace-admin access control.

- [ingestion/sharepoint](https://docs.databricks.com/aws/en/ingestion/sharepoint)
- [ingestion/lakeflow-connect/sharepoint-limits](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/sharepoint-limits)
- [ingestion/lakeflow-connect/sharepoint-reference](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/sharepoint-reference)
- [ingestion/lakeflow-connect/sharepoint](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/sharepoint)

### Private Link Beta features now name the workspace preview you must enable: "Context-Based Ingress: Workspace Private Access Policies" for private workspace access, and "Front-end Private Link for Custom URLs and Account" for account-level private access.

`behavioural` · preview enablement · 4 pages

The earlier notes announced the Beta without naming an enablement toggle.

- [security/network/classic/privatelink-dns](https://docs.databricks.com/aws/en/security/network/classic/privatelink-dns)
- [security/network/front-end/front-end-private-connect-account](https://docs.databricks.com/aws/en/security/network/front-end/front-end-private-connect-account)
- [security/network/front-end/front-end-private-connect](https://docs.databricks.com/aws/en/security/network/front-end/front-end-private-connect)
- [security/network/front-end/service-direct-privatelink](https://docs.databricks.com/aws/en/security/network/front-end/service-direct-privatelink)

### File upload docs now state that only the final path component of a part's `filename` is kept, and that an absent or empty `filename` is replaced with `unnamed`.

`behavioural` · api behaviour · 3 pages

Previously the upload parameter description did not describe this normalisation.

- [api/files/upload](https://platform.claude.com/docs/en/api/files/upload)
- [api/beta/files](https://platform.claude.com/docs/en/api/beta/files)
- [api/beta/files/upload](https://platform.claude.com/docs/en/api/beta/files/upload)

### Writing to liquid clustered tables with Zerobus is now generally available; the Beta labels were removed from the quota, feature and release-stage pages.

`behavioural` · GA · 3 pages

Liquid clustering remains the recommended layout for Zerobus ingestion.

- [ingestion/zerobus-quotas](https://docs.databricks.com/aws/en/ingestion/zerobus-quotas)
- [ingestion/zerobus-features](https://docs.databricks.com/aws/en/ingestion/zerobus-features)
- [ingestion/zerobus-release-stages](https://docs.databricks.com/aws/en/ingestion/zerobus-release-stages)

### You can now drop a Unity Catalog managed base table that still has live shallow clones — the clones keep reading — and `DROP TABLE` gains a `FORCE` option for managed tables with dependent shallow clones.

`behavioural` · semantics change · 3 pages

The clone page previously said dropping the source table breaks shallow-clone targets for managed tables. The DROP TABLE reference states FORCE is required only in certain workspace configurations and adds an UNDROP TABLE cross-reference.

- [tables/operations/drop-table](https://docs.databricks.com/aws/en/tables/operations/drop-table)
- [sql/language-manual/sql-ref-syntax-ddl-drop-table](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-ddl-drop-table)
- [tables/operations/clone-unity-catalog](https://docs.databricks.com/aws/en/tables/operations/clone-unity-catalog)

### Lakebase docs now state that scale to zero is available only for computes of 32 CU or smaller, and for an autoscaling compute the maximum size must be 32 CU or smaller.

`behavioural` · restriction · 3 pages

The autoscaling page adds that if you set a maximum larger than 32 CU you can't enable scale to zero.

- [oltp/projects/manage-computes](https://docs.databricks.com/aws/en/oltp/projects/manage-computes)
- [oltp/projects/autoscaling](https://docs.databricks.com/aws/en/oltp/projects/autoscaling)
- [oltp/projects/scale-to-zero](https://docs.databricks.com/aws/en/oltp/projects/scale-to-zero)

### Automatic Git deployments for Databricks Apps are no longer labelled Beta.

`behavioural` · preview stage · 3 pages

The Beta banner and inline Beta qualifiers were removed from the deploy, get-started and GitHub Actions pages.

- [dev-tools/databricks-apps/cicd-github-actions](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/cicd-github-actions)
- [dev-tools/databricks-apps/get-started](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/get-started)
- [dev-tools/databricks-apps/deploy](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/deploy)

### Materializing features to an online store now requires `CAN USE` on the Lakebase instance or project backing that store.

`behavioural` · permission requirement · 3 pages

Related updates: Kinesis stream authentication goes through a Unity Catalog connection of type `KINESIS` referencing a service credential, and a backfill table must include a UTC `stream_record_timestamp` column.

- [machine-learning/feature-store/materialized-features](https://docs.databricks.com/aws/en/machine-learning/feature-store/materialized-features)
- [machine-learning/feature-store/feature-views-api-reference](https://docs.databricks.com/aws/en/machine-learning/feature-store/feature-views-api-reference)
- [machine-learning/feature-store/streams](https://docs.databricks.com/aws/en/machine-learning/feature-store/streams)

### On dedicated compute, workloads that access Unity Catalog data must use a supported thread pool from `org.apache.spark.util.ThreadUtils`; ForkJoinPool, Scala parallel collections (`.par`) and `ThreadUtils.newForkJoinPool` are listed as unsupported.

`behavioural` · restriction · 2 pages

The earlier wording only said standard Scala thread pools are not supported and to use the special ThreadUtils pools; the JAR task page now enumerates the unsupported options explicitly.

- [data-governance/unity-catalog/requirements](https://docs.databricks.com/aws/en/data-governance/unity-catalog/requirements)
- [jobs/tasks/jar-create](https://docs.databricks.com/aws/en/jobs/tasks/jar-create)

### Lakeflow pipelines docs now state that `create_table` and `CREATE TABLE ... FLOW` cannot adopt an existing managed table — the target must be a new managed table.

`behavioural` · restriction · 2 pages

Added as a limitation bullet on both the Python and SQL references.

- [ldp/developer/ldp-python-ref-create-table](https://docs.databricks.com/aws/en/ldp/developer/ldp-python-ref-create-table)
- [ldp/developer/ldp-sql-ref-create-table-flow](https://docs.databricks.com/aws/en/ldp/developer/ldp-sql-ref-create-table-flow)

### Databricks Apps is now turned on by default for workspaces with the compliance security profile enabled, in all regions where the selected standard is available.

`behavioural` · default change · 2 pages

The earlier text said a workspace admin had to enable Apps for use with the compliance security profile.

- [dev-tools/databricks-apps/](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/)
- [security/privacy/security-profile](https://docs.databricks.com/aws/en/security/privacy/security-profile)

### To use a catalog backed by default storage for AI Gateway inference tables or the unified trace table, a workspace admin must enable the "Zerobus Ingest Default Storage" preview.

`behavioural` · enablement requirement · 2 pages

The inference tables page previously described only the `CREATE TABLE` privilege on an external storage catalog.

- [ai-gateway/inference-tables](https://docs.databricks.com/aws/en/ai-gateway/inference-tables)
- [ai-gateway/unified-trace-table](https://docs.databricks.com/aws/en/ai-gateway/unified-trace-table)

### The Jira and ServiceNow connectors do not reingest records that were deleted in the source and later restored.

`behavioural` · limitation · 2 pages

Added as a "Restored records" limitation section on both connectors.

- [ingestion/lakeflow-connect/jira-limits](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/jira-limits)
- [ingestion/lakeflow-connect/servicenow-limits](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/servicenow-limits)

### Spark JAR tasks are not supported on classic compute that uses the Environments dependency mode, and dependencies for supported tasks on such compute are managed with job environments rather than cluster libraries.

`behavioural` · restriction · 2 pages

The earlier environments-mode note said `%scala` code is not supported and will fail; the jobs compute page previously said only that libraries cannot be declared in a shared job cluster configuration.

- [jobs/compute](https://docs.databricks.com/aws/en/jobs/compute)
- [compute/environments-mode](https://docs.databricks.com/aws/en/compute/environments-mode)

### The minimum accepted `task_budget.total` is now stated as 20,000 tokens on every model that supports task budgets, replacing the previous "model-specific" wording.

`behavioural` · documented limit · 1 page

Readers who previously had to look up a per-model floor now have a single documented number.

- [build-with-claude/task-budgets](https://platform.claude.com/docs/en/build-with-claude/task-budgets)

### The thinking guide now states that Claude Mythos Preview accepts `max_tokens` up to 128K and that the Batches beta ceiling is not available for it.

`behavioural` · model limit · 1 page

A model/limit table was replaced by prose describing the Mythos Preview ceilings.

- [build-with-claude/thinking](https://platform.claude.com/docs/en/build-with-claude/thinking)

### Token counting now documents that it returns an `invalid_request_error` for a few inputs the Messages API accepts, including server tools.

`behavioural` · api behaviour · 1 page

The page previously framed this as a support note ("supports client tools and the advisor tool") rather than naming the error.

- [build-with-claude/token-counting](https://platform.claude.com/docs/en/build-with-claude/token-counting)

### Kimi K2.7 now has a published pay-per-token retirement date of October 30, 2026, with Kimi K3 named as the replacement.

`behavioural` · deprecation · 1 page

Listed in the retired models policy table.

- [machine-learning/retired-models-policy](https://docs.databricks.com/aws/en/machine-learning/retired-models-policy)

### Scheduling notebook jobs moves from Beta to Public Preview, and the note that workspace admins control access was dropped.

`behavioural` · preview stage · 1 page

The page now carries only the Public Preview banner.

- [notebooks/schedule-notebook-jobs](https://docs.databricks.com/aws/en/notebooks/schedule-notebook-jobs)

### Creating, modifying or dropping an ABAC GRANT policy or DENY policy (Beta) with SQL requires Databricks Runtime 18 LTS or above.

`behavioural` · version floor · 1 page

Stated in the CREATE POLICY reference alongside the SQL warehouse requirement.

- [sql/language-manual/sql-ref-syntax-ddl-create-policy](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-ddl-create-policy)

### Deleting a workspace now removes that workspace's audit events older than 14 days from `system.access.audit`.

`behavioural` · retention · 1 page

Added to the audit log system table page.

- [admin/system-tables/audit-logs](https://docs.databricks.com/aws/en/admin/system-tables/audit-logs)

### Unity Catalog data classification does not apply classification tags to view columns by default — views are classified but their columns are not tagged.

`behavioural` · restriction · 1 page

The page also carries a Beta banner requiring a workspace admin to turn the feature on.

- [data-governance/unity-catalog/data-classification](https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-classification)

### Clean room creation now describes a "central clean room" — an isolated Databricks-managed serverless environment you choose — whose cloud provider must match your workspace though the region can differ.

`behavioural` · requirement · 1 page

The page frames this as a data residency decision.

- [clean-rooms/create-clean-room](https://docs.databricks.com/aws/en/clean-rooms/create-clean-room)

## Additive — 33

### A large set of Admin API surfaces (analytics, RBAC groups and roles, spend limits, MCP tunnels, cost and usage reports) is now also documented under `api/beta/organization/*`.

`additive` · docs coverage · 22 pages

These pages are new in this run and mirror the existing `api/admin/*` reference sections.

- [api/beta/organization/analytics](https://platform.claude.com/docs/en/api/beta/organization/analytics)
- [api/beta/organization/analytics/usage](https://platform.claude.com/docs/en/api/beta/organization/analytics/usage)
- [api/beta/organization/analytics/usage/list](https://platform.claude.com/docs/en/api/beta/organization/analytics/usage/list)
- [api/beta/organization/analytics/cost](https://platform.claude.com/docs/en/api/beta/organization/analytics/cost)
- [api/beta/organization/analytics/users](https://platform.claude.com/docs/en/api/beta/organization/analytics/users)
- [api/beta/organization/analytics/connectors](https://platform.claude.com/docs/en/api/beta/organization/analytics/connectors)
- …and 16 more

### The Files, Skills and Message Batches endpoints now document an optional `anthropic-workspace-id` header.

`additive` · api reference · 20 pages

A Headers section listing `"anthropic-workspace-id": optional string` was added to each of these endpoint pages.

- [api/files](https://platform.claude.com/docs/en/api/files)
- [api/files/delete](https://platform.claude.com/docs/en/api/files/delete)
- [api/files/download](https://platform.claude.com/docs/en/api/files/download)
- [api/files/list](https://platform.claude.com/docs/en/api/files/list)
- [api/files/retrieve_metadata](https://platform.claude.com/docs/en/api/files/retrieve_metadata)
- [api/files/upload](https://platform.claude.com/docs/en/api/files/upload)
- …and 14 more

### Five new managed Lakeflow Connect connectors are documented: Anaplan, Anysphere Organization, Atlassian Audit Logs, Celigo and Google Workspace, each with a full overview/connection/pipeline/reference/limits/FAQ set.

`additive` · new connectors · 12 pages

Google Workspace ingests activity events from 33 application audit logs; Atlassian covers organization audit log events; Celigo covers integrator.io audit log events; Anaplan covers audit trail events and user account records.

- [ingestion/lakeflow-connect/anaplan](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anaplan)
- [ingestion/lakeflow-connect/anysphere-organization](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-organization)
- [ingestion/lakeflow-connect/atlassian-audit-logs](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/atlassian-audit-logs)
- [ingestion/lakeflow-connect/celigo](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/celigo)
- [ingestion/lakeflow-connect/google-workspace](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/google-workspace)
- [ingestion/lakeflow-connect/anaplan-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anaplan-pipeline)
- …and 6 more

### DeepSeek V4.1 Flash and Grok 4.6 now appear across the Databricks Foundation Model API docs, including region availability (`databricks-grok-4-6` in us-west-2), rate limits, function calling, vision and reasoning-effort support.

`additive` · model availability · 10 pages

`supported-models` gains a DeepSeek V4.1 Flash section describing a multimodal mixture-of-experts model with 552 billion backbone parameters hosted by Databricks, and the Unity Gateway release notes announce its availability.

- [machine-learning/model-serving/foundation-model-overview](https://docs.databricks.com/aws/en/machine-learning/model-serving/foundation-model-overview)
- [machine-learning/foundation-model-apis/supported-models](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/supported-models)
- [machine-learning/foundation-model-apis/limits](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/limits)
- [machine-learning/foundation-model-apis/priority-mode](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/priority-mode)
- [machine-learning/model-serving/function-calling](https://docs.databricks.com/aws/en/machine-learning/model-serving/function-calling)
- [machine-learning/model-serving/query-vision-models](https://docs.databricks.com/aws/en/machine-learning/model-serving/query-vision-models)
- …and 4 more

### Unity Catalog ABAC policies can now be attached at the metastore level (Beta), including a new DENY policy type, with a dedicated metastore-policies page.

`additive` · feature · 9 pages

GRANT and DENY policies can be attached `ON { METASTORE | CATALOG | SCHEMA }`; dropping a policy `ON METASTORE` requires a metastore admin; a limit of 100 policies per metastore attached directly is documented; and the best-practices page recommends metastore attachment for org-wide rules that must cover catalogs created later.

- [data-governance/unity-catalog/abac/metastore-policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/metastore-policies)
- [data-governance/unity-catalog/abac/deny-policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/deny-policies)
- [data-governance/unity-catalog/abac/grant-policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/grant-policies)
- [data-governance/unity-catalog/abac/policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/policies)
- [data-governance/unity-catalog/abac/best-practices](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/best-practices)
- [data-governance/unity-catalog/abac/core-concepts](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/core-concepts)
- …and 3 more

### The managed Google Drive connector now documents three authentication methods on separate pages, including Databricks-managed OAuth U2M that needs no Google Cloud project or app registration.

`additive` · authentication · 9 pages

The other two are custom-managed OAuth U2M (your own Google Cloud app, for control over app ownership and rate limits) and an OAuth service account key. The troubleshooting page describes rotating service account keys and re-authenticating custom-managed connections.

- [ingestion/lakeflow-connect/google-drive-source-setup](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/google-drive-source-setup)
- [ingestion/lakeflow-connect/google-drive-source-setup-u2m-databricks-managed](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/google-drive-source-setup-u2m-databricks-managed)
- [ingestion/lakeflow-connect/google-drive-source-setup-u2m](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/google-drive-source-setup-u2m)
- [ingestion/lakeflow-connect/google-drive-source-setup-service-account](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/google-drive-source-setup-service-account)
- [ingestion/lakeflow-connect/google-drive-connection](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/google-drive-connection)
- [ingestion/lakeflow-connect/google-drive-faq](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/google-drive-faq)
- …and 3 more

### Compliance session objects now carry a truncation flag that is true when a session has more than 100,000 inference calls, in which case the messages endpoint returns only part of the session.

`additive` · limit · 6 pages

The field and the 100,000-call ceiling are newly described on the session and session-message endpoints.

- [api/compliance/apps/sessions](https://platform.claude.com/docs/en/api/compliance/apps/sessions)
- [api/compliance/apps/sessions/local](https://platform.claude.com/docs/en/api/compliance/apps/sessions/local)
- [api/compliance/apps/sessions/local/list](https://platform.claude.com/docs/en/api/compliance/apps/sessions/local/list)
- [api/compliance/apps/sessions/local/retrieve](https://platform.claude.com/docs/en/api/compliance/apps/sessions/local/retrieve)
- [api/compliance/apps/sessions/local/messages](https://platform.claude.com/docs/en/api/compliance/apps/sessions/local/messages)
- [api/compliance/apps/sessions/local/messages/list](https://platform.claude.com/docs/en/api/compliance/apps/sessions/local/messages/list)

### The Messages API can now compact a conversation on demand, and the models endpoints expose a `compaction` capability field.

`additive` · feature · 5 pages

The release notes announce compact-on-demand and the compaction guide was substantially rewritten (it now describes choosing when to compact, running summarization in the background, and a retryable 529 `overloaded_error` for transient failures producing or reading a compaction block). The Models API schema gained `compaction: BetaCompactionCapability or null` alongside `summarize`.

- [release-notes/overview](https://platform.claude.com/docs/en/release-notes/overview)
- [build-with-claude/compaction](https://platform.claude.com/docs/en/build-with-claude/compaction)
- [api/beta/models](https://platform.claude.com/docs/en/api/beta/models)
- [api/beta/models/list](https://platform.claude.com/docs/en/api/beta/models/list)
- [api/beta/models/retrieve](https://platform.claude.com/docs/en/api/beta/models/retrieve)

### The `ant` CLI adds `ant beta:sessions connect`, which attaches your terminal to a Claude Managed Agents session; the quickstart install pin moves from 1.30.0 to 1.33.0.

`additive` · tooling · 5 pages

A new reference page documents following a session transcript live, sending messages, allowing or denying tool calls, and opening the session viewer. The events/streaming and permission-policy pages now point at the command as an interactive alternative to handling permission events yourself.

- [cli-sdks-libraries/cli/sessions-connect](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/sessions-connect)
- [release-notes/overview](https://platform.claude.com/docs/en/release-notes/overview)
- [cli-sdks-libraries/cli/quickstart](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/quickstart)
- [managed-agents/events-and-streaming](https://platform.claude.com/docs/en/managed-agents/events-and-streaming)
- [managed-agents/permission-policies](https://platform.claude.com/docs/en/managed-agents/permission-policies)

### Compliance API enums grew: organization settings now start with `access_transparency_enabled` and list 57 further values (was 52), and `organization_role` lists 8 further values (was 6).

`additive` · enum growth · 5 pages

The additional role and setting names beyond the first three are collapsed in the reference, so only the counts and the new leading entry are visible.

- [api/compliance/organizations](https://platform.claude.com/docs/en/api/compliance/organizations)
- [api/compliance/organizations/settings](https://platform.claude.com/docs/en/api/compliance/organizations/settings)
- [api/compliance/organizations/settings/retrieve](https://platform.claude.com/docs/en/api/compliance/organizations/settings/retrieve)
- [api/compliance/organizations/users](https://platform.claude.com/docs/en/api/compliance/organizations/users)
- [api/compliance/organizations/users/list](https://platform.claude.com/docs/en/api/compliance/organizations/users/list)

### Databricks now recommends context-based ingress over IP access lists and documents a `migrate-ip-acls` Databricks Labs CLI tool for converting existing workspace IP access lists into a context-based ingress policy.

`additive` · migration tooling · 5 pages

The ingress policy pages also describe applying policies to the account console and account-level Genie One, selecting specific API scopes, and allowlisting partner platform IPs.

- [security/network/front-end/migrate-to-context-based-ingress](https://docs.databricks.com/aws/en/security/network/front-end/migrate-to-context-based-ingress)
- [security/network/front-end/ip-access-list](https://docs.databricks.com/aws/en/security/network/front-end/ip-access-list)
- [security/network/front-end/ip-access-list-workspace](https://docs.databricks.com/aws/en/security/network/front-end/ip-access-list-workspace)
- [security/network/front-end/manage-ingress-policies](https://docs.databricks.com/aws/en/security/network/front-end/manage-ingress-policies)
- [security/network/context-based-policies](https://docs.databricks.com/aws/en/security/network/context-based-policies)

### Genie Code can now branch a chat into a separate thread, ask a side question with `/btw`, or edit an earlier message to regenerate the chat in place.

`additive` · feature · 5 pages

Documented on a new Branch and edit chats page and surfaced from the navigation and capabilities pages.

- [genie-code/branch](https://docs.databricks.com/aws/en/genie-code/branch)
- [genie-code/full-page](https://docs.databricks.com/aws/en/genie-code/full-page)
- [genie-code/navigate-genie-code](https://docs.databricks.com/aws/en/genie-code/navigate-genie-code)
- [genie-code/features-capabilities](https://docs.databricks.com/aws/en/genie-code/features-capabilities)
- [genie-code/use-genie-code](https://docs.databricks.com/aws/en/genie-code/use-genie-code)

### Continuous Spark Declarative Pipelines can now be given a maintenance window so platform-initiated updates and restarts happen at a predictable time, with maintenance start and complete notifications.

`additive` · feature · 4 pages

Configured on the job that runs the continuous pipeline.

- [ldp/maintenance-windows](https://docs.databricks.com/aws/en/ldp/maintenance-windows)
- [ldp/concepts/pipeline-mode](https://docs.databricks.com/aws/en/ldp/concepts/pipeline-mode)
- [ldp/pipeline-mode](https://docs.databricks.com/aws/en/ldp/pipeline-mode)
- [jobs/notifications](https://docs.databricks.com/aws/en/jobs/notifications)

### Claude Code is now named alongside Cursor, Codex CLI and Gemini CLI as a coding agent you can route through AI Gateway model services.

`additive` · integration · 4 pages

The Coding Agents usage-tracking tab and the governance tutorials were reworded to include it.

- [ai-gateway/usage-tracking](https://docs.databricks.com/aws/en/ai-gateway/usage-tracking)
- [ai-gateway/coding-agent-integration-model-services](https://docs.databricks.com/aws/en/ai-gateway/coding-agent-integration-model-services)
- [ai-gateway/govern-coding-agent-models](https://docs.databricks.com/aws/en/ai-gateway/govern-coding-agent-models)
- [ai-gateway/ai-governance](https://docs.databricks.com/aws/en/ai-gateway/ai-governance)

### A new `ai_transcribe()` SQL function (Beta) transcribes an audio file to text, returning time-stamped segments with speaker labels.

`additive` · new function · 4 pages

Added to the AI functions list and the alphabetical builtin function index.

- [sql/language-manual/functions/ai_transcribe](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_transcribe)
- [sql/language-manual/sql-ref-functions-builtin-alpha](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-functions-builtin-alpha)
- [large-language-models/ai-functions](https://docs.databricks.com/aws/en/large-language-models/ai-functions)
- [release-notes/product/2026/august](https://docs.databricks.com/aws/en/release-notes/product/2026/august)

### Genie Agents now support up to 50 tables, views or metric views (was 30) and a 200,000 conversation limit (was 10,000).

`additive` · limit raised · 3 pages

Both the setup requirements and the best-practices guidance were updated to the new numbers.

- [genie-agents/best-practices](https://docs.databricks.com/aws/en/genie-agents/best-practices)
- [genie-agents/set-up](https://docs.databricks.com/aws/en/genie-agents/set-up)
- [genie-agents/conversation-api](https://docs.databricks.com/aws/en/genie-agents/conversation-api)

### Lakeflow pipelines add `depends_on` flow ordering (Public Preview), so a flow starts only after named flows complete successfully — for example draining a backfill before switching to a live stream.

`additive` · feature · 3 pages

The append-flow reference also documents `import_checkpoint`, a path to an existing Structured Streaming checkpoint so a migrated stream resumes.

- [ldp/flows-depends-on](https://docs.databricks.com/aws/en/ldp/flows-depends-on)
- [ldp/developer/ldp-python-ref-update-flow](https://docs.databricks.com/aws/en/ldp/developer/ldp-python-ref-update-flow)
- [ldp/developer/ldp-python-ref-append-flow](https://docs.databricks.com/aws/en/ldp/developer/ldp-python-ref-append-flow)

### New recipes show how to install MLflow skills for coding agents (Claude Code, Cursor, VS Code, OpenCode) and how to set up the MLflow MCP server so those agents can query your traces and experiments from the IDE.

`additive` · tooling · 3 pages

The MLflow MCP page is reworded from "AI applications and coding assistants" to agents and coding assistants.

- [mlflow3/genai/recipes/set-up-coding-agent](https://docs.databricks.com/aws/en/mlflow3/genai/recipes/set-up-coding-agent)
- [mlflow3/genai/recipes/set-up-mcp-server](https://docs.databricks.com/aws/en/mlflow3/genai/recipes/set-up-mcp-server)
- [mlflow3/genai/tracing/mlflow-mcp](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/mlflow-mcp)

### Databricks Sandbox (Beta) gains a usage guide for creating, running commands in and managing sandbox lifecycles with the Python SDK, and the serverless migration agent documents its own Beta workspace toggle.

`additive` · feature · 3 pages

The sandbox page notes you are billed for data stored in your home directory until the sandbox is deleted; the migration page documents the `/compute` command in Genie Code.

- [compute/serverless/sandbox](https://docs.databricks.com/aws/en/compute/serverless/sandbox)
- [compute/serverless/sandbox-usage-guide](https://docs.databricks.com/aws/en/compute/serverless/sandbox-usage-guide)
- [compute/serverless/migration](https://docs.databricks.com/aws/en/compute/serverless/migration)

### Genie One adds personalized starter questions (Beta) — one-click prompts generated per user from their recent activity — controlled by workspace admins on the Previews page.

`additive` · feature · 3 pages

Shown on the home page alongside the existing customizable content.

- [genie-one/](https://docs.databricks.com/aws/en/genie-one/)
- [genie-one/chat](https://docs.databricks.com/aws/en/genie-one/chat)
- [genie-one/customize-genie-homepage](https://docs.databricks.com/aws/en/genie-one/customize-genie-homepage)

### A new Genie consumption guide covers planning enterprise spend: running a usage discovery period, defining persona tiers and setting budgets.

`additive` · guidance · 3 pages

Linked from the Genie budgets and cost monitoring pages.

- [genie/consumption-guide](https://docs.databricks.com/aws/en/genie/consumption-guide)
- [genie/budgets](https://docs.databricks.com/aws/en/genie/budgets)
- [genie/monitor-cost](https://docs.databricks.com/aws/en/genie/monitor-cost)

### A new `counter_diff` analytic window function converts consecutive cumulative counter values into per-row deltas.

`additive` · new function · 3 pages

Signature `counter_diff(value[, start_time])`, listed in the builtin function indexes.

- [sql/language-manual/functions/counter_diff](https://docs.databricks.com/aws/en/sql/language-manual/functions/counter_diff)
- [sql/language-manual/sql-ref-functions-builtin](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-functions-builtin)
- [sql/language-manual/sql-ref-functions-builtin-alpha](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-functions-builtin-alpha)

### Metric views add unitless numeric `offset` and `range` over a consecutive integer index column, which requires Databricks Runtime 19 or above.

`additive` · feature · 3 pages

Window measures previously needed a dated offset such as `-12 month` stepping along a date or timestamp column; `offset` also requires YAML specification version 1.1 or above.

- [uc-semantics/metric-views/yaml-reference](https://docs.databricks.com/aws/en/uc-semantics/metric-views/yaml-reference)
- [uc-semantics/metric-views/feature-availability](https://docs.databricks.com/aws/en/uc-semantics/metric-views/feature-availability)
- [uc-semantics/metric-views/advanced-techniques](https://docs.databricks.com/aws/en/uc-semantics/metric-views/advanced-techniques)

### Lakebase documents restoring from a snapshot by creating a branch with `source_snapshot`, including the long-running `create_snapshot` operation and a `createBranch` audit event that records the source snapshot.

`additive` · feature · 3 pages

`source_snapshot` is mutually exclusive with `source_branch`, `source_branch_lsn` and `source_branch_time`.

- [oltp/projects/snapshots](https://docs.databricks.com/aws/en/oltp/projects/snapshots)
- [oltp/projects/api-usage](https://docs.databricks.com/aws/en/oltp/projects/api-usage)
- [admin/account-settings/audit-logs](https://docs.databricks.com/aws/en/admin/account-settings/audit-logs)

### Tool names may now be up to 128 characters; the documented regex changed from ^[a-zA-Z0-9_-]{1,64}$ to ^[a-zA-Z0-9_-]{1,128}$.

`additive` · limit change · 2 pages

Both the tool-definition reference and the API primer table were updated in the same way. Names that were already valid remain valid.

- [agents-and-tools/tool-use/define-tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools)
- [claude_api_primer](https://platform.claude.com/docs/en/claude_api_primer)

### A new commerce agents use-case guide covers building shopping and merchant agents with Claude for commerce, with implementations on the Messages API, the Agent SDK and Managed Agents.

`additive` · new guide · 2 pages

The use-case overview page was updated to introduce the three build paths and link the new guide.

- [about-claude/use-case-guides/commerce-agents](https://platform.claude.com/docs/en/about-claude/use-case-guides/commerce-agents)
- [about-claude/use-case-guides/overview](https://platform.claude.com/docs/en/about-claude/use-case-guides/overview)

### Applying ABAC policies to views is in Beta and requires an account admin to enable it.

`additive` · preview · 2 pages

Tables, streaming tables, materialized views and now views (Beta) are listed as supported securables for row filter and column mask policies.

- [data-governance/unity-catalog/abac/requirements](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/requirements)
- [data-governance/unity-catalog/abac/core-concepts](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/core-concepts)

### A new rewind capability restores a Lakeflow pipeline to an earlier point in time so you can fix a problem and reprocess only the affected data.

`additive` · feature · 2 pages

The recovery page states rewind requires a pipeline on the Preview channel with the `pipelines.rewind.betaEnabled` config flag set, plus supported sources.

- [ldp/rewind](https://docs.databricks.com/aws/en/ldp/rewind)
- [ldp/recover-streaming](https://docs.databricks.com/aws/en/ldp/recover-streaming)

### Lakehouse Federation adds a page for running federated Amazon Redshift queries with AWS IAM authentication.

`additive` · authentication · 2 pages

Joins the existing IAM pages for RDS for MySQL and PostgreSQL, which clarify that only a single IAM role in the account running the instance is needed.

- [query-federation/redshift-iam](https://docs.databricks.com/aws/en/query-federation/redshift-iam)
- [query-federation/redshift](https://docs.databricks.com/aws/en/query-federation/redshift)

### Data Classification now has its own release notes page, linked from the release notes index.

`additive` · release notes · 2 pages

It tracks new classifiers, changes to classification behaviour and feature improvements.

- [release-notes/data-classification/](https://docs.databricks.com/aws/en/release-notes/data-classification/)
- [release-notes/](https://docs.databricks.com/aws/en/release-notes/)

### Users in a registered identity provider who aren't assigned to a workspace can now use a limited account-only Genie One experience, documented on a new page.

`additive` · access · 2 pages

The page covers what account-only users can do and how account admins manage their access, data permissions and compute.

- [genie-one/account-only-user-access](https://docs.databricks.com/aws/en/genie-one/account-only-user-access)
- [genie-one/](https://docs.databricks.com/aws/en/genie-one/)

### The Opus 5 migration guide now lists Claude Platform on AWS among the surfaces where the 1M context window is the default and the context-window beta header should be removed.

`additive` · availability · 1 page

The list previously named the Claude API, Amazon Bedrock, Google Cloud and Microsoft only.

- [models/opus-5/migration-guide](https://platform.claude.com/docs/en/models/opus-5/migration-guide)

### Configurable retention for system tables is in Beta; when an account admin enables it the free retention period becomes 395 days for all supported system tables.

`additive` · preview · 1 page

Documented on the system tables landing page.

- [admin/system-tables/](https://docs.databricks.com/aws/en/admin/system-tables/)

## Editorial — 10

### The API reference was regenerated: anonymous `object` unions are replaced by named schema types, example headers and timestamps were normalised, and the beta-header enum grew from "41 more" to "43 more" entries.

`editorial` · bulk regeneration · 39 pages

Recurring, non-semantic shapes across hundreds of pages: `array of object or object` becomes `array of Text or ToolUse or ToolResult`, `BetaOrganizationInvite`, `ComplianceProjectFileReference` and similar; Compliance API curl samples now carry `-H 'anthropic-version: 2023-06-01'`; several Admin API delete/validate samples switched between `Authorization: Bearer $ANTHROPIC_AUTH_TOKEN` and `X-Api-Key: $ANTHROPIC_API_KEY`; example `created_at`/`updated_at` values gained a `Z` suffix; and a long-standing typo in the temperature deprecation note ("A value of 1.0 of will be accepted") was fixed.

- [api/compliance/apps](https://platform.claude.com/docs/en/api/compliance/apps)
- [api/compliance/apps/artifacts](https://platform.claude.com/docs/en/api/compliance/apps/artifacts)
- [api/compliance/apps/chats](https://platform.claude.com/docs/en/api/compliance/apps/chats)
- [api/compliance/apps/chats/files](https://platform.claude.com/docs/en/api/compliance/apps/chats/files)
- [api/compliance/apps/projects](https://platform.claude.com/docs/en/api/compliance/apps/projects)
- [api/compliance/apps/projects/collaborators/list](https://platform.claude.com/docs/en/api/compliance/apps/projects/collaborators/list)
- …and 33 more

### The MLflow GenAI documentation was reorganised around agent observability: the tracing hub moved to `mlflow3/genai/tracing/overview`, new overview/concepts/recipes/prompt-management landing pages were added, and "GenAI app" was renamed to "agent" throughout.

`editorial` · docs restructure · 28 pages

Hundreds of links were repointed — `/tracing/` and `/tracing/tracing-101` now go to `/tracing/overview`, and Agent Evaluation links move from `agents/agent-evaluation/` to `mlflow3/genai/eval-monitor/`. New task pages consolidate automatic vs manual instrumentation, trace enrichment, PII redaction and governance, OTel export and Unity Catalog migration; a Langfuse integration page describes routing Langfuse OTel spans to the Databricks OTLP endpoint.

- [mlflow3/genai/tracing/overview](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/overview)
- [mlflow3/genai/tracing/automatic-tracing](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/automatic-tracing)
- [mlflow3/genai/tracing/manual-tracing](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/manual-tracing)
- [mlflow3/genai/tracing/enrich-traces](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/enrich-traces)
- [mlflow3/genai/tracing/govern-redact](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/govern-redact)
- [mlflow3/genai/tracing/otel-export](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/otel-export)
- …and 22 more

### Every Managed Agents page replaces the prose beta-header callout with a metadata block listing `Status: Beta` and the applicable beta header.

`editorial` · docs restructure · 24 pages

The header values are unchanged: `managed-agents-2026-04-01` for Managed Agents endpoints and `agent-memory-2026-07-22` on the memory page.

- [managed-agents/overview](https://platform.claude.com/docs/en/managed-agents/overview)
- [managed-agents/agent-setup](https://platform.claude.com/docs/en/managed-agents/agent-setup)
- [managed-agents/budgets](https://platform.claude.com/docs/en/managed-agents/budgets)
- [managed-agents/cloud-sandboxes-reference](https://platform.claude.com/docs/en/managed-agents/cloud-sandboxes-reference)
- [managed-agents/environments](https://platform.claude.com/docs/en/managed-agents/environments)
- [managed-agents/github](https://platform.claude.com/docs/en/managed-agents/github)
- …and 18 more

### Account console identity settings are now documented under a single "Identity provider setup" tab with an "Identity management" section, replacing the old "Authentication" tab paths in SSO, SCIM, JIT, MFA and federation-policy instructions.

`editorial` · console navigation · 20 pages

The SSO setup steps now describe clicking Enable SSO to save the configuration in a disabled state and run a connection test, then turning on JIT provisioning separately.

- [security/auth/single-sign-on/okta](https://docs.databricks.com/aws/en/security/auth/single-sign-on/okta)
- [security/auth/single-sign-on/azure-ad](https://docs.databricks.com/aws/en/security/auth/single-sign-on/azure-ad)
- [security/auth/single-sign-on/saml](https://docs.databricks.com/aws/en/security/auth/single-sign-on/saml)
- [security/auth/single-sign-on/oidc](https://docs.databricks.com/aws/en/security/auth/single-sign-on/oidc)
- [security/auth/single-sign-on/aws-iam](https://docs.databricks.com/aws/en/security/auth/single-sign-on/aws-iam)
- [security/auth/single-sign-on/jumpcloud](https://docs.databricks.com/aws/en/security/auth/single-sign-on/jumpcloud)
- …and 14 more

### PHP, Ruby and Java samples across the guides were rewritten to use typed block checks (`instanceof`, `match`, `array_find`) instead of array/shape inspection.

`editorial` · sample refresh · 12 pages

No documented API behaviour changes with these edits.

- [about-claude/use-case-guides/content-moderation](https://platform.claude.com/docs/en/about-claude/use-case-guides/content-moderation)
- [test-and-evaluate/develop-tests](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests)
- [agents-and-tools/tool-use/tool-runner](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner)
- [build-with-claude/cache-diagnostics](https://platform.claude.com/docs/en/build-with-claude/cache-diagnostics)
- [models/sonnet-5/migration-guide](https://platform.claude.com/docs/en/models/sonnet-5/migration-guide)
- [build-with-claude/handling-stop-reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons)
- …and 6 more

### The MCP tunnels research-preview access request link now points to claude.com/form/mcp-tunnels instead of the shared managed-agents form.

`editorial` · link change · 9 pages

Nine MCP tunnel pages changed identically; the preview status itself is unchanged.

- [agents-and-tools/mcp-tunnels/concepts](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/concepts)
- [agents-and-tools/mcp-tunnels/console](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/console)
- [agents-and-tools/mcp-tunnels/deploy-compose](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/deploy-compose)
- [agents-and-tools/mcp-tunnels/deploy-helm](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/deploy-helm)
- [agents-and-tools/mcp-tunnels/overview](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/overview)
- [agents-and-tools/mcp-tunnels/quickstart](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/quickstart)
- …and 3 more

### Guidance on keeping thinking blocks valid across a long Fable 5.1 session was rewritten across the thinking, context-editing, migration and error pages.

`editorial` · guidance rewrite · 7 pages

The advice is consistent with before — treat the conversation as append-only, add instructions via a mid-conversation system message, strip thinking blocks when replaying on an older model — but the wording, examples and cross-links were reworked, including how the error message names the `thinking-binding-controls-2026-08-01` beta header.

- [models/fable-5-1/whats-new-fable-5-1](https://platform.claude.com/docs/en/models/fable-5-1/whats-new-fable-5-1)
- [models/fable-5-1/migration-guide](https://platform.claude.com/docs/en/models/fable-5-1/migration-guide)
- [models/fable-5/migration-guide](https://platform.claude.com/docs/en/models/fable-5/migration-guide)
- [build-with-claude/thinking-troubleshooting](https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting)
- [build-with-claude/preserved-thinking](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking)
- [build-with-claude/context-editing](https://platform.claude.com/docs/en/build-with-claude/context-editing)
- …and 1 more

### Java cloud-backend artifacts in the docs move from 2.60.0 to 2.63.0, and the Java SDK page now describes the platform artifacts as add-ons to the base `com.anthropic:anthropic-java` dependency.

`editorial` · version bump · 6 pages

Affects the Bedrock, Vertex and Microsoft Foundry install snippets plus the MCP helper artifact note (`anthropic-java-mcp`, Java 17 or later).

- [build-with-claude/claude-on-vertex-ai](https://platform.claude.com/docs/en/build-with-claude/claude-on-vertex-ai)
- [build-with-claude/claude-in-amazon-bedrock](https://platform.claude.com/docs/en/build-with-claude/claude-in-amazon-bedrock)
- [build-with-claude/claude-in-microsoft-foundry](https://platform.claude.com/docs/en/build-with-claude/claude-in-microsoft-foundry)
- [build-with-claude/claude-on-amazon-bedrock-legacy](https://platform.claude.com/docs/en/build-with-claude/claude-on-amazon-bedrock-legacy)
- [cli-sdks-libraries/sdks/java](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/java)
- [agents-and-tools/mcp-connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector)

### "Unity Catalog Skills" is renamed "Unity Gateway Skills" on the skills landing page.

`editorial` · rename · 1 page

The described behaviour — a central place to discover, publish and govern agent skills with no copies — is unchanged.

- [agents/uc-skills/](https://docs.databricks.com/aws/en/agents/uc-skills/)

### The scheduled-refresh example sets `STATEMENT_TIMEOUT = 21600` (seconds) instead of `'6h'`.

`editorial` · example fix · 1 page

Only the sample statement changed on this page.

- [ldp/dbsql/schedule-refreshes](https://docs.databricks.com/aws/en/ldp/dbsql/schedule-refreshes)
