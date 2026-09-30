# Verifying claims with read-only org queries

Write each query for the specific claim you need to test. There is no fixed query list: choose checks from what this requirement's design depends on.

## Allowed commands

- `sf org display --json`
- `sf sobject describe --sobject <Name> --json`
- `sf sobject list --sobject custom --json`
- `sf data query --query "<single SELECT>" --json`, optionally with `--use-tooling-api`

Add `--target-org <alias>` to each command. Nothing else is allowed: no deploy, no retrieve, no DML, no anonymous Apex, no `sf data create/update/delete`. Select only the fields you need. Use `LIMIT` and aggregates (`COUNT`, `GROUP BY`); do not dump record data. Pipe `--json` through a short `python3 -c` parser that prints only what matters, and check `status` before you read `result`. Write each command out in full; do not put flags in shell variables (the shell may be zsh, which does not split words).

## What to verify (choose what applies)

- **Existence and exact API names** of every object, field, class, trigger, flow, or permission set that the design reuses, updates, or deletes. Also confirm that anything the design creates does not already exist.
- **Same concept elsewhere.** Before creating a field or object, search the whole org for one that already means the same thing: Tooling `CustomField WHERE DeveloperName LIKE '%<Concept>%'` (any object), `FieldDefinition` by label, and object names from `sf sobject list --sobject all` filtered by keyword. Reuse or map to it, or say why not.
- **Field semantics** that change the design: type, required, formula body, roll-up definition, picklist values, and relationship type.
- **Existing automation** on the objects involved: triggers, record-triggered flows, and validation rules. Check these before proposing new automation on the same object.
- **Dependencies** before any Update or Delete: what references the component, including other callers of a shared class, flow, or agent action. For a Delete or rename, cover each category (Apex, flows, layouts, FlexiPages, formulas, validation rules, list views, reports, prompt templates, permission sets) and say which ones could not be checked.
- **Editability** of every target: managed or namespaced components and platform-owned permission sets (`NamespacePrefix`, `Type`, `IsOwnedByProfile`) cannot be changed. Drop or redirect those changes.
- **Org edition and limits** when the design depends on them: `SELECT OrganizationType, IsSandbox FROM Organization`.
- **Data shape** behind a filter, threshold, or default: value distribution and null counts.
- **Missed components.** Scan the full field list of each object involved for fields that match the business concept, and find every creator and reader (`MetadataComponentDependency`, Apex bodies, flows). AskCoworker search can miss them.
- **Absence claims** ("no automation", "nothing reads X"): check every kind of reference, meaning dependencies, Apex bodies (reads as well as writes), flows, and validation rules. If you did not check, do not make the claim.

## API notes (Salesforce behavior, API v60+)

- `sobject describe` hides fields the running user cannot see (FLS). Cross-check the field list with Tooling `CustomField WHERE TableEnumOrId = '<DurableId>'` or `FieldDefinition WHERE EntityDefinition.QualifiedApiName = '<Object>'`.
- `sobject describe` gives each field's `type`, `calculated`, `calculatedFormula`, `nillable`, `updateable`, `referenceTo`, `relationshipName`, `cascadeDelete`, `picklistValues`, and the object's `childRelationships`. A calculated field with no `calculatedFormula` is usually a roll-up summary. Its reported precision comes from the summarized field and does not limit the stored value.
- Tooling `CustomField.Metadata` (roll-up operation and filter, `required`, `reparentableMasterDetail`, `deleteConstraint`, `formulaTreatBlanksAs`) can be selected only when the query returns one row. So:
  1. Find the object's `DurableId` from `EntityDefinition`.
  2. Get field IDs from `CustomField WHERE TableEnumOrId = '<DurableId>'`. `DeveloperName` has no `__c`.
  3. Query `Metadata` by `Id`.

  Semi-joins on `TableEnumOrId` are rejected.
- Tooling `ApexTrigger`: `TableEnumOrId` holds the object API name. `Usage*` fields show the trigger events.
- Standard-API `FlowDefinitionView` (not Tooling): `TriggerObjectOrEventId`, `TriggerType`, `RecordTriggerType`, `IsActive`. It does not support `OR`; use `IN` or separate queries. To read a flow's logic, use Tooling `Flow.Metadata` by the `ActiveVersionId` from `FlowDefinition`.
- Agentforce: `BotDefinition` and `BotVersion` (standard API); Tooling `GenAiPlannerDefinition`, `GenAiPluginDefinition` (topics), `GenAiFunctionDefinition` (actions; `InvocationTarget`), and the link tables `GenAiPlannerFunctionDef`, `GenAiPluginFunctionDef`, `GenAiPluginInstructionDef`.
- History tracking: `FieldDefinition.IsFieldHistoryTracked`; history rows in `<Object>__History` (custom) or `<Object>History` (standard).
- Licenses and add-ons (for example Field Audit Trail or Shield) cannot be confirmed with the allowed commands. A change that needs one is `Conditional:` on the license.
- Credentials: Tooling `NamedCredential` and Tooling `ExternalCredential` (`DeveloperName`). Data 360: `SELECT COUNT() FROM DataStream` (standard API).
- Apex source: Tooling `SELECT Name, Body FROM ApexClass WHERE Name IN (...)`, then search the body locally.
- Object settings (for example Allow Reports): Tooling `CustomObject.Metadata`, queried by `Id` so the query returns one row.
- Tooling `ValidationRule`: filter on `EntityDefinitionId = '<DurableId>'`.
- Tooling `MetadataComponentDependency`: `WHERE RefMetadataComponentId = '<Id>'` lists the components that reference a custom object or field. The Id is the object's `EntityDefinition.DurableId` (`01I…`) or the field's `CustomField.Id`. Filtering by name is not supported. If an 18-character ID returns no rows, retry with its first 15 characters. It often misses field references inside Apex, so always search Apex bodies as well.
- `ObjectPermissions` and `FieldPermissions` (standard API): filter on `SobjectType` or `Field`. `Parent.IsOwnedByProfile` separates profiles from permission sets.
- Formula results for edge cases (for example, divide by zero) come from querying the formula field on records that have that case.

Some metadata (for example Data 360 definitions, report and list view columns, assignment and escalation rule entries) cannot be read with the allowed commands. Record type names and paths as assumptions, and list any unreadable automation that could interfere with the design as a risk in Section 8.

If a query fails, record the check as not verified. Do not retry it with guessed field names more than once.
