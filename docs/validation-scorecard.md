# Corpus review scorecard

50 pages drawn from 6403 by `scripts/sample_review.py --n 50 --seed 1`, stratified
by company, category, and size decile. Re-drawing with the same seed gives the same sample.

**How to score.** Open the corpus file and its live URL side by side, then mark each
column `y` / `n` / `?`:

| Column | Question |
|---|---|
| `title` | Is the title right, and does the page open by naming itself? |
| `complete` | Is the whole page here — no section silently missing, nothing added? |
| `code` | Are code blocks intact: fenced, line breaks preserved, runnable as shown? |
| `links` | Do links point somewhere real, and are they absolute? |
| `metadata` | Are category, dates, description, and tags right for this page? |

Leave `notes` for anything a column cannot capture. A single `n` anywhere is worth
investigating — this project's worst defects were corpus-wide and looked fine in aggregate.

Score it with: `uv run python scripts/sample_review.py --score docs/validation-scorecard.md`

| # | page | url | title | complete | code | links | metadata | notes |
|---|---|---|---|---|---|---|---|---|
| 1 | `data/databricks/sparkr/2026-06/aws-en-sparkr-sparklyr.md` | https://docs.databricks.com/aws/en/sparkr/sparklyr |  |  |  |  |  |  |
| 2 | `data/databricks/mlflow/2023-10/aws-en-mlflow-workspace-model-registry-example.md` | https://docs.databricks.com/aws/en/mlflow/workspace-model-registry-example |  |  |  |  |  |  |
| 3 | `data/databricks/files/2026-07/aws-en-files-write-data.md` | https://docs.databricks.com/aws/en/files/write-data |  |  |  |  |  |  |
| 4 | `data/databricks/ingestion/2026-07/aws-en-ingestion-lakeflow-connect-netskope-logs-faq.md` | https://docs.databricks.com/aws/en/ingestion/lakeflow-connect/netskope-logs-faq |  |  |  |  |  |  |
| 5 | `data/anthropic/capabilities/2024-08/cookbook-capabilities-summarization-guide.md` | https://platform.claude.com/cookbook/capabilities-summarization-guide |  |  |  |  |  |  |
| 6 | `data/anthropic/cli-sdks-libraries/undated/docs-en-cli-sdks-libraries-cli-quickstart.md` | https://platform.claude.com/docs/en/cli-sdks-libraries/cli/quickstart |  |  |  |  |  |  |
| 7 | `data/databricks/semi-structured/2026-01/aws-en-semi-structured-complex-types.md` | https://docs.databricks.com/aws/en/semi-structured/complex-types |  |  |  |  |  |  |
| 8 | `data/databricks/partners/2023-10/aws-en-partners-data-security-hunters.md` | https://docs.databricks.com/aws/en/partners/data-security/hunters |  |  |  |  |  |  |
| 9 | `data/databricks/languages/2026-05/aws-en-languages-python.md` | https://docs.databricks.com/aws/en/languages/python |  |  |  |  |  |  |
| 10 | `data/databricks/external-access/2026-06/aws-en-external-access.md` | https://docs.databricks.com/aws/en/external-access/ |  |  |  |  |  |  |
| 11 | `data/anthropic/third-party/2024-03/cookbook-third-party-llamaindex-subquestion-query-engine.md` | https://platform.claude.com/cookbook/third-party-llamaindex-subquestion-query-engine |  |  |  |  |  |  |
| 12 | `data/databricks/partner-connect/2026-07/aws-en-partner-connect-admin.md` | https://docs.databricks.com/aws/en/partner-connect/admin |  |  |  |  |  |  |
| 13 | `data/databricks/ai-search/2026-06/aws-en-ai-search-embedding-with-oss-models.md` | https://docs.databricks.com/aws/en/ai-search/embedding-with-oss-models |  |  |  |  |  |  |
| 14 | `data/databricks/admin/2025-01/aws-en-admin-account-settings-serverless-quotas.md` | https://docs.databricks.com/aws/en/admin/account-settings/serverless-quotas |  |  |  |  |  |  |
| 15 | `data/databricks/jobs/2026-08/aws-en-jobs-monitor.md` | https://docs.databricks.com/aws/en/jobs/monitor |  |  |  |  |  |  |
| 16 | `data/databricks/error-messages/2026-08/aws-en-error-messages-managed-ingestion-pipeline-spec-validation-error-error-class.md` | https://docs.databricks.com/aws/en/error-messages/managed-ingestion-pipeline-spec-validation-error-error-class |  |  |  |  |  |  |
| 17 | `data/databricks/visualizations/2026-03/aws-en-visualizations-histogram.md` | https://docs.databricks.com/aws/en/visualizations/histogram |  |  |  |  |  |  |
| 18 | `data/databricks/files/2026-01/aws-en-files-workspace-modules.md` | https://docs.databricks.com/aws/en/files/workspace-modules |  |  |  |  |  |  |
| 19 | `data/databricks/ai-bi/2026-06/aws-en-ai-bi-admin-themes.md` | https://docs.databricks.com/aws/en/ai-bi/admin/themes |  |  |  |  |  |  |
| 20 | `data/databricks/optimizations/2026-06/aws-en-optimizations-low-shuffle-merge.md` | https://docs.databricks.com/aws/en/optimizations/low-shuffle-merge |  |  |  |  |  |  |
| 21 | `data/databricks/admin/2025-02/aws-en-admin-workspace-settings.md` | https://docs.databricks.com/aws/en/admin/workspace-settings/ |  |  |  |  |  |  |
| 22 | `data/anthropic/managed-agents/2026-07/cookbook-managed-agents-cma-use-skills-from-a-repo.md` | https://platform.claude.com/cookbook/managed-agents-cma-use-skills-from-a-repo |  |  |  |  |  |  |
| 23 | `data/databricks/compute/2026-08/aws-en-compute-cluster-metrics.md` | https://docs.databricks.com/aws/en/compute/cluster-metrics |  |  |  |  |  |  |
| 24 | `data/databricks/integrations/2026-04/aws-en-integrations-jdbc-authentication.md` | https://docs.databricks.com/aws/en/integrations/jdbc/authentication |  |  |  |  |  |  |
| 25 | `data/databricks/agents/2026-08/aws-en-agents-mcp-tools-uc-function-http.md` | https://docs.databricks.com/aws/en/agents/mcp-tools/uc-function-http |  |  |  |  |  |  |
| 26 | `data/databricks/libraries/2026-08/aws-en-libraries.md` | https://docs.databricks.com/aws/en/libraries/ |  |  |  |  |  |  |
| 27 | `data/anthropic/manage-claude/undated/docs-en-manage-claude-app-attest.md` | https://platform.claude.com/docs/en/manage-claude/app-attest |  |  |  |  |  |  |
| 28 | `data/databricks/oltp/2026-06/aws-en-oltp-projects-connection-strings.md` | https://docs.databricks.com/aws/en/oltp/projects/connection-strings |  |  |  |  |  |  |
| 29 | `data/anthropic/home/undated/docs-en-home.md` | https://platform.claude.com/docs/en/home |  |  |  |  |  |  |
| 30 | `data/databricks/error-messages/2026-01/aws-en-error-messages-delta-external-metadata-unsupported-source-error-class.md` | https://docs.databricks.com/aws/en/error-messages/delta-external-metadata-unsupported-source-error-class |  |  |  |  |  |  |
| 31 | `data/anthropic/build-with-claude/undated/docs-en-build-with-claude-multilingual-support.md` | https://platform.claude.com/docs/en/build-with-claude/multilingual-support |  |  |  |  |  |  |
| 32 | `data/databricks/semi-structured/2026-07/aws-en-semi-structured-variant.md` | https://docs.databricks.com/aws/en/semi-structured/variant |  |  |  |  |  |  |
| 33 | `data/databricks/tables/2026-06/aws-en-tables-features-generated-columns.md` | https://docs.databricks.com/aws/en/tables/features/generated-columns |  |  |  |  |  |  |
| 34 | `data/databricks/partners/2023-12/aws-en-partners-ml-john-snow-labs.md` | https://docs.databricks.com/aws/en/partners/ml/john-snow-labs |  |  |  |  |  |  |
| 35 | `data/databricks/notebooks/2026-07/aws-en-notebooks-notebook-export-import.md` | https://docs.databricks.com/aws/en/notebooks/notebook-export-import |  |  |  |  |  |  |
| 36 | `data/databricks/developers/2026-07/aws-en-developers-best-practices.md` | https://docs.databricks.com/aws/en/developers/best-practices |  |  |  |  |  |  |
| 37 | `data/databricks/release-notes/2026-04/aws-en-release-notes-product-2020-december.md` | https://docs.databricks.com/aws/en/release-notes/product/2020/december |  |  |  |  |  |  |
| 38 | `data/databricks/transform/2026-08/aws-en-transform-optimize-joins.md` | https://docs.databricks.com/aws/en/transform/optimize-joins |  |  |  |  |  |  |
| 39 | `data/databricks/dashboards/2026-02/aws-en-dashboards-manage-filters-field-filters.md` | https://docs.databricks.com/aws/en/dashboards/manage/filters/field-filters |  |  |  |  |  |  |
| 40 | `data/databricks/schemas/2026-08/aws-en-schemas-manage-schema.md` | https://docs.databricks.com/aws/en/schemas/manage-schema |  |  |  |  |  |  |
| 41 | `data/databricks/mlflow3/2026-05/aws-en-mlflow3-genai-tracing-integrations.md` | https://docs.databricks.com/aws/en/mlflow3/genai/tracing/integrations/ |  |  |  |  |  |  |
| 42 | `data/databricks/oltp/2026-08/aws-en-oltp-projects-terraform-typical-project.md` | https://docs.databricks.com/aws/en/oltp/projects/terraform-typical-project |  |  |  |  |  |  |
| 43 | `data/databricks/genie-code/2026-08/aws-en-genie-code-use-genie-code.md` | https://docs.databricks.com/aws/en/genie-code/use-genie-code |  |  |  |  |  |  |
| 44 | `data/anthropic/intro/undated/docs-en-intro.md` | https://platform.claude.com/docs/en/intro |  |  |  |  |  |  |
| 45 | `data/databricks/discover/2026-08/aws-en-discover-discover-page.md` | https://docs.databricks.com/aws/en/discover/discover-page |  |  |  |  |  |  |
| 46 | `data/databricks/volumes/2026-04/aws-en-volumes-privileges.md` | https://docs.databricks.com/aws/en/volumes/privileges |  |  |  |  |  |  |
| 47 | `data/databricks/dashboards/2026-08/aws-en-dashboards-manage-visualizations.md` | https://docs.databricks.com/aws/en/dashboards/manage/visualizations/ |  |  |  |  |  |  |
| 48 | `data/anthropic/observability/2025-08/cookbook-observability-usage-cost-api.md` | https://platform.claude.com/cookbook/observability-usage-cost-api |  |  |  |  |  |  |
| 49 | `data/databricks/machine-learning/2026-07/aws-en-machine-learning-model-serving-provider-native-apis.md` | https://docs.databricks.com/aws/en/machine-learning/model-serving/provider-native-apis |  |  |  |  |  |  |
| 50 | `data/anthropic/multimodal/2024-03/cookbook-multimodal-how-to-transcribe-text.md` | https://platform.claude.com/cookbook/multimodal-how-to-transcribe-text |  |  |  |  |  |  |
