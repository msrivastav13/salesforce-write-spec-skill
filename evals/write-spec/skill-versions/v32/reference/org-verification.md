# Verifying claims with read-only org queries

Write each query for the specific claim you need to test. There is no fixed query list: choose checks from what this requirement's design depends on.

## Allowed commands

- `sf org display --json`: parse it and print only `connectedStatus`, `alias`, `id`, and `apiVersion`. Never print the access token.
- `sf sobject describe --sobject <Name> --json` (add `--use-tooling-api` for Tooling objects; describe an object before guessing its column names)
- `sf sobject list --sobject custom --json`
- `sf data query --query "<single SELECT>" --json`, optionally with `--use-tooling-api`

Add `--target-org <alias>` to each command. Nothing else is allowed: no deploy, no retrieve, no DML, no anonymous Apex, no `sf data create/update/delete`. Select only the fields you need. Use `LIMIT` and aggregates (`COUNT`, `GROUP BY`); do not dump record data. Keep query output in memory, or in a scratch file under `design/.tmp/` that you delete afterwards. Pipe `--json` through a short `python3 -c` parser that prints only what matters, and check `status` before you read `result`. Write each command out in full; do not put flags in shell variables (the shell may be zsh, which does not split words).

## What to verify (choose what applies)

- **Existence and exact API names** of every object, field, class, trigger, flow, or permission set that the design reuses, updates, or deletes. Also confirm that anything the design creates does not already exist.
- **Creates of types that cannot be queried** (for example prompt templates): say that a duplicate could not be ruled out.
- **Same concept elsewhere.** Before creating a field or object, search the whole org for one that already means the same thing: Tooling `CustomField WHERE DeveloperName LIKE '%<Concept>%'` (any object), `FieldDefinition` by label, and object names from `sf sobject list --sobject all` filtered by keyword. In Data 360 orgs, filter out data model object fields (`TableEnumOrId` starting `9sd`) locally. Reuse or map to it, or say why not.
- **Field semantics** that change the design: type, required, formula body, roll-up definition, picklist values, and relationship type.
- **Existing automation** on the objects involved (when a check covers only unmanaged components, name the managed automation that exists on the object): triggers, record-triggered flows, and validation rules. Check these before proposing new automation on the same object.
- **Dependencies** before any Update or Delete: what references the component, including other callers of a shared class, flow, or agent action. For a Delete or rename, cover each category (Apex, flows, layouts, FlexiPages, formulas, validation rules, list views, reports, prompt templates, permission sets) and say which ones could not be checked. Reports and list views cannot be read, so add "check reports and list views for the field" as a deployment step (non-blocking).
- **Editability** of every target: managed or namespaced components and platform-owned permission sets (`NamespacePrefix`, `Type`, `IsOwnedByProfile`) cannot be changed. Drop or redirect those changes.
- **Org edition and limits** when the design depends on them: `SELECT OrganizationType, IsSandbox FROM Organization` (`DefaultCurrencyIsoCode` is unavailable in single-currency orgs; a currency field's `describe` shows the currency).
- **Platform support** questions (for example whether `DISTANCE` works on a custom address field) can often be settled with a harmless read-only query that uses the feature.
- **Data shape** behind (`GROUP BY` fails on Number/double fields; use range `COUNT()` queries instead) a filter, threshold, or default: value distribution and null counts.
- **Missed components.** For every candidate object, list its fields with Tooling `CustomField` (describe hides FLS-restricted fields). Scan the full field list of each object involved for fields that match the business concept, and find every creator and reader (`MetadataComponentDependency`, Apex bodies, flows). AskCoworker search can miss them. For UI requirements, also list existing LWC and Aura bundles (Tooling `LightningComponentBundle`, `AuraDefinitionBundle`) and record pages (Tooling `FlexiPage`).
- **Absence claims** ("no automation", "nothing reads X"): check every kind of reference, meaning dependencies, Apex bodies (reads as well as writes), flows, and validation rules. If you did not check, do not make the claim.

## API notes (Salesforce behavior, API v60+)

- `sobject describe` hides fields the running user cannot see (FLS). Tooling `CustomField WHERE TableEnumOrId = '<DurableId>'` is the complete list of custom fields; `FieldDefinition` can also hide fields.
- `sobject describe` gives each field's `type`, `calculated`, `calculatedFormula`, `nillable`, `updateable`, `referenceTo`, `relationshipName`, `cascadeDelete`, `picklistValues`, and the object's `childRelationships`. A calculated field with no `calculatedFormula` is usually a roll-up summary. Its reported precision comes from the summarized field and does not limit the stored value.
- Tooling `CustomField.Metadata` (roll-up operation and filter, `required`, `reparentableMasterDetail`, `deleteConstraint`, `formulaTreatBlanksAs`) can be selected only when the query returns one row. So:
  1. Find the object's `DurableId` from `EntityDefinition`.
  2. Get field IDs from `CustomField WHERE TableEnumOrId = '<DurableId>'`. `DeveloperName` has no `__c`.
  3. Query `Metadata` by `Id`.

  Semi-joins on `TableEnumOrId` are rejected.
- Tooling `ApexTrigger`: `TableEnumOrId` holds the object API name. `Usage*` fields show the trigger events.
- Standard-API `FlowDefinitionView` (not Tooling): `TriggerObjectOrEventId`, `TriggerType`, `RecordTriggerType`, `IsActive`. It does not support `OR`: it returns an empty result without an error, which looks like absence. Use `IN` or separate queries. To read a flow's logic, use Tooling `Flow.Metadata` by the `ActiveVersionId` from `FlowDefinition`.
- Agentforce: `BotDefinition` and `BotVersion` (standard API); Tooling `GenAiPlannerDefinition`, `GenAiPluginDefinition` (topics), `GenAiFunctionDefinition` (actions; `InvocationTarget` is an ID-type field: filter with `=` or `IN` on the class Id, not `LIKE`), and the link tables `GenAiPlannerFunctionDef`, `GenAiPluginFunctionDef`, `GenAiPluginInstructionDef`.
- Picklist values: the value set (`describe` `picklistValues`, or for Case status `CaseStatus`) is the truth. A value that appears only in record data is a deleted or off-list value, not an inactive one.
- History tracking: `FieldDefinition.IsFieldHistoryTracked`; history rows in `<Object>__History` (custom) or `<Object>History` (standard).
- Licenses, add-ons, and generative AI feature enablement (for example Field Audit Trail, Shield, or Prompt Builder) cannot be confirmed with the allowed commands. A change that needs one is `Conditional:` on the license.
- Org-wide email addresses and email deliverability are setup, not deployable metadata: `OrgWideEmailAddress` shows what exists.
- Credentials: Tooling `NamedCredential` and Tooling `ExternalCredential` (`DeveloperName`). Data 360: `SELECT COUNT() FROM DataStream` (standard API). Standard data model objects (for example `ssot__Individual__dlm`) exist as `__dlm` sObjects only after they are provisioned or mapped; if `sf sobject list` does not show one, it does not exist yet.
- A managed class whose name matches the object (for example `CaseRule`) is package code: check `NamespacePrefix` before treating it as a finding.
- `ApexCodeCoverageAggregate` with 0 covered lines usually means tests have not been run in the org, not that the code is untested.
- `ApexClass.IsValid = false` only means the class needs recompiling; it is not evidence that the class is broken.
- Apex source: Tooling `SELECT Name, Body FROM ApexClass WHERE Name IN (...)`, then search the body locally.
- Reports and dashboards: standard-API `Report` and `Dashboard` (`DeveloperName`, `FolderName`) for name checks. Custom report types cannot be listed with the allowed commands. Standard report types already include fields from lookup parents, so prefer them.
- Duplicate rules: standard-API `DuplicateRule` (`DeveloperName`, `SobjectType`, `IsActive`).
- Approval processes and legacy workflow: standard-API `ProcessDefinition WHERE TableEnumOrId = '<Object>'`; Tooling `WorkflowRule WHERE TableEnumOrId = '<Object>'`.
- Routing and assignment requirements: also check Omni-Channel routing flows (`FlowDefinitionView WHERE ProcessType = 'RoutingFlow'`) and `ServiceChannel` before designing custom assignment.
- Assignment rules: standard-API `AssignmentRule` (`Name`, `Active`, `SobjectType`) lists the rules; their entries cannot be read.
- Business days: `BusinessHours` (`IsDefault`, and day start and end times, where 00:00–00:00 means 24 hours) and `Holiday`.
- Org settings that have a metadata form (for example `LeadConvertSettings`, `AccountSettings`) are Update rows of that Settings type. Make them `Conditional:` when the current value cannot be read.
- Record pages: Tooling `FlexiPage.Metadata` is readable by `Id` (regions, components, Dynamic Forms fields); activation and assignment are not.
- Tabs: standard-API `TabDefinition WHERE SobjectName = '<Object>'`.
- Object settings (for example Allow Reports) are often not readable with the allowed commands. Record them as assumptions.
- Tooling `ValidationRule`: filter on `EntityDefinitionId = '<DurableId>'`. `ErrorConditionFormula` and `Metadata` can be selected only one rule at a time, by `Id`.
- Tooling `MetadataComponentDependency`: `WHERE RefMetadataComponentId = '<Id>'` lists the components that reference a custom object or field. The Id is the object's `EntityDefinition.DurableId` (`01I…`) or the field's `CustomField.Id`. Filtering by name is not supported. If an 18-character ID returns no rows, retry with its first 15 characters. It often misses field references inside Apex, so always search Apex bodies as well.
- `ObjectPermissions` and `FieldPermissions` (standard API): filter on `SobjectType` or `Field`. `Parent.IsOwnedByProfile` separates profiles from permission sets. No row means that permission set or profile grants nothing; check profile rows too. View All Data and Modify All Data do not override field-level security. Deploying a new field grants no field access to any profile or permission set that is not part of the deployment.
- Formula results for edge cases (for example, divide by zero) come from querying the formula field on records that have that case.

Some metadata (for example Data 360 definitions, report and list view columns, assignment and escalation rule entries, record page activation, org settings) cannot be read with the allowed commands. Record type names and paths as assumptions, and list any unreadable automation that could interfere with the design as a risk in Section 8. When the natural design extends an unreadable component (for example an assignment rule), weigh extending it, with "retrieve before editing" as a deployment step, against building a separate component, and record why.

If a query fails, record the check as not verified. Do not retry it with guessed field names more than once.
