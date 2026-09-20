# Change digest

> #6 (2026-09-09) → #7 (2026-09-18) · 6,329 changes · rendered 2026-09-20T19:26:32+00:00

## At a glance

68 findings — **7** breaking, **26** behavioural, **25** additive, **10** editorial — covering 404 of 6,329 changed pages. Anything not here is in the full feed report beside this file.

**If you read nothing else:**

1. Go SDK Files calls now take a params struct: `Files.Download(ctx, fileID, anthropic.FileDownloadParams{})` and `Files.GetMetadata(ctx, fileID, anthropic.FileGetMetadataParams{})`.
2. The partner-powered AI features toggle can no longer be turned off in the settings UI where it is enabled, and the setting is removed entirely on November 1, 2026.
3. Starting September 19, 2026, Anthropic models are removed from AWS GovCloud and AWS GovCloud DoD workspaces with DoD IL5 selected; affected endpoints must be migrated to another supported model.
4. The `--page-token` flag is gone from many Databricks CLI list commands, and `--max-results` is renamed `--limit` on some (for example `databricks tables list` and `workspace-bindings get-bindings`).
5. In serverless environment version 6 and above, `/databricks/runtime/info.json` is no longer available.
6. Lakebase scale to zero now requires the compute's maximum size to be 32 CU or smaller; larger computes can't use it, and setting a suspend timeout on a larger compute returns an error.
7. create_table and CREATE TABLE ... FLOW cannot adopt an existing managed table; the target must be a new managed table.

---

## Breaking — 7

### Go SDK Files calls now take a params struct: `Files.Download(ctx, fileID, anthropic.FileDownloadParams{})` and `Files.GetMetadata(ctx, fileID, anthropic.FileGetMetadataParams{})`.

`breaking` · sdk signature · 4 pages

Every Go example that downloaded a file or fetched metadata gained the extra trailing argument; the previous two-argument form appears only on the removed lines.

