# Change digest

> #1 (baseline) → #2 (after-refresh) · 1,334 changes · rendered 2026-08-30T14:43:38+00:00

## At a glance

41 findings — **8** breaking, **16** behavioural, **12** additive, **5** editorial — covering 544 of 1,334 changed pages. Anything not here is in the full feed report beside this file.

**If you read nothing else:**

1. Installing the `ant` CLI from source now requires Go 1.25 or later (was 1.22), and CLI examples switch to `--transform`/`--raw-output` piping and YAML-on-stdin.
2. Foundation Model Fine-tuning has reached end of life and is no longer supported — the previous notice said removal was scheduled for August 14, 2026, and the `databricks_genai` package and API are now past that date.
3. Bundle environment variables were renamed (`BUNDLE_ROOT` → `DATABRICKS_BUNDLE_ROOT`, `DATABRICKS_BUNDLE_ENV` → `DATABRICKS_BUNDLE_TARGET`), and from Databricks CLI 1.14.0 bundles still on the Terraform engine are migrated to the direct engine automatically.
4. Python SDK v1.0 is a breaking release: it removes `temperature`, `top_p` and `top_k` (passing them raises TypeError), drops the tool runner's client-side compaction, requires Python 3.10+, and uses httpx2.
5. The User Profiles beta header moved from `user-profiles-2026-03-24` to `user-profiles-2026-08-18`; update clients that send the old value.
6. The `pipelines.channel` table property (`PREVIEW`/`CURRENT`) is no longer supported for standalone materialized views and streaming tables — they always run on the latest Databricks SQL runtime.
7. The Agent Bricks Supervisor API (Beta) is deprecated and reaches end of life on September 30, 2026; after that date it stops being available.
8. The legacy Public Preview list of stable serverless outbound IPs was deprecated on May 25, 2026 and is now decommissioned — it is no longer available through the NCC UI or account console, so firewall allowlists built from it must be migrated.

---

## Breaking — 8

### Installing the `ant` CLI from source now requires Go 1.25 or later (was 1.22), and CLI examples switch to `--transform`/`--raw-output` piping and YAML-on-stdin.

`breaking` · toolchain version · 11 pages

The quickstart raises the `go install` floor to Go 1.25. Scripting examples were rewritten to `ant beta:agents list --transform id --raw-output`, `ant beta:messages create --beta compact-2026-01-12 --format jsonl <<'YAML'`, and heredoc-fed create commands. The `using` page also drops skills from the list of resources living under the `beta:` prefix, consistent with the Skills API going GA. The beta-headers page now shows the same request in cURL, the `ant` CLI and the SDKs.

