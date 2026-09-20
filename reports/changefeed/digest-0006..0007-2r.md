# Change digest

> #6 (2026-09-09) → #7 (2026-09-18) · 6,329 changes · rendered 2026-09-19T21:20:07+00:00

## At a glance

62 findings — **7** breaking, **17** behavioural, **28** additive, **10** editorial — covering 345 of 6,329 changed pages. Anything not here is in the full feed report beside this file.

**If you read nothing else:**

1. Go SDK file examples now pass a params struct to Files.Download and Files.GetMetadata (client.Files.Download(ctx, fileID, anthropic.FileDownloadParams{})), replacing the two-argument calls.
2. Materializing features to an online store now requires CAN USE on the Lakebase instance or project backing that store, and a Stream's creator plus anyone materializing with it need USE CONNECTION on the source connection.
3. Lakebase scale to zero is now limited to computes of 32 CU or smaller (for autoscaling computes, the maximum size must be 32 CU or smaller); enabling it on a larger compute returns an error.
4. The Databricks partner-powered AI features setting can no longer be turned off in the settings UI where it is enabled, and the toggle is removed entirely on November 1, 2026.
5. Lakeflow Declarative Pipelines now state that create_table and CREATE TABLE ... FLOW cannot adopt an existing managed table — the target must be a new managed table.
6. On serverless environment version 6 and above, the /databricks/runtime/info.json file is no longer available.
7. Starting September 19, 2026, Anthropic models are removed from Databricks on AWS GovCloud and AWS GovCloud DoD workspaces that have DoD IL5 enabled.

---

## Breaking — 7

### Go SDK file examples now pass a params struct to Files.Download and Files.GetMetadata (client.Files.Download(ctx, fileID, anthropic.FileDownloadParams{})), replacing the two-argument calls.

`breaking` · sdk-signature · 4 pages

Every Go snippet that downloaded a file or read file metadata was updated from Files.Download(ctx, fileID) / Files.GetMetadata(ctx, fileID) to the form taking anthropic.FileDownloadParams{} or anthropic.FileGetMetadataParams{}. Code written against the older signatures will not compile against the version the docs now show.