- [agents-and-tools/agent-skills/quickstart](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/quickstart)
- [build-with-claude/files](https://platform.claude.com/docs/en/build-with-claude/files)
- [build-with-claude/skills-guide](https://platform.claude.com/docs/en/build-with-claude/skills-guide)
- [agents-and-tools/tool-use/code-execution-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool)

### The partner-powered AI features toggle can no longer be turned off in the settings UI where it is enabled, and the setting is removed entirely on November 1, 2026.

`breaking` · setting removal · 2 pages

Until then, workspaces with the setting enabled see a disabled toggle and must use the Settings API to change it; workspaces where it is disabled can still enable it. After November 1, 2026 each workspace keeps its current value and changes require the Databricks account team.

- [databricks-ai/partner-powered](https://docs.databricks.com/aws/en/databricks-ai/partner-powered)
- [release-notes/product/](https://docs.databricks.com/aws/en/release-notes/product/)

### Starting September 19, 2026, Anthropic models are removed from AWS GovCloud and AWS GovCloud DoD workspaces with DoD IL5 selected; affected endpoints must be migrated to another supported model.

`breaking` · availability · 1 page

The page also now says IL5 controls are available on AWS GovCloud as well as GovCloud DoD, and moves serverless SQL warehouses there from Beta to Public Preview.

- [security/privacy/il5](https://docs.databricks.com/aws/en/security/privacy/il5)

### The `--page-token` flag is gone from many Databricks CLI list commands, and `--max-results` is renamed `--limit` on some (for example `databricks tables list` and `workspace-bindings get-bindings`).

`breaking` · cli flags · 24 pages

Both the flag documentation and the paginated examples were removed across account- and workspace-level list commands. Scripts that page explicitly with `--page-token`, or that pass `--max-results` to the renamed commands, need updating.

- [dev-tools/cli/reference/tables-commands](https://docs.databricks.com/aws/en/dev-tools/cli/reference/tables-commands)
- [dev-tools/cli/reference/catalogs-commands](https://docs.databricks.com/aws/en/dev-tools/cli/reference/catalogs-commands)
- [dev-tools/cli/reference/connections-commands](https://docs.databricks.com/aws/en/dev-tools/cli/reference/connections-commands)
- [dev-tools/cli/reference/external-locations-commands](https://docs.databricks.com/aws/en/dev-tools/cli/reference/external-locations-commands)
- [dev-tools/cli/reference/functions-commands](https://docs.databricks.com/aws/en/dev-tools/cli/reference/functions-commands)
- [dev-tools/cli/reference/providers-commands](https://docs.databricks.com/aws/en/dev-tools/cli/reference/providers-commands)
- …and 18 more

### In serverless environment version 6 and above, `/databricks/runtime/info.json` is no longer available.

`breaking` · removal · 1 page

The page adds a dedicated section for the removal; code that reads that file for runtime metadata will need another source.

- [release-notes/serverless/environment-version/six](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/six)

### Lakebase scale to zero now requires the compute's maximum size to be 32 CU or smaller; larger computes can't use it, and setting a suspend timeout on a larger compute returns an error.

`breaking` · restriction · 3 pages

The same 32 CU ceiling is stated on the autoscaling, scale-to-zero and manage-computes pages.

- [oltp/projects/scale-to-zero](https://docs.databricks.com/aws/en/oltp/projects/scale-to-zero)
- [oltp/projects/autoscaling](https://docs.databricks.com/aws/en/oltp/projects/autoscaling)
- [oltp/projects/manage-computes](https://docs.databricks.com/aws/en/oltp/projects/manage-computes)

### create_table and CREATE TABLE ... FLOW cannot adopt an existing managed table; the target must be a new managed table.

`breaking` · restriction · 2 pages

Added as an explicit limitation on both the Python and SQL references.

- [ldp/developer/ldp-python-ref-create-table](https://docs.databricks.com/aws/en/ldp/developer/ldp-python-ref-create-table)
- [ldp/developer/ldp-sql-ref-create-table-flow](https://docs.databricks.com/aws/en/ldp/developer/ldp-sql-ref-create-table-flow)

## Behavioural — 26

### File upload now documents that only the final path component of the multipart `filename` is kept, and an absent or empty filename is replaced with `unnamed`.

`behavioural` · upload handling · 4 pages

The same sentence was added to both the stable and beta Files upload references.

- [api/files](https://platform.claude.com/docs/en/api/files)
- [api/files/upload](https://platform.claude.com/docs/en/api/files/upload)
- [api/beta/files](https://platform.claude.com/docs/en/api/beta/files)
- [api/beta/files/upload](https://platform.claude.com/docs/en/api/beta/files/upload)

### With `drop_block`, the response now reports one dropped-block entry per thinking block in the history with a reason and its request position, and the guidance section is renamed "Keeping the prefix unchanged".

`behavioural` · thinking blocks · 5 pages

Previously the dropped count could be 0; pages that linked to "Preserved thinking" now point at "Keeping the prefix unchanged". Batch results describe where the removed block was, as `messages.{i}.content.{j}`.

- [build-with-claude/preserved-thinking](https://platform.claude.com/docs/en/build-with-claude/preserved-thinking)
- [api/errors](https://platform.claude.com/docs/en/api/errors)
- [build-with-claude/context-editing](https://platform.claude.com/docs/en/build-with-claude/context-editing)
- [api/beta/messages/batches/results](https://platform.claude.com/docs/en/api/beta/messages/batches/results)
- [build-with-claude/thinking-troubleshooting](https://platform.claude.com/docs/en/build-with-claude/thinking-troubleshooting)

### With `display: "omitted"` on the thinking configuration, the docs now say no thinking text is streamed (previously phrased as no `thinking_delta` events being sent).

`behavioural` · streaming · 1 page

The thinking block still opens and receives events; the wording change narrows what is suppressed.

- [build-with-claude/streaming](https://platform.claude.com/docs/en/build-with-claude/streaming)

### The token-counting endpoint now documents inputs it rejects that the Messages API accepts, including server tools and images supplied by URL or file ID.

`behavioural` · endpoint limits · 2 pages

Token counting returns an `invalid_request_error` for those inputs; for vision coordinates, a marked image supplied by URL or file ID is checked only at Messages time because counting does not fetch it.

- [build-with-claude/token-counting](https://platform.claude.com/docs/en/build-with-claude/token-counting)
- [build-with-claude/vision-coordinates](https://platform.claude.com/docs/en/build-with-claude/vision-coordinates)

### The minimum accepted `task_budget.total` is now stated as a flat 20,000 tokens on every model that supports task budgets, replacing "model-specific".

`behavioural` · limit · 1 page

Readers who relied on a lower per-model floor should check their configured budget against the stated minimum.

- [build-with-claude/task-budgets](https://platform.claude.com/docs/en/build-with-claude/task-budgets)

### Under customer-managed encryption keys, Claude Code on the web (including routines) and Claude in Slack are unavailable and chat search is disabled.

`behavioural` · restriction · 1 page

The page states new sessions cannot be started, Claude in Slack declines, and members cannot search past chats because titles and content are encrypted under your key.

- [manage-claude/cmek](https://platform.claude.com/docs/en/manage-claude/cmek)

### Permission policies now state that a tool call the server cannot reach a judgement on evaluates to `ask`.

`behavioural` · tool permissions · 4 pages

The same sentence propagated through the Agents and Sessions API schema text. The page also says a denied call keeps the session running and the client cannot override the denial.

- [managed-agents/permission-policies](https://platform.claude.com/docs/en/managed-agents/permission-policies)
- [api/beta/agents](https://platform.claude.com/docs/en/api/beta/agents)
- [api/beta/sessions](https://platform.claude.com/docs/en/api/beta/sessions)
- [api/beta/sessions/threads](https://platform.claude.com/docs/en/api/beta/sessions/threads)

### The top-level `workspace_id` on API key objects is deprecated in favour of `scope`, which reports the workspace's real ID even for the default workspace.

`behavioural` · deprecation · 4 pages

`scope` is documented as `BetaAPIKeyOrganizationScope or BetaAPIKeyWorkspaceScope`; the deprecated field is `null` when the key belongs to the default workspace.

- [api/admin/api_keys](https://platform.claude.com/docs/en/api/admin/api_keys)
- [api/admin/api_keys/list](https://platform.claude.com/docs/en/api/admin/api_keys/list)
- [api/admin/api_keys/retrieve](https://platform.claude.com/docs/en/api/admin/api_keys/retrieve)
- [api/admin/api_keys/update](https://platform.claude.com/docs/en/api/admin/api_keys/update)

### The inference hooks endpoint page now documents request body size limits and says a rejected body counts as a webhook failure.

`behavioural` · limits · 1 page

It calls out common framework defaults (`body-parser` at 1 MB, Express `express.json()` at 100 kB) and that enabling inference hooks requires a secret, so unsigned requests are rejected.

- [manage-claude/inference-hooks-endpoint](https://platform.claude.com/docs/en/manage-claude/inference-hooks-endpoint)

### AI Runtime tutorials now tell you to select the AI v6 environment instead of AI v5, and the GPU environment ships Serverless GPU Python API 0.5.25.

`behavioural` · version bump · 14 pages

Several examples now state they require Databricks AI environment version 6 or above.

- [machine-learning/ai-runtime/examples/tutorials/sgc-distributed-pytorch-fsdp](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-distributed-pytorch-fsdp)
- [machine-learning/ai-runtime/examples/tutorials/sgc-sft-trl-deepspeed-llama-1b](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-sft-trl-deepspeed-llama-1b)
- [machine-learning/ai-runtime/examples/tutorials/sgc-recommender-system-lightning](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-recommender-system-lightning)
- [machine-learning/ai-runtime/examples/tutorials/sgc-api-h100-starter](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-api-h100-starter)
- [machine-learning/ai-runtime/examples/tutorials/sgc-distributed-gpt-oss-20b](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-distributed-gpt-oss-20b)
- [machine-learning/ai-runtime/examples/tutorials/sgc-finetune-qwen3-4b](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-finetune-qwen3-4b)
- …and 8 more

### Databricks Runtime 18.1 (and 18.1 ML) and 13.3 LTS ML are now marked end-of-support, and their maintenance-update links were repointed to the maintenance-updates archive.

`behavioural` · end of support · 12 pages

Release-note references across 2025 and 2026 now read (EoS) and link to maintenance-updates-archive.

- [release-notes/runtime/18.1](https://docs.databricks.com/aws/en/release-notes/runtime/18.1)
- [release-notes/runtime/18.1ml](https://docs.databricks.com/aws/en/release-notes/runtime/18.1ml)
- [release-notes/runtime/13.3lts-ml](https://docs.databricks.com/aws/en/release-notes/runtime/13.3lts-ml)
- [release-notes/runtime/13.3lts](https://docs.databricks.com/aws/en/release-notes/runtime/13.3lts)
- [release-notes/gov-cloud/2026](https://docs.databricks.com/aws/en/release-notes/gov-cloud/2026)
- [release-notes/product/2026/february](https://docs.databricks.com/aws/en/release-notes/product/2026/february)
- …and 6 more

### Kimi K2.7 pay-per-token is scheduled for retirement on October 30, 2026, with Kimi K3 named as the replacement.

`behavioural` · deprecation · 1 page

Added to the retired-models schedule table.

- [machine-learning/retired-models-policy](https://docs.databricks.com/aws/en/machine-learning/retired-models-policy)

### Genie Agent file upload now documents a limit of 100 pages per PDF.

`behavioural` · limit · 1 page

The page also drops its previous note that the upload option is hidden without at least CAN RUN permission.

- [genie-agents/file-upload](https://docs.databricks.com/aws/en/genie-agents/file-upload)

### Scheduled notebook jobs moved from Beta to Public Preview, and the note about workspace admins controlling access was dropped.

`behavioural` · preview transition · 1 page

Status banner change only.

- [notebooks/schedule-notebook-jobs](https://docs.databricks.com/aws/en/notebooks/schedule-notebook-jobs)

### Zerobus writing to liquid clustered tables is now Generally Available; the Beta labels were removed across the Zerobus pages.

`behavioural` · ga transition · 4 pages

The C# / .NET SDK remains in Beta.

- [ingestion/zerobus-release-stages](https://docs.databricks.com/aws/en/ingestion/zerobus-release-stages)
- [ingestion/zerobus-quotas](https://docs.databricks.com/aws/en/ingestion/zerobus-quotas)
- [ingestion/zerobus-features](https://docs.databricks.com/aws/en/ingestion/zerobus-features)
- [ingestion/zerobus-ingest](https://docs.databricks.com/aws/en/ingestion/zerobus-ingest)

### The SQL Server integrated CDC pipeline page no longer lists the Beta workspace-enablement requirement or the "channel": "PREVIEW" pipeline-spec requirement.

`behavioural` · availability · 1 page

The SQL Server overview comparison table still labels integrated CDC as Beta.

- [ingestion/lakeflow-connect/sql-server-integrated-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/sql-server-integrated-pipeline)

### Unity Catalog thread-pool guidance was rewritten: on dedicated compute, workloads accessing Unity Catalog data must use a supported thread pool in org.apache.spark.util.ThreadUtils, and the JAR task page now enumerates the unsupported ones.

`behavioural` · restriction · 2 pages

The JAR page names ForkJoinPool, Scala parallel collections such as .par, and ThreadUtils.newForkJoinPool as unsupported.

- [data-governance/unity-catalog/requirements](https://docs.databricks.com/aws/en/data-governance/unity-catalog/requirements)
- [jobs/tasks/jar-create](https://docs.databricks.com/aws/en/jobs/tasks/jar-create)

### Deleting a workspace now removes that workspace's audit events older than 14 days from system.access.audit.

`behavioural` · retention · 1 page

Teams that rely on historical audit data for decommissioned workspaces should export before deletion.

- [admin/system-tables/audit-logs](https://docs.databricks.com/aws/en/admin/system-tables/audit-logs)

### The FILE type now requires serverless environment version 6 or above, replacing the previous statement that it isn't supported on serverless notebooks.

`behavioural` · requirement · 4 pages

The docs also now state that a UDF registered in Unity Catalog (CREATE FUNCTION) can read a FILE's metadata but not its contents, and cannot create files.

- [sql/language-manual/data-types/file-type](https://docs.databricks.com/aws/en/sql/language-manual/data-types/file-type)
- [pyspark/reference/file-type](https://docs.databricks.com/aws/en/pyspark/reference/file-type)
- [udf/python](https://docs.databricks.com/aws/en/udf/python)
- [unstructured/file-udfs](https://docs.databricks.com/aws/en/unstructured/file-udfs)

### The 2.0/jobs/list endpoint is now marked deprecated, with Jobs API 2.2 recommended instead.

`behavioural` · deprecation · 1 page

An Important callout was added to the Jobs 2.0 API reference.

- [reference/jobs-2.0-api](https://docs.databricks.com/aws/en/reference/jobs-2.0-api)

### Private access to account-level resources and workspace private access via context-based ingress now require explicitly enabling named Beta previews.

`behavioural` · beta gating · 4 pages

The pages name the Front-end Private Link for Custom URLs and Account preview and the Context-Based Ingress: Workspace Private Access Policies preview, and warn that requests are rejected until registration completes.

- [security/network/classic/privatelink-dns](https://docs.databricks.com/aws/en/security/network/classic/privatelink-dns)
- [security/network/front-end/front-end-private-connect-account](https://docs.databricks.com/aws/en/security/network/front-end/front-end-private-connect-account)
- [security/network/front-end/front-end-private-connect](https://docs.databricks.com/aws/en/security/network/front-end/front-end-private-connect)
- [security/network/front-end/service-direct-privatelink](https://docs.databricks.com/aws/en/security/network/front-end/service-direct-privatelink)

### Account console identity settings moved to an Identity provider setup tab, and SSO configuration is now saved in a disabled state until you click Enable SSO, which runs a connection test.

`behavioural` · console change · 20 pages

SCIM provisioning, automatic identity management, JIT provisioning and token regeneration are all reached through the new tab; just-in-time provisioning is enabled after SSO is turned on.

- [security/auth/single-sign-on/okta](https://docs.databricks.com/aws/en/security/auth/single-sign-on/okta)
- [security/auth/single-sign-on/azure-ad](https://docs.databricks.com/aws/en/security/auth/single-sign-on/azure-ad)
- [security/auth/single-sign-on/saml](https://docs.databricks.com/aws/en/security/auth/single-sign-on/saml)
- [security/auth/single-sign-on/oidc](https://docs.databricks.com/aws/en/security/auth/single-sign-on/oidc)
- [security/auth/single-sign-on/jumpcloud](https://docs.databricks.com/aws/en/security/auth/single-sign-on/jumpcloud)
- [security/auth/single-sign-on/keycloak](https://docs.databricks.com/aws/en/security/auth/single-sign-on/keycloak)
- …and 14 more

### Reading the change data feed on Databricks Runtime 15.4 LTS and above now returns _commit_timestamp in the session time zone.

`behavioural` · behaviour change · 1 page

Added as a named behaviour-change entry in the 15.4 LTS notes.

- [release-notes/runtime/15.4lts](https://docs.databricks.com/aws/en/release-notes/runtime/15.4lts)

### DROP TABLE docs now describe drop-time protection for base tables referenced by shallow clones, where FORCE is required and a plain drop fails with CANNOT_DROP_BASE_TABLE_REFERENCED_BY_SHALLOW_CLONE.

`behavioural` · drop protection · 6 pages

The pages also clarify that after the recovery window an asynchronous purge permanently deletes data files, and that shallow clones can keep reading for a time after the base table is no longer recoverable.

- [sql/language-manual/sql-ref-syntax-ddl-drop-table](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-ddl-drop-table)
- [tables/operations/clone-unity-catalog](https://docs.databricks.com/aws/en/tables/operations/clone-unity-catalog)
- [tables/operations/drop-table](https://docs.databricks.com/aws/en/tables/operations/drop-table)
- [tables/managed](https://docs.databricks.com/aws/en/tables/managed)
- [data-governance/unity-catalog/object-storage-lifecycle](https://docs.databricks.com/aws/en/data-governance/unity-catalog/object-storage-lifecycle)
- [sql/language-manual/sql-ref-syntax-aux-show-tables-dropped](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-aux-show-tables-dropped)

### Automatic Git deployments for Databricks Apps lost their Beta label, and Databricks Apps is now on by default for workspaces with the compliance security profile enabled.

`behavioural` · ga transition · 5 pages

The previous requirement that a workspace admin enable Databricks Apps from the Previews page for compliance-security-profile workspaces was removed.

- [dev-tools/databricks-apps/deploy](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/deploy)
- [dev-tools/databricks-apps/cicd-github-actions](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/cicd-github-actions)
- [dev-tools/databricks-apps/get-started](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/get-started)
- [dev-tools/databricks-apps/](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/)
- [security/privacy/security-profile](https://docs.databricks.com/aws/en/security/privacy/security-profile)

### Using a catalog backed by default storage for AI Gateway inference tables or the unified trace table requires a workspace admin to enable the Zerobus Ingest Default Storage preview.

`behavioural` · requirement · 2 pages

The previous requirement that the catalog be an external storage catalog with CREATE TABLE privileges was reworked.

- [ai-gateway/inference-tables](https://docs.databricks.com/aws/en/ai-gateway/inference-tables)
- [ai-gateway/unified-trace-table](https://docs.databricks.com/aws/en/ai-gateway/unified-trace-table)

## Additive — 25

### Tool names may now be up to 128 characters; the documented regex changed from `^[a-zA-Z0-9_-]{1,64}$` to `^[a-zA-Z0-9_-]{1,128}$`.

`additive` · limit change · 2 pages

Both the tool-definition reference and the API primer table now state the longer bound. Names that were already valid remain valid.

- [agents-and-tools/tool-use/define-tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools)
- [claude_api_primer](https://platform.claude.com/docs/en/claude_api_primer)

### The Messages API can now compact a conversation on demand, and the Models API exposes a per-model `compaction` capability.

`additive` · feature · 5 pages

The compaction guide was substantially expanded with on-demand compaction, and notes that if the last `assistant` turn ends in a tool call with no result yet the API rejects the request — send that turn's tool results first. Model objects now carry `compaction: BetaCompactionCapability or null`.

- [build-with-claude/compaction](https://platform.claude.com/docs/en/build-with-claude/compaction)
- [release-notes/overview](https://platform.claude.com/docs/en/release-notes/overview)
- [api/beta/models](https://platform.claude.com/docs/en/api/beta/models)
- [api/beta/models/list](https://platform.claude.com/docs/en/api/beta/models/list)
- [api/beta/models/retrieve](https://platform.claude.com/docs/en/api/beta/models/retrieve)

### The `ant` CLI adds `ant beta:sessions connect` for attaching a terminal to a Managed Agents session, and the quickstart pins VERSION 1.33.0 (was 1.30.0).

`additive` · tooling · 3 pages

A new reference page documents following a session transcript live, sending messages, allowing or denying tool calls, and opening the session viewer.

- [cli-sdks-libraries/cli/sessions-connect](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/sessions-connect)
- [cli-sdks-libraries/cli/quickstart](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/quickstart)
- [release-notes/overview](https://platform.claude.com/docs/en/release-notes/overview)

### Java platform SDK examples bump `anthropic-java-vertex`, `-bedrock` and `-foundry` from 2.60.0 to 2.63.0.

`additive` · version bump · 4 pages

Gradle/Maven snippets on all four cloud-platform pages were updated together.

- [build-with-claude/claude-on-vertex-ai](https://platform.claude.com/docs/en/build-with-claude/claude-on-vertex-ai)
- [build-with-claude/claude-in-amazon-bedrock](https://platform.claude.com/docs/en/build-with-claude/claude-in-amazon-bedrock)
- [build-with-claude/claude-in-microsoft-foundry](https://platform.claude.com/docs/en/build-with-claude/claude-in-microsoft-foundry)
- [build-with-claude/claude-on-amazon-bedrock-legacy](https://platform.claude.com/docs/en/build-with-claude/claude-on-amazon-bedrock-legacy)

### Files, Skills and Message Batches reference pages now document an optional `anthropic-workspace-id` header.

`additive` · header · 18 pages

A Headers section listing `"anthropic-workspace-id": optional string` was added to these endpoints.

- [api/files/delete](https://platform.claude.com/docs/en/api/files/delete)
- [api/files/download](https://platform.claude.com/docs/en/api/files/download)
- [api/files/list](https://platform.claude.com/docs/en/api/files/list)
- [api/files/retrieve_metadata](https://platform.claude.com/docs/en/api/files/retrieve_metadata)
- [api/skills](https://platform.claude.com/docs/en/api/skills)
- [api/skills/create](https://platform.claude.com/docs/en/api/skills/create)
- …and 12 more

### Mid-conversation system messages (`mid-conversation-output-config-2026-07-01`) are now documented on Google Cloud in addition to the Claude API.

`additive` · availability · 1 page

The beta remains scoped to Claude Fable 5.1, Claude Mythos 5.1 and Claude Opus 5.

- [build-with-claude/mid-conversation-system-messages](https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages)

### The Opus 5 migration guide now lists Claude Platform on AWS among the platforms where the 1M context window is the default and the context-window beta header should be removed.

`additive` · availability · 1 page

The list previously named the Claude API, Amazon Bedrock, Google Cloud and Microsoft Foundry.

- [models/opus-5/migration-guide](https://platform.claude.com/docs/en/models/opus-5/migration-guide)

### The beta organization namespace gained documented endpoints for analytics, cost and usage reports, MCP tunnels and certificates, RBAC groups and roles, and spend limits.

`additive` · new endpoints · 17 pages

These mirror the corresponding Admin API sections and are new pages in this run.

- [api/beta/organization/analytics](https://platform.claude.com/docs/en/api/beta/organization/analytics)
- [api/beta/organization/analytics/usage](https://platform.claude.com/docs/en/api/beta/organization/analytics/usage)
- [api/beta/organization/analytics/cost](https://platform.claude.com/docs/en/api/beta/organization/analytics/cost)
- [api/beta/organization/analytics/users](https://platform.claude.com/docs/en/api/beta/organization/analytics/users)
- [api/beta/organization/analytics/connectors](https://platform.claude.com/docs/en/api/beta/organization/analytics/connectors)
- [api/beta/organization/analytics/skills](https://platform.claude.com/docs/en/api/beta/organization/analytics/skills)
- …and 11 more

### A new commerce-agents use-case guide covers building shopping and merchant agents on the Messages API, the Agent SDK and Managed Agents.

`additive` · new guide · 2 pages

The use-case guides index now lists it alongside the existing paths for building with Claude.

- [about-claude/use-case-guides/commerce-agents](https://platform.claude.com/docs/en/about-claude/use-case-guides/commerce-agents)
- [about-claude/use-case-guides/overview](https://platform.claude.com/docs/en/about-claude/use-case-guides/overview)

### Compliance organization settings gained `access_transparency_enabled` (enum grew from 52 to 57 more values) and the organization role enum grew from 6 to 8 more values.

`additive` · enum growth · 5 pages

Clients that switch exhaustively on these enums should handle the new members.

- [api/compliance/organizations](https://platform.claude.com/docs/en/api/compliance/organizations)
- [api/compliance/organizations/settings](https://platform.claude.com/docs/en/api/compliance/organizations/settings)
- [api/compliance/organizations/settings/retrieve](https://platform.claude.com/docs/en/api/compliance/organizations/settings/retrieve)
- [api/compliance/organizations/users](https://platform.claude.com/docs/en/api/compliance/organizations/users)
- [api/compliance/organizations/users/list](https://platform.claude.com/docs/en/api/compliance/organizations/users/list)

### New Databricks pages landed for AI Runtime (overview, quickstart, productionizing training workloads, a TabFM tutorial), a Databricks Sandbox SDK usage guide, and a Data Classification release-notes feed.

`additive` · new pages · 6 pages

The AI Runtime overview and quickstart are new entry points for serverless GPU compute.

- [machine-learning/ai-runtime/overview](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/overview)
- [machine-learning/ai-runtime/quickstart](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/quickstart)
- [machine-learning/ai-runtime/productionizing-training-workloads](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/productionizing-training-workloads)
- [machine-learning/ai-runtime/examples/tutorials/sgc-tabfm](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/examples/tutorials/sgc-tabfm)
- [compute/serverless/sandbox-usage-guide](https://docs.databricks.com/aws/en/compute/serverless/sandbox-usage-guide)
- [release-notes/data-classification/](https://docs.databricks.com/aws/en/release-notes/data-classification/)

### DeepSeek V4.1 Flash is available on Databricks Foundation Model APIs, with entries in the supported-models, limits, function-calling, vision and licence tables.

`additive` · new model · 8 pages

It is described as a multimodal mixture-of-experts model with 552 billion backbone parameters, supports adjustable reasoning effort, and has a 200,000-token context with 10,000 output tokens and 7,200 queries per minute.

- [machine-learning/foundation-model-apis/supported-models](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/supported-models)
- [machine-learning/foundation-model-apis/limits](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/limits)
- [machine-learning/foundation-model-apis/priority-mode](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/priority-mode)
- [machine-learning/model-serving/function-calling](https://docs.databricks.com/aws/en/machine-learning/model-serving/function-calling)
- [machine-learning/model-serving/query-vision-models](https://docs.databricks.com/aws/en/machine-learning/model-serving/query-vision-models)
- [machine-learning/model-serving/acceptable-use-models](https://docs.databricks.com/aws/en/machine-learning/model-serving/acceptable-use-models)
- …and 2 more

### Genie Agents now accept up to 50 tables, views or metric views per agent (was 30) and a 200,000-conversation limit (was 10,000).

`additive` · limit change · 3 pages

Best-practice guidance to prejoin related tables now kicks in above 50 tables rather than 30.

- [genie-agents/set-up](https://docs.databricks.com/aws/en/genie-agents/set-up)
- [genie-agents/best-practices](https://docs.databricks.com/aws/en/genie-agents/best-practices)
- [genie-agents/conversation-api](https://docs.databricks.com/aws/en/genie-agents/conversation-api)

### Unity Catalog ABAC adds DENY policies (Beta) and metastore-level policy attachment, so one row filter, column mask, GRANT or DENY policy can apply across every catalog.

`additive` · feature · 9 pages

A new metastore-policies page was added; ON { METASTORE | CATALOG | SCHEMA } is now documented for GRANT and DENY, dropping a metastore-scoped policy requires metastore admin, and creating or dropping a DENY policy with SQL requires Databricks Runtime 18 LTS or above.

- [data-governance/unity-catalog/abac/metastore-policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/metastore-policies)
- [data-governance/unity-catalog/abac/deny-policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/deny-policies)
- [data-governance/unity-catalog/abac/grant-policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/grant-policies)
- [data-governance/unity-catalog/abac/](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/)
- [data-governance/unity-catalog/abac/requirements](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/requirements)
- [data-governance/unity-catalog/abac/core-concepts](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/core-concepts)
- …and 3 more

### Lakeflow Connect gained managed connectors for Anaplan, Atlassian Audit Logs, Anysphere Organization, Celigo and Google Workspace, each with full setup, pipeline, reference and troubleshooting pages.

`additive` · new connectors · 14 pages

Google Workspace ingests activity events from 33 application audit logs; Celigo and Atlassian ingest audit log events; Anaplan covers audit trail events and user accounts.

- [ingestion/lakeflow-connect/anaplan](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anaplan)
- [ingestion/lakeflow-connect/anaplan-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anaplan-pipeline)
- [ingestion/lakeflow-connect/anaplan-source-setup](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anaplan-source-setup)
- [ingestion/lakeflow-connect/atlassian-audit-logs](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/atlassian-audit-logs)
- [ingestion/lakeflow-connect/atlassian-audit-logs-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/atlassian-audit-logs-pipeline)
- [ingestion/lakeflow-connect/anysphere-organization](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/anysphere-organization)
- …and 8 more

### Google Drive connector authentication was split into three pages: Databricks-managed OAuth U2M (no Google Cloud project or app registration), custom-managed OAuth U2M, and an OAuth service account.

`additive` · restructure · 9 pages

The connection, pipeline, FAQ and troubleshooting pages were rewritten to route readers to the right method; the older standalone Google Drive ingestion page now points at the managed connector.

- [ingestion/lakeflow-connect/google-drive-source-setup-u2m-databricks-managed](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/google-drive-source-setup-u2m-databricks-managed)
- [ingestion/lakeflow-connect/google-drive-source-setup-u2m](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/google-drive-source-setup-u2m)
- [ingestion/lakeflow-connect/google-drive-source-setup-service-account](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/google-drive-source-setup-service-account)
- [ingestion/lakeflow-connect/google-drive-source-setup](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/google-drive-source-setup)
- [ingestion/lakeflow-connect/google-drive-connection](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/google-drive-connection)
- [ingestion/lakeflow-connect/google-drive-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/google-drive-pipeline)
- …and 3 more

### The SharePoint connector can now ingest SharePoint lists as structured Delta tables (Beta), with LIST ingestion requiring only entity_type and url.

`additive` · feature · 4 pages

Documented limits: list attachments are not supported, UI-based authoring is not supported for list ingestion, and the pipeline spec uses channel: PREVIEW.

- [ingestion/lakeflow-connect/sharepoint-limits](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/sharepoint-limits)
- [ingestion/lakeflow-connect/sharepoint-reference](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/sharepoint-reference)
- [ingestion/lakeflow-connect/sharepoint-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/sharepoint-pipeline)
- [ingestion/sharepoint](https://docs.databricks.com/aws/en/ingestion/sharepoint)

### Lakeflow pipelines gained flow ordering with depends_on (Public Preview), a rewind capability, and maintenance windows for continuous pipelines.

`additive` · feature · 9 pages

depends_on names flows that must finish before a flow starts. Rewind requires a pipeline on the Preview channel with pipelines.rewind.betaEnabled set plus supported sources and sinks. Maintenance windows are configured on the job running a continuous pipeline, with new maintenance start and complete notifications.

- [ldp/flows-depends-on](https://docs.databricks.com/aws/en/ldp/flows-depends-on)
- [ldp/rewind](https://docs.databricks.com/aws/en/ldp/rewind)
- [ldp/maintenance-windows](https://docs.databricks.com/aws/en/ldp/maintenance-windows)
- [ldp/developer/ldp-python-ref-append-flow](https://docs.databricks.com/aws/en/ldp/developer/ldp-python-ref-append-flow)
- [ldp/developer/ldp-python-ref-update-flow](https://docs.databricks.com/aws/en/ldp/developer/ldp-python-ref-update-flow)
- [ldp/recover-streaming](https://docs.databricks.com/aws/en/ldp/recover-streaming)
- …and 3 more

### Metric view window measures gained offset, which requires YAML specification version 1.1 or above; unitless numeric offset and range on a consecutive integer index column require Databricks Runtime 19 or above.

`additive` · feature · 4 pages

The level-of-detail page also states outer_aggregate must be a single-argument aggregate (SUM, AVG, MIN, MAX, COUNT, MEDIAN), and COUNT(DISTINCT ...) is called out as not qualifying.

- [uc-semantics/metric-views/yaml-reference](https://docs.databricks.com/aws/en/uc-semantics/metric-views/yaml-reference)
- [uc-semantics/metric-views/feature-availability](https://docs.databricks.com/aws/en/uc-semantics/metric-views/feature-availability)
- [uc-semantics/metric-views/advanced-techniques](https://docs.databricks.com/aws/en/uc-semantics/metric-views/advanced-techniques)
- [uc-semantics/metric-views/level-of-detail](https://docs.databricks.com/aws/en/uc-semantics/metric-views/level-of-detail)

### Databricks now recommends context-based ingress over workspace IP access lists and added a migration page for the Databricks Labs migrate-ip-acls CLI tool.

`additive` · migration · 6 pages

Ingress policies gained optional API scope selection, and context-based ingress is documented as requiring the Enterprise tier.

- [security/network/front-end/migrate-to-context-based-ingress](https://docs.databricks.com/aws/en/security/network/front-end/migrate-to-context-based-ingress)
- [security/network/front-end/ip-access-list-workspace](https://docs.databricks.com/aws/en/security/network/front-end/ip-access-list-workspace)
- [security/network/front-end/ip-access-list](https://docs.databricks.com/aws/en/security/network/front-end/ip-access-list)
- [security/network/front-end/context-based-ingress](https://docs.databricks.com/aws/en/security/network/front-end/context-based-ingress)
- [security/network/context-based-policies](https://docs.databricks.com/aws/en/security/network/context-based-policies)
- [security/network/front-end/manage-ingress-policies](https://docs.databricks.com/aws/en/security/network/front-end/manage-ingress-policies)

### OpenSharing shareable views can now be defined on foreign tables, and sharing foreign schemas and tables is generally available.

`additive` · feature · 4 pages

Sharing foreign Iceberg tables with open recipients that don't use Iceberg clients requires default storage. A shared FeatureSpec or model and all its dependencies must be in the same share.

- [opensharing/](https://docs.databricks.com/aws/en/opensharing/)
- [opensharing/create-share](https://docs.databricks.com/aws/en/opensharing/create-share)
- [opensharing/read-data-databricks](https://docs.databricks.com/aws/en/opensharing/read-data-databricks)
- [release-notes/product/](https://docs.databricks.com/aws/en/release-notes/product/)

### Two new SQL functions are documented: ai_transcribe (Beta), which transcribes audio into time-stamped, speaker-labelled segments, and the counter_diff analytic window function.

`additive` · new functions · 5 pages

counter_diff converts consecutive cumulative counter values into per-row deltas; both appear in the built-in function indexes.

- [sql/language-manual/functions/ai_transcribe](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_transcribe)
- [large-language-models/ai-functions](https://docs.databricks.com/aws/en/large-language-models/ai-functions)
- [sql/language-manual/sql-ref-functions-builtin](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-functions-builtin)
- [sql/language-manual/sql-ref-functions-builtin-alpha](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-functions-builtin-alpha)
- [release-notes/product/2026/august](https://docs.databricks.com/aws/en/release-notes/product/2026/august)

### Databricks Sandbox documents explicit lifecycle and customisation limits, and the serverless migration agent now reports a blocker and stops when it cannot safely migrate something.

`additive` · feature · 2 pages

You must delete a sandbox to stop paying for storage, and you cannot customise the environment at startup or persist an environment outside your home directory.

- [compute/serverless/sandbox](https://docs.databricks.com/aws/en/compute/serverless/sandbox)
- [compute/serverless/migration](https://docs.databricks.com/aws/en/compute/serverless/migration)

### Genie One documents an account-only experience for users in a registered identity provider who aren't assigned to a workspace, plus personalized starter questions on the home page.

`additive` · feature · 5 pages

A new page covers what account-only users can do and how account admins manage their access, data permissions and compute. Genie One also now asks you to confirm before saving a memory, and changing a connection's permissions requires each user to re-authenticate.

- [genie-one/](https://docs.databricks.com/aws/en/genie-one/)
- [genie-one/account-only-user-access](https://docs.databricks.com/aws/en/genie-one/account-only-user-access)
- [genie-one/customize-genie-homepage](https://docs.databricks.com/aws/en/genie-one/customize-genie-homepage)
- [genie-one/chat](https://docs.databricks.com/aws/en/genie-one/chat)
- [genie-one/external-sources](https://docs.databricks.com/aws/en/genie-one/external-sources)

### Lakehouse Federation adds AWS IAM authentication for Amazon Redshift, and the MySQL and PostgreSQL IAM pages clarify that only a single IAM role is needed, in the account where the instance runs.

`additive` · feature · 4 pages

The Redshift IAM page is new in this run.

- [query-federation/redshift-iam](https://docs.databricks.com/aws/en/query-federation/redshift-iam)
- [query-federation/redshift](https://docs.databricks.com/aws/en/query-federation/redshift)
- [query-federation/mysql-iam](https://docs.databricks.com/aws/en/query-federation/mysql-iam)
- [query-federation/postgresql-iam](https://docs.databricks.com/aws/en/query-federation/postgresql-iam)

## Editorial — 10

### The Compliance API 403 scope error message format changed from `Needed: [...]` to `Needed one of: [...]`.

`editorial` · error message · 1 page

Clients that string-match the message body should be re-checked.

- [manage-claude/compliance-api-access](https://platform.claude.com/docs/en/manage-claude/compliance-api-access)

### The MCP tunnels research-preview access request link moved from claude.com/form/claude-managed-agents to claude.com/form/mcp-tunnels.

`editorial` · link change · 9 pages

Same banner, new form; the preview status itself is unchanged.

- [agents-and-tools/mcp-tunnels/concepts](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/concepts)
- [agents-and-tools/mcp-tunnels/console](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/console)
- [agents-and-tools/mcp-tunnels/deploy-compose](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/deploy-compose)
- [agents-and-tools/mcp-tunnels/deploy-helm](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/deploy-helm)
- [agents-and-tools/mcp-tunnels/overview](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/overview)
- [agents-and-tools/mcp-tunnels/quickstart](https://platform.claude.com/docs/en/agents-and-tools/mcp-tunnels/quickstart)
- …and 3 more

### Managed Agents pages replaced the prose beta-header callout with a metadata block stating `Status: Beta` and the required beta header (`managed-agents-2026-04-01`, or `agent-memory-2026-07-22` on the memory page).

`editorial` · restructure · 25 pages

The header requirement itself is unchanged; only its presentation moved.

- [managed-agents/overview](https://platform.claude.com/docs/en/managed-agents/overview)
- [managed-agents/agent-setup](https://platform.claude.com/docs/en/managed-agents/agent-setup)
- [managed-agents/budgets](https://platform.claude.com/docs/en/managed-agents/budgets)
- [managed-agents/cloud-sandboxes-reference](https://platform.claude.com/docs/en/managed-agents/cloud-sandboxes-reference)
- [managed-agents/environments](https://platform.claude.com/docs/en/managed-agents/environments)
- [managed-agents/github](https://platform.claude.com/docs/en/managed-agents/github)
- …and 19 more

### Compliance API curl examples now include the `anthropic-version: 2023-06-01` header.

`editorial` · examples · 11 pages

Added across the compliance reference; the examples previously sent only the compliance API key.

- [api/compliance/apps/artifacts](https://platform.claude.com/docs/en/api/compliance/apps/artifacts)
- [api/compliance/apps/artifacts/download](https://platform.claude.com/docs/en/api/compliance/apps/artifacts/download)
- [api/compliance/apps/artifacts/retrieve](https://platform.claude.com/docs/en/api/compliance/apps/artifacts/retrieve)
- [api/compliance/apps/chats/delete](https://platform.claude.com/docs/en/api/compliance/apps/chats/delete)
- [api/compliance/apps/chats/files](https://platform.claude.com/docs/en/api/compliance/apps/chats/files)
- [api/compliance/apps/projects](https://platform.claude.com/docs/en/api/compliance/apps/projects)
- …and 5 more

### Several Admin API curl examples now use `-H "X-Api-Key: $ANTHROPIC_API_KEY"` instead of `-H "Authorization: Bearer $ANTHROPIC_AUTH_TOKEN"`.

`editorial` · examples · 6 pages

Only the sample auth header changed; the surrounding request shape is the same, and returned-field ordering was also reshuffled on these pages.

- [api/admin/users/delete](https://platform.claude.com/docs/en/api/admin/users/delete)
- [api/admin/invites/delete](https://platform.claude.com/docs/en/api/admin/invites/delete)
- [api/admin/spend_limits/delete](https://platform.claude.com/docs/en/api/admin/spend_limits/delete)
- [api/admin/external_keys/delete](https://platform.claude.com/docs/en/api/admin/external_keys/delete)
- [api/admin/workspaces/members/delete](https://platform.claude.com/docs/en/api/admin/workspaces/members/delete)
- [api/admin/external_keys/validate](https://platform.claude.com/docs/en/api/admin/external_keys/validate)

### Large parts of the API reference were regenerated: inline union types were replaced with named schema names, the `anthropic-beta` header description was standardised, and the beta-name enum count grew from "41 more" to "43 more".

`editorial` · bulk regeneration · 15 pages

Hundreds of pages show the same mechanical edits — `array of object or object` becoming named types such as `BetaOrganizationInvite` or `Text or ToolUse or ToolResult`, `"anthropic-beta": optional array of AnthropicBeta` replacing the multi-beta prose, and ISO timestamps in examples gaining a trailing `Z`. Treat these as regeneration noise rather than semantic changes.

- [api/beta](https://platform.claude.com/docs/en/api/beta)
- [api/admin](https://platform.claude.com/docs/en/api/admin)
- [api/admin/organizations](https://platform.claude.com/docs/en/api/admin/organizations)
- [api/beta/organization](https://platform.claude.com/docs/en/api/beta/organization)
- [api/beta/messages](https://platform.claude.com/docs/en/api/beta/messages)
- [api/beta/sessions](https://platform.claude.com/docs/en/api/beta/sessions)
- …and 9 more

### Lakeflow pipeline code samples were corrected throughout: import dp became from pyspark import pipelines as dp, @dp.materialized became @dp.materialized_view, and several SQL and PySpark snippets were fixed.

`editorial` · examples · 20 pages

Notably CREATE OR REFRESH STREAMING TABLE ... AS SELECT * FROM STREAM source_table now includes the STREAM keyword, and spark.readStream / spark.read.table replace older helper calls.

- [ldp/developer/python-dev](https://docs.databricks.com/aws/en/ldp/developer/python-dev)
- [ldp/load](https://docs.databricks.com/aws/en/ldp/load)
- [ldp/gdpr](https://docs.databricks.com/aws/en/ldp/gdpr)
- [ldp/stateful-processing](https://docs.databricks.com/aws/en/ldp/stateful-processing)
- [ldp/for-each-batch](https://docs.databricks.com/aws/en/ldp/for-each-batch)
- [ldp/best-practices](https://docs.databricks.com/aws/en/ldp/best-practices)
- …and 14 more

### Change data feed wording was normalised: sources must "use a change data feed", and what was called write-time change data feed is now "legacy change data feed" alongside automatic change data feed.

`editorial` · terminology · 5 pages

AI Search standard endpoints and Lakebase synced tables in Triggered or Continuous mode are the pages affected.

- [ai-search/ai-search](https://docs.databricks.com/aws/en/ai-search/ai-search)
- [ai-search/create-ai-search](https://docs.databricks.com/aws/en/ai-search/create-ai-search)
- [oltp/instances/sync-data/sync-table](https://docs.databricks.com/aws/en/oltp/instances/sync-data/sync-table)
- [oltp/projects/sync-tables](https://docs.databricks.com/aws/en/oltp/projects/sync-tables)
- [tables/features/change-data-feed](https://docs.databricks.com/aws/en/tables/features/change-data-feed)

### The Public Preview banner was removed from the Excel add-in, Excel Genie and Excel write-back pages.

`editorial` · status label · 5 pages

The setup page still tells you to ensure a workspace admin has enabled the Excel Connector preview, so the preview toggle itself remains.

- [integrations/excel](https://docs.databricks.com/aws/en/integrations/excel)
- [integrations/excel-genie](https://docs.databricks.com/aws/en/integrations/excel-genie)
- [integrations/excel-write-back](https://docs.databricks.com/aws/en/integrations/excel-write-back)
- [integrations/excel-query](https://docs.databricks.com/aws/en/integrations/excel-query)
- [integrations/excel-setup](https://docs.databricks.com/aws/en/integrations/excel-setup)

### The MLflow 3 GenAI docs were reorganised: tracing now has a /tracing/overview hub with automatic, manual, enrichment, governance, OTel-export and UC-migration pages, and links to the old Agent Evaluation pages were repointed to mlflow3/genai/eval-monitor.

`editorial` · restructure · 20 pages

Dozens of integration and agent pages had their MLflow Tracing links moved from /mlflow3/genai/tracing/ to /mlflow3/genai/tracing/overview, and tracing-101 content moved into the overview. New hub pages include agent observability and quality, core concepts, and recipes.

- [mlflow3/genai/tracing/overview](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/overview)
- [mlflow3/genai/tracing/automatic-tracing](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/automatic-tracing)
- [mlflow3/genai/tracing/manual-tracing](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/manual-tracing)
- [mlflow3/genai/tracing/enrich-traces](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/enrich-traces)
- [mlflow3/genai/tracing/govern-redact](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/govern-redact)
- [mlflow3/genai/tracing/otel-export](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/otel-export)
- …and 14 more