- [cli-sdks-libraries/cli/quickstart](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/quickstart)
- [cli-sdks-libraries/cli/scripting](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/scripting)
- [cli-sdks-libraries/cli/using](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/using)
- [build-with-claude/handling-stop-reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons)
- [build-with-claude/compaction](https://platform.claude.com/docs/en/build-with-claude/compaction)
- [managed-agents/quickstart](https://platform.claude.com/docs/en/managed-agents/quickstart)
- …and 5 more

### Foundation Model Fine-tuning has reached end of life and is no longer supported — the previous notice said removal was scheduled for August 14, 2026, and the `databricks_genai` package and API are now past that date.

`breaking` · end of life · 11 pages

The deprecation banner across the Foundation Model Fine-tuning pages was replaced with an end-of-life statement; surrounding pages now link to the feature as '(deprecated)'. Anything still calling `databricks_genai` for training runs needs to move to Databricks Model Training / alternative fine-tuning paths.

- [large-language-models/foundation-model-training/](https://docs.databricks.com/aws/en/large-language-models/foundation-model-training/)
- [large-language-models/foundation-model-training/data-preparation](https://docs.databricks.com/aws/en/large-language-models/foundation-model-training/data-preparation)
- [large-language-models/foundation-model-training/view-manage-runs](https://docs.databricks.com/aws/en/large-language-models/foundation-model-training/view-manage-runs)
- [large-language-models/foundation-model-training/fine-tune-run-tutorial](https://docs.databricks.com/aws/en/large-language-models/foundation-model-training/fine-tune-run-tutorial)
- [large-language-models/foundation-model-training/ui](https://docs.databricks.com/aws/en/large-language-models/foundation-model-training/ui)
- [large-language-models/foundation-model-training/create-fine-tune-run](https://docs.databricks.com/aws/en/large-language-models/foundation-model-training/create-fine-tune-run)
- …and 5 more

### Bundle environment variables were renamed (`BUNDLE_ROOT` → `DATABRICKS_BUNDLE_ROOT`, `DATABRICKS_BUNDLE_ENV` → `DATABRICKS_BUNDLE_TARGET`), and from Databricks CLI 1.14.0 bundles still on the Terraform engine are migrated to the direct engine automatically.

`breaking` · env var rename + engine migration · 7 pages

CI/CD pipelines that export the old variable names need updating. The direct-engine page replaced the 'Terraform will soon be deprecated' recommendation with automatic migration in CLI 1.14.0+. Deployment guidance also now pushes teams away from `/Workspace/Shared` toward team-owned bundle paths.

- [dev-tools/bundles/work-tasks](https://docs.databricks.com/aws/en/dev-tools/bundles/work-tasks)
- [dev-tools/ci-cd/azure-devops](https://docs.databricks.com/aws/en/dev-tools/ci-cd/azure-devops)
- [dev-tools/ci-cd/github](https://docs.databricks.com/aws/en/dev-tools/ci-cd/github)
- [dev-tools/bundles/direct](https://docs.databricks.com/aws/en/dev-tools/bundles/direct)
- [dev-tools/bundles/faqs](https://docs.databricks.com/aws/en/dev-tools/bundles/faqs)
- [dev-tools/bundles/sharing](https://docs.databricks.com/aws/en/dev-tools/bundles/sharing)
- …and 1 more

### Python SDK v1.0 is a breaking release: it removes `temperature`, `top_p` and `top_k` (passing them raises TypeError), drops the tool runner's client-side compaction, requires Python 3.10+, and uses httpx2.

`breaking` · SDK major version · 6 pages

model-deprecations now states that most SDKs keep deprecated sampling parameters in their request types, but the Python SDK (v1.0+) removes them so passing them raises a `TypeError`. The tool runner page now lists only the TypeScript and Ruby runners as supporting client-side compaction — Python was dropped in v1.0 — and points everyone at server-side compaction via `context_management`. The Python SDK page adds a Python 3.10-or-later floor, a v1 migration guide link, and tells you to use `DefaultHttpxClient`/`DefaultAsyncHttpxClient` rather than raw `httpx2` clients; sample code elsewhere switched to `httpx2` and Python 3.10.

- [about-claude/model-deprecations](https://platform.claude.com/docs/en/about-claude/model-deprecations)
- [agents-and-tools/tool-use/tool-runner](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner)
- [build-with-claude/context-editing](https://platform.claude.com/docs/en/build-with-claude/context-editing)
- [cli-sdks-libraries/sdks/python](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/python)
- [claude_api_primer](https://platform.claude.com/docs/en/claude_api_primer)
- [about-claude/use-case-guides/customer-support-chat](https://platform.claude.com/docs/en/about-claude/use-case-guides/customer-support-chat)

### The User Profiles beta header moved from `user-profiles-2026-03-24` to `user-profiles-2026-08-18`; update clients that send the old value.

`breaking` · beta header change · 6 pages

Every User Profiles example now sends `anthropic-beta: user-profiles-2026-08-18`. Callers still sending the March header should verify behaviour before the old value is retired.

- [api/beta/user_profiles](https://platform.claude.com/docs/en/api/beta/user_profiles)
- [api/beta/user_profiles/list](https://platform.claude.com/docs/en/api/beta/user_profiles/list)
- [api/beta/user_profiles/create](https://platform.claude.com/docs/en/api/beta/user_profiles/create)
- [api/beta/user_profiles/retrieve](https://platform.claude.com/docs/en/api/beta/user_profiles/retrieve)
- [api/beta/user_profiles/update](https://platform.claude.com/docs/en/api/beta/user_profiles/update)
- [api/beta/user_profiles/create_enrollment_url](https://platform.claude.com/docs/en/api/beta/user_profiles/create_enrollment_url)

### The `pipelines.channel` table property (`PREVIEW`/`CURRENT`) is no longer supported for standalone materialized views and streaming tables — they always run on the latest Databricks SQL runtime.

`breaking` · removed setting · 6 pages

The CREATE MATERIALIZED VIEW / CREATE STREAMING TABLE references and the DBSQL configuration pages replaced the channel guidance with a statement that the property is no longer supported. Connector examples that set `"channel": "PREVIEW"` (Jira, SharePoint) dropped it too. Remove the property from DDL and pipeline settings; workloads that relied on pinning to `current` will now follow the latest runtime.

- [sql/language-manual/sql-ref-syntax-ddl-create-materialized-view](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-ddl-create-materialized-view)
- [sql/language-manual/sql-ref-syntax-ddl-create-streaming-table](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-ddl-create-streaming-table)
- [ldp/dbsql/materialized-configure](https://docs.databricks.com/aws/en/ldp/dbsql/materialized-configure)
- [ldp/dbsql/streaming](https://docs.databricks.com/aws/en/ldp/dbsql/streaming)
- [ingestion/lakeflow-connect/jira-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/jira-pipeline)
- [ingestion/sharepoint](https://docs.databricks.com/aws/en/ingestion/sharepoint)

### The Agent Bricks Supervisor API (Beta) is deprecated and reaches end of life on September 30, 2026; after that date it stops being available.

`breaking` · deprecation with date · 5 pages

Every reference to the Supervisor API is now labelled '(Beta) (deprecated)' and the main page carries the EOL date. Agents that let Databricks run the loop need a migration plan to a custom agent.

- [agents/agent-bricks/supervisor-api](https://docs.databricks.com/aws/en/agents/agent-bricks/supervisor-api)
- [agents/custom-agents/supervisor-api-app](https://docs.databricks.com/aws/en/agents/custom-agents/supervisor-api-app)
- [agents/custom-agents/author-agent](https://docs.databricks.com/aws/en/agents/custom-agents/author-agent)
- [getting-started/gen-ai-llm-agent](https://docs.databricks.com/aws/en/getting-started/gen-ai-llm-agent)
- [release-notes/product/2026/april](https://docs.databricks.com/aws/en/release-notes/product/2026/april)

### The legacy Public Preview list of stable serverless outbound IPs was deprecated on May 25, 2026 and is now decommissioned — it is no longer available through the NCC UI or account console, so firewall allowlists built from it must be migrated.

`breaking` · decommission · 3 pages

The pages now say the legacy static IP list has been decommissioned rather than merely warning about it, and direct you to the current outbound-IP method for serverless firewall configuration. Anyone whose storage or third-party firewall rules were copied from an NCC in the account console needs to re-derive them.

- [security/network/serverless-network-security/](https://docs.databricks.com/aws/en/security/network/serverless-network-security/)
- [security/network/serverless-network-security/serverless-firewall-config](https://docs.databricks.com/aws/en/security/network/serverless-network-security/serverless-firewall-config)
- [resources/ip-domain-region](https://docs.databricks.com/aws/en/resources/ip-domain-region)

## Behavioural — 16

### Claude Enterprise user management left beta: the `ce-user-management-2026-07-13` header is no longer required for group and custom-role requests (it is still accepted), and members/invites are no longer flagged beta.

`behavioural` · beta exit · 26 pages

Requests that previously 404'd without the header now work without it, and the availability table lists Members, Invites, Groups and (read-only) Custom roles as Available rather than Beta for Claude Enterprise. Scope requirements (`read:members`, `write:members`, `read:rbac_groups`, `write:rbac_groups`, `read:org_audit`) are unchanged.

- [manage-claude/user-management](https://platform.claude.com/docs/en/manage-claude/user-management)
- [api/admin/rbac_groups](https://platform.claude.com/docs/en/api/admin/rbac_groups)
- [api/admin/rbac_groups/list](https://platform.claude.com/docs/en/api/admin/rbac_groups/list)
- [api/admin/rbac_groups/create](https://platform.claude.com/docs/en/api/admin/rbac_groups/create)
- [api/admin/rbac_groups/retrieve](https://platform.claude.com/docs/en/api/admin/rbac_groups/retrieve)
- [api/admin/rbac_groups/update](https://platform.claude.com/docs/en/api/admin/rbac_groups/update)
- …and 20 more

### The Admin API's MCP tunnel and external-key (CMEK) endpoints are now flagged Deprecated; use the beta tunnels and `beta/organization/external_keys` endpoints instead.

`behavioural` · deprecation · 18 pages

Every `/v1/organizations/tunnels/...` and `/v1/organizations/external_keys/...` operation page gained a Deprecated marker. Equivalent operations live under `api/beta/tunnels` and the new `api/beta/organization/external_keys` tree; the CMEK guides now show `client.Beta.Organization.ExternalKeys` calls.

- [api/admin/mcp_tunnels](https://platform.claude.com/docs/en/api/admin/mcp_tunnels)
- [api/admin/mcp_tunnels/list](https://platform.claude.com/docs/en/api/admin/mcp_tunnels/list)
- [api/admin/mcp_tunnels/retrieve](https://platform.claude.com/docs/en/api/admin/mcp_tunnels/retrieve)
- [api/admin/mcp_tunnels/archive](https://platform.claude.com/docs/en/api/admin/mcp_tunnels/archive)
- [api/admin/mcp_tunnels/reveal_token](https://platform.claude.com/docs/en/api/admin/mcp_tunnels/reveal_token)
- [api/admin/mcp_tunnels/rotate_token](https://platform.claude.com/docs/en/api/admin/mcp_tunnels/rotate_token)
- …and 12 more

### Smaller operational changes worth acting on: custom container images must now install the `acl` package, streaming backlog notifications aren't supported for pipeline tasks, Auto Loader clean-source moves may cross buckets within one external location, and a failed workspace can no longer be fixed by update — delete and recreate it.

`behavioural` · assorted operational changes · 17 pages

compute/custom-containers adds `acl` to the required Ubuntu packages for recent runtimes that install libraries. Jobs pages state streaming backlog thresholds/notifications don't apply to pipeline tasks. A new clean-source page documents `cloudFiles.cleanSource` (OFF/DELETE/MOVE) and the production page relaxes the move-destination rule from 'same bucket' to 'same external location, volume, or DBFS mount'. AI Search dropped the 'CMK not supported' limitation. Row tracking is now documented as available from Databricks Runtime 14.0 (the upgrade table still cites 14.1). Workspace creation docs say failed workspaces can't be recovered by update. Pipeline environment-version migrations now revert automatically before any data is written if an update fails, and creating Unity Catalog UDFs inside a pipeline is unsupported. Predictive optimization `VACUUM` also cleans Iceberg metadata on Iceberg-read-enabled tables.

- [compute/custom-containers](https://docs.databricks.com/aws/en/compute/custom-containers)
- [jobs/notifications](https://docs.databricks.com/aws/en/jobs/notifications)
- [jobs/configure-job](https://docs.databricks.com/aws/en/jobs/configure-job)
- [jobs/configure-task](https://docs.databricks.com/aws/en/jobs/configure-task)
- [ai-search/ai-search](https://docs.databricks.com/aws/en/ai-search/ai-search)
- [ai-search/create-ai-search](https://docs.databricks.com/aws/en/ai-search/create-ai-search)
- …and 11 more

### Several managed-connector limits changed: Oracle's recommended table ceiling per pipeline dropped from ~500 to 250, Kafka metadata columns are now available via `source_metadata_column`, Salesforce ingests `address`/`location` components (only `base64` is dropped), and Jira delete tracking needs `use_audit_logs`, a paid plan and global admin.

`behavioural` · connector limits · 16 pages

Kafka's 'metadata columns not available' limitation became 'not included by default' with an opt-in struct column. Salesforce's unsupported-type list shrank to `base64`. Query-based connectors relaxed hard-deletion tracking (no longer restricted to timestamp cursor columns) but still require primary keys and forbid SCD type 2. HubSpot CRM Hub object ingestion is Beta with an exact required-scope list. GitHub requires long-lived access tokens (don't expire user access tokens in the OAuth app). Gateway-snapshot resumption caveats were removed from Oracle/PostgreSQL/SQL Server limits.

- [ingestion/lakeflow-connect/oracle-integrated-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/oracle-integrated-pipeline)
- [ingestion/lakeflow-connect/kafka-limits](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/kafka-limits)
- [ingestion/lakeflow-connect/kafka-reference](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/kafka-reference)
- [ingestion/lakeflow-connect/salesforce-limits](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/salesforce-limits)
- [ingestion/lakeflow-connect/salesforce-troubleshoot](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/salesforce-troubleshoot)
- [ingestion/lakeflow-connect/salesforce-reference](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/salesforce-reference)
- …and 10 more

### A batch of features changed release stage: base environments and serverless dependencies moved Beta → Public Preview, default Python package repositories went GA for Lakeflow pipelines and classic compute (Beta only for Apps), external data access for pipeline tables left preview, and Genie Code / Private network gateway entered preview.

`behavioural` · preview status · 14 pages

Several admonitions were rewritten from Beta to Public Preview (base environment, serverless dependencies, OpenSharing Databricks reads). Default package repositories are now GA except for Databricks Apps. Unity AI Gateway and Unity Catalog asset governance are described as GA with no preview needed. External data access for pipeline-managed and standalone MVs/STs no longer carries the preview enrolment requirement. The August product release notes add Private network gateway (Private Preview) and ABAC context attributes (Beta).

- [admin/workspace-settings/base-environment](https://docs.databricks.com/aws/en/admin/workspace-settings/base-environment)
- [admin/workspace-settings/default-package-repositories](https://docs.databricks.com/aws/en/admin/workspace-settings/default-package-repositories)
- [compute/serverless/dependencies](https://docs.databricks.com/aws/en/compute/serverless/dependencies)
- [ai-gateway/ai-governance](https://docs.databricks.com/aws/en/ai-gateway/ai-governance)
- [genie-code/use-genie-code](https://docs.databricks.com/aws/en/genie-code/use-genie-code)
- [genie-code/](https://docs.databricks.com/aws/en/genie-code/)
- …and 8 more

### Unity AI Gateway adds a unified trace table for monitoring all AI activity, and the coding-agent CLI command changed from `ucode configure mcp` to `ucode mcp add`.

`behavioural` · new capability + CLI rename · 12 pages

Two new pages document the unified trace table and its column/attribute/event schema. MCP client setup examples now use `ucode mcp add --agents claude --services <catalog>.<schema>.<service>`, so existing setup scripts break. Service policies gained an explicit input (`ON CALL`) / output (`ON RESULT`) phase model, a documented DENY behaviour that returns HTTP 200 with a replacement assistant turn, and a note that MCP Service `EXECUTE` access can't be granted through a bundle's `uc_securable` resource.

- [ai-gateway/unified-trace-table](https://docs.databricks.com/aws/en/ai-gateway/unified-trace-table)
- [ai-gateway/unified-trace-table-reference](https://docs.databricks.com/aws/en/ai-gateway/unified-trace-table-reference)
- [ai-gateway/govern-coding-agent-tutorial](https://docs.databricks.com/aws/en/ai-gateway/govern-coding-agent-tutorial)
- [ai-gateway/coding-agent-integration-model-services](https://docs.databricks.com/aws/en/ai-gateway/coding-agent-integration-model-services)
- [agents/mcp-tools/connect-clients](https://docs.databricks.com/aws/en/agents/mcp-tools/connect-clients)
- [agents/mcp-tools/mcp-services](https://docs.databricks.com/aws/en/agents/mcp-tools/mcp-services)
- …and 6 more

### `temperature` and `top_p` are marked Deprecated across the Messages, Batches and Completions references: models released after Claude Opus 4.6 don't support them, and only permissive values are accepted for backwards compatibility.

`behavioural` · deprecation · 11 pages

The reference now carries a Deprecated flag with the note that a value of 1.0 for temperature and >= 0.99 for top_p is accepted for backwards compatibility on newer models; anything else is rejected. Combined with the Python SDK removal, code that tunes sampling needs a model-aware path.

- [api/completions](https://platform.claude.com/docs/en/api/completions)
- [api/completions/create](https://platform.claude.com/docs/en/api/completions/create)
- [api/messages](https://platform.claude.com/docs/en/api/messages)
- [api/messages/create](https://platform.claude.com/docs/en/api/messages/create)
- [api/messages/batches](https://platform.claude.com/docs/en/api/messages/batches)
- [api/messages/batches/create](https://platform.claude.com/docs/en/api/messages/batches/create)
- …and 5 more

### Role-based access control (Public Preview) must now be enabled by an account admin on the account Previews page before it becomes available in workspaces.

`behavioural` · enablement · 9 pages

The RBAC pages replaced 'enable this preview at the account level first' with an explicit instruction that an account admin turns on the **Role-based access control (RBAC)** setting on the account Previews page. Downstream features that depend on RBAC — running a job as a role, group Git credentials — carry the same requirement.

- [security/auth/rbac/](https://docs.databricks.com/aws/en/security/auth/rbac/)
- [security/auth/rbac/limitations](https://docs.databricks.com/aws/en/security/auth/rbac/limitations)
- [security/auth/rbac/switch-roles](https://docs.databricks.com/aws/en/security/auth/rbac/switch-roles)
- [security/auth/rbac/exclusive-access](https://docs.databricks.com/aws/en/security/auth/rbac/exclusive-access)
- [security/auth/rbac/abac-interaction](https://docs.databricks.com/aws/en/security/auth/rbac/abac-interaction)
- [security/auth/rbac/sharing-controls](https://docs.databricks.com/aws/en/security/auth/rbac/sharing-controls)
- …and 3 more

### Several Compliance API endpoints are now marked Deprecated (chat messages, project list/retrieve), and combining `updated_at` filters with `user_ids[]` on chat listing is deprecated and will be removed.

`behavioural` · deprecation · 8 pages

Chat message and project endpoints carry Deprecated markers. Chat listing documents `user_ids[]` (max 10 per request) for scoping to named custodians and states that combining updated_at filters with `user_ids[]` is deprecated. Legal-hold and export pipelines built on these endpoints should plan a migration.

- [api/compliance/apps/chats/messages](https://platform.claude.com/docs/en/api/compliance/apps/chats/messages)
- [api/compliance/apps/chats/messages/list](https://platform.claude.com/docs/en/api/compliance/apps/chats/messages/list)
- [api/compliance/apps/projects/list](https://platform.claude.com/docs/en/api/compliance/apps/projects/list)
- [api/compliance/apps/projects/retrieve](https://platform.claude.com/docs/en/api/compliance/apps/projects/retrieve)
- [api/compliance/apps/chats](https://platform.claude.com/docs/en/api/compliance/apps/chats)
- [api/compliance/apps/chats/list](https://platform.claude.com/docs/en/api/compliance/apps/chats/list)
- …and 2 more

### Claude Opus 5 turns thinking on by default — responses can start with thinking blocks, and `thinking: {"type": "disabled"}` is only accepted at effort `high` or below.

`behavioural` · model behaviour · 8 pages

The what's-new page calls this a breaking change for code that ran without thinking on Opus 4.8: a response can begin with one or more thinking blocks, and disabling thinking is rejected above the high effort level. Sonnet 5 documents adaptive thinking on by default, sampling parameters not accepted, and 1M-token context by default. Parsers that assume the first content block is text need updating.

- [about-claude/models/whats-new-opus-5](https://platform.claude.com/docs/en/about-claude/models/whats-new-opus-5)
- [about-claude/models/migration-guide](https://platform.claude.com/docs/en/about-claude/models/migration-guide)
- [build-with-claude/thinking](https://platform.claude.com/docs/en/build-with-claude/thinking)
- [build-with-claude/prompt-engineering/prompting-claude-opus-5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5)
- [build-with-claude/prompt-engineering/prompting-claude-sonnet-5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5)
- [build-with-claude/prompt-engineering/prompting-claude-fable-5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5)
- …and 2 more

### Key ownership and workspace scoping are now explicit: personal and service-account keys stop working in a workspace shortly after the identity is removed from it, archiving a workspace archives its keys, and multi-workspace keys need the `anthropic-workspace-id` header.

`behavioural` · key lifecycle · 5 pages

get-api-key introduces 'workspace keys' as legacy owner-less keys that keep working, versus personal and service-account keys tied to an identity. The workspaces page warns that removing a user or service account from a workspace disables their key there within seconds, and that archiving a workspace archives every key created for it. api/overview documents `anthropic-workspace-id` for choosing the workspace a request runs in, and the CLI guide notes `ANTHROPIC_API_KEY` overrides every profile. Audit any automation that assumes a key survives membership changes.

- [get-api-key](https://platform.claude.com/docs/en/get-api-key)
- [manage-claude/workspaces](https://platform.claude.com/docs/en/manage-claude/workspaces)
- [manage-claude/authentication](https://platform.claude.com/docs/en/manage-claude/authentication)
- [cli-sdks-libraries/cli/authentication](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/authentication)
- [api/overview](https://platform.claude.com/docs/en/api/overview)

### Querying Unity AI Gateway model and model-provider services now requires either Workspace access or Consumer access with the opt-in 'Consumer access to Unity AI Gateway' preview enabled.

`behavioural` · entitlement change · 5 pages

The query prerequisites gained the consumer-access entitlement path, and what's-coming warns account admins to set budgets and rate limits (or disable direct model access) for consumer-access users before the change rolls out more broadly. Consumer-tier users cannot query these services until the preview is enabled.

- [ai-gateway/query-model-provider-services](https://docs.databricks.com/aws/en/ai-gateway/query-model-provider-services)
- [ai-gateway/query-model-services](https://docs.databricks.com/aws/en/ai-gateway/query-model-services)
- [security/auth/entitlements](https://docs.databricks.com/aws/en/security/auth/entitlements)
- [ai-bi/consumers/](https://docs.databricks.com/aws/en/ai-bi/consumers/)
- [release-notes/whats-coming](https://docs.databricks.com/aws/en/release-notes/whats-coming)

### On API key objects, top-level `workspace_id` is deprecated in favour of `scope`, which reports the real workspace ID even for the default workspace.

`behavioural` · field deprecation · 4 pages

The reference now says `workspace_id` is deprecated (null for keys in the default workspace) and that `scope` carries the workspace's real ID. Move parsers to `scope` before `workspace_id` is removed.

- [api/admin/api_keys](https://platform.claude.com/docs/en/api/admin/api_keys)
- [api/admin/api_keys/list](https://platform.claude.com/docs/en/api/admin/api_keys/list)
- [api/admin/api_keys/retrieve](https://platform.claude.com/docs/en/api/admin/api_keys/retrieve)
- [api/admin/api_keys/update](https://platform.claude.com/docs/en/api/admin/api_keys/update)

### Uploaded files and custom Skills are explicitly documented as workspace-wide: any API key with workspace access can read them, so don't treat them as per-user or per-session data.

`behavioural` · security scope · 2 pages

Both guides gained a prominent warning that uploads and custom Skills are accessible to the entire workspace, not scoped to an end user, conversation or session. If you multiplex end users through one workspace, isolate them with separate workspaces or keep user data out of Files/Skills.

- [build-with-claude/files](https://platform.claude.com/docs/en/build-with-claude/files)
- [build-with-claude/skills-guide](https://platform.claude.com/docs/en/build-with-claude/skills-guide)

### `429 rate_limit_error` now also means a spend limit was reached, not just a rate limit, and the Files API has its own per-organization limit.

`behavioural` · error semantics · 2 pages

The errors page broadens the 429 description to cover organizations that have hit a rate limit or reached a spend limit, and broadens 400 `invalid_request_error` to other 4xx-class conditions. The rate limits page adds a per-organization Files API limit shared across file operations and drops the old per-tier monthly spend cap wording. Retry logic that treats every 429 as transient may loop forever against a spend limit.

- [api/errors](https://platform.claude.com/docs/en/api/errors)
- [api/rate-limits](https://platform.claude.com/docs/en/api/rate-limits)

### Fast mode's research preview is now documented as unavailable on Claude Platform on AWS as well as Bedrock, Google Cloud and Microsoft Foundry.

`behavioural` · availability · 1 page

The exclusion list gained Claude Platform on AWS. The existing model-specific notes are unchanged: `claude-opus-4-7` with `speed: "fast"` errors, while `claude-opus-4-6` silently runs at standard speed and standard billing.

- [build-with-claude/fast-mode](https://platform.claude.com/docs/en/build-with-claude/fast-mode)

## Additive — 12

### Admin API operations now have a `beta/organization/...` reference tree, matching the SDK surface `client.beta.organization.*` (users, invites, workspaces, service accounts, rate limits, federation, external keys).

`additive` · namespace move · 74 pages

A large set of new reference pages mirrors the existing `/v1/organizations/...` Admin API under the beta organization namespace. The Admin API guide now says the Python, TypeScript, C#, Go, Java, PHP and Ruby SDKs expose the Admin API under `client.beta.organization`, with the `ant` CLI following suit; the WIF admin guide switched its examples to `client.beta.organization.service_accounts` and `client.beta.organization.federation.issuers`.

- [api/beta/organization](https://platform.claude.com/docs/en/api/beta/organization)
- [api/beta/organization/retrieve](https://platform.claude.com/docs/en/api/beta/organization/retrieve)
- [api/beta/organization/api_keys](https://platform.claude.com/docs/en/api/beta/organization/api_keys)
- [api/beta/organization/api_keys/list](https://platform.claude.com/docs/en/api/beta/organization/api_keys/list)
- [api/beta/organization/api_keys/retrieve](https://platform.claude.com/docs/en/api/beta/organization/api_keys/retrieve)
- [api/beta/organization/api_keys/update](https://platform.claude.com/docs/en/api/beta/organization/api_keys/update)
- …and 68 more

### Zerobus Ingest got a full documentation set (concepts, protocols, message types, recovery, networking, release stages) and the Kafka-compatible APIs are documented as Beta with their own quota, at-least-once delivery and JSON-only records.

`additive` · docs expansion · 21 pages

New pages cover streams and clients, gRPC/REST/OpenTelemetry protocols, blocking vs future-based ingestion, acknowledgment callbacks, resilient recovery, and per-feature release stages. The overview stresses that Zerobus never auto-evolves your Delta schema — the table schema is the contract — and the rescue column Beta is limited to JSON ingestion. 'Zerobus Ingest connector quotas' was renamed 'Zerobus Ingest quotas' and linked from the OpenTelemetry guides.

- [ingestion/zerobus-overview](https://docs.databricks.com/aws/en/ingestion/zerobus-overview)
- [ingestion/zerobus-ingest](https://docs.databricks.com/aws/en/ingestion/zerobus-ingest)
- [ingestion/zerobus-kafka](https://docs.databricks.com/aws/en/ingestion/zerobus-kafka)
- [ingestion/zerobus-quotas](https://docs.databricks.com/aws/en/ingestion/zerobus-quotas)
- [ingestion/zerobus-arrow-flight](https://docs.databricks.com/aws/en/ingestion/zerobus-arrow-flight)
- [ingestion/zerobus-rescue-column](https://docs.databricks.com/aws/en/ingestion/zerobus-rescue-column)
- …and 15 more

### The Files API and Skills API are now generally available: non-beta `/v1/files` and `/v1/skills` reference pages exist, and recent SDKs expose them at `client.files` / `client.skills` instead of `client.beta.*`.

`additive` · GA / namespace move · 19 pages

New top-level reference sections were added for Files and Skills. The guides now say that starting with Python SDK 1.2.0, TypeScript 0.122.0, Go 1.68.0, Java 2.59.0, Ruby 1.67.0 and C# 12.44.0 the non-beta client path is available; beta client paths and the `files-api-2025-04-14` / `skills-2025-10-02` headers still work but are no longer required. Code that pins the beta namespace keeps working, but new examples throughout the docs (citations, PDF support, vision, managed agents) use the GA path.

- [api/files](https://platform.claude.com/docs/en/api/files)
- [api/files/upload](https://platform.claude.com/docs/en/api/files/upload)
- [api/files/list](https://platform.claude.com/docs/en/api/files/list)
- [api/files/download](https://platform.claude.com/docs/en/api/files/download)
- [api/files/delete](https://platform.claude.com/docs/en/api/files/delete)
- [api/files/retrieve_metadata](https://platform.claude.com/docs/en/api/files/retrieve_metadata)
- …and 13 more

### A browser use tool ships alongside computer use, and both are now toolsets (`browser_toolset_20260801`, `computer_toolset_20260801`) whose member tools carry `toolset_name` and per-member `defer_loading`.

`additive` · new tool / toolsets · 17 pages

A new browser-use-tool page documents driving webpages in your own browser environment. `computer_toolset_20260801` is described as the stable successor to the beta `computer_20251124` and `computer_20250124` versions, which remain available in beta for existing integrations and older models. Practical consequences: a `tool_result` must echo the same `toolset_name` as its `tool_use`; `defer_loading` must resolve to the same value on every enabled member; input examples are not supported for client toolsets; and pricing now quotes toolset definition overhead of about 6,600 input tokens for `browser_toolset_20260801` with default members, replacing the old 466–499-token computer-use system prompt figure. Platform capability lists on Bedrock, Vertex AI and Microsoft Foundry were updated accordingly.

- [agents-and-tools/tool-use/browser-use-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/browser-use-tool)
- [agents-and-tools/tool-use/computer-use-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool)
- [agents-and-tools/tool-use/tool-reference](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-reference)
- [agents-and-tools/tool-use/tool-search-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool)
- [agents-and-tools/tool-use/strict-tool-use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use)
- [agents-and-tools/tool-use/programmatic-tool-calling](https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling)
- …and 11 more

### Genie Agent mode APIs are no longer labelled Beta and moved to a dedicated API reference, a Genie One desktop app joins the mobile app, and Genie Agents can be shared and mounted through OpenSharing.

`additive` · GA + new surfaces · 17 pages

'Agent mode APIs (Beta)' became 'Agent mode APIs' pointing at the new Genie API reference (`/api/genie/v1/...`). New pages cover the macOS desktop app and OpenSharing of Genie Agents (a point-in-time snapshot the recipient can modify). Genie One creation now needs **Workspace access** or **Databricks SQL access** (previously worded as both), and Teams/Slack usage is auditable through `system.access.audit`.

- [genie-agents/concepts](https://docs.databricks.com/aws/en/genie-agents/concepts)
- [genie-agents/volumes](https://docs.databricks.com/aws/en/genie-agents/volumes)
- [genie-agents/api](https://docs.databricks.com/aws/en/genie-agents/api)
- [genie-agents/conversation-api](https://docs.databricks.com/aws/en/genie-agents/conversation-api)
- [genie-one/desktop](https://docs.databricks.com/aws/en/genie-one/desktop)
- [genie-one/desktop-attributions](https://docs.databricks.com/aws/en/genie-one/desktop-attributions)
- …and 11 more

### AI Functions no longer require serverless compute: every task-specific function and `ai_query` now states Databricks Runtime 15.4 LTS or above (18.2+ recommended), and the 'not available on Pro or Classic SQL warehouses' restriction was dropped.

`additive` · requirements change · 16 pages

The requirements bullet changed from '[Serverless compute] is required for notebooks and Databricks workflows' to 'Databricks Runtime 15.4 LTS or above is required. Databricks Runtime 18.2 or above is recommended for the best performance and access to the latest features.' The same edit landed on `vector_search` and on the batch-inference pipeline guidance. If you moved workloads to serverless purely to run AI Functions, classic compute on a recent runtime is now documented as supported.

- [large-language-models/ai-query](https://docs.databricks.com/aws/en/large-language-models/ai-query)
- [large-language-models/ai-functions-example](https://docs.databricks.com/aws/en/large-language-models/ai-functions-example)
- [large-language-models/ai-functions](https://docs.databricks.com/aws/en/large-language-models/ai-functions)
- [large-language-models/batch-inference-pipelines](https://docs.databricks.com/aws/en/large-language-models/batch-inference-pipelines)
- [sql/language-manual/functions/ai_query](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_query)
- [sql/language-manual/functions/ai_analyze_sentiment](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_analyze_sentiment)
- …and 10 more

### Foundation Model APIs added new hosted models (Grok 4.6, DeepSeek V4 Pro, GLM-5.3-Flash and others) with regenerated per-region availability, and 'provisioned throughput' was split into on-demand versus a new reserved 1- or 3-month term at a lower per-unit rate.

`additive` · model availability / pricing option · 12 pages

The region availability matrix, function-calling support table, rate limits and reasoning-model tables were all regenerated with the new model IDs. Pages that said 'Provisioned throughput Foundation Model APIs' now say 'On-demand provisioned throughput', and a new page documents reserved provisioned throughput for fixed-term capacity commitments.

- [machine-learning/model-serving/foundation-model-overview](https://docs.databricks.com/aws/en/machine-learning/model-serving/foundation-model-overview)
- [machine-learning/foundation-model-apis/supported-models](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/supported-models)
- [machine-learning/foundation-model-apis/limits](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/limits)
- [machine-learning/foundation-model-apis/](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/)
- [machine-learning/foundation-model-apis/deploy-prov-throughput-foundation-model-apis](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/deploy-prov-throughput-foundation-model-apis)
- [machine-learning/foundation-model-apis/reserved-provisioned-throughput](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/reserved-provisioned-throughput)
- …and 6 more

### Unity Catalog gains fine-grained DML privileges (`INSERT`, `UPDATE`, `DELETE`, Beta) as alternatives to blanket `MODIFY`, plus ABAC identity attributes and context attributes (both Beta) usable in row filter and column mask conditions.

`additive` · new privileges / ABAC attributes · 12 pages

A new page documents which operations each fine-grained DML privilege covers and its Beta limitations; grant guidance across securable-objects and tables-concepts now offers them instead of `MODIFY`. ABAC pages add identity attributes (`has_identity_attribute_value()`, `has_identity_attribute_tag_match()`) and context attributes such as `request.client_id`, with warnings that disabling the **UC ABAC Context Attributes** preview while policies still use those functions breaks queries, and that the functions aren't supported in `MATCH COLUMNS` or `GRANT`/`DENY`.

- [data-governance/unity-catalog/access-control/fine-grained-dml-privileges](https://docs.databricks.com/aws/en/data-governance/unity-catalog/access-control/fine-grained-dml-privileges)
- [data-governance/unity-catalog/access-control/permissions-concepts](https://docs.databricks.com/aws/en/data-governance/unity-catalog/access-control/permissions-concepts)
- [data-governance/unity-catalog/access-control/privileges-reference](https://docs.databricks.com/aws/en/data-governance/unity-catalog/access-control/privileges-reference)
- [data-governance/unity-catalog/securable-objects](https://docs.databricks.com/aws/en/data-governance/unity-catalog/securable-objects)
- [tables/tables-concepts](https://docs.databricks.com/aws/en/tables/tables-concepts)
- [data-governance/unity-catalog/abac/core-concepts](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/core-concepts)
- …and 6 more

### Lakebase raised the per-branch storage quota from 16 TB to 32 TB, added PCI-DSS and HITRUST support in `us-east-1`, and now documents an SLA; Lakebase CDF is unsupported when destination catalog storage sits behind a private endpoint.

`additive` · limits and compliance · 8 pages

manage-projects doubles the operational storage quota per branch. data-protection and private-link add PCI-DSS/HITRUST in us-east-1 on AWS. high-availability points at a published Lakebase SLA. lakebase-cdf adds a private-endpoint restriction on the destination Unity Catalog catalog's managed storage, and the sync-table pages document automatic change data feed (Public Preview) alongside LTAP Direct Writes. The Postgres API guide now says only some operations remain Beta rather than the whole API.

- [oltp/projects/manage-projects](https://docs.databricks.com/aws/en/oltp/projects/manage-projects)
- [oltp/projects/data-protection](https://docs.databricks.com/aws/en/oltp/projects/data-protection)
- [oltp/projects/private-link](https://docs.databricks.com/aws/en/oltp/projects/private-link)
- [oltp/projects/high-availability](https://docs.databricks.com/aws/en/oltp/projects/high-availability)
- [oltp/projects/lakebase-cdf](https://docs.databricks.com/aws/en/oltp/projects/lakebase-cdf)
- [oltp/projects/sync-tables](https://docs.databricks.com/aws/en/oltp/projects/sync-tables)
- …and 2 more

### Excel downloads from dashboards now allow up to 1,000,000 rows (was 100,000); CSV/TSV stays at ~1 GB.

`additive` · limit increase · 6 pages

The dashboard download limit was raised tenfold and the equivalent statement was dropped from the SQL editor results page. Visualization docs also add path maps over GEOMETRY/GEOGRAPHY columns, per-widget categorical colour consistency, counter sparkline toggles, and independent header alignment for table columns.

- [dashboards/manage/](https://docs.databricks.com/aws/en/dashboards/manage/)
- [sql/user/sql-editor/results](https://docs.databricks.com/aws/en/sql/user/sql-editor/results)
- [dashboards/manage/visualizations/maps](https://docs.databricks.com/aws/en/dashboards/manage/visualizations/maps)
- [dashboards/manage/visualizations/types](https://docs.databricks.com/aws/en/dashboards/manage/visualizations/types)
- [dashboards/manage/visualizations/](https://docs.databricks.com/aws/en/dashboards/manage/visualizations/)
- [dashboards/manage/visualizations/tables](https://docs.databricks.com/aws/en/dashboards/manage/visualizations/tables)

### Serverless compute access control is generally available (two built-in workspace entitlements), and serverless rate limits are in Private Preview requiring Databricks Runtime 17.3.1 or above.

`additive` · GA + preview · 4 pages

A new 'Manage serverless compute' page describes how workspace admins govern who can run serverless workloads. Rate limits are gated behind a Private Preview and a runtime floor of 17.3.1 (jobs pick the latest runtime automatically; Spark Declarative Pipelines need attention). Fine-grained access control is documented as not respecting serverless access controls.

- [compute/serverless/access-control](https://docs.databricks.com/aws/en/compute/serverless/access-control)
- [compute/serverless/manage-serverless-compute](https://docs.databricks.com/aws/en/compute/serverless/manage-serverless-compute)
- [release-notes/serverless/](https://docs.databricks.com/aws/en/release-notes/serverless/)
- [compute/single-user-fgac](https://docs.databricks.com/aws/en/compute/single-user-fgac)

### File uploads now accept an expiry: seconds from upload until the bytes become permanently unavailable, between 3600 (1 hour) and 7776000 (90 days).

`additive` · new parameter · 2 pages

The Files upload reference documents a per-file expiration window. Files that expire are gone permanently, so long-lived pipelines should either re-upload or set the maximum window.

- [api/beta/files](https://platform.claude.com/docs/en/api/beta/files)
- [api/beta/files/upload](https://platform.claude.com/docs/en/api/beta/files/upload)

## Editorial — 5

### Beta/Preview admonitions were reworded corpus-wide from 'Workspace admins can control access to this feature' to explicit 'a workspace admin must turn on <setting> on the Previews page' text.

`editorial` · boilerplate rewrite · 31 pages

A large number of pages changed only in the shape of their preview banner (or replaced a bare '> **Beta:**' marker with the full release-types link). No functional change, but it accounts for much of this run's volume.

- [ingestion/lakeflow-connect/amplitude-overview](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/amplitude-overview)
- [ingestion/lakeflow-connect/amplitude-connection](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/amplitude-connection)
- [ingestion/lakeflow-connect/amplitude-faq](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/amplitude-faq)
- [ingestion/lakeflow-connect/amplitude-limits](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/amplitude-limits)
- [ingestion/lakeflow-connect/amplitude-pipeline](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/amplitude-pipeline)
- [ingestion/lakeflow-connect/amplitude-reference](https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/amplitude-reference)
- …and 25 more

### Model documentation moved to a per-family tree under `/docs/en/models/…` (overview, migration guide, what's-new per family) and links across the corpus were repointed from `about-claude/models/overview` to `models/overview`.

`editorial` · information architecture · 30 pages

New per-model pages were added for Opus 5/4.8/4.7/4.6/4.5, Sonnet 5/4.6/4.5, Haiku 4.5, Fable 5 and Mythos 5, each with lifecycle status, model IDs on every platform, limits and pricing. Dozens of pages had their model links rewritten. Update bookmarks and any docs links you generate; the old `about-claude/models/*` pages still exist but now largely point into the new tree.

- [models/overview](https://platform.claude.com/docs/en/models/overview)
- [models/opus-5/overview](https://platform.claude.com/docs/en/models/opus-5/overview)
- [models/opus-5/migration-guide](https://platform.claude.com/docs/en/models/opus-5/migration-guide)
- [models/opus-5/whats-new-opus-5](https://platform.claude.com/docs/en/models/opus-5/whats-new-opus-5)
- [models/sonnet-5/overview](https://platform.claude.com/docs/en/models/sonnet-5/overview)
- [models/sonnet-5/migration-guide](https://platform.claude.com/docs/en/models/sonnet-5/migration-guide)
- …and 24 more

### Several Databricks doc trees were reorganised: real-time mode moved to `structured-streaming/real-time/`, the AI Runtime CLI pages moved under `ai-runtime/cli/`, Kinesis authentication split into its own page, and the ingestion landing pages were rewritten around connector categories.

`editorial` · information architecture · 26 pages

Many pages in this run are moves or link repointing rather than content changes ('Standard connectors in Lakeflow Connect' → 'Choose a standard connector', `structured-streaming/real-time/concepts` → `structured-streaming/real-time/`). New content in the moved trees includes a Ray Tune LoRA hyperparameter-search example and Kinesis authentication via Unity Catalog connections/service credentials.

- [structured-streaming/real-time/](https://docs.databricks.com/aws/en/structured-streaming/real-time/)
- [structured-streaming/real-time/concepts](https://docs.databricks.com/aws/en/structured-streaming/real-time/concepts)
- [structured-streaming/real-time/setup](https://docs.databricks.com/aws/en/structured-streaming/real-time/setup)
- [structured-streaming/real-time/tutorial](https://docs.databricks.com/aws/en/structured-streaming/real-time/tutorial)
- [structured-streaming/real-time/examples](https://docs.databricks.com/aws/en/structured-streaming/real-time/examples)
- [structured-streaming/real-time/limitations](https://docs.databricks.com/aws/en/structured-streaming/real-time/limitations)
- …and 20 more

### Most of the API reference was regenerated: object field lists collapsed (`BetaTunnel object { … }` → `BetaTunnel object`), HTTP verbs uppercased (`get` → `GET`), and the beta-header enum grew from '30 more' to '38 more'.

`editorial` · bulk regeneration · 22 pages

Hundreds of reference pages changed only in generated formatting — schema summaries dropping inline field lists, method casing, default/min/max lines being surfaced, and union spellings. The one substantive signal in the noise is the enumerated `anthropic-beta` header list growing by eight values.

- [api/beta](https://platform.claude.com/docs/en/api/beta)
- [api/admin](https://platform.claude.com/docs/en/api/admin)
- [api/compliance](https://platform.claude.com/docs/en/api/compliance)
- [api/beta/sessions](https://platform.claude.com/docs/en/api/beta/sessions)
- [api/beta/agents](https://platform.claude.com/docs/en/api/beta/agents)
- [api/beta/deployments](https://platform.claude.com/docs/en/api/beta/deployments)
- …and 16 more

### 'Lakebase Autoscaling' is now just 'Lakebase' throughout the docs, and Lakebase gets its own release-notes section.

`editorial` · rename · 17 pages

Product naming was normalised across the OLTP guides, tutorials and historical release notes; a new `release-notes/lakebase/` index was added. Behaviour is unchanged, but search terms, screenshots and internal runbooks referencing 'Lakebase Autoscaling' will drift.

- [oltp/projects/build-applications](https://docs.databricks.com/aws/en/oltp/projects/build-applications)
- [oltp/projects/connection-pooling](https://docs.databricks.com/aws/en/oltp/projects/connection-pooling)
- [oltp/projects/external-apps-manual-api](https://docs.databricks.com/aws/en/oltp/projects/external-apps-manual-api)
- [oltp/projects/manage-roles](https://docs.databricks.com/aws/en/oltp/projects/manage-roles)
- [oltp/projects/feature-store](https://docs.databricks.com/aws/en/oltp/projects/feature-store)
- [oltp/projects/ltap-overview](https://docs.databricks.com/aws/en/oltp/projects/ltap-overview)
- …and 11 more