- [agents-and-tools/agent-skills/quickstart](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/quickstart)
- [build-with-claude/files](https://platform.claude.com/docs/en/build-with-claude/files)
- [build-with-claude/skills-guide](https://platform.claude.com/docs/en/build-with-claude/skills-guide)
- [agents-and-tools/tool-use/code-execution-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool)

### Materializing features to an online store now requires CAN USE on the Lakebase instance or project backing that store, and a Stream's creator plus anyone materializing with it need USE CONNECTION on the source connection.

`breaking` · permission · 4 pages

The feature-view pages also restate that a sawtooth window_duration must be greater than two days and that the Stream's ingestion table must already contain history covering the full window.

- [machine-learning/feature-store/materialized-features](https://docs.databricks.com/aws/en/machine-learning/feature-store/materialized-features)
- [machine-learning/feature-store/feature-views](https://docs.databricks.com/aws/en/machine-learning/feature-store/feature-views)
- [machine-learning/feature-store/feature-views-api-reference](https://docs.databricks.com/aws/en/machine-learning/feature-store/feature-views-api-reference)
- [machine-learning/feature-store/streams](https://docs.databricks.com/aws/en/machine-learning/feature-store/streams)

### Lakebase scale to zero is now limited to computes of 32 CU or smaller (for autoscaling computes, the maximum size must be 32 CU or smaller); enabling it on a larger compute returns an error.

`breaking` · restriction · 3 pages

manage-computes adds that setting a suspend timeout on a larger compute returns an error. Existing larger computes configured to scale to zero are directly affected.

- [oltp/projects/scale-to-zero](https://docs.databricks.com/aws/en/oltp/projects/scale-to-zero)
- [oltp/projects/autoscaling](https://docs.databricks.com/aws/en/oltp/projects/autoscaling)
- [oltp/projects/manage-computes](https://docs.databricks.com/aws/en/oltp/projects/manage-computes)

### The Databricks partner-powered AI features setting can no longer be turned off in the settings UI where it is enabled, and the toggle is removed entirely on November 1, 2026.

`breaking` · setting-removal · 2 pages

Until that date, workspaces with the setting disabled can still enable it, and the Settings API can still change the value either way. After November 1, 2026 each workspace keeps its current value and changes require contacting your Databricks account team. The account and workspace how-to sections were retitled from 'Disable or enable' to 'Enable'.

- [databricks-ai/partner-powered](https://docs.databricks.com/aws/en/databricks-ai/partner-powered)
- [release-notes/product/](https://docs.databricks.com/aws/en/release-notes/product/)

### Lakeflow Declarative Pipelines now state that create_table and CREATE TABLE ... FLOW cannot adopt an existing managed table — the target must be a new managed table.

`breaking` · restriction · 2 pages

Added as a limitation on both the Python and SQL reference pages.

- [ldp/developer/ldp-python-ref-create-table](https://docs.databricks.com/aws/en/ldp/developer/ldp-python-ref-create-table)
- [ldp/developer/ldp-sql-ref-create-table-flow](https://docs.databricks.com/aws/en/ldp/developer/ldp-sql-ref-create-table-flow)

### On serverless environment version 6 and above, the /databricks/runtime/info.json file is no longer available.

`breaking` · removal · 1 page

Called out under its own heading in the version 6 release notes.

- [release-notes/serverless/environment-version/six](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/six)

### Starting September 19, 2026, Anthropic models are removed from Databricks on AWS GovCloud and AWS GovCloud DoD workspaces that have DoD IL5 enabled.

`breaking` · availability · 1 page

Stated in a warning on the IL5 compliance page, which also lists serverless SQL warehouses as Public Preview.

- [security/privacy/il5](https://docs.databricks.com/aws/en/security/privacy/il5)

## Behavioural — 17

### AI Runtime tutorials now tell you to select the Databricks AI v6 environment instead of AI v5, and several examples state they require AI environment version 6 or above.

`behavioural` · version-floor · 15 pages

The six-gpu environment notes Serverless GPU Python API 0.5.25 (was 0.5.24). The environment page still warns that torch and torchvision are not pre-installed as of version 5.

- [machine-learning/ai-runtime/examples/tutorials/sgc-distributed-pytorch-fsdp](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-distributed-pytorch-fsdp)
- [machine-learning/ai-runtime/examples/tutorials/sgc-sft-trl-deepspeed-llama-1b](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-sft-trl-deepspeed-llama-1b)
- [machine-learning/ai-runtime/examples/tutorials/sgc-recommender-system-lightning](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-recommender-system-lightning)
- [machine-learning/ai-runtime/examples/tutorials/sgc-api-h100-starter](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-api-h100-starter)
- [machine-learning/ai-runtime/examples/tutorials/sgc-distributed-gpt-oss-20b](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-distributed-gpt-oss-20b)
- [machine-learning/ai-runtime/examples/tutorials/sgc-finetune-qwen3-4b](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-finetune-qwen3-4b)
- …and 9 more

### Databricks Runtime 18.1 (and 18.1 ML) and 13.3 LTS (and 13.3 LTS ML) are now marked end-of-support, and their maintenance-update histories moved to the maintenance-updates-archive page.

`behavioural` · end-of-support · 13 pages

Release-note titles gained the '(EoS)' suffix and links across product and gov-cloud release notes were repointed to the archive.

- [release-notes/runtime/18.1](https://docs.databricks.com/aws/en/release-notes/runtime/18.1)
- [release-notes/runtime/18.1ml](https://docs.databricks.com/aws/en/release-notes/runtime/18.1ml)
- [release-notes/runtime/13.3lts](https://docs.databricks.com/aws/en/release-notes/runtime/13.3lts)
- [release-notes/runtime/13.3lts-ml](https://docs.databricks.com/aws/en/release-notes/runtime/13.3lts-ml)
- [release-notes/runtime/maintenance-updates](https://docs.databricks.com/aws/en/release-notes/runtime/maintenance-updates)
- [release-notes/gov-cloud/2026](https://docs.databricks.com/aws/en/release-notes/gov-cloud/2026)
- …and 7 more

### Managed-table drop semantics were rewritten: after the recovery window ends an asynchronous purge permanently deletes the files, shallow clones can keep reading for a time after the base table is no longer recoverable, and DROP TABLE ... FORCE is required only where the workspace enforces drop-time protection for shallow clones.

`behavioural` · clarification · 10 pages

The docs say a plain DROP TABLE on such a base table can fail with CANNOT_DROP_BASE_TABLE_REFERENCED_BY_SHALLOW_CLONE, and the 'Drop a managed table' anchor was renamed, repointing links across the catalog and schema DDL pages.

- [tables/operations/drop-table](https://docs.databricks.com/aws/en/tables/operations/drop-table)
- [sql/language-manual/sql-ref-syntax-ddl-drop-table](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-ddl-drop-table)
- [tables/managed](https://docs.databricks.com/aws/en/tables/managed)
- [tables/operations/clone-unity-catalog](https://docs.databricks.com/aws/en/tables/operations/clone-unity-catalog)
- [data-governance/unity-catalog/object-storage-lifecycle](https://docs.databricks.com/aws/en/data-governance/unity-catalog/object-storage-lifecycle)
- [sql/language-manual/sql-ref-syntax-aux-show-tables-dropped](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-aux-show-tables-dropped)
- …and 4 more

### SSO setup now has an explicit Enable SSO step: Databricks saves the configuration in a disabled state and runs a connection test before SSO takes effect, with JIT provisioning enabled afterwards.

`behavioural` · workflow · 8 pages

All eight identity-provider walkthroughs were updated with the new step order.

- [security/auth/single-sign-on/aws-iam](https://docs.databricks.com/aws/en/security/auth/single-sign-on/aws-iam)
- [security/auth/single-sign-on/okta](https://docs.databricks.com/aws/en/security/auth/single-sign-on/okta)
- [security/auth/single-sign-on/saml](https://docs.databricks.com/aws/en/security/auth/single-sign-on/saml)
- [security/auth/single-sign-on/oidc](https://docs.databricks.com/aws/en/security/auth/single-sign-on/oidc)
- [security/auth/single-sign-on/jumpcloud](https://docs.databricks.com/aws/en/security/auth/single-sign-on/jumpcloud)
- [security/auth/single-sign-on/keycloak](https://docs.databricks.com/aws/en/security/auth/single-sign-on/keycloak)
- …and 2 more

### Thinking prefix-mismatch handling is now documented per block: with "drop_block" the response reports one entry per thinking block in the history with a reason and position (messages.{i}.content.{j}), and the 'Preserved thinking' section was renamed 'Keeping the prefix unchanged' with links repointed.

`behavioural` · thinking-prefix · 7 pages

The batch results reference also describes removals attributed to thinking.block_binding.prefix_mismatch_behavior. Guidance to treat long conversations as append-only is unchanged in substance.

- [build-with-claude/preserved-thinking](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking)
- [api/errors](https://platform.claude.com/docs/en/api/errors)
- [build-with-claude/context-editing](https://platform.claude.com/docs/en/build-with-claude/context-editing)
- [build-with-claude/thinking-troubleshooting](https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting)
- [api/beta/messages/batches/results](https://platform.claude.com/docs/en/api/beta/messages/batches/results)
- [models/fable-5-1/whats-new-fable-5-1](https://platform.claude.com/docs/en/models/fable-5-1/whats-new-fable-5-1)
- …and 1 more

### Databricks now recommends context-based ingress controls over IP access lists and ships a Databricks Labs CLI tool, migrate-ip-acls, documented on a new page for converting existing workspace IP access lists into a context-based ingress policy.

`behavioural` · recommendation · 6 pages

Ingress policies can now also allow or deny access to Databricks APIs with optional per-API scopes, and context-based ingress requires the Enterprise tier.

- [security/network/front-end/migrate-to-context-based-ingress](https://docs.databricks.com/aws/en/security/network/front-end/migrate-to-context-based-ingress)
- [security/network/front-end/ip-access-list](https://docs.databricks.com/aws/en/security/network/front-end/ip-access-list)
- [security/network/front-end/ip-access-list-workspace](https://docs.databricks.com/aws/en/security/network/front-end/ip-access-list-workspace)
- [security/network/front-end/context-based-ingress](https://docs.databricks.com/aws/en/security/network/front-end/context-based-ingress)
- [security/network/context-based-policies](https://docs.databricks.com/aws/en/security/network/context-based-policies)
- [security/network/front-end/manage-ingress-policies](https://docs.databricks.com/aws/en/security/network/front-end/manage-ingress-policies)

### The user profiles beta API now states that once external_id is set it cannot be cleared and null is rejected, and that the field is accepted under the user-profiles-2026-09-04 beta header.

`behavioural` · restriction · 5 pages

Maximum length stays 255 characters and the value is not enforced unique; earlier headers (user-profiles-2026-03-24, -2026-08-18) are still referenced for presence of the field.

- [api/beta/user_profiles](https://platform.claude.com/docs/en/api/beta/user_profiles)
- [api/beta/user_profiles/create](https://platform.claude.com/docs/en/api/beta/user_profiles/create)
- [api/beta/user_profiles/update](https://platform.claude.com/docs/en/api/beta/user_profiles/update)
- [api/beta/user_profiles/list](https://platform.claude.com/docs/en/api/beta/user_profiles/list)
- [api/beta/user_profiles/retrieve](https://platform.claude.com/docs/en/api/beta/user_profiles/retrieve)

### The FILE type now requires serverless environment version 6 or above, replacing the earlier statement that it isn't supported on serverless notebooks, and the docs add that a Unity Catalog-registered UDF can read a FILE's metadata but not its contents and can't create files.

`behavioural` · version-floor · 4 pages

Previously the FILE type was documented as supported only on notebooks attached to serverless SQL warehouses.

- [sql/language-manual/data-types/file-type](https://docs.databricks.com/aws/en/sql/language-manual/data-types/file-type)
- [pyspark/reference/file-type](https://docs.databricks.com/aws/en/pyspark/reference/file-type)
- [unstructured/file-udfs](https://docs.databricks.com/aws/en/unstructured/file-udfs)
- [udf/python](https://docs.databricks.com/aws/en/udf/python)

### Private access to account-level resources and workspace private access via context-based ingress are Beta features that must be switched on by name: 'Front-end Private Link for Custom URLs and Account' and 'Context-Based Ingress: Workspace Private Access Policies'.

`behavioural` · preview-gating · 4 pages

The private-link pages previously said only that the capability was in Beta. service-direct-privatelink adds that you should enable it only after registration completes, because requests are rejected until then.

- [security/network/classic/privatelink-dns](https://docs.databricks.com/aws/en/security/network/classic/privatelink-dns)
- [security/network/front-end/front-end-private-connect-account](https://docs.databricks.com/aws/en/security/network/front-end/front-end-private-connect-account)
- [security/network/front-end/front-end-private-connect](https://docs.databricks.com/aws/en/security/network/front-end/front-end-private-connect)
- [security/network/front-end/service-direct-privatelink](https://docs.databricks.com/aws/en/security/network/front-end/service-direct-privatelink)

### The beta Environments API now states that API organizations support only visibility scope 'organization' and that 'account' is rejected, with the default depending on organization type.

`behavioural` · restriction · 2 pages

Previously the field description only explained what the two scopes mean.

- [api/beta/environments](https://platform.claude.com/docs/en/api/beta/environments)
- [api/beta/environments/create](https://platform.claude.com/docs/en/api/beta/environments/create)

### Unity Catalog requirements now state that on dedicated compute, workloads accessing Unity Catalog data must use a supported thread pool in org.apache.spark.util.ThreadUtils, and the JAR task page enumerates unsupported pools including ForkJoinPool, Scala parallel collections (.par) and ThreadUtils.newForkJoinPool.

`behavioural` · restriction · 2 pages

The earlier wording said only that standard Scala thread pools are not supported.

- [data-governance/unity-catalog/requirements](https://docs.databricks.com/aws/en/data-governance/unity-catalog/requirements)
- [jobs/tasks/jar-create](https://docs.databricks.com/aws/en/jobs/tasks/jar-create)

### Databricks Apps is now turned on by default for workspaces with the compliance security profile enabled, replacing the requirement that a workspace admin enable it from the Previews page.

`behavioural` · default-change · 2 pages

Applies in all regions where the selected profile is supported, per the Apps landing page.

- [dev-tools/databricks-apps/](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/)
- [security/privacy/security-profile](https://docs.databricks.com/aws/en/security/privacy/security-profile)

### Compliance API scope failures now return a 403 worded 'Missing required scopes. Got: [...] Needed one of: [...]' instead of 'Needed: [...]'.

`behavioural` · error-message · 1 page

Clients that parse the 403 body string should expect the new wording.

- [manage-claude/compliance-api-access](https://platform.claude.com/docs/en/manage-claude/compliance-api-access)

### The minimum accepted task_budget.total is now documented as a flat 20,000 tokens on every model that supports task budgets, where the page previously said the minimum was model-specific.

`behavioural` · limit · 1 page

Callers that relied on a lower per-model floor should check their configured budgets against 20,000.

- [build-with-claude/task-budgets](https://platform.claude.com/docs/en/build-with-claude/task-budgets)

### Genie Agent file upload now states that each PDF must contain no more than 100 pages.

`behavioural` · limit · 1 page

The page also reworked its description of who can upload; the permission sentence about needing at least CAN RUN was replaced.

- [genie-agents/file-upload](https://docs.databricks.com/aws/en/genie-agents/file-upload)

### The 2.0/jobs/list endpoint is now marked deprecated, with Jobs API 2.2 recommended instead.

`behavioural` · deprecation · 1 page

Added as an Important callout in the Jobs 2.0 API reference.

- [reference/jobs-2.0-api](https://docs.databricks.com/aws/en/reference/jobs-2.0-api)

### Deleting a workspace now removes that workspace's audit events older than 14 days from system.access.audit.

`behavioural` · retention · 1 page

Added as a note on the audit log system table page.

- [admin/system-tables/audit-logs](https://docs.databricks.com/aws/en/admin/system-tables/audit-logs)

## Additive — 28

### The Files, Skills and Message Batches endpoints now document an optional "anthropic-workspace-id" request header.

`additive` · header · 18 pages

Added as a Headers entry on each endpoint page.

- [api/files](https://platform.claude.com/docs/en/api/files)
- [api/files/list](https://platform.claude.com/docs/en/api/files/list)
- [api/files/upload](https://platform.claude.com/docs/en/api/files/upload)
- [api/files/download](https://platform.claude.com/docs/en/api/files/download)
- [api/files/delete](https://platform.claude.com/docs/en/api/files/delete)
- [api/files/retrieve_metadata](https://platform.claude.com/docs/en/api/files/retrieve_metadata)
- …and 12 more

### A large block of admin endpoints is now documented under /v1/organizations beta paths: analytics (usage, cost, users, skills, connectors, artifacts, plugins, chat projects), RBAC groups and roles, MCP tunnels and tunnel certificates, spend limits with increase requests, and usage/cost reports.

`additive` · new-endpoints · 12 pages

These pages are new in this run and mirror the existing api/admin/* reference for the same resources.

- [api/beta/organization/analytics](https://platform.claude.com/docs/en/api/beta/organization/analytics)
- [api/beta/organization/analytics/usage](https://platform.claude.com/docs/en/api/beta/organization/analytics/usage)
- [api/beta/organization/analytics/cost](https://platform.claude.com/docs/en/api/beta/organization/analytics/cost)
- [api/beta/organization/analytics/users](https://platform.claude.com/docs/en/api/beta/organization/analytics/users)
- [api/beta/organization/rbac_groups](https://platform.claude.com/docs/en/api/beta/organization/rbac_groups)
- [api/beta/organization/rbac_roles](https://platform.claude.com/docs/en/api/beta/organization/rbac_roles)
- …and 6 more

### Five managed Lakeflow Connect connectors are newly documented: Anaplan, Atlassian Audit Logs, Celigo, Google Workspace (33 application audit logs) and Anysphere Organization, each with connection, pipeline, reference, limits, FAQ and troubleshooting pages.

`additive` · new-connectors · 12 pages

The connector FAQ index and SaaS overview were updated to list them.

- [ingestion/lakeflow-connect/anaplan](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anaplan)
- [ingestion/lakeflow-connect/anaplan-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anaplan-pipeline)
- [ingestion/lakeflow-connect/atlassian-audit-logs](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/atlassian-audit-logs)
- [ingestion/lakeflow-connect/atlassian-audit-logs-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/atlassian-audit-logs-pipeline)
- [ingestion/lakeflow-connect/celigo](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/celigo)
- [ingestion/lakeflow-connect/celigo-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/celigo-pipeline)
- …and 6 more

### Unity Catalog ABAC adds DENY policies (Beta) and metastore-level policy attachment, so a single row filter, column mask, GRANT or DENY policy can apply across every catalog, including catalogs created later.

`additive` · feature · 11 pages

A new metastore-policies page documents the scope; ON { METASTORE | CATALOG | SCHEMA } is now shown for GRANT and DENY policies, dropping a policy ON METASTORE (Beta) requires metastore admin, and creating or dropping a DENY policy with SQL requires Databricks Runtime 18 LTS or above. A limit of 100 policies per metastore attached directly is documented.

- [data-governance/unity-catalog/abac/deny-policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/deny-policies)
- [data-governance/unity-catalog/abac/metastore-policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/metastore-policies)
- [data-governance/unity-catalog/abac/grant-policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/grant-policies)
- [data-governance/unity-catalog/abac/](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/)
- [data-governance/unity-catalog/abac/best-practices](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/best-practices)
- [data-governance/unity-catalog/abac/requirements](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/requirements)
- …and 5 more

### Google Drive ingestion setup was split into three documented authentication paths, including a Databricks-managed OAuth U2M option that needs no Google Cloud project or app registration.

`additive` · auth-options · 9 pages

Custom-managed OAuth U2M (bring your own Google Cloud app, for control over app ownership and API rate limiting) and an OAuth service account path get their own pages; the connection, pipeline, FAQ and troubleshooting pages point at them.

- [ingestion/lakeflow-connect/google-drive-source-setup](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/google-drive-source-setup)
- [ingestion/lakeflow-connect/google-drive-source-setup-u2m-databricks-managed](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/google-drive-source-setup-u2m-databricks-managed)
- [ingestion/lakeflow-connect/google-drive-source-setup-u2m](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/google-drive-source-setup-u2m)
- [ingestion/lakeflow-connect/google-drive-source-setup-service-account](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/google-drive-source-setup-service-account)
- [ingestion/lakeflow-connect/google-drive-connection](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/google-drive-connection)
- [ingestion/lakeflow-connect/google-drive](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/google-drive)
- …and 3 more

### Java platform artifacts (anthropic-java-vertex, -bedrock, -foundry) are documented at 2.63.0, up from 2.60.0, and the SDK page now states they are add-ons to the base com.anthropic:anthropic-java dependency.

`additive` · version-bump · 6 pages

The Gradle/Maven snippets on each cloud-platform page were bumped. cli-sdks-libraries/sdks/java rewords the backend section to say the platform artifacts supplement the base dependency that provides AnthropicOkHttpClient; the MCP helper artifact anthropic-java-mcp still requires Java 17.

- [build-with-claude/claude-on-vertex-ai](https://platform.claude.com/docs/en/build-with-claude/claude-on-vertex-ai)
- [build-with-claude/claude-in-amazon-bedrock](https://platform.claude.com/docs/en/build-with-claude/claude-in-amazon-bedrock)
- [build-with-claude/claude-in-microsoft-foundry](https://platform.claude.com/docs/en/build-with-claude/claude-in-microsoft-foundry)
- [build-with-claude/claude-on-amazon-bedrock-legacy](https://platform.claude.com/docs/en/build-with-claude/claude-on-amazon-bedrock-legacy)
- [cli-sdks-libraries/sdks/java](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/java)
- [agents-and-tools/mcp-connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector)

### DeepSeek V4.1 Flash, a 552B-parameter multimodal mixture-of-experts model with adjustable reasoning effort, is now available in Foundation Model APIs with documented rate limits, function calling and licensing.

`additive` · new-model · 6 pages

limits lists 200,000 context / 10,000 output / 7,200 tokens per minute for the model.

- [machine-learning/foundation-model-apis/supported-models](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/supported-models)
- [machine-learning/foundation-model-apis/limits](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/limits)
- [machine-learning/model-serving/function-calling](https://docs.databricks.com/aws/en/machine-learning/model-serving/function-calling)
- [machine-learning/model-serving/acceptable-use-models](https://docs.databricks.com/aws/en/machine-learning/model-serving/acceptable-use-models)
- [machine-learning/model-serving/query-vision-models](https://docs.databricks.com/aws/en/machine-learning/model-serving/query-vision-models)
- [release-notes/unity-gateway/](https://docs.databricks.com/aws/en/release-notes/unity-gateway/)

### Compliance API enums grew: organization settings now list access_transparency_enabled and collapse to '57 more' (was 52), and organization_role collapses to '8 more' (was 6).

`additive` · enum-growth · 5 pages

The pages name access_transparency_enabled explicitly; the other added values remain inside the collapsed counts.

- [api/compliance/organizations](https://platform.claude.com/docs/en/api/compliance/organizations)
- [api/compliance/organizations/settings](https://platform.claude.com/docs/en/api/compliance/organizations/settings)
- [api/compliance/organizations/settings/retrieve](https://platform.claude.com/docs/en/api/compliance/organizations/settings/retrieve)
- [api/compliance/organizations/users](https://platform.claude.com/docs/en/api/compliance/organizations/users)
- [api/compliance/organizations/users/list](https://platform.claude.com/docs/en/api/compliance/organizations/users/list)

### The Messages API can now compact a conversation on demand, and the beta Models API reports a per-model `compaction: BetaCompactionCapability` field.

`additive` · feature · 5 pages

release-notes/overview announces compact-on-demand; the compaction guide covers controlling when compaction happens, pausing while a summary is written, and keeping recent turns and their thinking after the summary, and states that if the last assistant turn ends in a tool call with no result the API rejects the request.

- [build-with-claude/compaction](https://platform.claude.com/docs/en/build-with-claude/compaction)
- [release-notes/overview](https://platform.claude.com/docs/en/release-notes/overview)
- [api/beta/models](https://platform.claude.com/docs/en/api/beta/models)
- [api/beta/models/list](https://platform.claude.com/docs/en/api/beta/models/list)
- [api/beta/models/retrieve](https://platform.claude.com/docs/en/api/beta/models/retrieve)

### Metric view window measures accept unitless numeric `offset` and `range` over a consecutive integer index column, requiring YAML specification version 1.1 or above and Databricks Runtime 19 or above.

`additive` · feature · 5 pages

The runtime 19 notes also relax a related row-tracking feature from 'Databricks Runtime 19 LTS or above' to 'Databricks Runtime 19 or above' and rename Delta Lake Sharing to Delta Sharing.

- [uc-semantics/metric-views/yaml-reference](https://docs.databricks.com/aws/en/uc-semantics/metric-views/yaml-reference)
- [uc-semantics/metric-views/feature-availability](https://docs.databricks.com/aws/en/uc-semantics/metric-views/feature-availability)
- [uc-semantics/metric-views/advanced-techniques](https://docs.databricks.com/aws/en/uc-semantics/metric-views/advanced-techniques)
- [release-notes/whats-coming](https://docs.databricks.com/aws/en/release-notes/whats-coming)
- [release-notes/runtime/19](https://docs.databricks.com/aws/en/release-notes/runtime/19)

### Zerobus writes to liquid clustered tables are now generally available; the Beta labels were removed from the features, quotas and release-stage pages.

`additive` · ga · 4 pages

The C# / .NET SDK remains in Beta, though the qualifying sentence about the Databricks.Zerobus.Ingest.Sdk package was trimmed.

- [ingestion/zerobus-quotas](https://docs.databricks.com/aws/en/ingestion/zerobus-quotas)
- [ingestion/zerobus-features](https://docs.databricks.com/aws/en/ingestion/zerobus-features)
- [ingestion/zerobus-release-stages](https://docs.databricks.com/aws/en/ingestion/zerobus-release-stages)
- [ingestion/zerobus-ingest](https://docs.databricks.com/aws/en/ingestion/zerobus-ingest)

### Genie Agent limits were raised: up to 50 tables, views or metric views per agent (was 30) and a 200,000 conversation limit (was 10,000).

`additive` · limit-raised · 4 pages

Best practices now advises prejoining into views or metric views only above 50 tables.

- [genie-agents/best-practices](https://docs.databricks.com/aws/en/genie-agents/best-practices)
- [genie-agents/set-up](https://docs.databricks.com/aws/en/genie-agents/set-up)
- [genie-agents/conversation-api](https://docs.databricks.com/aws/en/genie-agents/conversation-api)
- [resources/limits](https://docs.databricks.com/aws/en/resources/limits)

### New recipes show how to install MLflow skills for coding agents (Claude Code, Cursor, VS Code, OpenCode) and how to set up the MLflow MCP server so those agents can query traces and experiments from your IDE; a Langfuse integration page routes Langfuse OTel spans to the Databricks OTLP endpoint.

`additive` · tooling · 4 pages

The Langfuse page stores those traces in Unity Catalog tables alongside other MLflow traces.

- [mlflow3/genai/recipes/set-up-coding-agent](https://docs.databricks.com/aws/en/mlflow3/genai/recipes/set-up-coding-agent)
- [mlflow3/genai/recipes/set-up-mcp-server](https://docs.databricks.com/aws/en/mlflow3/genai/recipes/set-up-mcp-server)
- [mlflow3/genai/tracing/mlflow-mcp](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/mlflow-mcp)
- [mlflow3/genai/tracing/integrations/langfuse](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/langfuse)

### Continuous Lakeflow pipelines can now have a maintenance window so platform-initiated updates and restarts happen at a predictable time, configured on the job that runs the pipeline.

`additive` · feature · 4 pages

Jobs notifications add maintenance start and maintenance complete events for continuous jobs with a configured window.

- [ldp/maintenance-windows](https://docs.databricks.com/aws/en/ldp/maintenance-windows)
- [ldp/pipeline-mode](https://docs.databricks.com/aws/en/ldp/pipeline-mode)
- [ldp/concepts/pipeline-mode](https://docs.databricks.com/aws/en/ldp/concepts/pipeline-mode)
- [jobs/notifications](https://docs.databricks.com/aws/en/jobs/notifications)

### A new Beta SQL function ai_transcribe() transcribes an audio file to text, returning time-stamped segments with speaker labels.

`additive` · new-function · 4 pages

Listed in the AI functions index and the alphabetical builtin list.

- [sql/language-manual/functions/ai_transcribe](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_transcribe)
- [large-language-models/ai-functions](https://docs.databricks.com/aws/en/large-language-models/ai-functions)
- [sql/language-manual/sql-ref-functions-builtin-alpha](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-functions-builtin-alpha)
- [release-notes/product/2026/august](https://docs.databricks.com/aws/en/release-notes/product/2026/august)

### Sharing foreign schemas and tables with OpenSharing is generally available, and shareable views may now be defined on foreign tables in addition to Delta tables and other shareable views.

`additive` · ga · 4 pages

create-share adds that sharing foreign Iceberg tables with open recipients that don't use Iceberg clients requires default storage.

- [opensharing/create-share](https://docs.databricks.com/aws/en/opensharing/create-share)
- [opensharing/](https://docs.databricks.com/aws/en/opensharing/)
- [data-governance/unity-catalog/abac/opensharing](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/opensharing)
- [release-notes/product/](https://docs.databricks.com/aws/en/release-notes/product/)

### The ant CLI quickstart pins VERSION=1.33.0 and a new page documents `ant beta:sessions connect`, added in 1.32.0, which attaches your terminal to a Claude Managed Agents session.

`additive` · cli · 3 pages

release-notes/overview announces the command; the new cli-sdks-libraries/cli/sessions-connect page covers following a transcript live, sending messages, allowing or denying tool calls, and opening the session viewer.

- [cli-sdks-libraries/cli/quickstart](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/quickstart)
- [cli-sdks-libraries/cli/sessions-connect](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/sessions-connect)
- [release-notes/overview](https://platform.claude.com/docs/en/release-notes/overview)

### Automatic Git deployments for Databricks Apps are no longer labelled Beta.

`additive` · ga · 3 pages

The Beta callout was removed from the deploy page and the cross-references dropped the '(Beta)' qualifier.

- [dev-tools/databricks-apps/deploy](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/deploy)
- [dev-tools/databricks-apps/cicd-github-actions](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/cicd-github-actions)
- [dev-tools/databricks-apps/get-started](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/get-started)

### Lakeflow pipelines add a Public Preview `depends_on` flow option that makes a flow start only after named flows complete successfully, for cases like draining a backfill before switching to a live stream.

`additive` · feature · 3 pages

Documented on a new page plus the append_flow and update_flow Python references; accepts a single flow name or a list.

- [ldp/flows-depends-on](https://docs.databricks.com/aws/en/ldp/flows-depends-on)
- [ldp/developer/ldp-python-ref-append-flow](https://docs.databricks.com/aws/en/ldp/developer/ldp-python-ref-append-flow)
- [ldp/developer/ldp-python-ref-update-flow](https://docs.databricks.com/aws/en/ldp/developer/ldp-python-ref-update-flow)

### A new counter_diff analytic window function converts consecutive cumulative counter values into per-row deltas.

`additive` · new-function · 3 pages

Added to the builtin function lists as counter_diff(value[, start_time]).

- [sql/language-manual/functions/counter_diff](https://docs.databricks.com/aws/en/sql/language-manual/functions/counter_diff)
- [sql/language-manual/sql-ref-functions-builtin](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-functions-builtin)
- [sql/language-manual/sql-ref-functions-builtin-alpha](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-functions-builtin-alpha)

### Tool names may now be up to 128 characters: the documented regex changed from ^[a-zA-Z0-9_-]{1,64}$ to ^[a-zA-Z0-9_-]{1,128}$.

`additive` · limit-raised · 2 pages

Both the tool-definition reference and the API primer table now show the longer pattern. Existing names that fit the old 64-character limit are unaffected.

- [agents-and-tools/tool-use/define-tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools)
- [claude_api_primer](https://platform.claude.com/docs/en/claude_api_primer)

### A new use-case guide covers Claude for commerce, an open-source blueprint for shopping and merchant agents with implementations on the Messages API, the Claude Agent SDK and Claude Managed Agents.

`additive` · new-guide · 2 pages

The use-case guides overview adds a Commerce agent entry and reframes the three paths for building with Claude by how much implementation you offload.

- [about-claude/use-case-guides/commerce-agents](https://platform.claude.com/docs/en/about-claude/use-case-guides/commerce-agents)
- [about-claude/use-case-guides/overview](https://platform.claude.com/docs/en/about-claude/use-case-guides/overview)

### Lakeflow pipelines document Rewind, which restores a pipeline to an earlier point in time so you can fix a problem and reprocess only the affected data.

`additive` · feature · 2 pages

Rewind requires a pipeline on the Preview channel with the pipelines.rewind.betaEnabled config flag set, plus supported sources and sinks; the recovery guide notes it cannot recover every case.

- [ldp/rewind](https://docs.databricks.com/aws/en/ldp/rewind)
- [ldp/recover-streaming](https://docs.databricks.com/aws/en/ldp/recover-streaming)

### Mid-conversation system messages are now in beta on Google Cloud in addition to the Claude API, for Claude Fable 5.1, Mythos 5.1 and Opus 5, still behind the mid-conversation-output-config-2026-07-01 beta header.

`additive` · availability · 1 page

The supported-platform sentence added Google Cloud.

- [build-with-claude/mid-conversation-system-messages](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages)

### The Opus 5 migration guide now lists Claude Platform on AWS among the platforms where the 1M context window is the default and the context-window beta header should be removed.

`additive` · availability · 1 page

Previously the list was Claude API, Amazon Bedrock, Google Cloud and Microsoft Foundry.

- [models/opus-5/migration-guide](https://platform.claude.com/docs/en/models/opus-5/migration-guide)

### The SQL Server integrated CDC connector dropped its Beta gating: no workspace-level enablement is required and pipeline specs no longer need "channel": "PREVIEW" (channel is optional and defaults to CURRENT).

`additive` · ga · 1 page

All example specs removed the channel field, and the limitation entries for Beta enablement and the PREVIEW channel were deleted. Continuous mode remains in Beta.

- [ingestion/lakeflow-connect/sql-server-integrated-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/sql-server-integrated-pipeline)

### The Unity Gateway API for managing model services, model provider services and MCP services is now generally available with create, read, update and delete operations.

`additive` · ga · 1 page

Announced in the Unity Gateway release notes.

- [release-notes/unity-gateway/](https://docs.databricks.com/aws/en/release-notes/unity-gateway/)

### Scheduled notebook jobs moved from Beta to Public Preview, and the note that workspace admins control access to the feature was dropped.

`additive` · preview-stage · 1 page

- [notebooks/schedule-notebook-jobs](https://docs.databricks.com/aws/en/notebooks/schedule-notebook-jobs)

## Editorial — 10

### Managed Agents pages replaced the inline beta-header callout with a standard metadata block listing Status: Beta and the beta header (managed-agents-2026-04-01, or agent-memory-2026-07-22 on the memory page).

`editorial` · docs-format · 26 pages

The header values are unchanged; only the presentation moved from a prose note to a per-page status block.

- [managed-agents/overview](https://platform.claude.com/docs/en/managed-agents/overview)
- [managed-agents/agent-setup](https://platform.claude.com/docs/en/managed-agents/agent-setup)
- [managed-agents/budgets](https://platform.claude.com/docs/en/managed-agents/budgets)
- [managed-agents/cloud-sandboxes-reference](https://platform.claude.com/docs/en/managed-agents/cloud-sandboxes-reference)
- [managed-agents/environments](https://platform.claude.com/docs/en/managed-agents/environments)
- [managed-agents/github](https://platform.claude.com/docs/en/managed-agents/github)
- …and 20 more

### The MLflow 3 GenAI documentation was restructured: /mlflow3/genai/tracing/ landing links were repointed to /tracing/overview, new hub pages (agent observability and quality, core concepts, recipes, automatic vs manual tracing, enrich, govern/redact, OTel export, migrate to UC) were added, and 'GenAI app' was reworded to 'agent' throughout.

`editorial` · docs-reorg · 19 pages

Hundreds of cross-links across agents/*, mlflow*/ and release notes were repointed, including Agent Evaluation links now going to mlflow3/genai/eval-monitor/. This is a documentation reorganization rather than a product change.

- [mlflow3/genai/tracing/overview](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/overview)
- [mlflow3/genai/agent-observability-and-quality](https://docs.databricks.com/aws/en/mlflow3/genai/agent-observability-and-quality)
- [mlflow3/genai/concepts/core-concepts](https://docs.databricks.com/aws/en/mlflow3/genai/concepts/core-concepts)
- [mlflow3/genai/recipes/](https://docs.databricks.com/aws/en/mlflow3/genai/recipes/)
- [mlflow3/genai/tracing/automatic-tracing](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/automatic-tracing)
- [mlflow3/genai/tracing/manual-tracing](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/manual-tracing)
- …and 13 more

### Account console identity configuration is now a single 'Identity provider setup' page: SSO, SCIM provisioning, JIT, MFA, automatic identity management and identity attributes are all reached from that tab instead of the former Authentication tab and scattered sections.

`editorial` · console-ui · 13 pages

Step-by-step instructions across the SSO, SCIM and AIM pages were renumbered accordingly.

- [security/auth/](https://docs.databricks.com/aws/en/security/auth/)
- [security/auth/jit](https://docs.databricks.com/aws/en/security/auth/jit)
- [security/auth/mfa](https://docs.databricks.com/aws/en/security/auth/mfa)
- [security/auth/single-sign-on/unified-login](https://docs.databricks.com/aws/en/security/auth/single-sign-on/unified-login)
- [security/auth/single-sign-on/emergency-access](https://docs.databricks.com/aws/en/security/auth/single-sign-on/emergency-access)
- [admin/users-groups/scim/](https://docs.databricks.com/aws/en/admin/users-groups/scim/)
- …and 7 more

### The Anthropic API reference was regenerated: union fields now name concrete Beta* schema types instead of 'object or object', the anthropic-beta header is rendered as an optional array of AnthropicBeta, and the collapsed beta-enum count moved from '41 more' to '43 more'.

`editorial` · reference-regeneration · 12 pages

This accounts for the bulk of the api/* churn in this run — shape and naming changes in the generated reference rather than behaviour changes. The enum count rising from 41 to 43 implies two additional beta identifiers in the collapsed list, which the pages do not name.

- [api/admin](https://platform.claude.com/docs/en/api/admin)
- [api/beta](https://platform.claude.com/docs/en/api/beta)
- [api/admin/organizations](https://platform.claude.com/docs/en/api/admin/organizations)
- [api/beta/organization](https://platform.claude.com/docs/en/api/beta/organization)
- [api/admin/analytics](https://platform.claude.com/docs/en/api/admin/analytics)
- [api/admin/federation_rules](https://platform.claude.com/docs/en/api/admin/federation_rules)
- …and 6 more

### PHP and other SDK samples across the guides were rewritten to use typed block checks (instanceof \Anthropic\Messages\TextBlock, match/array_find) instead of ad-hoc property tests.

`editorial` · example-refresh · 12 pages

Example style only; no API behaviour is described as changing.

- [about-claude/use-case-guides/content-moderation](https://platform.claude.com/docs/en/about-claude/use-case-guides/content-moderation)
- [test-and-evaluate/develop-tests](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests)
- [build-with-claude/cache-diagnostics](https://platform.claude.com/docs/en/build-with-claude/cache-diagnostics)
- [agents-and-tools/tool-use/tool-runner](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner)
- [build-with-claude/handling-stop-reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons)
- [models/sonnet-5/migration-guide](https://platform.claude.com/docs/en/models/sonnet-5/migration-guide)
- …and 6 more

### Roughly 4,800 Databricks pages were recorded as moved this run, a site-wide URL and navigation reshuffle spanning admin, SQL reference, PySpark reference, CLI reference, compute, security, ingestion, jobs and pipelines.

`editorial` · url-reorg · 10 pages

Content on these pages is unchanged; only their locations moved. Deep links into the affected sections should be re-checked.

- [admin/](https://docs.databricks.com/aws/en/admin/)
- [sql/language-manual/](https://docs.databricks.com/aws/en/sql/language-manual/)
- [pyspark/reference/](https://docs.databricks.com/aws/en/pyspark/reference/)
- [dev-tools/cli/reference/jobs-commands](https://docs.databricks.com/aws/en/dev-tools/cli/reference/jobs-commands)
- [release-notes/dlt/](https://docs.databricks.com/aws/en/release-notes/dlt/)
- [compute/](https://docs.databricks.com/aws/en/compute/)
- …and 4 more

### The MCP tunnels research-preview access request link changed from claude.com/form/claude-managed-agents to claude.com/form/mcp-tunnels across all nine tunnel pages.

`editorial` · link-change · 9 pages

The research-preview status itself is unchanged.

- [agents-and-tools/mcp-tunnels/concepts](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/concepts)
- [agents-and-tools/mcp-tunnels/console](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/console)
- [agents-and-tools/mcp-tunnels/deploy-compose](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/deploy-compose)
- [agents-and-tools/mcp-tunnels/deploy-helm](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/deploy-helm)
- [agents-and-tools/mcp-tunnels/overview](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/overview)
- [agents-and-tools/mcp-tunnels/quickstart](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/quickstart)
- …and 3 more

### Compliance API sample payloads now show UTC timestamps with a trailing Z (2025-03-12T18:22:41.123456Z) instead of bare microsecond timestamps.

`editorial` · example-change · 8 pages

Examples only; no field or format requirement is stated to have changed.

- [api/compliance/groups](https://platform.claude.com/docs/en/api/compliance/groups)
- [api/compliance/groups/list](https://platform.claude.com/docs/en/api/compliance/groups/list)
- [api/compliance/groups/retrieve](https://platform.claude.com/docs/en/api/compliance/groups/retrieve)
- [api/compliance/groups/members](https://platform.claude.com/docs/en/api/compliance/groups/members)
- [api/compliance/groups/members/list](https://platform.claude.com/docs/en/api/compliance/groups/members/list)
- [api/compliance/organizations/roles](https://platform.claude.com/docs/en/api/compliance/organizations/roles)
- …and 2 more

### Several admin delete/validate endpoints now show curl examples authenticating with -H "X-Api-Key: $ANTHROPIC_API_KEY" where they previously showed -H "Authorization: Bearer $ANTHROPIC_AUTH_TOKEN".

`editorial` · example-change · 6 pages

Only the sample requests changed; the pages do not state that either header stopped working.

- [api/admin/external_keys/delete](https://platform.claude.com/docs/en/api/admin/external_keys/delete)
- [api/admin/invites/delete](https://platform.claude.com/docs/en/api/admin/invites/delete)
- [api/admin/spend_limits/delete](https://platform.claude.com/docs/en/api/admin/spend_limits/delete)
- [api/admin/users/delete](https://platform.claude.com/docs/en/api/admin/users/delete)
- [api/admin/workspaces/members/delete](https://platform.claude.com/docs/en/api/admin/workspaces/members/delete)
- [api/admin/external_keys/validate](https://platform.claude.com/docs/en/api/admin/external_keys/validate)

### The materialized view refresh example now sets SET STATEMENT_TIMEOUT = 21600 (seconds) instead of the string '6h'.

`editorial` · example-fix · 1 page

- [ldp/dbsql/schedule-refreshes](https://docs.databricks.com/aws/en/ldp/dbsql/schedule-refreshes)
